# backend/app/cfdi_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..core.models import User
from ..core.cfdi_models import CFDICertificate
from ..core.feature_flags import FeatureFlags
from ..cfdi.generator import CFDIGenerator
from ..cfdi.certificates import CertificateManager
from ..cfdi.validator import CFDIValidator
from ..cfdi.pac_manager import PACManager
from pydantic import BaseModel
from typing import List, Optional
import os

# Schemas
class ImpuestoTraslado(BaseModel):
    base: float
    impuesto: str
    tipo_factor: str
    tasa_o_cuota: float
    importe: float

class ConceptoImpuestos(BaseModel):
    traslados: List[ImpuestoTraslado]

class Concepto(BaseModel):
    clave_prod_serv: str
    cantidad: float
    clave_unidad: str
    unidad: Optional[str] = None
    descripcion: str
    valor_unitario: float
    importe: float
    objeto_imp: str = "02"
    descuento: Optional[float] = 0.0
    impuestos: Optional[ConceptoImpuestos] = None

class Receptor(BaseModel):
    rfc: str
    nombre: str
    uso_cfdi: str
    domicilio_fiscal: Optional[str] = None
    regimen_fiscal: Optional[str] = None
    forma_pago: Optional[str] = None
    metodo_pago: Optional[str] = None

class ImpuestosGlobales(BaseModel):
    traslados: List[ImpuestoTraslado]

class CFDIRequest(BaseModel):
    receptor: Receptor
    conceptos: List[Concepto]
    impuestos: ImpuestosGlobales
    forma_pago: Optional[str] = "99" # Global
    metodo_pago: Optional[str] = "PUE" # Global

# Dependencias
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependencia de autenticación (placeholder para integración)
def get_current_user_placeholder():
    # En un entorno real, esto debería obtener el usuario del token
    # Por ahora, devolvemos un usuario de prueba para desarrollo
    return User(
        id=1,
        username="test_cfdi_user",
        business_name="NEGOCIO PRUEBA",
        business_rfc="TEST010101AAA",
        postal_code="06300",
        role="negocio"
    )

router = APIRouter(prefix="/api/cfdi", tags=["cfdi"])

@router.get("/features")
async def get_user_features():
    """Retorna features del usuario (implementación simplificada)"""
    return {
        "cfdi_generation_enabled": True,
        "cfdi_timbrado_enabled": False,  # Default: modo prueba
        "cfdi_cert_upload_enabled": True
        "cfdi_sandbox_mode": True
    }

@router.post("/features/request")
async def request_feature(feature: str):
    """Endpoint para solicitar activación de features"""
    # Lógica simplificada: siempre devuelve éxito
    return {"success": True, "message": f"Solicitud de {feature} recibida"}

@router.post("/generate")
async def generate_cfdi(
    invoice_data: CFDIRequest,
    current_user = Depends(get_current_user_placeholder),
    db: Session = Depends(get_db)
):
    user_id = current_user.id
    
    # 1. Verificar feature flag
    if not FeatureFlags.is_enabled(db, user_id, FeatureFlags.CFDI_GENERATION):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Módulo CFDI no habilitado para tu cuenta"
        )
    
    # 2. Verificar certificado activo
    master_key = os.getenv("MASTER_ENCRYPTION_KEY")
    if not master_key:
        raise HTTPException(status_code=500, detail="Error de configuración del servidor")

    cert = db.query(CFDICertificate).filter(
        CFDICertificate.user_id == user_id,
        CFDICertificate.is_active == True
    ).first()
    
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tienes certificados SAT activos. Por favor, sube uno."
        )
    
    # 3. Validar datos
    validator = CFDIValidator(db)
    validation = validator.validate_cfdi_data(invoice_data.dict())
    if not validation['valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Datos inválidos: {', '.join(validation['errors'])}"
        )
    
    # 4. Generar XML
    emisor_data = {
        "rfc": current_user.business_rfc or "TEST010101AAA",
        "nombre": current_user.business_name or "NEGOCIO PRUEBA",
        "regimen_fiscal": "601",  # TODO: Obtener del perfil de usuario
        "postal_code": current_user.postal_code or "06300"
    }
    
    generator = CFDIGenerator(
        emisor=emisor_data,
        receptor=invoice_data.receptor.dict(),
        conceptos=[c.dict() for c in invoice_data.conceptos],
        impuestos=invoice_data.impuestos.dict()
    )
    
    xml_draft = generator.generate_xml()
    
    # 5. Firmar XML
    cert_manager = CertificateManager(db, master_key)
    sign_result = cert_manager.sign_xml(xml_draft, cert.id, user_id)
    
    if not sign_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error firmando XML: {sign_result.get('error')}"
        )
    
    xml_signed = sign_result["xml_signed"]
    
    # 6. Timbrar (si está habilitado)
    pac_manager = PACManager(db)
    result = await pac_manager.timbrar_with_feature_flags(xml_signed, user_id)
    
    return result