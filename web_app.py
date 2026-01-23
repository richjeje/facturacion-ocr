from fastapi import (
    FastAPI,
    File,
    UploadFile,
    Depends,
    HTTPException,
    status,
    Header,
    WebSocket,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.websockets import WebSocketDisconnect
import uvicorn
import os
import json
from typing import List, Dict, Any
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import jwt
from passlib.context import CryptContext
import shutil
from tasks import process_file_task

# Config DB Neon PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@host/db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)


class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    client_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    fecha = Column(String)
    proveedor = Column(String)
    concepto = Column(String)
    folio = Column(String)
    subtotal = Column(Float)
    iva = Column(Float)
    total = Column(Float)
    metodo_extraccion = Column(String)
    confianza_proveedor = Column(Float)
    url = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

# Auth
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
security = HTTPBearer()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_api_key(x_api_key: str = Header(None), db: SessionLocal = Depends(get_db)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    key = db.query(APIKey).filter(APIKey.key == x_api_key).first()
    if not key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key.client_name


@app.post("/login")
def login(username: str, password: str, db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode({"sub": username}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("templates/index.html", "r") as f:
        return f.read()


@app.post("/api/upload")
@limiter.limit("100/minute")
def api_upload_file(
    file: UploadFile = File(...), client: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    # Sanitize filename
    import re
    safe_filename = re.sub(r'[^\w\.-]', '_', file.filename)
    if len(safe_filename) > 100:
        safe_filename = safe_filename[:100]

    # Log API call
    import logging
    logging.info(f"API upload from client: {client}, file: {safe_filename}")

    # Save file temporarily
    temp_path = f"temp_{safe_filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Submit to Celery
    task = process_file_task.delay(temp_path, file.filename, client)
    return {
        "status": "queued",
        "task_id": task.id,
        "message": "Factura en cola para procesamiento",
        "metadata": {"client": client, "timestamp": datetime.utcnow().isoformat()},
    }


@app.get("/api/status/{task_id}")
def api_get_status(task_id: str, client: str = Depends(verify_api_key)):
    from tasks import celery_app

    result = celery_app.AsyncResult(task_id)
    if result.state == "PENDING":
        return {"status": "pending", "task_id": task_id, "metadata": {"client": client}}
    elif result.state == "SUCCESS":
        return {
            "status": "completed",
            "task_id": task_id,
            "data": result.result,
            "metadata": {"client": client},
        }
    else:
        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(result.info),
            "metadata": {"client": client},
        }


@app.get("/api/results")
@limiter.limit("200/minute")
def api_get_results(
    client: str = Depends(verify_api_key), db: SessionLocal = Depends(get_db)
) -> Dict[str, Any]:
    invoices = db.query(Invoice).all()
    return {
        "status": "success",
        "data": [
            {
                "id": i.id,
                "fecha": i.fecha,
                "proveedor": i.proveedor,
                "total": i.total,
                "folio": i.folio,
            }
            for i in invoices
        ],
        "metadata": {"client": client, "count": len(invoices)},
    }


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    username: str = Depends(verify_token), db: SessionLocal = Depends(get_db)
):
    invoices = db.query(Invoice).all()
    # Generate Plotly charts
    import plotly.graph_objects as go
    from plotly.utils import PlotlyJSONEncoder
    import json

    # Gastos por proveedor
    proveedores = {}
    for inv in invoices:
        proveedores[inv.proveedor] = proveedores.get(inv.proveedor, 0) + inv.total
    fig1 = go.Figure(
        data=[go.Bar(x=list(proveedores.keys()), y=list(proveedores.values()))]
    )
    fig1.update_layout(title="Gastos por Proveedor")

    # Errores por tipo (simulado, ya que no hay campo error, usar confianza baja)
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

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <h1>Dashboard de Facturas</h1>
        <div id="chart1"></div>
        <div id="chart2"></div>
        <form id="filter-form">
            <label>Fecha Inicio: <input type="date" id="start-date"></label>
            <label>Fecha Fin: <input type="date" id="end-date"></label>
            <button type="submit">Filtrar</button>
        </form>
        <button onclick="exportPDF()">Exportar PDF</button>
        <script>
            Plotly.newPlot('chart1', {charts["gastos"]});
            Plotly.newPlot('chart2', {charts["errores"]});

            const ws = new WebSocket('ws://localhost:8000/ws');
            ws.onmessage = function(event) {{
                const data = JSON.parse(event.data);
                // Update charts
                console.log('Update:', data);
            }};
        </script>
    </body>
    </html>
    """
    return html


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.receive_text()
            # Simulate real-time update
            await websocket.send_text(json.dumps({"update": "new_invoice"}))
    except WebSocketDisconnect:
        pass


@app.get("/export/pdf")
def export_pdf(
    username: str = Depends(verify_token), db: SessionLocal = Depends(get_db)
):
    from reportlab.pdfgen import canvas
    from io import BytesIO

    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "Reporte de Facturas")
    invoices = db.query(Invoice).all()
    y = 700
    for inv in invoices[:10]:  # Limit to 10
        c.drawString(100, y, f"{inv.fecha} - {inv.proveedor} - {inv.total}")
        y -= 20
    c.save()

    buffer.seek(0)
    return FileResponse(buffer, media_type="application/pdf", filename="reporte.pdf")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
