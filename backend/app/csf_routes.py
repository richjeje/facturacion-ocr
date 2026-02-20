# backend/app/csf_routes.py
"""
Rutas API para Cédula de Identificación Fiscal (CSF)
Endpoints para generación, validación y gestión de CSF
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import json
from datetime import datetime, date

from core.database import get_db
from core.cfdi_models import CSFRecord, CSFValidationCache, CSFHistory
from core.models import User
from core.csf_validator import CSFValidator
from core.csf_generator import CSFGenerator, CSFConfig
from core.feature_flags import FeatureFlags, get_user_settings
from app.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/csf", tags=["CSF"])

# Feature flags
CSF_FEATURE = "csf_enabled"

@router.get("/status")
async def get_csf_status(current_user: User = Depends(get_current_user)):
    """Verifica si módulo CSF está habilitado para el usuario"""
    try:
        user_settings = get_user_settings(current_user.id)
        feature_flags = FeatureFlags(user_settings)
        
        return {
            "enabled": feature_flags.is_enabled(CSF_FEATURE),
            "user_id": current_user.id,
            "role": current_user.role,
            "available_features": {
                "validation": True,
                "generation": True,
                "qr_codes": True,
                "xml_export": True,
                "pdf_export": feature_flags.is_enabled("csf_pdf_export")
            }
        }
    except Exception as e:
        logger.error(f"Error checking CSF status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error verificando estado CSF")

@router.post("/validate")
async def validate_csf_data(
    csf_data: Dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Valida datos de CSF según reglas SAT"""
    try:
        # Verificar feature flag
        user_settings = get_user_settings(current_user.id)
        feature_flags = FeatureFlags(user_settings)
        
        if not feature_flags.is_enabled(CSF_FEATURE):
            raise HTTPException(status_code=403, detail="Módulo CSF no habilitado")
        
        validator = CSFValidator()
        validation_results = validator.validate_complete_csf(csf_data)
        
        # Guardar en cache de validaciones
        rfc = csf_data.get('rfc', '').upper()
        if rfc:
            cache_entry = CSFValidationCache(
                rfc=rfc,
                validation_type="complete_validation",
                result={
                    field: {
                        "is_valid": result.is_valid,
                        "errors": result.errors,
                        "warnings": result.warnings
                    }
                    for field, result in validation_results.items()
                },
                is_valid=all(result.is_valid for result in validation_results.values()),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(cache_entry)
            db.commit()
        
        return {
            "success": True,
            "validations": {
                field: {
                    "is_valid": result.is_valid,
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "normalized_value": result.normalized_value
                }
                for field, result in validation_results.items()
            },
            "rfc": rfc,
            "is_valid_for_invoicing": all(result.is_valid for result in validation_results.values()),
            "validation_date": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error validating CSF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error validando CSF: {str(e)}")

@router.post("/generate")
async def generate_csf(
    csf_data: Dict,
    format_type: str = "json",  # json, xml, both
    include_qr: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Genera CSF en formato solicitado"""
    try:
        # Verificar feature flag
        user_settings = get_user_settings(current_user.id)
        feature_flags = FeatureFlags(user_settings)
        
        if not feature_flags.is_enabled(CSF_FEATURE):
            raise HTTPException(status_code=403, detail="Módulo CSF no habilitado")
        
        generator = CSFGenerator()
        
        # Validar primero
        validator = CSFValidator()
        validation_results = validator.validate_complete_csf(csf_data)
        
        critical_errors = []
        for field_name, result in validation_results.items():
            if not result.is_valid:
                critical_errors.extend([f"{field_name}: {error}" for error in result.errors])
        
        if critical_errors:
            return {
                "success": False,
                "errors": critical_errors,
                "validation_results": validation_results
            }
        
        # Generar en formatos solicitados
        result = {"success": True, "generated_at": datetime.utcnow().isoformat()}
        
        if format_type in ["json", "both"]:
            json_response, _ = generator.generate_csf_json(csf_data)
            result["json"] = json_response
        
        if format_type in ["xml", "both"]:
            xml_content, xml_validation = generator.generate_csf_xml(csf_data, include_qr)
            result["xml"] = xml_content
            result["xml_validation"] = {
                "is_valid": xml_validation.is_valid,
                "errors": xml_validation.errors,
                "warnings": xml_validation.warnings
            }
        
        # Guardar registro en BD
        rfc = csf_data.get('rfc', '').upper()
        
        # Buscar si ya existe
        existing_csf = db.query(CSFRecord).filter(
            CSFRecord.user_id == current_user.id,
            CSFRecord.rfc == rfc
        ).first()
        
        if existing_csf:
            # Guardar en historial antes de actualizar
            for field_name, result in validation_results.items():
                if result.normalized_value:
                    current_value = getattr(existing_csf, field_name, None)
                    if current_value != result.normalized_value:
                        history_entry = CSFHistory(
                            csf_record_id=existing_csf.id,
                            rfc=rfc,
                            field_name=field_name,
                            old_value=str(current_value) if current_value else None,
                            new_value=result.normalized_value,
                            change_reason="Generación/Actualización CSF",
                            changed_by_user_id=current_user.id
                        )
                        db.add(history_entry)
            
            # Actualizar registro existente
            existing_csf.nombre_completo = csf_data.get('nombre_completo')
            existing_csf.denominacion_razon_social = csf_data.get('denominacion_razon_social')
            existing_csf.codigo_postal = csf_data.get('codigo_postal')
            existing_csf.regimen_fiscal_key = csf_data.get('regimen_fiscal_key')
            existing_csf.updated_at = datetime.utcnow()
            
            if format_type in ["xml", "both"]:
                existing_csf.cedula_xml_content = xml_content
            
            if include_qr:
                qr_content = generator._generate_qr_content(csf_data)
                existing_csf.cedula_qr_content = qr_content
            
        else:
            # Crear nuevo registro
            new_csf = CSFRecord(
                user_id=current_user.id,
                rfc=rfc,
                curp=csf_data.get('curp'),
                nombre_completo=csf_data.get('nombre_completo'),
                denominacion_razon_social=csf_data.get('denominacion_razon_social'),
                codigo_postal=csf_data.get('codigo_postal'),
                calle=csf_data.get('calle'),
                numero_exterior=csf_data.get('numero_exterior'),
                numero_interior=csf_data.get('numero_interior'),
                colonia=csf_data.get('colonia'),
                localidad=csf_data.get('localidad'),
                municipio=csf_data.get('municipio'),
                estado=csf_data.get('estado'),
                regimen_fiscal_key=csf_data.get('regimen_fiscal_key'),
                regimen_fiscal=csf_data.get('regimen_fiscal'),
                estatus=csf_data.get('estatus', 'active'),
                is_verified=True,
                verified_at=datetime.utcnow()
            )
            
            if format_type in ["xml", "both"]:
                new_csf.cedula_xml_content = xml_content
            
            if include_qr:
                qr_content = generator._generate_qr_content(csf_data)
                new_csf.cedula_qr_content = qr_content
            
            db.add(new_csf)
        
        db.commit()
        
        result["rfc"] = rfc
        result["validation_results"] = {
            field: {
                "is_valid": result.is_valid,
                "errors": result.errors,
                "warnings": result.warnings
            }
            for field, result in validation_results.items()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating CSF: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error generando CSF: {str(e)}")

@router.get("/list")
async def list_csf_records(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista registros CSF del usuario"""
    try:
        # Verificar feature flag
        user_settings = get_user_settings(current_user.id)
        feature_flags = FeatureFlags(user_settings)
        
        if not feature_flags.is_enabled(CSF_FEATURE):
            raise HTTPException(status_code=403, detail="Módulo CSF no habilitado")
        
        records = db.query(CSFRecord).filter(
            CSFRecord.user_id == current_user.id
        ).offset(offset).limit(limit).all()
        
        total = db.query(CSFRecord).filter(
            CSFRecord.user_id == current_user.id
        ).count()
        
        return {
            "success": True,
            "records": [
                {
                    "id": record.id,
                    "rfc": record.rfc,
                    "nombre_completo": record.nombre_completo,
                    "denominacion_razon_social": record.denominacion_razon_social,
                    "regimen_fiscal_key": record.regimen_fiscal_key,
                    "codigo_postal": record.codigo_postal,
                    "estatus": record.estatus,
                    "is_verified": record.is_verified,
                    "created_at": record.created_at.isoformat(),
                    "updated_at": record.updated_at.isoformat() if record.updated_at else None
                }
                for record in records
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing CSF records: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listando registros CSF: {str(e)}")

@router.get("/{rfc}")
async def get_csf_details(
    rfc: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene detalles de un registro CSF específico"""
    try:
        user_settings = get_user_settings(current_user.id)
        feature_flags = FeatureFlags(user_settings)
        
        if not feature_flags.is_enabled(CSF_FEATURE):
            raise HTTPException(status_code=403, detail="Módulo CSF no habilitado")
        
        record = db.query(CSFRecord).filter(
            CSFRecord.user_id == current_user.id,
            CSFRecord.rfc == rfc.upper()
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="Registro CSF no encontrado")
        
        # Obtener historial de cambios
        history = db.query(CSFHistory).filter(
            CSFHistory.csf_record_id == record.id
        ).order_by(CSFHistory.created_at.desc()).limit(20).all()
        
        return {
            "success": True,
            "record": {
                "id": record.id,
                "rfc": record.rfc,
                "curp": record.curp,
                "nombre_completo": record.nombre_completo,
                "primer_apellido": record.primer_apellido,
                "segundo_apellido": record.segundo_apellido,
                "denominacion_razon_social": record.denominacion_razon_social,
                "domicilio_fiscal": {
                    "codigo_postal": record.codigo_postal,
                    "calle": record.calle,
                    "numero_exterior": record.numero_exterior,
                    "numero_interior": record.numero_interior,
                    "colonia": record.colonia,
                    "localidad": record.localidad,
                    "municipio": record.municipio,
                    "estado": record.estado,
                    "pais": record.pais
                },
                "regimen_fiscal": {
                    "clave": record.regimen_fiscal_key,
                    "descripcion": record.regimen_fiscal
                },
                "estatus": record.estatus,
                "fecha_inicio_operaciones": record.fecha_inicio_operaciones.isoformat() if record.fecha_inicio_operaciones else None,
                "ultima_actualizacion_sat": record.ultima_actualizacion_sat.isoformat() if record.ultima_actualizacion_sat else None,
                "is_verified": record.is_verified,
                "verified_at": record.verified_at.isoformat() if record.verified_at else None,
                "cedula_qr_content": record.cedula_qr_content,
                "cedula_xml_content": record.cedula_xml_content,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat() if record.updated_at else None
            },
            "history": [
                {
                    "field_name": h.field_name,
                    "old_value": h.old_value,
                    "new_value": h.new_value,
                    "change_reason": h.change_reason,
                    "created_at": h.created_at.isoformat()
                }
                for h in history
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CSF details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo detalles CSF: {str(e)}")

@router.delete("/{rfc}")
async def delete_csf_record(
    rfc: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina un registro CSF"""
    try:
        user_settings = get_user_settings(current_user.id)
        feature_flags = FeatureFlags(user_settings)
        
        if not feature_flags.is_enabled(CSF_FEATURE):
            raise HTTPException(status_code=403, detail="Módulo CSF no habilitado")
        
        record = db.query(CSFRecord).filter(
            CSFRecord.user_id == current_user.id,
            CSFRecord.rfc == rfc.upper()
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="Registro CSF no encontrado")
        
        # Eliminar historial relacionado
        db.query(CSFHistory).filter(
            CSFHistory.csf_record_id == record.id
        ).delete()
        
        # Eliminar registro
        db.delete(record)
        db.commit()
        
        return {
            "success": True,
            "message": f"Registro CSF para RFC {rfc} eliminado correctamente",
            "deleted_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting CSF record: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error eliminando registro CSF: {str(e)}")

@router.get("/catalogs/regimenes-fiscales")
async def get_regimenes_fiscales(current_user: User = Depends(get_current_user)):
    """Obtiene catálogo de regímenes fiscales SAT"""
    try:
        user_settings = get_user_settings(current_user.id)
        feature_flags = FeatureFlags(user_settings)
        
        if not feature_flags.is_enabled(CSF_FEATURE):
            raise HTTPException(status_code=403, detail="Módulo CSF no habilitado")
        
        from core.csf_validator import CATALOGO_REGIMENES_FISCALES
        
        return {
            "success": True,
            "catalog": CATALOGO_REGIMENES_FISCALES,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting regimenes catalog: {str(e)}")
        raise HTTPException(status_code=500, detail="Error obteniendo catálogo de regímenes")

@router.post("/enable-feature")
async def enable_csf_feature(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Habilita feature CSF para el usuario (solo admin)"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Solo administradores pueden habilitar features")
        
        from core.feature_flags import FeatureFlags
        
        user_settings = get_user_settings(current_user.id)
        feature_flags = FeatureFlags(user_settings)
        feature_flags.enable_for_user(CSF_FEATURE, current_user.id)
        
        return {
            "success": True,
            "message": f"Feature CSF habilitado para usuario {current_user.id}",
            "enabled_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error enabling CSF feature: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error habilitando feature CSF: {str(e)}")