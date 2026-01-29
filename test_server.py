# Servidor temporal simplificado para pruebas
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import sys
import os

sys.path.append('.')

from backend.core.database import get_db
from backend.core.all_models import User

app = FastAPI(title="Facturación OCR - Test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Servidor de prueba funcionando"}

@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    """Login simplificado para pruebas"""
    try:
        print(f"Intentando login con username: {username}")
        
        user = db.query(User).filter(User.username == username).first()
        
        if user:
            print(f"Usuario encontrado: {user.username}")
            return {"message": "Login exitoso", "user": user.username}
        else:
            print("Usuario no encontrado")
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
            
    except Exception as e:
        print(f"Error en login: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok", "database": "connected"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)