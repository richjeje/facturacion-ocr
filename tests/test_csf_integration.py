# tests/test_csf_integration.py
"""
Tests de integración para módulo CSF completo
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

# Mock para evitar dependencias reales
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class TestCSFIntegration:
    """Casos de prueba de integración para CSF"""
    
    def setup_method(self):
        """Setup para cada test"""
        # Mock de datos de prueba
        self.csf_persona_fisica_valid = {
            'rfc': 'GODE561231GR5',
            'curp': 'GODE561231HDFRRN09',
            'nombre_completo': 'JUAN GÓMEZ DÍAZ',
            'primer_apellido': 'GÓMEZ',
            'segundo_apellido': 'DÍAZ',
            'codigo_postal': '06000',
            'calle': 'AVENIDA JUÁREZ',
            'numero_exterior': '123',
            'numero_interior': 'A',
            'colonia': 'CENTRO',
            'localidad': 'CIUDAD DE MÉXICO',
            'municipio': 'CUAUHTÉMOC',
            'estado': 'CIUDAD DE MÉXICO',
            'pais': 'MEXICO',
            'regimen_fiscal_key': '612',
            'regimen_fiscal': 'Personas Físicas con Actividades Empresariales y Profesionales',
            'estatus': 'active',
            'fecha_inicio_operaciones': '2020-01-01'
        }
        
        self.csf_persona_moral_valid = {
            'rfc': 'ABC123456XYZ',
            'denominacion_razon_social': 'EMPRESA DEMO SA DE CV',
            'codigo_postal': '06000',
            'calle': 'AVENIDA REFORMA',
            'numero_exterior': '456',
            'colonia': 'JUÁREZ',
            'municipio': 'CUAUHTÉMOC',
            'estado': 'CIUDAD DE MÉXICO',
            'pais': 'MEXICO',
            'regimen_fiscal_key': '601',
            'regimen_fiscal': 'General de Ley Personas Morales',
            'estatus': 'active'
        }
    
    @patch('backend.app.csf_routes.get_current_user')
    @patch('backend.app.csf_routes.get_db')
    @patch('backend.app.csf_routes.get_user_settings')
    @patch('backend.app.csf_routes.FeatureFlags')
    def test_csf_status_endpoint(self, mock_flags, mock_settings, mock_db, mock_user):
        """Test endpoint de status CSF"""
        # Setup mocks
        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user_instance.role = "cliente"
        mock_user.return_value = mock_user_instance
        
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance
        
        mock_flags_instance = MagicMock()
        mock_flags_instance.is_enabled.return_value = True
        mock_flags.return_value = mock_flags_instance
        
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        # Importar client
        from backend.app.main import app
        client = TestClient(app)
        
        response = client.get("/api/csf/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] == True
        assert "available_features" in data
    
    @patch('backend.app.csf_routes.get_current_user')
    @patch('backend.app.csf_routes.get_db')
    @patch('backend.app.csf_routes.get_user_settings')
    @patch('backend.app.csf_routes.FeatureFlags')
    def test_validate_csf_persona_fisica(self, mock_flags, mock_settings, mock_db, mock_user):
        """Test validación CSF persona física"""
        # Setup mocks
        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user.return_value = mock_user_instance
        
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance
        
        mock_flags_instance = MagicMock()
        mock_flags_instance.is_enabled.return_value = True
        mock_flags.return_value = mock_flags_instance
        
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        # Mock para cache
        mock_cache_instance = MagicMock()
        mock_db_instance.add = MagicMock()
        mock_db_instance.commit = MagicMock()
        
        from backend.app.main import app
        client = TestClient(app)
        
        response = client.post("/api/csf/validate", json=self.csf_persona_fisica_valid)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["is_valid_for_invoicing"] == True
        assert "validations" in data
        assert "rfc" in data["validations"]
        assert "curp" in data["validations"]
        assert "nombres" in data["validations"]
        assert "domicilio" in data["validations"]
        assert "regimen_fiscal" in data["validations"]
    
    @patch('backend.app.csf_routes.get_current_user')
    @patch('backend.app.csf_routes.get_db')
    @patch('backend.app.csf_routes.get_user_settings')
    @patch('backend.app.csf_routes.FeatureFlags')
    def test_validate_csf_persona_moral(self, mock_flags, mock_settings, mock_db, mock_user):
        """Test validación CSF persona moral"""
        # Setup mocks
        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user.return_value = mock_user_instance
        
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance
        
        mock_flags_instance = MagicMock()
        mock_flags_instance.is_enabled.return_value = True
        mock_flags.return_value = mock_flags_instance
        
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        from backend.app.main import app
        client = TestClient(app)
        
        response = client.post("/api/csf/validate", json=self.csf_persona_moral_valid)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["is_valid_for_invoicing"] == True
        # Para persona moral, no debe validar CURP
        assert "curp" not in data["validations"] or data["validations"].get("curp", {}).get("warnings") is not None
    
    @patch('backend.app.csf_routes.get_current_user')
    @patch('backend.app.csf_routes.get_db')
    @patch('backend.app.csf_routes.get_user_settings')
    @patch('backend.app.csf_routes.FeatureFlags')
    @patch('backend.core.cfdi_models.CSFRecord')
    @patch('backend.core.cfdi_models.CSFHistory')
    def test_generate_csf_json_format(self, mock_history, mock_csf_record, mock_flags, mock_settings, mock_db, mock_user):
        """Test generación CSF formato JSON"""
        # Setup mocks
        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user.return_value = mock_user_instance
        
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance
        
        mock_flags_instance = MagicMock()
        mock_flags_instance.is_enabled.return_value = True
        mock_flags.return_value = mock_flags_instance
        
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        # Mock CSFRecord no existe
        mock_csf_record.filter.return_value.first.return_value = None
        mock_csf_record.return_value.id = 1
        
        mock_history_instance = MagicMock()
        mock_history.return_value = mock_history_instance
        
        mock_db_instance.add = MagicMock()
        mock_db_instance.commit = MagicMock()
        
        from backend.app.main import app
        client = TestClient(app)
        
        payload = {**self.csf_persona_fisica_valid, "format_type": "json", "include_qr": True}
        response = client.post("/api/csf/generate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "json" in data
        assert data["json"]["rfc"] == self.csf_persona_fisica_valid["rfc"].upper()
        assert "domicilio_fiscal" in data["json"]
        assert "regimen_fiscal" in data["json"]
        assert "codigo_qr" in data["json"]
        assert "validaciones" in data["json"]
    
    @patch('backend.app.csf_routes.get_current_user')
    @patch('backend.app.csf_routes.get_db')
    @patch('backend.app.csf_routes.get_user_settings')
    @patch('backend.app.csf_routes.FeatureFlags')
    @patch('backend.core.cfdi_models.CSFRecord')
    def test_generate_csf_xml_format(self, mock_csf_record, mock_flags, mock_settings, mock_db, mock_user):
        """Test generación CSF formato XML"""
        # Setup mocks
        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user.return_value = mock_user_instance
        
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance
        
        mock_flags_instance = MagicMock()
        mock_flags_instance.is_enabled.return_value = True
        mock_flags.return_value = mock_flags_instance
        
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        # Mock CSFRecord no existe
        mock_csf_record.filter.return_value.first.return_value = None
        mock_csf_record.return_value.id = 1
        
        mock_db_instance.add = MagicMock()
        mock_db_instance.commit = MagicMock()
        
        from backend.app.main import app
        client = TestClient(app)
        
        payload = {**self.csf_persona_fisica_valid, "format_type": "xml", "include_qr": True}
        response = client.post("/api/csf/generate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "xml" in data
        assert "xml_validation" in data
        assert data["xml_validation"]["is_valid"] == True
        
        # Validar estructura básica del XML
        xml_content = data["xml"]
        assert "<CedulaIdentificacionFiscal" in xml_content
        assert "Version=\"4.0\"" in xml_content
        assert "<Identificacion>" in xml_content
        assert "<RFC>" in xml_content
        assert self.csf_persona_fisica_valid["rfc"].upper() in xml_content
    
    @patch('backend.app.csf_routes.get_current_user')
    @patch('backend.app.csf_routes.get_db')
    @patch('backend.app.csf_routes.get_user_settings')
    @patch('backend.app.csf_routes.FeatureFlags')
    @patch('backend.core.cfdi_models.CSFRecord')
    def test_generate_csf_both_formats(self, mock_csf_record, mock_flags, mock_settings, mock_db, mock_user):
        """Test generación CSF ambos formatos"""
        # Setup mocks
        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user.return_value = mock_user_instance
        
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance
        
        mock_flags_instance = MagicMock()
        mock_flags_instance.is_enabled.return_value = True
        mock_flags.return_value = mock_flags_instance
        
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        mock_csf_record.filter.return_value.first.return_value = None
        mock_csf_record.return_value.id = 1
        
        mock_db_instance.add = MagicMock()
        mock_db_instance.commit = MagicMock()
        
        from backend.app.main import app
        client = TestClient(app)
        
        payload = {**self.csf_persona_fisica_valid, "format_type": "both", "include_qr": True}
        response = client.post("/api/csf/generate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "json" in data
        assert "xml" in data
        assert "xml_validation" in data
    
    @patch('backend.app.csf_routes.get_current_user')
    @patch('backend.app.csf_routes.get_db')
    @patch('backend.app.csf_routes.get_user_settings')
    @patch('backend.app.csf_routes.FeatureFlags')
    def test_generate_csf_invalid_data(self, mock_flags, mock_settings, mock_db, mock_user):
        """Test generación CSF con datos inválidos"""
        # Setup mocks
        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user.return_value = mock_user_instance
        
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance
        
        mock_flags_instance = MagicMock()
        mock_flags_instance.is_enabled.return_value = True
        mock_flags.return_value = mock_flags_instance
        
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        from backend.app.main import app
        client = TestClient(app)
        
        # Datos inválidos (RFC incorrecto, faltan campos)
        invalid_data = {
            'rfc': 'INVALIDO',
            'nombre_completo': 'TEST'
        }
        
        response = client.post("/api/csf/generate", json=invalid_data)
        
        assert response.status_code == 200  # Success pero con errores
        data = response.json()
        assert data["success"] == False
        assert "errors" in data
        assert len(data["errors"]) > 0
    
    @patch('backend.app.csf_routes.get_current_user')
    @patch('backend.app.csf_routes.get_db')
    @patch('backend.app.csf_routes.get_user_settings')
    @patch('backend.app.csf_routes.FeatureFlags')
    @patch('backend.core.cfdi_models.CSFRecord')
    def test_list_csf_records(self, mock_csf_record, mock_flags, mock_settings, mock_db, mock_user):
        """Test listar registros CSF"""
        # Setup mocks
        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user.return_value = mock_user_instance
        
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance
        
        mock_flags_instance = MagicMock()
        mock_flags_instance.is_enabled.return_value = True
        mock_flags.return_value = mock_flags_instance
        
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        # Mock registros
        mock_record1 = MagicMock()
        mock_record1.id = 1
        mock_record1.rfc = "GODE561231GR5"
        mock_record1.nombre_completo = "JUAN GÓMEZ"
        mock_record1.regimen_fiscal_key = "612"
        mock_record1.codigo_postal = "06000"
        mock_record1.estatus = "active"
        mock_record1.is_verified = True
        mock_record1.created_at = datetime.now()
        mock_record1.updated_at = datetime.now()
        
        mock_record2 = MagicMock()
        mock_record2.id = 2
        mock_record2.rfc = "ABC123456XYZ"
        mock_record2.denominacion_razon_social = "EMPRESA DEMO"
        mock_record2.regimen_fiscal_key = "601"
        mock_record2.codigo_postal = "06000"
        mock_record2.estatus = "active"
        mock_record2.is_verified = True
        mock_record2.created_at = datetime.now()
        mock_record2.updated_at = None
        
        mock_query = MagicMock()
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = [mock_record1, mock_record2]
        mock_query.filter.return_value.count.return_value = 2
        mock_db_instance.query.return_value = mock_query
        
        from backend.app.main import app
        client = TestClient(app)
        
        response = client.get("/api/csf/list")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["records"]) == 2
        assert data["pagination"]["total"] == 2
        assert data["records"][0]["rfc"] == "GODE561231GR5"
        assert data["records"][1]["rfc"] == "ABC123456XYZ"
    
    @patch('backend.app.csf_routes.get_current_user')
    @patch('backend.app.csf_routes.get_db')
    @patch('backend.app.csf_routes.get_user_settings')
    @patch('backend.app.csf_routes.FeatureFlags')
    def test_get_catalog_regimenes_fiscales(self, mock_flags, mock_settings, mock_db, mock_user):
        """Test obtener catálogo de regímenes fiscales"""
        # Setup mocks
        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user.return_value = mock_user_instance
        
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance
        
        mock_flags_instance = MagicMock()
        mock_flags_instance.is_enabled.return_value = True
        mock_flags.return_value = mock_flags_instance
        
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        from backend.app.main import app
        client = TestClient(app)
        
        response = client.get("/api/csf/catalogs/regimenes-fiscales")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "catalog" in data
        assert "601" in data["catalog"]  # General de Ley Personas Morales
        assert "612" in data["catalog"]  # Personas Físicas con Actividades Empresariales
        assert "621" in data["catalog"]  # Incorporación Fiscal
        assert data["catalog"]["601"] == "General de Ley Personas Morales"
    
    @patch('backend.app.csf_routes.get_current_user')
    @patch('backend.app.csf_routes.get_db')
    @patch('backend.app.csf_routes.get_user_settings')
    @patch('backend.app.csf_routes.FeatureFlags')
    def test_csf_feature_disabled(self, mock_flags, mock_settings, mock_db, mock_user):
        """Test comportamiento cuando feature CSF está deshabilitado"""
        # Setup mocks
        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user.return_value = mock_user_instance
        
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance
        
        mock_flags_instance = MagicMock()
        mock_flags_instance.is_enabled.return_value = False  # Feature deshabilitado
        mock_flags.return_value = mock_flags_instance
        
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        from backend.app.main import app
        client = TestClient(app)
        
        # Test status endpoint
        response = client.get("/api/csf/status")
        assert response.status_code == 200
        assert response.json()["enabled"] == False
        
        # Test validate endpoint (debe dar 403)
        response = client.post("/api/csf/validate", json=self.csf_persona_fisica_valid)
        assert response.status_code == 403
        
        # Test generate endpoint (debe dar 403)
        response = client.post("/api/csf/generate", json=self.csf_persona_fisica_valid)
        assert response.status_code == 403