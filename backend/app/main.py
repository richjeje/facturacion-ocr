from fastapi import (
    FastAPI,
    File,
    UploadFile,
    Depends,
    HTTPException,
    status,
    Header,
    Request,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import Response, StreamingResponse, HTMLResponse
from fastapi.websockets import WebSocket, WebSocketDisconnect
import uvicorn
import os
import json
import shutil
import redis
from datetime import datetime
from typing import List, Dict, Any, Optional
import sentry_sdk
from datetime import datetime
from typing import List, Dict, Any
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

import sys
import os
# Add backend directory to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from core.database import Base, SessionLocal, engine
from core.all_models import (
    User, APIKey, Invoice, CFDICertificate, CFDIInvoice, 
    CFDICatalog, CFDISettings
)
from worker.tasks import process_file_task
from app.auth import get_current_user

# Auth
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), traces_sample_rate=1.0)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.on_event("startup")
def _startup_create_tables() -> None:
    # Importar todos los modelos para crear tablas
    from core.all_models import (
        User, APIKey, Invoice, CFDICertificate, CFDIInvoice, 
        CFDICatalog, CFDISettings, CSFDocument, CSFProfileHistory,
        CSFRecord, CSFValidationCache, CSFHistory
    )
    
    # Crear todas las tablas con manejo de errores
    models_to_create = [
        User, APIKey, Invoice,
        CFDICertificate, CFDIInvoice, CFDICatalog, CFDISettings,
        CSFDocument, CSFProfileHistory, CSFRecord, CSFValidationCache, CSFHistory
    ]
    
    for model in models_to_create:
        try:
            model.metadata.create_all(bind=engine)
            print(f"✓ Created table for {model.__name__}")
        except Exception as e:
            print(f"Warning: Could not create table for {model.__name__}: {e}")
    
    # Create fictitious users
    db = SessionLocal()
    try:
        # Create Admin
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            db.add(User(
                username="admin",
                email="admin@mistica.com",
                hashed_password=pwd_context.hash("admin123"),
                role="admin",
                status="active"
            ))
            db.commit()
            print("User 'admin' created.")

        # Create fictitious 'Vanta' business user if not exists
        vanta = db.query(User).filter(User.username == "vanta").first()
        if not vanta:
            hashed_pw = pwd_context.hash("1234")
            new_vanta = User(
                username="vanta",
                email="vanta@negocio.com",
                hashed_password=hashed_pw,
                role="negocio",
                status="active",
                business_name="Vanta",
                owner_name="Vanta Owner"
            )
            db.add(new_vanta)
            db.commit()
            print("User 'vanta' created.")
    finally:
        db.close()

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


def verify_token(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials if credentials else None
    
    # Fallback to cookie if header is missing
    if not token:
        token = request.cookies.get("access_token")
        
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_api_key_or_token(
    x_api_key: Optional[str] = Header(None), 
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Try API Key first
    if x_api_key:
        key = db.query(APIKey).filter(APIKey.key == x_api_key).first()
        if key:
            return key.client_name
    
    # Try JWT Token
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username:
            user = db.query(User).filter(User.username == username).first()
            if user:
                return user.business_name or user.username
    except Exception:
        pass
        
    raise HTTPException(status_code=401, detail="Valid API Key or Token required")


@app.post("/login")
def login(response: Response, username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, str(user.hashed_password)):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user.status and user.status == "pending_approval":
        raise HTTPException(status_code=403, detail="Cuenta pendiente de aprobación")
        
    token = jwt.encode({"sub": username, "role": user.role}, SECRET_KEY, algorithm=ALGORITHM)
    
    # Set cookie for browser sessions
    response.set_cookie(
        key="access_token", 
        value=token, 
        httponly=True, 
        max_age=86400, # 1 day
        samesite="lax"
    )
    
    return {"access_token": token, "token_type": "bearer", "role": user.role}


@app.post("/api/register/cliente")
def register_cliente(username: str, email: str, password: str, db: Session = Depends(get_db)):
    existing = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Usuario o email ya existe")
    
    new_user = User(
        username=username,
        email=email,
        hashed_password=pwd_context.hash(password),
        role="cliente",
        status="active"
    )
    db.add(new_user)
    db.commit()
    return {"message": "Cliente registrado exitosamente"}


@app.post("/api/register/negocio")
def register_negocio(username: str, email: str, business_name: str, rfc: str, db: Session = Depends(get_db)):
    existing = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Usuario o email ya existe")
    
    # Note: Password will be created by admin as per instructions (admin approves and assigns)
    # However, for the initial step, we might want to let them set a password or generate one.
    # Instruction says: "la creara admin". So we might not need password in this step.
    # But User model needs hashed_password. I'll put a dummy one or handle it.
    
    new_user = User(
        username=username,
        email=email,
        business_name=business_name,
        business_rfc=rfc,
        role="negocio",
        status="pending_approval",
        hashed_password=pwd_context.hash("pending") # Placeholder
    )
    db.add(new_user)
    db.commit()
    return {"message": "Registro de negocio enviado para aprobación"}


@app.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})





@app.post("/api/upload")
@limiter.limit("100/minute")
def api_upload_file(
    request: Request, file: UploadFile = File(...), client: str = Depends(verify_api_key_or_token)
) -> Dict[str, Any]:
    import re
    _filename: str = str(file.filename or "unknown")
    safe_filename = re.sub(r'[^\w\.-]', '_', _filename)
    if len(safe_filename) > 100:
        safe_filename = safe_filename[:100]

    temp_path = f"temp_{safe_filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    from worker.tasks import process_file_task
    task = process_file_task.delay(temp_path, _filename, client)
    return {
        "status": "queued",
        "task_id": task.id,
        "message": "Factura en cola",
        "metadata": {"client": client, "timestamp": datetime.utcnow().isoformat()},
    }


