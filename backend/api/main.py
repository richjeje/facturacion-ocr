"""FastAPI application — punto de entrada de la API Web.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional

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
    Request,
    UploadFile,
    WebSocket,
    status,
)
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocketDisconnect
from passlib.context import CryptContext
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from backend.core.config import setup_logging
from backend.core.database import Base, SessionLocal, engine
from backend.core.all_models import APIKey, Invoice, User
from backend.worker.tasks import process_file_task

# Import routers from backend.app
from backend.app.csf_routes import router as csf_router
from backend.app.csf_profile_routes import router as csf_profile_router
from backend.app.cfdi_routes import router as cfdi_router

# ---------------------------------------------------------------------------
# Inicialización
# ---------------------------------------------------------------------------
setup_logging()
logger = logging.getLogger(__name__)

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN", ""), traces_sample_rate=1.0)

# Auth
_SECRET_KEY = os.environ.get("SECRET_KEY", "mistica_super_secret_key_2024")
_ALGORITHM = "HS256"
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_security = HTTPBearer(auto_error=False)

# Rate limiting
_limiter = Limiter(key_func=get_remote_address)

# Redis
_redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis_client = redis.Redis.from_url(_redis_url, decode_responses=True)

# Rutas de frontend (relativas al repositorio)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_STATIC_DIR = os.path.abspath(os.path.join(_BASE_DIR, "..", "..", "frontend", "static"))
_TEMPLATES_DIR = os.path.abspath(os.path.join(_BASE_DIR, "..", "..", "frontend", "templates"))

# Templates
templates = Jinja2Templates(directory=_TEMPLATES_DIR)

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
# app.add_middleware(SlowAPIMiddleware)

if os.path.exists(_STATIC_DIR):
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

# Incluir routers
app.include_router(csf_router)
app.include_router(csf_profile_router)
app.include_router(cfdi_router)

@app.on_event("startup")
def _startup_create_tables() -> None:
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


def get_current_client_name(
    x_api_key: str = Header(None),
    auth: Optional[HTTPAuthorizationCredentials] = Depends(_security),
    db: Session = Depends(get_db)
) -> str:
    """Consolidated client identification via API Key or JWT."""
    if x_api_key:
        key = db.query(APIKey).filter(APIKey.key == x_api_key).first()
        if key: return key.client_name
    
    if auth:
        try:
            payload = jwt.decode(auth.credentials, _SECRET_KEY, algorithms=[_ALGORITHM])
            return payload.get("sub", "unknown")
        except:
            pass
    
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticación requerida")


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@app.post("/login", summary="Obtener token JWT")
def login(
    username: str, password: str, db: Session = Depends(get_db)
) -> Dict[str, str]:
    user = db.query(User).filter(User.username == username).first()
    if not user or not _pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = jwt.encode({"sub": username}, _SECRET_KEY, algorithm=_ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/logout")
def logout():
    return {"message": "Sesión cerrada"}

@app.post("/api/register/cliente")
def register_cliente(username: str, email: str, password: str, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    
    new_user = User(
        username=username,
        email=email,
        hashed_password=_pwd_context.hash(password),
        role="cliente",
        status="active"
    )
    db.add(new_user)
    db.commit()
    return {"message": "Registro exitoso"}

@app.post("/api/register/negocio")
def register_negocio(username: str, email: str, business_name: str, rfc: str, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    
    new_user = User(
        username=username,
        email=email,
        # Default password is "temp" or something, needs approval
        hashed_password=_pwd_context.hash("temp"), 
        role="negocio",
        status="pending_approval",
        fullname=business_name # Or something similar
    )
    db.add(new_user)
    db.commit()
    return {"message": "Solicitud enviada, pendiente de aprobación"}


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse, include_in_schema=False)
def read_signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse, summary="Dashboard de reportes")
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
@app.post("/api/upload", summary="Subir factura para procesamiento asíncrono")
def api_upload_file(
    request: Request,
    file: UploadFile = File(...),
    client: str = Depends(get_current_client_name),
) -> Dict[str, Any]:
    safe_filename = re.sub(r"[^\w.\-]", "_", file.filename or "upload")
    if len(safe_filename) > 100:
        safe_filename = safe_filename[:100]

    logger.info("API upload — cliente: %s, archivo: %s", client, safe_filename)

    temp_path = os.path.join(os.getcwd(), f"temp_{safe_filename}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    task = process_file_task.delay(temp_path, file.filename, client)
    return {
        "status": "queued",
        "task_id": task.id,
        "message": "Factura en cola para procesamiento",
        "metadata": {"client": client, "timestamp": datetime.utcnow().isoformat()},
    }


@app.get("/api/results", summary="Listar facturas procesadas")
def api_get_results(
    request: Request,
    client: str = Depends(get_current_client_name),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    invoices = db.query(Invoice).all()
    return {
        "status": "success",
        "metadata": {"client": client, "count": len(invoices)},
        "data": [
            {
                "id": inv.id,
                "fecha": inv.issued_date,
                "proveedor": inv.supplier_name,
                "total": inv.total,
                "folio": inv.invoice_number,
            }
            for inv in invoices
        ],
    }

@app.get("/api/dashboard/stats")
def dashboard_stats(
    username: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    import plotly.graph_objects as go
    from plotly.utils import PlotlyJSONEncoder

    invoices = (
        db.query(Invoice).order_by(Invoice.issued_date.desc()).limit(100).all()
    )

    proveedores: Dict[str, float] = {}
    for inv in invoices:
        proveedores[inv.supplier_name] = proveedores.get(inv.supplier_name, 0) + inv.total

    fig1 = go.Figure(
        data=[go.Bar(x=list(proveedores.keys()), y=list(proveedores.values()))]
    )
    fig1.update_layout(title="Gastos por Proveedor")

    errores = sum(1 for inv in invoices if (inv.supplier_confidence or 0) < 70)
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
        "gastos": json.loads(json.dumps(fig1, cls=PlotlyJSONEncoder)),
        "errores": json.loads(json.dumps(fig2, cls=PlotlyJSONEncoder)),
    }
    return charts


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
    db: Session = Depends(get_db),
) -> StreamingResponse:
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "Reporte de Facturas")
    invoices = db.query(Invoice).all()
    y = 700
    for inv in invoices[:10]:
        c.drawString(100, y, f"{inv.issued_date} — {inv.supplier_name} — {inv.total}")
        y -= 20
    c.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=reporte.pdf"})


# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
