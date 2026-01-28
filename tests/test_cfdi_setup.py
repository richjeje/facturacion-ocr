# tests/test_cfdi_setup.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.database import Base
from backend.core.cfdi_models import CFDICertificate, CFDIInvoice, CFDICatalog, CFDISettings
from backend.core.feature_flags import FeatureFlags
from backend.core.models import User

# Setup in-memory DB
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(bind=engine)

def setup_module(module):
    # Remove schema from tables for SQLite test since Base is configured for Postgres
    for table in Base.metadata.tables.values():
        table.schema = None
    Base.metadata.create_all(bind=engine)

def test_cfdi_models_creation():
    db = SessionLocal()
    try:
        # Create a user first
        user = User(username="test_cfdi", email="test@cfdi.com", role="negocio")
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create CFDISettings
        settings = CFDISettings(
            user_id=user.id,
            feature_flags={"cfdi_generation_enabled": True}
        )
        db.add(settings)
        db.commit()

        # Check FeatureFlags
        assert FeatureFlags.is_enabled(db, user.id, "cfdi_generation_enabled") is True
        assert FeatureFlags.is_enabled(db, user.id, "cfdi_timbrado_enabled") is False

        # Enable a feature
        FeatureFlags.enable_for_user(db, user.id, FeatureFlags.CFDI_TIMBRADO)
        assert FeatureFlags.is_enabled(db, user.id, "cfdi_timbrado_enabled") is True

        # Disable a feature
        FeatureFlags.disable_for_user(db, user.id, FeatureFlags.CFDI_TIMBRADO)
        assert FeatureFlags.is_enabled(db, user.id, "cfdi_timbrado_enabled") is False

        # Create CFDICertificate (dummy data)
        cert = CFDICertificate(
            user_id=user.id,
            certificate_name="Test Cert",
            cer_file_content=b"encrypted_cer",
            key_file_content=b"encrypted_key",
            password_encrypted="encrypted_pass",
            sat_rfc="ABC123456T1A",
            certificate_number="00001000000400000000"
        )
        db.add(cert)
        db.commit()

        saved_cert = db.query(CFDICertificate).filter_by(sat_rfc="ABC123456T1A").first()
        assert saved_cert is not None
        assert saved_cert.certificate_name == "Test Cert"

    finally:
        db.close()

if __name__ == "__main__":
    pytest.main([__file__])
