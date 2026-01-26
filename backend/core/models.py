from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from .database import Base


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
    fecha = Column(String, index=True)
    proveedor = Column(String, index=True)
    concepto = Column(String)
    folio = Column(String)
    subtotal = Column(Float)
    iva = Column(Float)
    total = Column(Float)
    metodo_extraccion = Column(String)
    confianza_proveedor = Column(Float)
    url = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
