# backend/core/feature_flags.py
from sqlalchemy.orm import Session
from .cfdi_models import CFDISettings
from typing import Optional
import json

class FeatureFlags:
    CFDI_GENERATION = "cfdi_generation_enabled"
    CFDI_TIMBRADO = "cfdi_timbrado_enabled" 
    CFDI_CERT_UPLOAD = "cfdi_cert_upload_enabled"
    CFDI_SANDBOX_MODE = "cfdi_sandbox_mode"
    
    @staticmethod
    def get_user_settings(db: Session, user_id: int):
        return db.query(CFDISettings).filter(CFDISettings.user_id == user_id).first()

    @staticmethod
    def is_enabled(db: Session, user_id: int, flag: str) -> bool:
        settings = FeatureFlags.get_user_settings(db, user_id)
        if not settings:
            return False
        # feature_flags is a JSON/dict
        flags = settings.feature_flags or {}
        return flags.get(flag, False)
    
    @staticmethod
    def enable_for_user(db: Session, user_id: int, flag: str):
        settings = FeatureFlags.get_user_settings(db, user_id)
        if not settings:
            # Create settings if they don't exist
            settings = CFDISettings(user_id=user_id, feature_flags={})
            db.add(settings)
        
        flags = dict(settings.feature_flags) if settings.feature_flags else {}
        flags[flag] = True
        settings.feature_flags = flags
        db.commit()
    
    @staticmethod
    def disable_for_user(db: Session, user_id: int, flag: str):
        settings = FeatureFlags.get_user_settings(db, user_id)
        if settings and settings.feature_flags:
            flags = dict(settings.feature_flags)
            flags[flag] = False
            settings.feature_flags = flags
            db.commit()

def get_user_settings(user_id: int, db: Session) -> Optional[CFDISettings]:
    """Get CFDI settings for a user"""
    return db.query(CFDISettings).filter(CFDISettings.user_id == user_id).first()
