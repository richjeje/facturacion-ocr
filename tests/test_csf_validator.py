# tests/test_csf_validator.py
"""
Tests para el módulo de validación CSF
"""
import pytest
from datetime import date, datetime
from backend.core.csf_validator import CSFValidator, ValidationResult

class TestCSFValidator:
    """Casos de prueba para CSFValidator"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.validator = CSFValidator()
    
    def test_validate_rfc_persona_fisica_valido(self):
        """Valida RFC de persona física correcto"""
        rfc_valido = "GODE561231GR5"
        result = self.validator.validate_rfc(rfc_valido, persona_fisica=True)
        
        assert result.is_valid == True
        assert len(result.errors) == 0
        assert result.normalized_value == rfc_valido
    
    def test_validate_rfc_persona_moral_valido(self):
        """Valida RFC de persona moral correcto"""
        rfc_valido = "ABC123456XYZ"
        result = self.validator.validate_rfc(rfc_valido, persona_fisica=False)
        
        assert result.is_valid == True
        assert len(result.errors) == 0
        assert result.normalized_value == rfc_valido
    
    def test_validate_rfc_longitud_incorrecta(self):
        """Valida RFC con longitud incorrecta"""
        rfc_invalido = "GODE561231G"  # 12 caracteres en lugar de 13
        result = self.validator.validate_rfc(rfc_invalido, persona_fisica=True)
        
        assert result.is_valid == False
        assert any("13 caracteres" in error for error in result.errors)
    
    def test_validate_rfc_formato_invalido(self):
        """Valida RFC con formato incorrecto"""
        rfc_invalido = "GODE56-231-GR5"
        result = self.validator.validate_rfc(rfc_invalido, persona_fisica=True)
        
        assert result.is_valid == False
        assert any("formato inválido" in error for error in result.errors)
    
    def test_validate_curp_valido(self):
        """Valida CURP correcto"""
        curp_valido = "GODE561231HDFRRN09"
        result = self.validator.validate_curp(curp_valido)
        
        assert result.is_valid == True
        assert len(result.errors) == 0
        assert result.normalized_value == curp_valido
    
    def test_validate_curp_longitud_incorrecta(self):
        """Valida CURP con longitud incorrecta"""
        curp_invalido = "GODE561231HDF"  # 13 caracteres en lugar de 18
        result = self.validator.validate_curp(curp_invalido)
        
        assert result.is_valid == False
        assert any("18 caracteres" in error for error in result.errors)
    
    def test_validate_curp_genero_invalido(self):
        """Valida CURP con género inválido"""
        curp_invalido = "GODE561231XDFRRN09"  # 'X' en lugar de 'H' o 'M'
        result = self.validator.validate_curp(curp_invalido)
        
        assert result.is_valid == False
        assert any("Género" in error for error in result.errors)
    
    def test_validate_nombre_persona_fisica_valido(self):
        """Valida nombre de persona física correcto"""
        result = self.validator.validate_nombre(
            nombre="JUAN",
            primer_apellido="GÓMEZ",
            segundo_apellido="DÍAZ"
        )
        
        assert result.is_valid == True
        assert len(result.errors) == 0
    
    def test_validate_nombre_vacio(self):
        """Valida que nombre es requerido"""
        result = self.validator.validate_nombre(nombre="")
        
        assert result.is_valid == False
        assert any("requerido" in error for error in result.errors)
    
    def test_validate_nombre_caracteres_invalidos(self):
        """Valida nombre con caracteres especiales"""
        result = self.validator.validate_nombre(nombre="JUAN123")
        
        assert result.is_valid == False
        assert any("inválidos" in error for error in result.errors)
    
    def test_validate_domicilio_completo_valido(self):
        """Valida domicilio fiscal completo correcto"""
        result = self.validator.validate_domicilio(
            codigo_postal="06000",
            calle="AVENIDA JUÁREZ",
            numero_exterior="123",
            estado="CIUDAD DE MÉXICO"
        )
        
        assert result.is_valid == True
        assert len(result.errors) == 0
    
    def test_validate_codigo_postal_invalido(self):
        """Valida código postal inválido"""
        result = self.validator.validate_domicilio(
            codigo_postal="1234",  # 4 dígitos en lugar de 5
            calle="AVENIDA JUÁREZ",
            numero_exterior="123"
        )
        
        assert result.is_valid == False
        assert any("5 dígitos" in error for error in result.errors)
    
    def test_validate_calle_requerida(self):
        """Valida que calle es requerida"""
        result = self.validator.validate_domicilio(
            codigo_postal="06000",
            numero_exterior="123"
        )
        
        assert result.is_valid == False
        assert any("Calle" in error for error in result.errors)
    
    def test_validate_regimen_fiscal_valido(self):
        """Valida régimen fiscal correcto"""
        regimen_valido = "612"  # Personas Físicas con Actividades Empresariales
        result = self.validator.validate_regimen_fiscal(regimen_valido)
        
        assert result.is_valid == True
        assert len(result.errors) == 0
        assert result.normalized_value == regimen_valido
    
    def test_validate_regimen_fiscal_invalido(self):
        """Valida régimen fiscal inválido"""
        regimen_invalido = "999"
        result = self.validator.validate_regimen_fiscal(regimen_invalido)
        
        assert result.is_valid == False
        assert any("no está en catálogo" in error for error in result.errors)
    
    def test_validate_codigo_qr_valido(self):
        """Valida formato de código QR correcto"""
        qr_valido = "?re=GODE561231GR5&rr=ABC123456XYZ&tt=1234.56&id=12345678-1234-1234-1234-123456789012"
        result = self.validator.validate_codigo_qr(qr_valido)
        
        assert result.is_valid == True
        assert len(result.errors) == 0
    
    def test_validate_codigo_qr_formato_invalido(self):
        """Valida código QR con formato incorrecto"""
        qr_invalido = "contenido_sin_formato"
        result = self.validator.validate_codigo_qr(qr_invalido)
        
        assert result.is_valid == False
        assert any("inválido" in error for error in result.errors)
    
    def test_validate_complete_csf_persona_fisica(self):
        """Valida CSF completa para persona física"""
        csf_data = {
            'rfc': 'GODE561231GR5',
            'curp': 'GODE561231HDFRRN09',
            'nombre_completo': 'JUAN GÓMEZ DÍAZ',
            'primer_apellido': 'GÓMEZ',
            'segundo_apellido': 'DÍAZ',
            'codigo_postal': '06000',
            'calle': 'AVENIDA JUÁREZ',
            'numero_exterior': '123',
            'estado': 'CIUDAD DE MÉXICO',
            'regimen_fiscal_key': '612',
            'regimen_fiscal': 'Personas Físicas con Actividades Empresariales y Profesionales'
        }
        
        results = self.validator.validate_complete_csf(csf_data)
        
        assert all(result.is_valid for result in results.values())
        assert 'rfc' in results
        assert 'curp' in results
        assert 'nombres' in results
        assert 'domicilio' in results
        assert 'regimen_fiscal' in results
    
    def test_validate_complete_csf_persona_moral(self):
        """Valida CSF completa para persona moral"""
        csf_data = {
            'rfc': 'ABC123456XYZ',
            'denominacion_razon_social': 'EMPRESA SA DE CV',
            'codigo_postal': '06000',
            'calle': 'AVENIDA REFORMA',
            'numero_exterior': '456',
            'estado': 'CIUDAD DE MÉXICO',
            'regimen_fiscal_key': '601',
            'regimen_fiscal': 'General de Ley Personas Morales'
        }
        
        results = self.validator.validate_complete_csf(csf_data)
        
        assert all(result.is_valid for result in results.values())
        assert 'rfc' in results
        # CURP no debe estar presente para persona moral
        assert 'curp' not in results
    
    def test_generate_validation_hash(self):
        """Genera hash de validación"""
        csf_data = {
            'rfc': 'GODE561231GR5',
            'curp': 'GODE561231HDFRRN09',
            'nombre_completo': 'JUAN GÓMEZ DÍAZ',
            'codigo_postal': '06000',
            'regimen_fiscal_key': '612'
        }
        
        hash1 = self.validator.generate_validation_hash(csf_data)
        hash2 = self.validator.generate_validation_hash(csf_data)
        
        # Mismos datos deben generar mismo hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256
    
    def test_is_valid_csf_for_invoicing_true(self):
        """Verifica CSF válida para facturación"""
        csf_data = {
            'rfc': 'GODE561231GR5',
            'nombre_completo': 'JUAN GÓMEZ DÍAZ',
            'codigo_postal': '06000',
            'regimen_fiscal_key': '612'
        }
        
        is_valid, errors = self.validator.is_valid_csf_for_invoicing(csf_data)
        
        assert is_valid == True
        assert len(errors) == 0
    
    def test_is_valid_csf_for_invoicing_false(self):
        """Verifica CSF inválida para facturación"""
        csf_data = {
            'rfc': 'GODE561231GR5',
            # Faltan campos requeridos
        }
        
        is_valid, errors = self.validator.is_valid_csf_for_invoicing(csf_data)
        
        assert is_valid == False
        assert len(errors) > 0
        assert any("requerido" in error for error in errors)
    
    def test_validate_fecha_futura_rfc(self):
        """Valida que detecte fecha futura en RFC"""
        fecha_futura = date(2050, 1, 1)
        rfc_futuro = f"GO{fecha_futura.strftime('%y%m%d')}GR5"
        result = self.validator.validate_rfc(rfc_futuro, persona_fisica=True)
        
        assert result.is_valid == False
        assert any("futura" in error for error in result.errors)
    
    def test_validate_fecha_antigua_rfc(self):
        """Valida que detecte fecha muy antigua en RFC"""
        rfc_antiguo = "GO300101GR5"  # 1930
        result = self.validator.validate_rfc(rfc_antiguo, persona_fisica=True)
        
        assert result.is_valid == True  # Debe ser válido pero con advertencia
        assert len(result.warnings) > 0
        assert any("antiguo" in warning for warning in result.warnings)