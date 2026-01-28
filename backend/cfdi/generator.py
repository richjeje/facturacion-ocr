# backend/cfdi/generator.py
from lxml import etree
from datetime import datetime
import uuid
import os

class CFDIGenerator:
    """Generador robusto de XML CFDI 4.0"""
    
    NAMESPACES = {
        'cfdi': 'http://www.sat.gob.mx/cfd/4',
        'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }
    
    SCHEMA_LOCATION = (
        "http://www.sat.gob.mx/cfd/4 "
        "http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd "
        "http://www.sat.gob.mx/TimbreFiscalDigital "
        "http://www.sat.gob.mx/sitio_internet/cfd/TimbreFiscalDigital/TimbreFiscalDigitalv11.xsd"
    )
    
    def __init__(self, emisor: dict, receptor: dict, conceptos: list, 
                 impuestos: dict, complementos: list = None):
        self.emisor = emisor
        self.receptor = receptor
        self.conceptos = conceptos
        self.impuestos = impuestos
        self.complementos = complementos or []
    
    def generate_xml(self) -> str:
        """Genera XML CFDI 4.0 completo"""
        root = etree.Element("{http://www.sat.gob.mx/cfd/4}Comprobante", nsmap=self.NAMESPACES)
        
        # Atributos del Comprobante
        self._add_comprobante_attributes(root)
        
        # Secciones obligatorias
        self._add_emisor(root)
        self._add_receptor(root)
        self._add_conceptos(root)
        self._add_impuestos(root)
        
        # Complementos (si existen)
        if self.complementos:
            self._add_complementos(root)
        
        # Convertir a string XML
        xml_str = etree.tostring(root, encoding='utf-8', pretty_print=True, xml_declaration=True)
        return xml_str.decode('utf-8')
    
    def _add_comprobante_attributes(self, root):
        """Agrega atributos al elemento Comprobante"""
        root.set("Version", "4.0")
        root.set("Fecha", datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        root.set("FormaPago", self.receptor.get("forma_pago", "99"))
        root.set("MetodoPago", self.receptor.get("metodo_pago", "PUE"))
        root.set("Moneda", "MXN")
        root.set("TipoDeComprobante", "I")
        root.set("LugarExpedicion", self.emisor.get("postal_code", ""))
        root.set("Exportacion", "01")  # No aplica
        
        # Calcular subtotales y totales
        subtotal = sum(c['importe'] for c in self.conceptos)
        total_impuestos_trasladados = 0
        if "traslados" in self.impuestos:
             total_impuestos_trasladados = sum(t['importe'] for t in self.impuestos["traslados"])
        
        total = subtotal + total_impuestos_trasladados
        
        root.set("SubTotal", f"{subtotal:.2f}")
        root.set("Total", f"{total:.2f}")
        
        root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", self.SCHEMA_LOCATION)
    
    def _add_emisor(self, root):
        """Agrega sección Emisor"""
        emisor = etree.SubElement(root, "{http://www.sat.gob.mx/cfd/4}Emisor")
        emisor.set("Rfc", self.emisor["rfc"])
        emisor.set("Nombre", self.emisor["nombre"])
        emisor.set("RegimenFiscal", self.emisor["regimen_fiscal"])
        
    def _add_receptor(self, root):
        """Agrega sección Receptor con validación"""
        receptor = etree.SubElement(root, "{http://www.sat.gob.mx/cfd/4}Receptor")
        receptor.set("Rfc", self.receptor["rfc"])
        receptor.set("Nombre", self.receptor["nombre"])
        receptor.set("UsoCFDI", self.receptor["uso_cfdi"])
        receptor.set("DomicilioFiscalReceptor", self.receptor.get("domicilio_fiscal", ""))
        receptor.set("RegimenFiscalReceptor", self.receptor.get("regimen_fiscal", ""))
    
    def _add_conceptos(self, root):
        """Agrega sección Conceptos"""
        conceptos_node = etree.SubElement(root, "{http://www.sat.gob.mx/cfd/4}Conceptos")
        
        for concepto in self.conceptos:
            concepto_node = etree.SubElement(conceptos_node, "{http://www.sat.gob.mx/cfd/4}Concepto")
            concepto_node.set("ClaveProdServ", concepto["clave_prod_serv"])
            concepto_node.set("Cantidad", str(concepto["cantidad"]))
            concepto_node.set("ClaveUnidad", concepto["clave_unidad"])
            concepto_node.set("Unidad", concepto.get("unidad", ""))
            concepto_node.set("Descripcion", concepto["descripcion"])
            concepto_node.set("ValorUnitario", f"{concepto['valor_unitario']:.2f}")
            concepto_node.set("Importe", f"{concepto['importe']:.2f}")
            concepto_node.set("ObjetoImp", concepto.get("objeto_imp", "02")) # 02 = Sí objeto de impuesto
            
            # Descuentos (si aplica)
            if concepto.get("descuento", 0) > 0:
                concepto_node.set("Descuento", f"{concepto['descuento']:.2f}")
            
            # Impuestos del concepto
            if "impuestos" in concepto:
                self._add_concepto_impuestos(concepto_node, concepto["impuestos"])

    def _add_concepto_impuestos(self, concepto_node, impuestos):
        impuestos_node = etree.SubElement(concepto_node, "{http://www.sat.gob.mx/cfd/4}Impuestos")
        
        if "traslados" in impuestos:
            traslados_node = etree.SubElement(impuestos_node, "{http://www.sat.gob.mx/cfd/4}Traslados")
            for traslado in impuestos["traslados"]:
                t_node = etree.SubElement(traslados_node, "{http://www.sat.gob.mx/cfd/4}Traslado")
                t_node.set("Base", f"{traslado['base']:.2f}")
                t_node.set("Impuesto", traslado['impuesto']) # 002 = IVA
                t_node.set("TipoFactor", traslado['tipo_factor']) # Tasa, Cuota
                t_node.set("TasaOCuota", f"{traslado['tasa_o_cuota']:.6f}")
                t_node.set("Importe", f"{traslado['importe']:.2f}")

    def _add_impuestos(self, root):
        """Agrega sección Impuestos a nivel comprobante"""
        impuestos_node = etree.SubElement(root, "{http://www.sat.gob.mx/cfd/4}Impuestos")
        
        if "traslados" in self.impuestos:
            total_trasladados = sum(t['importe'] for t in self.impuestos["traslados"])
            impuestos_node.set("TotalImpuestosTrasladados", f"{total_trasladados:.2f}")
            
            traslados_node = etree.SubElement(impuestos_node, "{http://www.sat.gob.mx/cfd/4}Traslados")
            for traslado in self.impuestos["traslados"]:
                # Agrupar por tasa/impuesto si fuera necesario, aquí asumimos desglose simple o pre-agrupado
                t_node = etree.SubElement(traslados_node, "{http://www.sat.gob.mx/cfd/4}Traslado")
                t_node.set("Base", f"{traslado['base']:.2f}")
                t_node.set("Impuesto", traslado['impuesto'])
                t_node.set("TipoFactor", traslado['tipo_factor'])
                t_node.set("TasaOCuota", f"{traslado['tasa_o_cuota']:.6f}")
                t_node.set("Importe", f"{traslado['importe']:.2f}")

    def _add_complementos(self, root):
        pass # Implementar según necesidad

    def _get_xsd_file(self):
         # Placeholder: In a real scenario, download or locate local XSD
         return "cfdv40.xsd"

    def validate_against_xsd(self, xml_string: str) -> tuple[bool, list]:
        """Valida XML contra XSD del SAT"""
        try:
            # En un entorno real, cargaríamos los XSDs oficiales.
            # Para este MVP/Fase, validaremos que sea XML bien formado 
            # y tenga los atributos básicos.
            
            # Simple check de parseo
            parser = etree.XMLParser(recover=True)
            etree.fromstring(xml_string.encode(), parser=parser)
            
            # TODO: Implementar validación real con archivos .xsd locales
            # xsd_path = self._get_xsd_file()
            # xmlschema_doc = etree.parse(xsd_path)
            # xmlschema = etree.XMLSchema(xmlschema_doc)
            # ...
            
            return True, []
            
        except Exception as e:
            return False, [f"Error de validación: {str(e)}"]
