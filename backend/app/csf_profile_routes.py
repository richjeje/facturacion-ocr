# backend/app/csf_profile_routes.py
"""
API routes para gestión de CSF en perfiles de usuario
Upload, parsing, preview y aplicación de datos CSF
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import os
import shutil
from datetime import datetime

from core.database import get_db
from core.profile_models import CSFDocument, CSFProfileHistory
from core.models import User
from parsing.csf_parser import CSFParser
from app.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/profile", tags=["CSF Profile"])

# Configuración
UPLOAD_DIR = "uploads/csf"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/upload-csf")
async def upload_and_parse_csf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sube CSF PDF y extrae datos (sin aplicar aún)"""
    
    # Validaciones iniciales
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, 
            detail="Solo se aceptan archivos PDF con extensión .pdf"
        )
    
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="El archivo excede el tamaño máximo permitido (10MB)"
        )
    
    # Crear directorio de uploads
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    try:
        # Generar nombre único
        timestamp = int(datetime.utcnow().timestamp())
        filename = f"csf_{current_user.id}_{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parsear CSF
        parser = CSFParser()
        extracted_data, parse_result = parser.parse_pdf_csf(file_path)
        
        if not parse_result.success:
            # Limpiar archivo si falló parsing
            os.unlink(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"No se pudo procesar el CSF: {', '.join(parse_result.errors)}"
            )
        
        # Crear registro del documento
        csf_doc = CSFDocument(
            user_id=current_user.id,
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file.size,
            extracted_data=extracted_data,
            extraction_method=parse_result.extraction_method,
            confidence_score=parse_result.confidence_score,
            validation_errors=parse_result.errors,
            validation_warnings=parse_result.warnings,
            status="processed"
        )
        
        db.add(csf_doc)
        db.commit()
        db.refresh(csf_doc)
        
        return {
            "success": True,
            "csf_id": csf_doc.id,
            "extracted_data": extracted_data,
            "confidence": parse_result.confidence_score,
            "validation": {
                "errors": parse_result.errors,
                "warnings": parse_result.warnings
            },
            "extraction_method": parse_result.extraction_method,
            "message": "CSF procesado correctamente. Revisa los datos antes de aplicar."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading CSF: {str(e)}")
        # Limpiar archivo en caso de error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.unlink(file_path)
        
        raise HTTPException(
            status_code=500,
            detail="Error interno procesando el CSF"
        )

@router.get("/csf-list")
def get_user_csf_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todos los CSFs del usuario"""
    try:
        csf_docs = db.query(CSFDocument).filter(
            CSFDocument.user_id == current_user.id
        ).order_by(CSFDocument.created_at.desc()).all()
        
        return {
            "success": True,
            "csf_documents": [
                {
                    "id": doc.id,
                    "filename": doc.original_filename,
                    "extraction_date": doc.created_at.isoformat(),
                    "confidence": doc.confidence_score,
                    "is_active": doc.is_active,
                    "status": doc.status,
                    "extracted_data": doc.extracted_data,
                    "validation_errors": doc.validation_errors,
                    "validation_warnings": doc.validation_warnings
                }
                for doc in csf_docs
            ],
            "total": len(csf_docs)
        }
    except Exception as e:
        logger.error(f"Error listing CSFs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo lista de CSFs"
        )

@router.post("/apply-csf/{csf_id}")
async def apply_csf_to_profile(
    csf_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aplica CSF específico al perfil con datos modificados"""
    
    try:
        # Obtener datos del request body
        body = await request.json()
        apply_data = body.get("apply_data", {})
        set_as_active = body.get("set_as_active", True)
        user_notes = body.get("user_notes", "")
        
        # Buscar documento CSF
        csf_doc = db.query(CSFDocument).filter(
            CSFDocument.id == csf_id,
            CSFDocument.user_id == current_user.id
        ).first()
        
        if not csf_doc:
            raise HTTPException(
                status_code=404,
                detail="CSF no encontrado"
            )
        
        # Guardar estado actual del perfil para historial
        profile_before = {
            "business_name": current_user.business_name,
            "business_rfc": current_user.business_rfc,
            "owner_name": current_user.owner_name,
            "address": current_user.address,
            "postal_code": current_user.postal_code,
            "phone": current_user.phone,
            "email": current_user.email
        }
        
        # Validar datos antes de aplicar
        validation_errors = []
        
        if apply_data.get("rfc"):
            rfc = apply_data["rfc"].upper().strip()
            if not rfc or len(rfc) not in [12, 13]:
                validation_errors.append("RFC inválido")
            
            # Advertencia si cambia RFC (permitido con advertencia)
            if current_user.business_rfc and rfc != current_user.business_rfc:
                logger.warning(
                    f"User {current_user.id} changing RFC from {current_user.business_rfc} to {rfc}"
                )
        
        # Aplicar cambios al perfil
        if apply_data.get("rfc"):
            current_user.business_rfc = apply_data["rfc"].upper().strip()
        
        # Nombre/denominación
        nombre = apply_data.get("nombre_completo") or apply_data.get("denominacion_razon_social")
        if nombre:
            if current_user.role == "negocio":
                current_user.business_name = nombre.strip()
            else:
                current_user.owner_name = nombre.strip()
        
        # Dirección y CP
        if apply_data.get("codigo_postal"):
            current_user.postal_code = apply_data["codigo_postal"].strip()
        
        if apply_data.get("direccion_completa"):
            current_user.address = apply_data["direccion_completa"].strip()
        
        # Email y teléfono si vienen en CSF
        if apply_data.get("email"):
            current_user.email = apply_data["email"].strip()
        
        if apply_data.get("telefono"):
            current_user.phone = apply_data["telefono"].strip()
        
        # Configurar CSF activo
        if set_as_active:
            # Desactivar otros CSFs
            db.query(CSFDocument).filter(
                CSFDocument.user_id == current_user.id,
                CSFDocument.is_active == True
            ).update({"is_active": False})
            
            # Activar este CSF
            csf_doc.is_active = True
        
        # Guardar historial
        profile_after = {
            "business_name": current_user.business_name,
            "business_rfc": current_user.business_rfc,
            "owner_name": current_user.owner_name,
            "address": current_user.address,
            "postal_code": current_user.postal_code,
            "phone": current_user.phone,
            "email": current_user.email
        }
        
        history = CSFProfileHistory(
            user_id=current_user.id,
            csf_document_id=csf_doc.id,
            profile_data_before=profile_before,
            profile_data_after=profile_after,
            operation_type="apply",
            operation_reason="Aplicación de CSF al perfil",
            was_modified_by_user=True,  # Usuario modificó datos en preview
            user_notes=user_notes,
            applied_by_user_id=current_user.id
        )
        
        db.add(history)
        db.commit()
        
        return {
            "success": True,
            "message": "Perfil actualizado con datos del CSF",
            "csf_active": csf_doc.is_active,
            "applied_fields": list(apply_data.keys()),
            "profile_before": profile_before,
            "profile_after": profile_after
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying CSF to profile: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error aplicando CSF al perfil"
        )

@router.post("/set-active-csf/{csf_id}")
def set_active_csf(
    csf_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Establece CSF como principal para facturación"""
    
    try:
        # Desactivar todos los CSFs del usuario
        db.query(CSFDocument).filter(
            CSFDocument.user_id == current_user.id
        ).update({"is_active": False})
        
        # Activar el CSF especificado
        csf_doc = db.query(CSFDocument).filter(
            CSFDocument.id == csf_id,
            CSFDocument.user_id == current_user.id
        ).first()
        
        if not csf_doc:
            raise HTTPException(
                status_code=404,
                detail="CSF no encontrado"
            )
        
        csf_doc.is_active = True
        db.commit()
        
        return {
            "success": True,
            "message": f"CSF '{csf_doc.original_filename}' establecido como principal",
            "active_csf_id": csf_id,
            "active_csf_filename": csf_doc.original_filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting active CSF: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error estableciendo CSF activo"
        )

@router.get("/csf/{csf_id}/preview")
def get_csf_preview(
    csf_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene datos preview de un CSF específico"""
    
    try:
        csf_doc = db.query(CSFDocument).filter(
            CSFDocument.id == csf_id,
            CSFDocument.user_id == current_user.id
        ).first()
        
        if not csf_doc:
            raise HTTPException(
                status_code=404,
                detail="CSF no encontrado"
            )
        
        return {
            "success": True,
            "csf_document": {
                "id": csf_doc.id,
                "filename": csf_doc.original_filename,
                "extracted_data": csf_doc.extracted_data,
                "confidence": csf_doc.confidence_score,
                "validation_errors": csf_doc.validation_errors,
                "validation_warnings": csf_doc.validation_warnings,
                "created_at": csf_doc.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CSF preview: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo preview del CSF"
        )

@router.delete("/csf/{csf_id}")
def delete_csf_document(
    csf_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina un documento CSF"""
    
    try:
        csf_doc = db.query(CSFDocument).filter(
            CSFDocument.id == csf_id,
            CSFDocument.user_id == current_user.id
        ).first()
        
        if not csf_doc:
            raise HTTPException(
                status_code=404,
                detail="CSF no encontrado"
            )
        
        # No permitir eliminar CSF activo
        if csf_doc.is_active:
            raise HTTPException(
                status_code=400,
                detail="No se puede eliminar el CSF activo. Activa otro primero."
            )
        
        # Eliminar archivo físico
        if csf_doc.file_path and os.path.exists(csf_doc.file_path):
            os.unlink(csf_doc.file_path)
        
        # Eliminar registro de BD
        db.delete(csf_doc)
        db.commit()
        
        return {
            "success": True,
            "message": f"CSF '{csf_doc.original_filename}' eliminado correctamente",
            "deleted_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting CSF: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error eliminando CSF"
        )

@router.get("/csf-history")
def get_csf_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene historial de cambios CSF del usuario"""
    
    try:
        history = db.query(CSFProfileHistory).filter(
            CSFProfileHistory.user_id == current_user.id
        ).order_by(CSFProfileHistory.applied_date.desc()).offset(offset).limit(limit).all()
        
        total = db.query(CSFProfileHistory).filter(
            CSFProfileHistory.user_id == current_user.id
        ).count()
        
        return {
            "success": True,
            "history": [
                {
                    "id": h.id,
                    "csf_filename": h.csf_document.original_filename if h.csf_document else "N/A",
                    "operation_type": h.operation_type,
                    "operation_reason": h.operation_reason,
                    "was_modified_by_user": h.was_modified_by_user,
                    "user_notes": h.user_notes,
                    "applied_date": h.applied_date.isoformat(),
                    "profile_before": h.profile_data_before,
                    "profile_after": h.profile_data_after
                }
                for h in history
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting CSF history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo historial de CSF"
        )