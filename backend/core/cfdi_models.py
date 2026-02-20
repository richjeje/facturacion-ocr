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
        content = self.key_file_content
        if isinstance(content, bytes):
            return fernet.decrypt(content)
        else:
            return fernet.decrypt(content.encode())
    
    def get_decrypted_password(self, master_key: str) -> str:
        fernet = Fernet(master_key.encode())
        content = self.password_encrypted
        if isinstance(content, bytes):
            return fernet.decrypt(content).decode()
        else:
            return fernet.decrypt(content.encode()).decode()

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

# Modelos para CSF (Cédula de Identificación Fiscal)
class CSFRecord(Base):
    __tablename__ = "csf_records"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    rfc = Column(String(13), nullable=False, index=True)
    curp = Column(String(18))
    nombre_completo = Column(String(255), nullable=False)
    primer_apellido = Column(String(100))
    segundo_apellido = Column(String(100))
    denominacion_razon_social = Column(String(255))
    
    # Domicilio fiscal
    codigo_postal = Column(String(5))
    calle = Column(String(255))
    numero_exterior = Column(String(50))
    numero_interior = Column(String(50))
    colonia = Column(String(255))
    localidad = Column(String(255))
    municipio = Column(String(255))
    estado = Column(String(100))
    pais = Column(String(100), default="MEX")
    
    # Régimen fiscal
    regimen_fiscal = Column(String(100))
    regimen_fiscal_key = Column(String(3))
    
    # Estatus y validación
    estatus = Column(String(20), default='active')  # active, inactive, suspended
    fecha_inicio_operaciones = Column(Date)
    ultima_actualizacion_sat = Column(DateTime)
    
    # Archivos CSF
    cedula_pdf_path = Column(String(500))
    cedula_qr_content = Column(Text)  # Contenido del código QR
    cedula_xml_content = Column(Text) # XML del SAT (si está disponible)
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime)
    is_verified = Column(Boolean, default=False)
    
    # Relaciones
    user = relationship("User", back_populates="csf_records")

class CSFValidationCache(Base):
    __tablename__ = "csf_validation_cache"
    
    id = Column(Integer, primary_key=True)
    rfc = Column(String(13), nullable=False, index=True)
    validation_type = Column(String(50))  # rfc_format, curp_match, sat_lookup
    result = Column(JSON)  # Resultado de la validación
    is_valid = Column(Boolean)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Cache TTL
    
    # Índices para performance
    __table_args__ = (
        {'schema': None}
    )

class CSFHistory(Base):
    __tablename__ = "csf_history"
    
    id = Column(Integer, primary_key=True)
    csf_record_id = Column(Integer, ForeignKey("csf_records.id", ondelete="CASCADE"))
    rfc = Column(String(13))
    field_name = Column(String(100))  # nombre, regimen_fiscal, etc.
    old_value = Column(Text)
    new_value = Column(Text)
    change_reason = Column(String(255))
    changed_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    csf_record = relationship("CSFRecord")
    changed_by = relationship("User")
