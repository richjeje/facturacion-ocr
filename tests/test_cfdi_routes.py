# tests/test_cfdi_routes.py
import pytest
from fastapi.testclient import TestClient
from backend.app.cfdi_routes import app
from unittest.mock import MagicMock, patch

def test_generate_cfdi_endpoint():
    """Test para el endpoint de generación CFDI simplificado"""
    
    client = TestClient(app)
    
    payload = {
        "receptor": {
            "rfc": "XAXX010101000",
            "nombre": "PUBLICO EN GENERAL",
            "uso_cfdi": "S01",
            "postal_code": "06300"
        },
        "conceptos": [
            {
                "clave_prod_serv": "01010101",
                "cantidad": 1,
                "clave_unidad": "H87",
                "descripcion": "Venta",
                "valor_unitario": 100.00,
                "importe": 100.00,
                "impuestos": {
                    "traslados": [
                        {"base": 100.00, "impuesto": "002", "tipo_factor": "Tasa", "tasa_o_cuota": 0.160000, "importe": 16.00}
                    ]
                }
            }
        ],
        "impuestos": {
            "traslados": [
                {"base": 100.00, "impuesto": "002", "tipo_factor": "Tasa", "tasa_o_cuota": 0.160000, "importe": 16.00}
            ]
        }
    }
    
    # Mock de CertificateManager para evitar operaciones cripto reales
    with patch("backend.app.cfdi_routes.CertificateManager") as MockCertManager:
        mock_instance = MockCertManager.return_value
        mock_instance.sign_xml.return_value = {
            "success": True,
            "xml_signed": "<xml>Firmado</xml>",
            "signature_b64": "FirmaBase64"
        }
        
        # Mock de PACManager para evitar llamadas HTTP reales
        with patch("backend.app.cfdi_routes.PACManager") as MockPACManager:
            pac_instance = MockPACManager.return_value
            pac_instance.timbrar_with_feature_flags.return_value = {
                "success": True,
                "message": "Modo prueba: XML generado pero no timbrado",
                "xml_timbrado": None,
                "requires_timbrado": True
            }
        
        response = client.post("/api/cfdi/generate", json=payload)
    
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["requires_timbrado"] is True
        assert "Modo prueba" in data["message"]

def test_user_features_endpoint():
    """Test para el endpoint de features"""
    client = TestClient(app)
    
    response = client.get("/api/cfdi/features")
    
    assert response.status_code == 200
    data = response.json()
    assert "cfdi_generation_enabled" in data
    assert "cfdi_timbrado_enabled" not in data  # Modo prueba por defecto
    assert data["cfdi_sandbox_mode"] is True

if __name__ == "__main__":
    pytest.main([__file__])