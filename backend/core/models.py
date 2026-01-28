from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    email = Column(String, unique=True, nullable=True)
    role = Column(String, default="cliente")  # "cliente" o "negocio"
    status = Column(String, default="active")  # "active" o "pending_approval"
    profile_photo = Column(String, nullable=True)  # URL o path de la foto
    
    # Business fields (nullable for clients)
    business_name = Column(String, nullable=True)
    business_rfc = Column(String, nullable=True)
    owner_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)



class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    client_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relación con registros CSF
    csf_records = relationship("CSFRecord", back_populates="user")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    client_id = Column(String, index=True)
    file_id = Column(String)
    job_id = Column(String)
    issued_date = Column(String, index=True)
    supplier_name = Column(String, index=True)
    supplier_rfc = Column(String)
    invoice_number = Column(String)
    concept = Column(String)
    currency = Column(String)
    subtotal = Column(Float)
    tax_iva = Column(Float)
    total = Column(Float)
    extraction_method = Column(String)
    supplier_confidence = Column(Float)
    raw_text = Column(Text)
    extra = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
