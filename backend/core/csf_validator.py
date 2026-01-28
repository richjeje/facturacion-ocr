# backend/core/csf_validator.py
"""
Módulo de validación de Cédula de Identificación Fiscal (CSF)
Cumple con las reglas y formatos del SAT 2026
"""
import re
import hashlib
from datetime import datetime, date, timedelta
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

# Catálogos del SAT
CATALOGO_REGIMENES_FISCALES = {
    "601": "General de Ley Personas Morales",
    "603": "Personas Morales con Fines no Lucrativos",
    "605": "Sueldos y Salarios e Ingresos Asimilados a Salarios",
    "606": "Arrendamiento",
    "607": "Régimen de Enajenación o Adquisición de Bienes",
    "608": "Demás ingresos",
    "610": "Residentes en el Extranjero sin Establecimiento Permanente en México",
    "611": "Ingresos por Dividendos (socios y accionistas)",
    "612": "Personas Físicas con Actividades Empresariales y Profesionales",
    "614": "Ingresos por intereses",
    "615": "Régimen de los ingresos por obtención de premios",
    "616": "Sin obligaciones fiscales",
    "620": "Sociedades Cooperativas de Producción",
    "621": "Incorporación Fiscal (Régimen Simplificado)",
    "622": "Actividades Agrícolas, Ganaderas, Pesqueras y Silvícolas (Régimen Simplificado)",
    "623": "Opcional para Grupos de Sociedades",
    "624": "Coordinados",
    "625": "Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas",
    "626": "Régimen Simplificado de Confianza",
    "628": "Hidrocarburos"
}

ESTADOS_MEXICO = [
    "AGUASCALIENTES", "BAJA CALIFORNIA", "BAJA CALIFORNIA SUR", "CAMPECHE",
    "COAHUILA DE ZARAGOZA", "COLIMA", "CHIAPAS", "CHIHUAHUA", "CIUDAD DE MÉXICO",
    "DURANGO", "GUANAJUATO", "GUERRERO", "HIDALGO", "JALISCO", "MÉXICO",
    "MICHOACÁN DE OCAMPO", "MORELOS", "NAYARIT", "NUEVO LEÓN", "OAXACA",
    "PUEBLA", "QUERÉTARO", "QUINTANA ROO", "SAN LUIS POTOSÍ", "SINALOA",
    "SONORA", "TABASCO", "TAMAULIPAS", "TLAXCALA", "VERACRUZ DE IGNACIO DE LA LLAVE",
    "YUCATÁN", "ZACATECAS"
]

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    field_name: Optional[str] = None
    original_value: Optional[str] = None
    normalized_value: Optional[str] = None

