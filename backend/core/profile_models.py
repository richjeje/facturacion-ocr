# backend/core/profile_models.py
"""
Modelos de base de datos para gestión de CSF en perfiles de usuario
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base

class CSFDocument(Base):
    """Documento CSF individual subido por usuario"""
    __tablename__ = "csf_documents"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    filename = Column(String(255))  # Nombre del archivo en servidor
    original_filename = Column(String(255))  # Nombre original del archivo
    file_path = Column(String(500))  # Ruta completa al archivo
    file_size = Column(Integer)  # Tamaño en bytes
    
    # Datos extraídos (JSON)
    extracted_data = Column(JSON)
    
    # Metadatos
    extraction_method = Column(String(20), default="ocr_pdf")  # "ocr_pdf"
    confidence_score = Column(Float, default=0.0)
    extraction_date = Column(DateTime, default=datetime.utcnow)
    
    # Estado y configuración
    is_active = Column(Boolean, default=False)  # CSF principal para facturación
    status = Column(String(20), default="processing")  # processing, processed, error
    
    # Datos de validación
    validation_errors = Column(JSON)  # Lista de errores si falló validación
    validation_warnings = Column(JSON)  # Lista de advertencias
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="csf_documents")
    profile_histories = relationship("CSFProfileHistory", back_populates="csf_document")

class CSFProfileHistory(Base):
    """Historial de aplicación de CSFs al perfil"""
    __tablename__ = "csf_profile_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    csf_document_id = Column(Integer, ForeignKey("csf_documents.id", ondelete="CASCADE"))
    
    # Datos del perfil (snapshots)
    profile_data_before = Column(JSON)  # Estado antes de aplicar
    profile_data_after = Column(JSON)   # Estado después de aplicar
    
    # Metadatos de la operación
    operation_type = Column(String(20), default="apply")  # apply, modify, overwrite
    operation_reason = Column(String(255))  # Razón del cambio
    
    # Control de usuario
    was_modified_by_user = Column(Boolean, default=False)  # Si el usuario modificó datos antes de aplicar
    user_notes = Column(Text)  # Notas del usuario
    
    applied_by_user_id = Column(Integer, ForeignKey("users.id"))
    applied_date = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", foreign_keys=[user_id])
    csf_document = relationship("CSFDocument", back_populates="profile_histories")
    applied_by = relationship("User", foreign_keys=[applied_by_user_id])