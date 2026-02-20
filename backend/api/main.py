"""FastAPI application — punto de entrada de la API Web.

Arranca con:
    uvicorn backend.api.main:app --reload
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
from datetime import datetime
from io import BytesIO
from typing import Any, Dict

import jwt
import redis
import sentry_sdk
import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    UploadFile,
    WebSocket,
    status,
)
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocketDisconnect
from passlib.context import CryptContext
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from backend.core.config import setup_logging
from backend.core.database import Base, SessionLocal, engine
from backend.core.models import APIKey, Invoice, User
from backend.worker.tasks import process_file_task

# ---------------------------------------------------------------------------
# Inicialización
# ---------------------------------------------------------------------------
setup_logging()
logger = logging.getLogger(__name__)

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN", ""), traces_sample_rate=1.0)

# Auth
_SECRET_KEY = os.environ["SECRET_KEY"]  # Falla rápido si no está configurado
_ALGORITHM = "HS256"
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_security = HTTPBearer()

# Rate limiting
_limiter = Limiter(key_func=get_remote_address)

# Redis
_redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis_client = redis.Redis.from_url(_redis_url, decode_responses=True)

# Rutas de frontend (relativas al repositorio)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_STATIC_DIR = os.path.join(_BASE_DIR, "..", "..", "frontend", "static")
_TEMPLATES_DIR = os.path.join(_BASE_DIR, "..", "..", "frontend", "templates")

# ---------------------------------------------------------------------------
# Aplicación
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Facturación OCR API",
    description="API para automatizar la extracción de datos de facturas mexicanas.",
    version="1.0.0",
)
app.state.limiter = _limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


@app.on_event("startup")
def _startup_create_tables() -> None:
    # En producción preferir migraciones con Alembic.
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Dependencias
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> str:
    try:
        payload = jwt.decode(
            credentials.credentials, _SECRET_KEY, algorithms=[_ALGORITHM]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


def verify_api_key(
    x_api_key: str = Header(None), db: SessionLocal = Depends(get_db)
) -> str:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Se requiere API key")
    key = db.query(APIKey).filter(APIKey.key == x_api_key).first()
    if not key:
        raise HTTPException(status_code=401, detail="API key inválida")
    return key.client_name


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@app.post("/login", summary="Obtener token JWT")
def login(
    username: str, password: str, db: SessionLocal = Depends(get_db)
) -> Dict[str, str]:
    user = db.query(User).filter(User.username == username).first()
    if not user or not _pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = jwt.encode({"sub": username}, _SECRET_KEY, algorithm=_ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def read_root() -> str:
    index_path = os.path.join(_TEMPLATES_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
@app.post("/api/upload", summary="Subir factura para procesamiento asíncrono")
@_limiter.limit("100/minute")
def api_upload_file(
    file: UploadFile = File(...),
    client: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    safe_filename = re.sub(r"[^\w.\-]", "_", file.filename or "upload")
    if len(safe_filename) > 100:
        safe_filename = safe_filename[:100]

    logger.info("API upload — cliente: %s, archivo: %s", client, safe_filename)

    temp_path = f"temp_{safe_filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    task = process_file_task.delay(temp_path, file.filename, client)
    return {
        "status": "queued",
        "task_id": task.id,
        "message": "Factura en cola para procesamiento",
        "metadata": {"client": client, "timestamp": datetime.utcnow().isoformat()},
    }


@app.get("/api/status/{task_id}", summary="Consultar estado de una tarea")
def api_get_status(
    task_id: str, client: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.worker.tasks import celery_app

    result = celery_app.AsyncResult(task_id)
    base = {"task_id": task_id, "metadata": {"client": client}}
    if result.state == "PENDING":
        return {**base, "status": "pending"}
    if result.state == "SUCCESS":
        return {**base, "status": "completed", "data": result.result}
    return {**base, "status": "failed", "error": str(result.info)}


@app.get("/api/results", summary="Listar facturas procesadas")
@_limiter.limit("200/minute")
def api_get_results(
    client: str = Depends(verify_api_key),
    db: SessionLocal = Depends(get_db),
) -> Dict[str, Any]:
    invoices = db.query(Invoice).all()
    return {
        "status": "success",
        "metadata": {"client": client, "count": len(invoices)},
        "data": [
            {
                "id": inv.id,
                "fecha": inv.fecha,
                "proveedor": inv.proveedor,
                "total": inv.total,
                "folio": inv.folio,
            }
            for inv in invoices
        ],
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.get("/dashboard", response_class=HTMLResponse, summary="Dashboard de reportes")
def dashboard(
    username: str = Depends(verify_token),
    db: SessionLocal = Depends(get_db),
) -> str:
    cache_key = "dashboard_data"
    cached = _redis_client.get(cache_key)
    if cached:
        charts = json.loads(cached)
    else:
        import plotly.graph_objects as go
        from plotly.utils import PlotlyJSONEncoder

        invoices = (
            db.query(Invoice).order_by(Invoice.fecha.desc()).limit(100).all()
        )

        proveedores: Dict[str, float] = {}
        for inv in invoices:
            proveedores[inv.proveedor] = proveedores.get(inv.proveedor, 0) + inv.total

        fig1 = go.Figure(
            data=[go.Bar(x=list(proveedores.keys()), y=list(proveedores.values()))]
        )
        fig1.update_layout(title="Gastos por Proveedor")

        errores = sum(1 for inv in invoices if inv.confianza_proveedor < 70)
        fig2 = go.Figure(
            data=[
                go.Pie(
                    labels=["Exitosos", "Errores"],
                    values=[len(invoices) - errores, errores],
                )
            ]
        )
        fig2.update_layout(title="Facturas Procesadas")

        charts = {
            "gastos": json.dumps(fig1, cls=PlotlyJSONEncoder),
            "errores": json.dumps(fig2, cls=PlotlyJSONEncoder),
        }
        _redis_client.setex(cache_key, 300, json.dumps(charts))

    dashboard_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Dashboard — Facturación OCR</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>Dashboard de Facturas</h1>
    <div id="chart-gastos"></div>
    <div id="chart-estado"></div>
    <form id="filter-form">
        <label>Fecha Inicio: <input type="date" id="start-date"></label>
        <label>Fecha Fin: <input type="date" id="end-date"></label>
        <button type="submit">Filtrar</button>
    </form>
    <button onclick="window.location='/export/pdf'">Exportar PDF</button>
    <script>
        Plotly.newPlot('chart-gastos', {charts["gastos"]});
        Plotly.newPlot('chart-estado', {charts["errores"]});
        const ws = new WebSocket('ws://' + location.host + '/ws');
        ws.onmessage = (event) => console.log('WS update:', JSON.parse(event.data));
    </script>
</body>
</html>"""
    return dashboard_html


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            await websocket.receive_text()
            await websocket.send_text(json.dumps({"update": "new_invoice"}))
    except WebSocketDisconnect:
        pass


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
@app.get("/export/pdf", summary="Exportar reporte en PDF")
def export_pdf(
    username: str = Depends(verify_token),
    db: SessionLocal = Depends(get_db),
) -> FileResponse:
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "Reporte de Facturas")
    invoices = db.query(Invoice).all()
    y = 700
    for inv in invoices[:10]:
        c.drawString(100, y, f"{inv.fecha} — {inv.proveedor} — {inv.total}")
        y -= 20
    c.save()
    buffer.seek(0)
    return FileResponse(buffer, media_type="application/pdf", filename="reporte.pdf")


# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
