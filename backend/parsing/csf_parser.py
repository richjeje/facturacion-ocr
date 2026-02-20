# backend/parsing/csf_parser.py
"""
Parser específico para Constancia de Situación Fiscal (CSF)
Enfocado en OCR de PDFs con patrones SAT 2026
"""
import re
import pdfplumber
import pytesseract
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

# Catálogos SAT para validación
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

@dataclass
class CSFParseResult:
    """Resultado del parsing CSF"""
    success: bool
    data: Dict
    confidence_score: float
    errors: List[str]
    warnings: List[str]
    extraction_method: str = "ocr_pdf"

class CSFParser:
    """Parser especializado para CSF desde PDFs"""
    
    def __init__(self):
        self.regex_patterns = {
            # RFC: 12-13 caracteres alfanuméricos
            'rfc': re.compile(r'\b[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}\b'),
            
            # CURP: 18 caracteres específicos
            'curp': re.compile(r'\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]{2}\b'),
            
            # Código postal: 5 dígitos
            'codigo_postal': re.compile(r'\b\d{5}\b'),
            
            # Fechas: DD/MM/YYYY o DD-MM-YYYY
            'fecha': re.compile(r'\b(0[1-9]|[12]\d|3[01])[/\-](0[1-9]|1[0-2])[/\-]\d{4}\b'),
            
            # Nombres generales (después de etiquetas)
            'nombre_despues_etiqueta': re.compile(r'(?:Nombre|Denominación|Razón Social)[\s:]*(.+?)\n'),
            
            # Domicilio patrones
            'calle': re.compile(r'(?:Calle|C\/)[\s:]*(.+?)\n'),
            'numero_exterior': re.compile(r'(?:N\.?Ext\.?|Número|No\.?)[\s:]*(.+?)\n'),
            'colonia': re.compile(r'(?:Colonia|Col\.?)[\s:]*(.+?)\n'),
            'municipio': re.compile(r'(?:Municipio|Municipio\/Alcaldía)[\s:]*(.+?)\n'),
            'estado': re.compile(r'(?:Estado|Entidad)[\s:]*(.+?)\n'),
            
            # Régimen fiscal (clave + descripción)
            'regimen_clave': re.compile(r'(?:Régimen|Clave)[\s:]*(\d{3})'),
            'regimen_descripcion': re.compile(r'Régimen[\s:]*(.+?)(?:\n|$)'),
        }
        
        # Lista de palabras clave para contexto CSF
        self.csf_keywords = [
            'constancia', 'situación fiscal', 'cédula de identificación fiscal',
            'RFC', 'CURP', 'régimen fiscal', 'domicilio fiscal',
            'SAT', 'Servicio de Administración Tributaria'
        ]
    
    def parse_pdf_csf(self, pdf_path: str) -> Tuple[Dict, CSFParseResult]:
        """Parsea PDF CSF usando OCR y patrones específicos"""
        
        try:
            # Extraer texto del PDF
            text = self._extract_text_from_pdf(pdf_path)
            
            if not text or len(text.strip()) < 50:
                return {}, CSFParseResult(
                    success=False,
                    data={},
                    confidence_score=0.0,
                    errors=["No se pudo extraer texto del PDF"],
                    warnings=[]
                )
            
            # Validar que sea un CSF
            if not self._is_csf_document(text):
                return {}, CSFParseResult(
                    success=False,
                    data={},
                    confidence_score=0.0,
                    errors=["El PDF no parece ser una Constancia de Situación Fiscal"],
                    warnings=[]
                )
            
            # Extraer datos usando patrones
            extracted_data = self._extract_data_patterns(text)
            
            # Validar y normalizar datos
            validated_data = self._validate_and_normalize_data(extracted_data)
            
            # Calcular confianza
            confidence = self._calculate_confidence(text, validated_data)
            
            # Detectar tipo de persona
            validated_data['tipo_persona'] = self._detect_persona_tipo(validated_data)
            
            # Formatear dirección completa
            validated_data['direccion_completa'] = self._format_direccion(validated_data)
            
            result = CSFParseResult(
                success=True,
                data=validated_data,
                confidence_score=confidence,
                errors=[],
                warnings=self._generate_warnings(validated_data)
            )
            
            return validated_data, result
            
        except Exception as e:
            logger.error(f"Error parsing CSF PDF: {str(e)}")
            return {}, CSFParseResult(
                success=False,
                data={},
                confidence_score=0.0,
                errors=[f"Error procesando PDF: {str(e)}"],
                warnings=[]
            )
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrae texto del PDF con múltiples métodos"""
        text = ""
        
        # Método 1: Extraer texto nativo del PDF
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.warning(f"Error extrayendo texto nativo PDF: {e}")
        
        # Si hay poco texto, aplicar OCR
        if len(text.strip()) < 100:
            try:
                text = self._ocr_pdf(pdf_path)
            except Exception as e:
                logger.warning(f"Error OCR PDF: {e}")
        
        return text
    
    def _ocr_pdf(self, pdf_path: str) -> str:
        """Aplica OCR a PDF usando imágenes"""
        text = ""
        
        try:
            # Convertir PDF a imágenes usando pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    # Convertir página a imagen
                    img = page.to_image(resolution=300)
                    pil_img = img.original
                    
                    # Pre-procesamiento para mejor OCR
                    gray = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
                    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    # OCR con pytesseract (configurado para español)
                    page_text = pytesseract.image_to_string(
                        thresh,
                        lang='spa',
                        config='--psm 6 --oem 3 -c preserve_interword_spaces=1'
                    )
                    
                    text += f"Página {i+1}:\n{page_text}\n"
        except Exception as e:
            raise Exception(f"Error en OCR: {e}")
        
        return text
    
    def _is_csf_document(self, text: str) -> bool:
        """Valida que el texto corresponda a un CSF"""
        text_upper = text.upper()
        
        # Contar palabras clave encontradas
        keyword_count = sum(1 for keyword in self.csf_keywords 
                          if keyword.upper() in text_upper)
        
        # Umbral mínimo para considerar CSF
        return keyword_count >= 2
    
    def _extract_data_patterns(self, text: str) -> Dict:
        """Extrae datos usando patrones regex"""
        extracted = {}
        
        # Limpiar texto
        text = text.upper()
        
        for field, pattern in self.regex_patterns.items():
            matches = pattern.findall(text)
            if matches:
                # Tomar el match más relevante (generalmente el primero)
                extracted[field] = matches[0].strip()
        
        # Búsqueda mejorada para RFC
        rfc_matches = self.regex_patterns['rfc'].findall(text)
        if rfc_matches:
            # Filtrar RFCs válidos
            valid_rfcs = [rfc for rfc in rfc_matches if self._validate_rfc_format(rfc)]
            if valid_rfcs:
                extracted['rfc'] = valid_rfcs[0]
        
        # Búsqueda mejorada para nombre/denominación
        nombre_variants = ['NOMBRE', 'DENOMINACIÓN', 'RAZÓN SOCIAL', 'DENOMINACION SOCIAL']
        for variant in nombre_variants:
            if variant in text:
                pattern = re.compile(f'{variant}[\\s:]*([^\\n]+?)(?:\\n|RFCCURP|$)')
                match = pattern.search(text)
                if match:
                    extracted['nombre_completo'] = match.group(1).strip()
                    break
        
        return extracted
    
    def _validate_rfc_format(self, rfc: str) -> bool:
        """Valida formato básico de RFC"""
        if len(rfc) not in [12, 13]:
            return False
        
        # Verificar estructura: letras-números-letras/números
        pattern = r'^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$'
        return bool(re.match(pattern, rfc))
    
    def _validate_and_normalize_data(self, data: Dict) -> Dict:
        """Valida y normaliza los datos extraídos"""
        normalized = {}
        
        # RFC
        if 'rfc' in data:
            rfc = data['rfc'].upper().strip()
            if self._validate_rfc_format(rfc):
                normalized['rfc'] = rfc
        
        # CURP
        if 'curp' in data:
            curp = data['curp'].upper().strip()
            if len(curp) == 18:
                normalized['curp'] = curp
        
        # Nombre/Denominación
        nombre_fields = ['nombre_completo', 'nombre_despues_etiqueta']
        for field in nombre_fields:
            if field in data and data[field]:
                normalized['nombre_completo'] = data[field].strip().title()
                break
        
        # Código postal
        if 'codigo_postal' in data:
            cp = data['codigo_postal'].strip()
            if len(cp) == 5 and cp.isdigit():
                normalized['codigo_postal'] = cp
        
        # Domicilio
        domicilio_fields = ['calle', 'numero_exterior', 'colonia', 'municipio', 'estado']
        for field in domicilio_fields:
            if field in data and data[field]:
                normalized[field] = data[field].strip().title()
        
        # Régimen fiscal
        if 'regimen_clave' in data:
            clave = data['regimen_clave'].strip()
            if clave in CATALOGO_REGIMENES_FISCALES:
                normalized['regimen_fiscal_key'] = clave
                normalized['regimen_fiscal'] = CATALOGO_REGIMENES_FISCALES[clave]
        elif 'regimen_descripcion' in data:
            # Buscar clave por descripción
            desc = data['regimen_descripcion'].strip()
            for clave, descripcion in CATALOGO_REGIMENES_FISCALES.items():
                if desc in descripcion or descripcion in desc:
                    normalized['regimen_fiscal_key'] = clave
                    normalized['regimen_fiscal'] = descripcion
                    break
        
        # Fecha de inicio
        if 'fecha' in data:
            fecha_str = data['fecha'].strip()
            try:
                # Intentar parsear fecha
                for sep in ['/', '-']:
                    if sep in fecha_str:
                        parts = fecha_str.split(sep)
                        if len(parts) == 3:
                            dia, mes, año = map(int, parts)
                            if 1900 <= año <= 2026:
                                fecha_obj = date(año, mes, dia)
                                normalized['fecha_inicio_operaciones'] = fecha_obj.isoformat()
                                break
            except Exception:
                pass
        
        return normalized
    
    def _detect_persona_tipo(self, data: Dict) -> str:
        """Detecta si es persona física o moral"""
        if data.get('curp'):
            return 'fisica'
        elif data.get('nombre_completo') and len(data.get('rfc', '')) == 12:
            return 'moral'
        else:
            # Por longitud del RFC
            rfc = data.get('rfc', '')
            return 'moral' if len(rfc) == 12 else 'fisica'
    
    def _format_direccion(self, data: Dict) -> str:
        """Formatea dirección completa"""
        partes = []
        
        if data.get('calle'):
            partes.append(data['calle'])
        
        if data.get('numero_exterior'):
            if partes:
                partes[-1] += f" #{data['numero_exterior']}"
            else:
                partes.append(data['numero_exterior'])
        
        if data.get('colonia'):
            partes.append(f"Col. {data['colonia']}")
        
        if data.get('municipio'):
            partes.append(data['municipio'])
        
        if data.get('estado'):
            partes.append(data['estado'])
        
        if data.get('codigo_postal'):
            partes.append(f"C.P. {data['codigo_postal']}")
        
        return ', '.join(partes)
    
    def _calculate_confidence(self, text: str, data: Dict) -> float:
        """Calcula puntaje de confianza del parsing"""
        score = 0.0
        max_score = 100.0
        
        # Confianza base por contenido CSF
        keyword_score = sum(1 for keyword in self.csf_keywords 
                          if keyword.upper() in text.upper())
        score += (keyword_score / len(self.csf_keywords)) * 30  # Máx 30 pts
        
        # RFC (campo crítico)
        if data.get('rfc'):
            score += 20  # +20 pts
        
        # Nombre/Denominación
        if data.get('nombre_completo'):
            score += 15  # +15 pts
        
        # Código postal
        if data.get('codigo_postal'):
            score += 10  # +10 pts
        
        # Régimen fiscal
        if data.get('regimen_fiscal_key'):
            score += 15  # +15 pts
        
        # Domicilio completo
        domicilio_fields = ['calle', 'numero_exterior', 'colonia', 'municipio', 'estado']
        domicilio_count = sum(1 for field in domicilio_fields if data.get(field))
        score += (domicilio_count / len(domicilio_fields)) * 10  # Máx 10 pts
        
        return min(score, max_score) / max_score
    
    def _generate_warnings(self, data: Dict) -> List[str]:
        """Genera advertencias sobre datos extraídos"""
        warnings = []
        
        # Si no hay RFC
        if not data.get('rfc'):
            warnings.append("No se detectó RFC")
        
        # Si no hay régimen fiscal
        if not data.get('regimen_fiscal_key'):
            warnings.append("No se detectó régimen fiscal")
        
        # Si el domicilio está incompleto
        if not data.get('codigo_postal'):
            warnings.append("No se detectó código postal")
        
        # Confianza baja
        # (calculado en el método que llama)
        
        return warnings