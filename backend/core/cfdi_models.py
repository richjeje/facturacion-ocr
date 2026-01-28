# backend/core/cfdi_models.py
from cryptography.fernet import Fernet
import base64
from sqlalchemy import Column, Integer, String, LargeBinary, Text, Date, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class CFDICertificate(Base):
    __tablename__ = "cfdi_certificates"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    certificate_name = Column(String(255))
    cer_file_content = Column(LargeBinary)  # Encriptado
    key_file_content = Column(LargeBinary)   # Encriptado
    password_encrypted = Column(Text)        # Encriptado
    valid_from = Column(Date)
    valid_until = Column(Date)
    is_active = Column(Boolean, default=True)
    sat_rfc = Column(String(13))
    certificate_number = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Método para desencriptar contenido
    def get_decrypted_key_content(self, master_key: str) -> bytes:
        fernet = Fernet(master_key.encode())
        return fernet.decrypt(self.key_file_content)
    
    def get_decrypted_password(self, master_key: str) -> str:
        fernet = Fernet(master_key.encode())
        return fernet.decrypt(self.password_encrypted.encode()).decode()

class CFDIInvoice(Base):
    __tablename__ = "cfdi_invoices"
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"))
    uuid = Column(String(36), unique=True, nullable=True)
    xml_draft = Column(Text)
    xml_signed = Column(Text)
    xml_timbrado = Column(Text)
    pdf_path = Column(String(500))
    pac_name = Column(String(100), default='facturama')
    pac_response = Column(JSON)
    status = Column(String(20), default='draft') # draft/signed/timbrado/cancelled/error
    stamp_date = Column(DateTime)
    cancel_date = Column(DateTime)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    invoice = relationship("Invoice")

class CFDICatalog(Base):
    __tablename__ = "cfdi_catalogs"

    id = Column(Integer, primary_key=True)
    catalog_type = Column(String(50))        # c_ClaveProdServ, c_FormaPago, etc.
    key = Column(String(10))               # Clave SAT  
    description = Column(String(255))        # Descripción
    version = Column(String(10), default='4.0')
    is_active = Column(Boolean, default=True)
    valid_from = Column(Date)
    valid_until = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

class CFDISettings(Base):
    __tablename__ = "cfdi_settings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    pac_api_key_encrypted = Column(Text)     # API Key del PAC encriptada
    pac_secret_encrypted = Column(Text)       # Secret del PAC encriptado
    is_test_mode = Column(Boolean, default=True) # Sandbox/producción
    feature_flags = Column(JSON, default={})  # Configuración de features
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
