# tests/test_csf_profile_integration.py
"""
Tests de integración para módulo CSF Profile
Subida, parsing, preview y aplicación de CSF a perfiles
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from io import BytesIO
import tempfile
import os

# Importar clases a testear
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class TestCSFProfileIntegration:
    
    def setup_method(self):
        """Setup para cada test"""
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.business_rfc = "TEST123456ABC"
        self.mock_user.business_name = "Test Business"
        
        self.mock_db = MagicMock()
        
        # Sample data para CSF
        self.csf_sample_data = {
            "rfc": "GODE561231GR5",
            "curp": "GODE561231HDFRRN09",
            "nombre_completo": "JUAN GÓMEZ DÍAZ",
            "codigo_postal": "06000",
            "calle": "AVENIDA JUÁREZ",
            "numero_exterior": "123",
            "colonia": "CENTRO",
            "municipio": "CUAUHTÉMOC",
            "estado": "CIUDAD DE MÉXICO",
            "regimen_fiscal_key": "612",
            "regimen_fiscal": "Personas Físicas con Actividades Empresariales y Profesionales",
            "direccion_completa": "AVENIDA JUÁREZ #123, CENTRO, CUAUHTÉMOC, CIUDAD DE MÉXICO, C.P. 06000",
            "tipo_persona": "fisica",
            "confidence_score": 0.95
        }
    
    def test_csf_pdf_parser_valido(self):
        """Test parsing de PDF CSF válido"""
        from backend.parsing.csf_parser import CSFParser
        
        parser = CSFParser()
        
        # Mock del texto extraído de un CSF PDF
        mock_csf_text = """
        CONSTANCIA DE SITUACIÓN FISCAL
        
        RFC: GODE561231GR5
        CURP: GODE561231HDFRRN09
        
        Nombre: JUAN GÓMEZ DÍAZ
        
        Domicilio Fiscal:
        Calle: AVENIDA JUÁREZ
        Número Exterior: 123
        Colonia: CENTRO
        Municipio: CUAUHTÉMOC
        Estado: CIUDAD DE MÉXICO
        Código Postal: 06000
        
        Régimen Fiscal: 612 - Personas Físicas con Actividades Empresariales y Profesionales
        """
        
        with patch.object(parser, '_extract_text_from_pdf', return_value=mock_csf_text):
            extracted_data, result = parser.parse_pdf_csf("mock_file.pdf")
        
        assert result.success == True
        assert result.confidence_score >= 0.8
        assert extracted_data.get('rfc') == "GODE561231GR5"
        assert extracted_data.get('curp') == "GODE561231HDFRRN09"
        assert extracted_data.get('tipo_persona') == "fisica"
    
    def test_csf_pdf_parser_invalido(self):
        """Test parsing de PDF inválido (no es CSF)"""
        from backend.parsing.csf_parser import CSFParser
        
        parser = CSFParser()
        
        # Texto que no es CSF
        mock_non_csf_text = """
        ESTE DOCUMENTO NO ES UNA CONSTANCIA FISCAL
        Es solo un documento de prueba sin datos fiscales.
        """
        
        with patch.object(parser, '_extract_text_from_pdf', return_value=mock_non_csf_text):
            extracted_data, result = parser.parse_pdf_csf("mock_file.pdf")
        
        assert result.success == False
        assert "no parece ser una Constancia" in result.errors[0]
    
    def test_validate_csf_file_valido(self):
        """Test validación de archivo CSF válido"""
        from backend.app.csf_profile_routes import validateCSFFile
        
        # Mock file PDF válido
        mock_file = MagicMock()
        mock_file.filename = "constancia_fiscal.pdf"
        mock_file.size = 1024 * 1024  # 1MB
        
        validation = validateCSFFile(mock_file)
        
        assert validation.valid == True
        assert validation.error is None
    
    def test_validate_csf_file_invalido(self):
        """Test validación de archivo CSF inválido"""
        from backend.app.csf_profile_routes import validateCSFFile
        
        # Test archivo no PDF
        mock_file = MagicMock()
        mock_file.filename = "archivo.txt"
        mock_file.size = 1024
        
        validation = validateCSFFile(mock_file)
        
        assert validation.valid == False
        assert "Solo se aceptan archivos PDF" in validation.error
        
        # Test archivo muy grande
        mock_file.filename = "constancia.pdf"
        mock_file.size = 15 * 1024 * 1024  # 15MB
        
        validation = validateCSFFile(mock_file)
        
        assert validation.valid == False
        assert "excede 10MB" in validation.error
    
    @patch('backend.app.csf_profile_routes.os.makedirs')
    @patch('backend.app.csf_profile_routes.shutil.copyfileobj')
    @patch('backend.app.csf_profile_routes.open', create=True)
    def test_upload_csf_endpoint_success(self, mock_open, mock_copy, mock_makedirs):
        """Test endpoint upload CSF exitoso"""
        from backend.app.csf_profile_routes import upload_and_parse_csf
        from backend.parsing.csf_parser import CSFParser
        
        # Mock file
        mock_file = MagicMock()
        mock_file.filename = "test_csf.pdf"
        mock_file.size = 1024 * 1024
        
        # Mock parsing result
        mock_parser_result = MagicMock()
        mock_parser_result.success = True
        mock_parser_result.confidence_score = 0.95
        mock_parser_result.errors = []
        mock_parser_result.warnings = []
        
        with patch.object(CSFParser, 'parse_pdf_csf') as mock_parse:
            mock_parse.return_value = (self.csf_sample_data, mock_parser_result)
            
            with patch('builtins.open', mock_open):
                result = upload_and_parse_csf(
                    file=mock_file,
                    current_user=self.mock_user,
                    db=self.mock_db
                )
        
        assert result["success"] == True
        assert "csf_id" in result
        assert result["confidence"] == 0.95
        assert "extracted_data" in result
    
    def test_upload_csf_endpoint_invalid_file(self):
        """Test endpoint upload CSF con archivo inválido"""
        from backend.app.csf_profile_routes import upload_and_parse_csf
        from fastapi import HTTPException
        
        # Mock file inválido
        mock_file = MagicMock()
        mock_file.filename = "archivo.txt"
        mock_file.size = 1024
        
        with pytest.raises(HTTPException) as exc_info:
            upload_and_parse_csf(
                file=mock_file,
                current_user=self.mock_user,
                db=self.mock_db
            )
        
        assert "Solo se aceptan archivos PDF" in str(exc_info.value.detail)
    
    def test_apply_csf_to_profile_success(self):
        """Test aplicación de CSF al perfil exitosa"""
        from backend.app.csf_profile_routes import apply_csf_to_profile
        from backend.core.profile_models import CSFDocument, CSFProfileHistory
        from fastapi import Request
        
        # Mock CSF document
        mock_csf_doc = MagicMock()
        mock_csf_doc.id = 1
        mock_csf_doc.original_filename = "test_csf.pdf"
        
        # Mock request body
        mock_request = MagicMock()
        mock_request.json.return_value = {
            "apply_data": {
                "rfc": "GODE561231GR5",
                "nombre_completo": "JUAN GÓMEZ DÍAZ",
                "codigo_postal": "06000",
                "direccion_completa": "AVENIDA JUÁREZ #123",
                "email": "juan@example.com",
                "telefono": "5512345678",
                "regimen_fiscal_key": "612"
            },
            "set_as_active": True,
            "user_notes": "Aplicación desde preview"
        }
        
        # Mock database queries
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_csf_doc
        self.mock_db.query.return_value = mock_query
        
        result = apply_csf_to_profile(
            csf_id=1,
            request=mock_request,
            current_user=self.mock_user,
            db=self.mock_db
        )
        
        assert result["success"] == True
        assert "applied_fields" in result
        assert result["csf_active"] == True
        
        # Verificar que se guardó historial
        self.mock_db.add.assert_called()
        self.mock_db.commit.assert_called()
    
    def test_apply_csf_rfc_diferente_advertencia(self):
        """Test aplicación de CSF con RFC diferente (permitido con advertencia)"""
        from backend.app.csf_profile_routes import apply_csf_to_profile
        from backend.core.profile_models import CSFDocument
        from fastapi import Request
        
        # Mock CSF con RFC diferente
        mock_csf_doc = MagicMock()
        mock_csf_doc.id = 1
        mock_csf_doc.original_filename = "test_csf.pdf"
        
        # Mock request con RFC diferente al perfil
        mock_request = MagicMock()
        mock_request.json.return_value = {
            "apply_data": {
                "rfc": "NUEVO123456XYZ",  # RFC diferente
                "nombre_completo": "NUEVO NOMBRE",
                "codigo_postal": "06100"
            },
            "set_as_active": True
        }
        
        # Mock database queries
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_csf_doc
        self.mock_db.query.return_value = mock_query
        
        with patch('backend.app.csf_profile_routes.logger') as mock_logger:
            result = apply_csf_to_profile(
                csf_id=1,
                request=mock_request,
                current_user=self.mock_user,
                db=self.mock_db
            )
        
        # Verificar advertencia de RFC
        mock_logger.warning.assert_called()
        assert "changing RFC" in str(mock_logger.warning.call_args)
        
        assert result["success"] == True  # Debe permitir el cambio
    
    def test_set_active_csf_success(self):
        """Test establecer CSF activo exitoso"""
        from backend.app.csf_profile_routes import set_active_csf
        from backend.core.profile_models import CSFDocument
        
        # Mock CSF document
        mock_csf_doc = MagicMock()
        mock_csf_doc.id = 1
        mock_csf_doc.original_filename = "test_csf.pdf"
        
        # Mock database queries
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_csf_doc
        self.mock_db.query.return_value = mock_query
        
        result = set_active_csf(
            csf_id=1,
            current_user=self.mock_user,
            db=self.mock_db
        )
        
        assert result["success"] == True
        assert result["active_csf_id"] == 1
        assert result["active_csf_filename"] == "test_csf.pdf"
    
    def test_delete_csf_document_success(self):
        """Test eliminación de CSF document exitosa"""
        from backend.app.csf_profile_routes import delete_csf_document
        from backend.core.profile_models import CSFDocument
        
        # Mock CSF document (no activo)
        mock_csf_doc = MagicMock()
        mock_csf_doc.id = 1
        mock_csf_doc.original_filename = "test_csf.pdf"
        mock_csf_doc.is_active = False
        mock_csf_doc.file_path = "/tmp/test_csf.pdf"
        
        # Mock database queries
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_csf_doc
        self.mock_db.query.return_value = mock_query
        
        with patch('os.path.exists', return_value=True):
            with patch('os.unlink') as mock_unlink:
                result = delete_csf_document(
                    csf_id=1,
                    current_user=self.mock_user,
                    db=self.mock_db
                )
        
        assert result["success"] == True
        mock_unlink.assert_called_with("/tmp/test_csf.pdf")
        self.mock_db.delete.assert_called()
        self.mock_db.commit.assert_called()
    
    def test_delete_csf_activo_prohibido(self):
        """Test que no se puede eliminar CSF activo"""
        from backend.app.csf_profile_routes import delete_csf_document
        from backend.core.profile_models import CSFDocument
        from fastapi import HTTPException
        
        # Mock CSF document activo
        mock_csf_doc = MagicMock()
        mock_csf_doc.id = 1
        mock_csf_doc.is_active = True  # Activo - no se debe eliminar
        
        # Mock database queries
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_csf_doc
        self.mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            delete_csf_document(
                csf_id=1,
                current_user=self.mock_user,
                db=self.mock_db
            )
        
        assert "No se puede eliminar el CSF activo" in str(exc_info.value.detail)
    
    def test_get_csf_list_empty(self):
        """Test obtener lista de CSFs vacía"""
        from backend.app.csf_profile_routes import get_user_csf_documents
        
        # Mock query vacío
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query
        
        result = get_user_csf_documents(
            current_user=self.mock_user,
            db=self.mock_db
        )
        
        assert result["success"] == True
        assert result["csf_documents"] == []
        assert result["total"] == 0
    
    def test_get_csf_list_with_documents(self):
        """Test obtener lista de CSFs con documentos"""
        from backend.app.csf_profile_routes import get_user_csf_documents
        
        # Mock CSF documents
        mock_doc1 = MagicMock()
        mock_doc1.id = 1
        mock_doc1.original_filename = "csf_1.pdf"
        mock_doc1.is_active = True
        mock_doc1.confidence_score = 0.95
        mock_doc1.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_doc1.extracted_data = {"rfc": "TEST123456ABC"}
        
        mock_doc2 = MagicMock()
        mock_doc2.id = 2
        mock_doc2.original_filename = "csf_2.pdf"
        mock_doc2.is_active = False
        mock_doc2.confidence_score = 0.85
        mock_doc2.created_at.isoformat.return_value = "2024-01-02T00:00:00"
        mock_doc2.extracted_data = {"rfc": "OLD123456XYZ"}
        
        # Mock query con documentos
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_doc1, mock_doc2]
        self.mock_db.query.return_value = mock_query
        
        result = get_user_csf_documents(
            current_user=self.mock_user,
            db=self.mock_db
        )
        
        assert result["success"] == True
        assert result["total"] == 2
        assert len(result["csf_documents"]) == 2
        
        # Verificar primer documento (activo)
        doc1 = result["csf_documents"][0]
        assert doc1["id"] == 1
        assert doc1["is_active"] == True
        assert doc1["confidence"] == 0.95
        assert doc1["extracted_data"]["rfc"] == "TEST123456ABC"
        
        # Verificar segundo documento (no activo)
        doc2 = result["csf_documents"][1]
        assert doc2["id"] == 2
        assert doc2["is_active"] == False
        assert doc2["confidence"] == 0.85