@app.get("/api/status/{task_id}")
def api_get_status(task_id: str, client: str = Depends(verify_api_key_or_token)):
    from worker.tasks import celery_app
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
    client: str = Depends(verify_api_key_or_token),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Dict[str, Any]:
    invoices = db.query(Invoice).offset(skip).limit(limit).all()
    total_count = db.query(Invoice).count()
    return {
        "status": "success",
        "data": [
            {
                "id": i.id, 
                "fecha": i.issued_date, 
                "proveedor": i.supplier_name, 
                "total": i.total, 
                "folio": i.invoice_number,
                "concepto": i.concept,
                "subtotal": i.subtotal,
                "iva": i.tax_iva
            }
            for i in invoices
        ],
        "metadata": {"client": client, "total": total_count, "skip": skip, "limit": limit},
    }


@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_page(request: Request, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})


@app.get("/api/admin/pending")
def get_pending_businesses(username: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    
    pending = db.query(User).filter(User.status == "pending_approval").all()
    return pending


@app.post("/api/admin/approve/{user_id}")
def approve_business(user_id: int, password: str, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.username == username).first()
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    
    business = db.query(User).filter(User.id == user_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    business.status = "active"
    business.hashed_password = pwd_context.hash(password)
    db.commit()
    return {"message": f"Negocio {business.business_name} aprobado"}


@app.delete("/api/admin/reject/{user_id}")
def reject_business(user_id: int, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.username == username).first()
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    
    business = db.query(User).filter(User.id == user_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(business)
    db.commit()
    return {"message": "Solicitud rechazada y eliminada"}


@app.get("/business/profile", response_class=HTMLResponse)
def business_profile_page(request: Request, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    print(f"DEBUG: username={username}")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"DEBUG: User not found for username={username}")
        raise HTTPException(status_code=403, detail="Usuario no encontrado")
    print(f"DEBUG: user={user.username}, role={user.role}")
    if user.role not in ["negocio", "cliente"]:
        print(f"DEBUG: Role {user.role} not in allowed roles")
        raise HTTPException(status_code=403, detail="No autorizado")
    print(f"DEBUG: Access granted for {user.username}")
    return templates.TemplateResponse("business_profile.html", {"request": request, "user": user})


@app.post("/api/business/profile")
def update_business_profile(
    business_name: str, 
    owner_name: str, 
    rfc: str, 
    phone: str, 
    email: str, 
    address: str, 
    postal_code: str,
    username: str = Depends(verify_token), 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.role != "negocio":
        raise HTTPException(status_code=403, detail="No autorizado")
    
    if user.status != "active":
        raise HTTPException(status_code=403, detail="Cuenta aún no aprobada")

    user.business_name = business_name
    user.owner_name = owner_name
    user.business_rfc = rfc
    user.phone = phone
    user.email = email
    user.address = address
    user.postal_code = postal_code
    
    db.commit()
    return {"message": "Perfil actualizado exitosamente"}


@app.post("/api/profile/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Ensure upload directory exists
    upload_dir = os.path.join(_STATIC_DIR, "uploads", "profiles")
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    _filename = file.filename or "unknown.jpg"
    file_ext = _filename.split(".")[-1]
    file_name = f"profile_{user.id}_{int(datetime.utcnow().timestamp())}.{file_ext}"
    file_path = os.path.join(upload_dir, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update user
    user.profile_photo = f"/static/uploads/profiles/{file_name}"
    db.commit()
    
    return {"url": user.profile_photo}



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


@app.get("/api/issued")
def get_issued_invoices(username: str = Depends(verify_token), db: Session = Depends(get_db)):
    # This would normally query an 'issued_invoices' table
    # For now, return empty or dummy data
    return {"status": "success", "data": []}


@app.post("/api/invoicing")
def create_manual_invoice(
    concept: str, 
    total: float, 
    client_id: int = None,
    username: str = Depends(verify_token), 
    db: Session = Depends(get_db)
):
    # This would create a new record in 'issued_invoices'
    return {"status": "success", "message": "Factura emitida (simulado)"}

# Rutas simplificadas para CSF Profile
@app.post("/api/profile/upload-csf")
async def upload_csf_simple(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload básico de CSF PDF para usuarios de negocio y clientes"""
    if current_user.role not in ["negocio", "cliente"]:
        raise HTTPException(status_code=403, detail="Solo usuarios autorizados pueden subir CSF")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
    
    # Directorio de uploads
    upload_dir = "uploads/csf"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Guardar archivo
    timestamp = int(datetime.utcnow().timestamp())
    filename = f"csf_{current_user.id}_{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Respuesta simple
    return {
        "success": True,
        "message": "CSF subido correctamente",
        "filename": filename,
        "file_path": file_path,
        "extracted_data": {
            "rfc": "XAXX010101000",  # Placeholder
            "nombre": "Datos extraídos del PDF",
            "regimen_fiscal": "612 - Personas Físicas con Actividades Empresariales"
        }
    }

@app.get("/api/profile/list-csf")
async def list_csf_simple(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar CSFs del usuario (implementación básica)"""
    return {
        "success": True,
        "csf_documents": [
            {
                "id": 1,
                "filename": "ejemplo_csf.pdf",
                "extracted_data": {
                    "rfc": "XAXX010101000",
                    "nombre": "Empresa Ejemplo SA de CV",
                    "regimen_fiscal": "601 - General de Ley Personas Morales"
                },
                "created_at": datetime.utcnow().isoformat()
            }
        ]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
