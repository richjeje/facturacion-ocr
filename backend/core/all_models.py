# backend/core/all_models.py
"""
Archivo unificado de modelos para resolver importaciones cíclicas
"""
from sqlalchemy.orm import relationship
from .models import User, APIKey, Invoice
from .profile_models import CSFDocument, CSFProfileHistory
from .cfdi_models import (
    CFDICertificate, CFDIInvoice, CFDICatalog, CFDISettings,
    CSFRecord, CSFValidationCache, CSFHistory
)

# Configurar relaciones después de importar todos los modelos
# User relaciones
User.csf_records = relationship("CSFRecord", back_populates="user")
User.csf_documents = relationship("CSFDocument", back_populates="user")

# Exportar todos los modelos
__all__ = [
    # Models básicos
    'User', 'APIKey', 'Invoice',
    # CSF Profile
    'CSFDocument', 'CSFProfileHistory', 
    # CFDI y CSF Records
    'CFDICertificate', 'CFDIInvoice', 'CFDICatalog', 'CFDISettings',
    'CSFRecord', 'CSFValidationCache', 'CSFHistory'
]