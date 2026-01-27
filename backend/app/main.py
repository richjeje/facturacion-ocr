from fastapi import (
    FastAPI,
    File,
    UploadFile,
    Depends,
    HTTPException,
    status,
    Header,
    WebSocket,
    Request,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import Response, StreamingResponse, HTMLResponse
from fastapi.websockets import WebSocketDisconnect
import uvicorn
import os
import json
import shutil
import redis
import sentry_sdk
from datetime import datetime
from typing import List, Dict, Any
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.core.database import Base, SessionLocal, engine
from backend.core.models import User, APIKey, Invoice
from backend.worker.tasks import process_file_task

# Auth
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
security = HTTPBearer()

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), traces_sample_rate=1.0)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.on_event("startup")
def _startup_create_tables() -> None:
    Base.metadata.create_all(bind=engine)

# Redis for caching
_redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(_redis_url, decode_responses=True)

# Path setup
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_STATIC_DIR = os.path.join(_BASE_DIR, "frontend", "static")
_TEMPLATES_DIR = os.path.join(_BASE_DIR, "frontend", "templates")

app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
templates = Jinja2Templates(directory=_TEMPLATES_DIR)


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


def verify_api_key(x_api_key: str = Header(None), db: Session = Depends(get_db)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    key = db.query(APIKey).filter(APIKey.key == x_api_key).first()
    if not key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key.client_name


@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, str(user.hashed_password)):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode({"sub": username}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "username": username})


@app.post("/api/upload")
@limiter.limit("100/minute")
def api_upload_file(
    request: Request, file: UploadFile = File(...), client: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    import re
    _filename: str = str(file.filename or "unknown")
    safe_filename = re.sub(r'[^\w\.-]', '_', _filename)
    if len(safe_filename) > 100:
        safe_filename = safe_filename[:100]

    temp_path = f"temp_{safe_filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    task = process_file_task.delay(temp_path, _filename, client)
    return {
        "status": "queued",
        "task_id": task.id,
        "message": "Factura en cola",
        "metadata": {"client": client, "timestamp": datetime.utcnow().isoformat()},
    }


@app.get("/api/status/{task_id}")
def api_get_status(task_id: str, client: str = Depends(verify_api_key)):
    from backend.worker.tasks import celery_app
    result = celery_app.AsyncResult(task_id)
    return {
        "status": result.state.lower(),
        "task_id": task_id,
        "result": result.result if result.state == "SUCCESS" else None,
        "metadata": {"client": client}
    }


@app.get("/api/results")
@limiter.limit("200/minute")
def api_get_results(
    request: Request,
    client: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Dict[str, Any]:
    invoices = db.query(Invoice).offset(skip).limit(limit).all()
    total_count = db.query(Invoice).count()
    return {
        "status": "success",
        "data": [
            {"id": i.id, "fecha": i.fecha, "proveedor": i.proveedor, "total": i.total, "folio": i.folio}
            for i in invoices
        ],
        "metadata": {"client": client, "total": total_count, "skip": skip, "limit": limit},
    }


@app.get("/api/notifications")
def get_notifications():
    return [
        {"title": "Sistema Listo", "message": "El motor OCR está activo.", "created_at": datetime.utcnow().isoformat()},
    ]


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.receive_text()
            await websocket.send_text(json.dumps({"update": "new_invoice"}))
    except WebSocketDisconnect:
        pass


@app.get("/export/pdf")
def export_pdf(username: str = Depends(verify_token), db: Session = Depends(get_db)):
    from reportlab.pdfgen import canvas
    from io import BytesIO
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "Reporte de Facturas")
    invoices = db.query(Invoice).all()
    y = 700
    for inv in invoices[:10]:
        c.drawString(100, y, f"{inv.fecha} - {inv.proveedor} - {inv.total}")
        y -= 20
    c.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=reporte.pdf"})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
