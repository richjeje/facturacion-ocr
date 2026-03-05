# tests/test_cfdi_core.py
import pytest
from backend.cfdi.generator import CFDIGenerator
from backend.cfdi.certificates import CertificateManager
from backend.cfdi.validator import CFDIValidator
from backend.core.database import Base
from backend.core.cfdi_models import CFDICatalog, CFDICertificate
from backend.core.all_models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID
import datetime

# Setup in-memory DB
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(bind=engine)

def setup_module(module):
    # Remove schema from tables for SQLite test
    for table in Base.metadata.tables.values():
        table.schema = None
    Base.metadata.create_all(bind=engine)

def generate_self_signed_cert():
    # Generate private key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    # Generate certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"MX"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Distrito Federal"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Coyoacán"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Servicio de Administración Tributaria"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"SAT"),
        # Use OID 2.5.4.45 for RFC as per our implementation assumption
        x509.NameAttribute(x509.ObjectIdentifier("2.5.4.45"), u"AAA010101AAA"), 
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow() - datetime.timedelta(days=1)
    ).not_valid_after(
        # Valid for 10 days
        datetime.datetime.utcnow() + datetime.timedelta(days=10)
    ).sign(key, hashes.SHA256())
    
    # Serialize
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.BestAvailableEncryption(b"password_dummy")
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    
    return cert_pem, key_pem

def test_cfdi_generation():
    emisor = {"rfc": "AAA010101AAA", "nombre": "ACCEM SERVICIOS EMPRESARIALES SC", "regimen_fiscal": "601", "postal_code": "06300"}
    receptor = {"rfc": "XAXX010101000", "nombre": "PUBLICO EN GENERAL", "uso_cfdi": "S01", "forma_pago": "01", "metodo_pago": "PUE", "postal_code": "06300"}
    conceptos = [
        {"clave_prod_serv": "01010101", "cantidad": 1, "clave_unidad": "H87", "descripcion": "Venta", "valor_unitario": 100.00, "importe": 100.00, "impuestos": {"traslados": [{"base": 100.00, "impuesto": "002", "tipo_factor": "Tasa", "tasa_o_cuota": 0.160000, "importe": 16.00}]}}
    ]
    impuestos = {"traslados": [{"base": 100.00, "impuesto": "002", "tipo_factor": "Tasa", "tasa_o_cuota": 0.160000, "importe": 16.00}]}
    
    generator = CFDIGenerator(emisor, receptor, conceptos, impuestos)
    xml_str = generator.generate_xml()
    
    assert "Version=\"4.0\"" in xml_str
    assert "AAA010101AAA" in xml_str
    assert "Total=\"116.00\"" in xml_str
    assert "SubTotal=\"100.00\"" in xml_str

def test_validator():
    db = SessionLocal()
    # Insert catalog data
    db.add(CFDICatalog(catalog_type='c_UsoCFDI', key='S01', description='Sin efectos fiscales', is_active=True))
    db.commit()
    
    validator = CFDIValidator(db)
    
    data = {
        'emisor': {'rfc': 'A', 'nombre': 'B', 'regimen_fiscal': 'C'},
        'receptor': {'rfc': 'D', 'nombre': 'E', 'uso_cfdi': 'S01', 'postal_code': '12345'}, # Added postal_code
        'conceptos': [{'clave_prod_serv': 'X', 'cantidad': 1, 'clave_unidad': 'Y', 'descripcion': 'Z', 'valor_unitario': 10, 'importe': 10}]
    }
    
    result = validator.validate_cfdi_data(data)
    assert result['valid'] is True
    
    # Test invalid catalog
    data['receptor']['uso_cfdi'] = 'INVALID'
    result = validator.validate_cfdi_data(data)
    assert result['valid'] is False
    assert "UsoCFDI 'INVALID' no válido" in result['errors'][0]
    
    db.close()

def test_certificate_manager():
    db = SessionLocal()
    master_key = Fernet.generate_key().decode()
    manager = CertificateManager(db, master_key)
    
    cert_pem, key_pem = generate_self_signed_cert()
    
    # Test Import
    result = manager.import_certificate(1, cert_pem, key_pem, "password_dummy") # pwd ignored for unencrypted key
    if not result["success"]:
        print(f"Import failed: {result.get('error')}")
    assert result["success"] is True
    cert_id = result["certificate_id"]
    
    # Test Sign
    xml_sample = '<cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4" Version="4.0"></cfdi:Comprobante>'
    sign_result = manager.sign_xml(xml_sample, cert_id, 1)
    
    assert sign_result["success"] is True
    assert "Sello=" in sign_result["xml_signed"]
    assert len(sign_result["signature_b64"]) > 0

    db.close()

if __name__ == "__main__":
    pytest.main([__file__])
