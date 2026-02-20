# backend/cfdi/pac_manager.py
from sqlalchemy.orm import Session
from ..core.cfdi_models import CFDISettings
from .pacs.facturama import FacturamaAdapter
from ..core.feature_flags import FeatureFlags
from cryptography.fernet import Fernet
import os
from typing import Dict, Any

class PACManager:
    """Gestor con fallback múltiple y feature flags"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.adapters = {
            'facturama': FacturamaAdapter,
            # Futuros: 'fiscalapi': FiscalAPIAdapter, etc.
        }
    
    async def timbrar_with_feature_flags(self, xml_signed: str, user_id: int) -> Dict[str, Any]:
        """Timbrado con control de features"""
        
        # Verificar si el timbrado está habilitado para el usuario
        if not FeatureFlags.is_enabled(self.db, user_id, FeatureFlags.CFDI_TIMBRADO):
            return {
                "success": True,
                "message": "Modo prueba: XML generado pero no timbrado",
                "xml_timbrado": None,
                "requires_timbrado": True
            }
        
        # Obtener configuración PAC del usuario
        user_settings = self.db.query(CFDISettings).filter(
            CFDISettings.user_id == user_id
        ).first()
        
        if not user_settings:
            # Fallback a credenciales globales si no hay por usuario (opcional)
            # Para este diseño, exigimos config por usuario
            return {
                "success": False,
                "error": "Usuario no tiene configuración PAC"
            }
        
        # Determinar si usar sandbox o producción
        is_test_mode = FeatureFlags.is_enabled(self.db, user_id, FeatureFlags.CFDI_SANDBOX_MODE)
        
        # Desencriptar credenciales PAC
        master_key = os.getenv("MASTER_ENCRYPTION_KEY")
        if not master_key:
             return {"success": False, "error": "Error de configuración de seguridad servidor"}

        fernet = Fernet(master_key.encode())
        
        try:
            api_key = fernet.decrypt(user_settings.pac_api_key_encrypted.encode()).decode()
            secret = fernet.decrypt(user_settings.pac_secret_encrypted.encode()).decode()
        except Exception:
             return {"success": False, "error": "Error desencriptando credenciales PAC"}

        # Crear adaptador principal (Por defecto Facturama)
        # TODO: Permitir seleccionar PAC por usuario
        adapter = self.adapters['facturama'](
            api_key=api_key,
            secret=secret,
            sandbox=is_test_mode
        )
        
        # Intentar timbrado
        result = await adapter.timbrar_xml(xml_signed)
        
        # Si falla y tenemos fallbacks, intentar con otros PACs
        if not result["success"] and len(self.adapters) > 1:
            for pac_name, pac_class in self.adapters.items():
                if pac_name != 'facturama':
                    # Asumimos que las credenciales son válidas para otros PACs o tenemos mapeo
                    # Simplificación: Usar mismas credenciales no funcionará en la realidad.
                    # Se requeriría tabla de credenciales por PAC.
                    # Para Fase 1, solo soportamos Facturama.
                    pass
        
        return result