class CSFValidator:
    """Validador de Cédula de Identificación Fiscal según reglas SAT"""
    
    def __init__(self):
        self.regex_rfc = re.compile(r'^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$')
        self.regex_curp = re.compile(r'^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]{2}$')
        self.regex_cp = re.compile(r'^\d{5}$')
        self.regex_codigo_qr = re.compile(r'^\?re=[^&]+&rr=[^&]+&tt=[^&]+&id=[^&]+$')
    
    def validate_rfc(self, rfc: str, persona_fisica: bool = True) -> ValidationResult:
        """Valida formato y estructura del RFC"""
        errors = []
        warnings = []
        
        if not rfc:
            return ValidationResult(False, ["RFC es requerido"], [])
        
        rfc_clean = rfc.upper().strip()
        
        # Validar longitud y formato
        if persona_fisica and len(rfc_clean) != 13:
            errors.append("RFC de persona física debe tener 13 caracteres")
        elif not persona_fisica and len(rfc_clean) != 12:
            errors.append("RFC de persona moral debe tener 12 caracteres")
        
        # Validar formato con regex
        if not self.regex_rfc.match(rfc_clean):
            errors.append("RFC tiene formato inválido")
        
        # Validar fecha de RFC (posiciones 4-9 para persona física, 3-8 para moral)
        if len(rfc_clean) >= 10:
            fecha_str = rfc_clean[4:10] if persona_fisica else rfc_clean[3:9]
            try:
                if len(fecha_str) == 6:
                    año = int(fecha_str[:2])
                    mes = int(fecha_str[2:4])
                    día = int(fecha_str[4:6])
                    
                    # Ajustar año según formato YY
                    if año >= 0 and año <= 30:
                        año += 2000
                    elif año >= 31 and año <= 99:
                        año += 1900
                    
                    fecha = date(año, mes, día)
                    fecha_limite = date(1930, 1, 1)
                    if fecha < fecha_limite:
                        warnings.append("Fecha en RFC es muy antigua")
                    elif fecha > date.today():
                        errors.append("Fecha en RFC no puede ser futura")
                        
            except ValueError:
                errors.append("Fecha en RFC es inválida")
        
        # Validar homoclave (últimos 2 caracteres)
        if len(rfc_clean) >= 13:
            homoclave = rfc_clean[-2:]
            if not re.match(r'^[A-Z0-9]{2}$', homoclave):
                errors.append("Homoclave del RFC inválida")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_name="rfc",
            original_value=rfc,
            normalized_value=rfc_clean if len(errors) == 0 else None
        )
    
    def validate_curp(self, curp: str) -> ValidationResult:
        """Valida formato y estructura del CURP"""
        errors = []
        warnings = []
        
        if not curp:
            return ValidationResult(True, [], ["CURP no proporcionado"])
        
        curp_clean = curp.upper().strip()
        
        if len(curp_clean) != 18:
            errors.append("CURP debe tener 18 caracteres")
        
        if not self.regex_curp.match(curp_clean):
            errors.append("CURP tiene formato inválido")
        
        # Validar fecha en CURP (posiciones 4-9)
        if len(curp_clean) >= 10:
            try:
                año = int(curp_clean[4:6])
                mes = int(curp_clean[6:8])
                día = int(curp_clean[8:10])
                
                # Ajustar año
                if año >= 0 and año <= 30:
                    año += 2000
                elif año >= 31 and año <= 99:
                    año += 1900
                
                fecha = date(año, mes, día)
                if fecha > date.today():
                    errors.append("Fecha en CURP no puede ser futura")
                    
            except ValueError:
                errors.append("Fecha en CURP es inválida")
        
        # Validar género (H/M)
        if len(curp_clean) >= 11:
            genero = curp_clean[10]
            if genero not in ['H', 'M']:
                errors.append("Género en CURP debe ser H o M")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_name="curp",
            original_value=curp,
            normalized_value=curp_clean if len(errors) == 0 else None
        )
    
    def validate_nombre(self, nombre: str, primer_apellido: str = None, 
                       segundo_apellido: str = None, denominacion: str = None) -> ValidationResult:
        """Valida nombres y apellidos según reglas SAT"""
        errors = []
        warnings = []
        
        # Validar que se proporcione nombre completo o denominación
        if not nombre and not denominacion:
            errors.append("Debe proporcionar nombre o denominación social")
        
        if nombre:
            nombre_clean = nombre.strip().title()
            if len(nombre_clean) < 2:
                errors.append("Nombre debe tener al menos 2 caracteres")
            
            if len(nombre_clean) > 100:
                warnings.append("Nombre muy largo, podría ser truncado")
            
            # Validar caracteres permitidos
            if not re.match(r'^[A-ZÁÉÍÓÚÑ\s\.]+$', nombre_clean):
                errors.append("Nombre contiene caracteres inválidos")
        
        # Validar apellidos para personas físicas
        if primer_apellido:
            apellido_clean = primer_apellido.strip().title()
            if len(apellido_clean) < 2:
                errors.append("Primer apellido debe tener al menos 2 caracteres")
            
            if not re.match(r'^[A-ZÁÉÍÓÚÑ\s\.]+$', apellido_clean):
                errors.append("Primer apellido contiene caracteres inválidos")
        
        if segundo_apellido and segundo_apellido.strip():
            apellido_clean = segundo_apellido.strip().title()
            if not re.match(r'^[A-ZÁÉÍÓÚÑ\s\.]+$', apellido_clean):
                errors.append("Segundo apellido contiene caracteres inválidos")
        
        # Validar denominación para personas morales
        if denominacion:
            denom_clean = denominacion.strip().title()
            if len(denom_clean) < 5:
                errors.append("Denominación social debe tener al menos 5 caracteres")
            
            if len(denom_clean) > 250:
                warnings.append("Denominación muy larga, podría ser truncada")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_domicilio(self, codigo_postal: str, calle: str = None, 
                          numero_exterior: str = None, estado: str = None) -> ValidationResult:
        """Valida domicilio fiscal según reglas SAT"""
        errors = []
        warnings = []
        
        # Validar código postal
        if not codigo_postal:
            errors.append("Código postal es requerido")
        elif not self.regex_cp.match(codigo_postal.strip()):
            errors.append("Código postal debe tener 5 dígitos")
        else:
            # Validar rango de códigos postales válidos para México
            cp_int = int(codigo_postal.strip())
            if cp_int < 1000 or cp_int > 99999:
                errors.append("Código postal fuera de rango válido")
        
        # Validar calle
        if not calle or len(calle.strip()) < 3:
            errors.append("Calle debe tener al menos 3 caracteres")
        elif len(calle) > 200:
            warnings.append("Nombre de calle muy largo")
        
        # Validar número exterior
        if not numero_exterior or len(numero_exterior.strip()) < 1:
            errors.append("Número exterior es requerido")
        
        # Validar estado
        if estado:
            estado_clean = estado.strip().upper()
            if estado_clean not in ESTADOS_MEXICO:
                warnings.append(f"Estado '{estado}' no coincide con catálogo SAT")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_regimen_fiscal(self, regimen_key: str) -> ValidationResult:
        """Valida régimen fiscal contra catálogo SAT"""
        errors = []
        warnings = []
        
        if not regimen_key:
            errors.append("Régimen fiscal es requerido")
        elif regimen_key not in CATALOGO_REGIMENES_FISCALES:
            errors.append(f"Clave de régimen '{regimen_key}' no está en catálogo SAT")
            warnings.append("Regímenes válidos: " + ", ".join(CATALOGO_REGIMENES_FISCALES.keys()))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            original_value=regimen_key,
            normalized_value=regimen_key if len(errors) == 0 else None
        )
    
    def validate_codigo_qr(self, qr_content: str) -> ValidationResult:
        """Valida formato de código QR para cédula fiscal"""
        errors = []
        warnings = []
        
        if not qr_content:
            return ValidationResult(True, [], ["No se proporcionó código QR"])
        
        # Validar estructura básica del QR
        if not self.regex_codigo_qr.match(qr_content):
            errors.append("Formato de código QR inválido")
        
        # Extraer y validar componentes del QR
        try:
            params = dict(x.split('=') for x in qr_content[1:].split('&'))
            
            if 're' in params:
                rfc_emisor = params['re']
                if not self.regex_rfc.match(rfc_emisor):
                    errors.append("RFC emisor en QR inválido")
            
            if 'rr' in params:
                rfc_receptor = params['rr']
                if not self.regex_rfc.match(rfc_receptor):
                    errors.append("RFC receptor en QR inválido")
            
            if 'tt' in params:
                total = params['tt']
                try:
                    total_float = float(total)
                    if total_float < 0:
                        errors.append("Total en QR no puede ser negativo")
                except ValueError:
                    errors.append("Total en QR inválido")
                    
        except Exception:
            errors.append("No se pudieron parsear los parámetros del QR")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_complete_csf(self, csf_data: Dict) -> Dict[str, ValidationResult]:
        """Valida todos los campos de una CSF"""
        results = {}
        
        # Determinar si es persona física o moral
        is_persona_fisica = csf_data.get('rfc', '').__len__() == 13
        
        # Validar RFC
        results['rfc'] = self.validate_rfc(csf_data.get('rfc', ''), is_persona_fisica)
        
        # Validar CURP (solo personas físicas)
        if is_persona_fisica:
            results['curp'] = self.validate_curp(csf_data.get('curp', ''))
        
        # Validar nombres
        results['nombres'] = self.validate_nombre(
            csf_data.get('nombre_completo'),
            csf_data.get('primer_apellido'),
            csf_data.get('segundo_apellido'),
            csf_data.get('denominacion_razon_social')
        )
        
        # Validar domicilio
        results['domicilio'] = self.validate_domicilio(
            csf_data.get('codigo_postal'),
            csf_data.get('calle'),
            csf_data.get('numero_exterior'),
            csf_data.get('estado')
        )
        
        # Validar régimen fiscal
        results['regimen_fiscal'] = self.validate_regimen_fiscal(
            csf_data.get('regimen_fiscal_key')
        )
        
        # Validar código QR si existe
        if csf_data.get('cedula_qr_content'):
            results['codigo_qr'] = self.validate_codigo_qr(csf_data['cedula_qr_content'])
        
        return results
    
    def generate_validation_hash(self, csf_data: Dict) -> str:
        """Genera hash para detección de cambios en CSF"""
        relevant_fields = [
            csf_data.get('rfc', ''),
            csf_data.get('curp', ''),
            csf_data.get('nombre_completo', ''),
            csf_data.get('codigo_postal', ''),
            csf_data.get('regimen_fiscal_key', '')
        ]
        
        content = '|'.join(str(field).upper().strip() for field in relevant_fields)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def is_valid_csf_for_invoicing(self, csf_data: Dict) -> Tuple[bool, List[str]]:
        """Verifica si la CSF es válida para facturación según reglas SAT 2026"""
        required_fields = ['rfc', 'nombre_completo', 'codigo_postal', 'regimen_fiscal_key']
        errors = []
        
        for field in required_fields:
            if not csf_data.get(field):
                errors.append(f"Campo requerido faltante: {field}")
        
        # Validaciones adicionales para 2026
        if csf_data.get('rfc'):
            rfc_result = self.validate_rfc(csf_data['rfc'], len(csf_data['rfc']) == 13)
            if not rfc_result.is_valid:
                errors.extend([f"RFC: {error}" for error in rfc_result.errors])
        
        return len(errors) == 0, errors