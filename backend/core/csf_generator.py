# backend/core/csf_generator.py
"""
Motor de generación de Cédula de Identificación Fiscal (CSF) XML
Cumple con especificaciones técnicas del SAT 2026
"""
import xml.etree.ElementTree as ET
from datetime import datetime, date
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import base64
import qrcode
from io import BytesIO
import hashlib

from .csf_validator import CSFValidator, ValidationResult

@dataclass
class CSFConfig:
    """Configuración para generación de CSF"""
    version: str = "4.0"
    xmlns: str = "http://www.sat.gob.mx/cfd/4"
    xsi: str = "http://www.w3.org/2001/XMLSchema-instance"
    schema_location: str = "http://www.sat.gob.mx/cfd/4 http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd"

class CSFGenerator:
    """Generador de CSF XML según estándares SAT"""
    
    def __init__(self, config: Optional[CSFConfig] = None):
        self.config = config or CSFConfig()
        self.validator = CSFValidator()
        
        # Nombrespaces para XML
        self.nsmap = {
            None: self.config.xmlns,
            'xsi': self.config.xsi
        }
    
    def generate_csf_xml(self, csf_data: Dict, include_qr: bool = True) -> Tuple[str, ValidationResult]:
        """Genera XML completo para CSF"""
        
        # Validar datos primero
        validation_results = self.validator.validate_complete_csf(csf_data)
        
        # Verificar que no haya errores críticos
        critical_errors = []
        for field_name, result in validation_results.items():
            if not result.is_valid:
                critical_errors.extend([f"{field_name}: {error}" for error in result.errors])
        
        if critical_errors:
            return "", ValidationResult(False, critical_errors, [])
        
        # Crear elemento raíz
        cedula = ET.Element("CedulaIdentificacionFiscal", attrib={
            "Version": self.config.version,
            f"{{{self.config.xsi}}}schemaLocation": self.config.schema_location
        })
        
        # Agregar datos de identificación
        self._add_identificacion(cedula, csf_data)
        
        # Agregar domicilio fiscal
        self._add_domicilio(cedula, csf_data)
        
        # Agregar régimen fiscal
        self._add_regimen_fiscal(cedula, csf_data)
        
        # Agregar metadatos
        self._add_metadatos(cedula, csf_data)
        
        # Generar y agregar código QR si se solicita
        if include_qr:
            qr_content = self._generate_qr_content(csf_data)
            self._add_codigo_qr(cedula, qr_content)
        
        # Convertir a string XML
        xml_str = self._prettify_xml(cedula)
        
        return xml_str, ValidationResult(True, [], [])
    
    def _add_identificacion(self, parent: ET.Element, data: Dict):
        """Agrega sección de identificación fiscal"""
        identificacion = ET.SubElement(parent, "Identificacion")
        
        # RFC
        rfc = ET.SubElement(identificacion, "RFC")
        rfc.text = data.get('rfc', '').upper()
        
        # CURP (solo personas físicas)
        if data.get('curp'):
            curp = ET.SubElement(identificacion, "CURP")
            curp.text = data.get('curp').upper()
        
        # Nombre o denominación
        if data.get('denominacion_razon_social'):
            # Persona moral
            denominacion = ET.SubElement(identificacion, "DenominacionRazonSocial")
            denominacion.text = data['denominacion_razon_social'].title()
        else:
            # Persona física
            nombre = ET.SubElement(identificacion, "Nombre")
            nombre.text = data.get('nombre_completo', '').title()
            
            if data.get('primer_apellido'):
                primer_apellido = ET.SubElement(identificacion, "ApellidoPaterno")
                primer_apellido.text = data['primer_apellido'].title()
            
            if data.get('segundo_apellido'):
                segundo_apellido = ET.SubElement(identificacion, "ApellidoMaterno")
                segundo_apellido.text = data['segundo_apellido'].title()
        
        # Fecha de inicio de operaciones
        if data.get('fecha_inicio_operaciones'):
            fecha_inicio = ET.SubElement(identificacion, "FechaInicioOperaciones")
            if isinstance(data['fecha_inicio_operaciones'], date):
                fecha_inicio.text = data['fecha_inicio_operaciones'].strftime("%Y-%m-%d")
            else:
                fecha_inicio.text = data['fecha_inicio_operaciones']
    
    def _add_domicilio(self, parent: ET.Element, data: Dict):
        """Agrega sección de domicilio fiscal"""
        domicilio = ET.SubElement(parent, "DomicilioFiscal")
        
        # Código postal
        if data.get('codigo_postal'):
            cp = ET.SubElement(domicilio, "CodigoPostal")
            cp.text = data['codigo_postal']
        
        # Calle
        if data.get('calle'):
            calle = ET.SubElement(domicilio, "Calle")
            calle.text = data['calle'].title()
        
        # Número exterior
        if data.get('numero_exterior'):
            num_ext = ET.SubElement(domicilio, "NumeroExterior")
            num_ext.text = data['numero_exterior']
        
        # Número interior (opcional)
        if data.get('numero_interior'):
            num_int = ET.SubElement(domicilio, "NumeroInterior")
            num_int.text = data['numero_interior']
        
        # Colonia
        if data.get('colonia'):
            colonia = ET.SubElement(domicilio, "Colonia")
            colonia.text = data['colonia'].title()
        
        # Localidad
        if data.get('localidad'):
            localidad = ET.SubElement(domicilio, "Localidad")
            localidad.text = data['localidad'].title()
        
        # Municipio
        if data.get('municipio'):
            municipio = ET.SubElement(domicilio, "Municipio")
            municipio.text = data['municipio'].title()
        
        # Estado
        if data.get('estado'):
            estado = ET.SubElement(domicilio, "Estado")
            estado.text = data['estado'].title()
        
        # País (default México)
        pais = ET.SubElement(domicilio, "Pais")
        pais.text = data.get('pais', 'MEXICO')
    
    def _add_regimen_fiscal(self, parent: ET.Element, data: Dict):
        """Agrega sección de régimen fiscal"""
        regimen = ET.SubElement(parent, "RegimenFiscal")
        
        # Clave del régimen
        if data.get('regimen_fiscal_key'):
            clave = ET.SubElement(regimen, "Clave")
            clave.text = data['regimen_fiscal_key']
        
        # Descripción (opcional, se puede inferir del catálogo)
        if data.get('regimen_fiscal'):
            descripcion = ET.SubElement(regimen, "Descripcion")
            descripcion.text = data['regimen_fiscal']
        
        # Fecha de alta en el régimen
        if data.get('fecha_alta_regimen'):
            fecha_alta = ET.SubElement(regimen, "FechaAlta")
            if isinstance(data['fecha_alta_regimen'], date):
                fecha_alta.text = data['fecha_alta_regimen'].strftime("%Y-%m-%d")
            else:
                fecha_alta.text = data['fecha_alta_regimen']
    
    def _add_metadatos(self, parent: ET.Element, data: Dict):
        """Agrega metadatos de la cédula"""
        metadatos = ET.SubElement(parent, "Metadatos")
        
        # Fecha y hora de generación
        fecha_generacion = ET.SubElement(metadatos, "FechaGeneracion")
        fecha_generacion.text = datetime.now().isoformat()
        
        # Número de serie único (hash de contenido)
        hash_content = self.validator.generate_validation_hash(data)
        serie = ET.SubElement(metadatos, "NumeroSerie")
        serie.text = hash_content[:32].upper()  # Primeros 32 caracteres
        
        # Estatus
        estatus = ET.SubElement(metadatos, "Estatus")
        estatus.text = data.get('estatus', 'active').upper()
        
        # Última actualización SAT
        if data.get('ultima_actualizacion_sat'):
            ult_actualizacion = ET.SubElement(metadatos, "UltimaActualizacionSAT")
            if isinstance(data['ultima_actualizacion_sat'], datetime):
                ult_actualizacion.text = data['ultima_actualizacion_sat'].isoformat()
            else:
                ult_actualizacion.text = str(data['ultima_actualizacion_sat'])
    
    def _generate_qr_content(self, data: Dict) -> str:
        """Genera contenido para código QR según formato SAT"""
        rfc = data.get('rfc', '').upper()
        
        # Formato estándar SAT para QR en cédulas
        # ?re=RFC_EMISOR&rr=RFC_RECEPTOR&tt=TOTAL&id=UUID
        # Para CSF, usamos formato simplificado
        
        qr_params = {
            're': rfc,  # RFC del contribuyente
            'tp': 'CSF',  # Tipo de documento
            'fc': datetime.now().strftime("%Y%m%d"),  # Fecha de consulta
            'id': hashlib.sha256(rfc.encode()).hexdigest()[:16]  # ID único
        }
        
        qr_string = "?" + "&".join([f"{k}={v}" for k, v in qr_params.items()])
        return qr_string
    
    def _add_codigo_qr(self, parent: ET.Element, qr_content: str):
        """Agrega sección de código QR a la cédula"""
        codigo_qr = ET.SubElement(parent, "CodigoQR")
        
        # Contenido del QR
        contenido = ET.SubElement(codigo_qr, "Contenido")
        contenido.text = qr_content
        
        # Generar imagen QR en base64
        qr_img = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr_img.add_data(qr_content)
        qr_img.make(fit=True)
        
        # Convertir a imagen y luego a base64
        img = qr_img.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Agregar imagen codificada
        imagen = ET.SubElement(codigo_qr, "ImagenBase64")
        imagen.text = img_base64
    
    def _prettify_xml(self, elem: ET.Element) -> str:
        """Convierte elemento XML a string con formato correcto"""
        from xml.dom import minidom
        
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding=None)
    
    def generate_csf_json(self, csf_data: Dict) -> Tuple[Dict, ValidationResult]:
        """Genera representación JSON de CSF para API"""
        
        # Validar datos
        validation_results = self.validator.validate_complete_csf(csf_data)
        
        critical_errors = []
        for field_name, result in validation_results.items():
            if not result.is_valid:
                critical_errors.extend([f"{field_name}: {error}" for error in result.errors])
        
        if critical_errors:
            return {}, ValidationResult(False, critical_errors, [])
        
        # Generar QR
        qr_content = self._generate_qr_content(csf_data)
        
        # Construir JSON response
        json_response = {
            "version": self.config.version,
            "rfc": csf_data.get('rfc', '').upper(),
            "nombre_completo": csf_data.get('nombre_completo', '').title(),
            "denominacion_razon_social": csf_data.get('denominacion_razon_social'),
            "curp": csf_data.get('curp', '').upper() if csf_data.get('curp') else None,
            "domicilio_fiscal": {
                "codigo_postal": csf_data.get('codigo_postal'),
                "calle": csf_data.get('calle'),
                "numero_exterior": csf_data.get('numero_exterior'),
                "numero_interior": csf_data.get('numero_interior'),
                "colonia": csf_data.get('colonia'),
                "localidad": csf_data.get('localidad'),
                "municipio": csf_data.get('municipio'),
                "estado": csf_data.get('estado'),
                "pais": csf_data.get('pais', 'MEXICO')
            },
            "regimen_fiscal": {
                "clave": csf_data.get('regimen_fiscal_key'),
                "descripcion": csf_data.get('regimen_fiscal'),
                "fecha_alta": csf_data.get('fecha_alta_regimen')
            },
            "metadatos": {
                "fecha_generacion": datetime.now().isoformat(),
                "numero_serie": self.validator.generate_validation_hash(csf_data)[:32].upper(),
                "estatus": csf_data.get('estatus', 'active').upper(),
                "ultima_actualizacion_sat": csf_data.get('ultima_actualizacion_sat')
            },
            "codigo_qr": {
                "contenido": qr_content,
                "imagen_generada": True
            },
            "validaciones": {
                field: {
                    "es_valido": result.is_valid,
                    "errores": result.errors,
                    "advertencias": result.warnings,
                    "valor_normalizado": result.normalized_value
                }
                for field, result in validation_results.items()
            }
        }
        
        return json_response, ValidationResult(True, [], [])
    
    def validate_sat_structure(self, xml_content: str) -> ValidationResult:
        """Valida que el XML cumpla con estructura SAT básica"""
        errors = []
        warnings = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Validar nombre de raíz
            if root.tag != "CedulaIdentificacionFiscal":
                errors.append("Raíz del XML debe ser 'CedulaIdentificacionFiscal'")
            
            # Validar versión
            version = root.get("Version")
            if version != self.config.version:
                errors.append(f"Versión debe ser {self.config.version}, se encontró: {version}")
            
            # Validar namespace
            xmlns = root.get("xmlns")
            if xmlns != self.config.xmlns:
                errors.append(f"Namespace inválido, se esperaba: {self.config.xmlns}")
            
            # Validar elementos requeridos
            required_elements = ["Identificacion", "DomicilioFiscal", "RegimenFiscal"]
            for elem_name in required_elements:
                elem = root.find(f"./{elem_name}")
                if elem is None:
                    errors.append(f"Falta elemento requerido: {elem_name}")
            
            # Validar RFC
            rfc_elem = root.find(".//RFC")
            if rfc_elem is None or not rfc_elem.text:
                errors.append("RFC es requerido")
            else:
                rfc_validation = self.validator.validate_rfc(rfc_elem.text, len(rfc_elem.text) == 13)
                if not rfc_validation.is_valid:
                    errors.extend([f"RFC: {error}" for error in rfc_validation.errors])
            
        except ET.ParseError as e:
            errors.append(f"Error parseando XML: {str(e)}")
        except Exception as e:
            errors.append(f"Error inesperado validando XML: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )