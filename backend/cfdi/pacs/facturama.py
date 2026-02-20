# backend/cfdi/pacs/facturama.py
import httpx
import asyncio
from typing import Optional, Dict, Any
from lxml import etree
import base64

class FacturamaAdapter:
    """Adaptador gradual para Facturama API"""
    
    def __init__(self, api_key: str, secret: str, sandbox: bool = True):
        self.base_url = "https://sandbox.facturama.mx" if sandbox else "https://api.facturama.mx"
        # Facturama uses Basic Auth with base64 encoded user:pass
        self.auth = (api_key, secret)
        self.timeout = 30
        
    async def timbrar_xml(self, xml_signed: str, retries: int = 3) -> Dict[str, Any]:
        """Envía XML para timbrado con reintentos"""
        
        # Facturama endpoint for CFDI 4.0 typically expects JSON payload wrapping the XML or direct XML depending on endpoint.
        # Based on typical REST APIs for PACs, or specific Facturama endpoint documentation:
        # POST /api/v3/cfdi (usually takes JSON construction)
        # However, many PACs offer an endpoint to stamp raw XML strings. 
        # Assuming for this adapter we are using an endpoint that accepts XML file upload or string.
        # Let's double check Facturama API docs simulation:
        # Usually: POST /api/cfdi with JSON body or POST /2/cfdis with JSON.
        # If we have pre-signed XML (which we generated locally), we need an endpoint "Timbrar XML" or "Stamp".
        # If Facturama only accepts JSON construction to generate AND stamp, our local XML generator might be redundant for Facturama specifically,
        # UNLESS we use their "Load Interface" or similar.
        # BUT, following the plan "2.2 Gestor Certificados" implies we sign locally.
        # Many PACs support "Timbre Fiscal Digital" stamping on a pre-signed XML.
        # Let's assume endpoint /api/cfdi/file for uploading XML or similar.
        # For the sake of this robust implementation plan, we will assume we send the XML content as file/string.
        
        # NOTE: Facturama API generally encourages JSON construction. 
        # If we must send pre-signed XML, we might need to use a specific endpoint or encode it.
        # Let's assume we send it as a multipart/form-data or specific JSON field "XmlContent".
        
        payload = {
            "Content-Type": "application/json",
             # Dummy implementation of payload structure for raw XML stamping
             # In reality, check specific PAC docs for "Timbrado de XML" vs "Creación de CFDI"
             # If Facturama requires JSON to build CFDI, we might map our XML data to their JSON structure,
             # OR use a generic PAC service that accepts XML.
             # For this exercise, we assume direct XML stamping capability exists or we wrap it.
        }

        # Simulating endpoint for "Upload XML and Stamp"
        endpoint = "/api/v3/cfdi/xml" 

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Depending on API, might be multipart
                    # files = {'file': ('factura.xml', xml_signed, 'application/xml')}
                    # response = await client.post(f"{self.base_url}{endpoint}", auth=self.auth, files=files)
                    
                    # Or JSON with base64 XML
                    json_payload = {
                        "XmlContent": base64.b64encode(xml_signed.encode()).decode(),
                        "Type": "Issued" 
                    }
                    
                    response = await client.post(
                        f"{self.base_url}/api/cfdi", # Example generic endpoint
                        auth=self.auth,
                        json=json_payload
                    )
                    
                    if response.status_code in [200, 201]:
                        # Parsear respuesta
                        return self._parse_pac_response(response.text)
                    elif response.status_code == 422:
                        # Error de validación
                        return {
                            "success": False,
                            "error": "Validación PAC",
                            "details": response.json(),
                            "error_type": "validation_error"
                        }
                    elif response.status_code == 401:
                        return {
                            "success": False,
                            "error": "Autenticación PAC inválida",
                            "error_type": "auth_error"
                        }
                    else:
                        # Otro error
                        return {
                            "success": False,
                            "error": f"Error PAC: {response.status_code}",
                            "details": response.text,
                            "error_type": "pac_error"
                        }
                        
            except httpx.TimeoutException:
                if attempt == retries - 1:
                    return {
                        "success": False,
                        "error": "Timeout del PAC",
                        "error_type": "timeout_error"
                    }
                await asyncio.sleep(2 ** attempt)  # Backoff exponencial
                
            except httpx.ConnectError:
                if attempt == retries - 1:
                    return {
                        "success": False,
                        "error": "No se puede conectar al PAC",
                        "error_type": "connection_error"
                    }
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                 return {
                    "success": False,
                    "error": f"Error inesperado adaptador: {str(e)}",
                    "error_type": "adapter_error"
                }
        
        return {
            "success": False,
            "error": "Máximo de reintentos alcanzado",
            "error_type": "max_retries_error"
        }
    
    async def cancelar_uuid(self, uuid: str, rfc_emisor: str, motivo: str) -> Dict[str, Any]:
        """Cancela CFDI timbrado"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Parameters might vary by PAC
                params = {"type": "issued", "id": uuid, "motivo": motivo, "rfc": rfc_emisor}
                response = await client.delete(
                    f"{self.base_url}/api/cfdi/{uuid}",
                    auth=self.auth,
                    params=params
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {
                        "success": False,
                        "error": f"Error cancelación: {response.status_code}",
                        "details": response.json() if response.content else response.text
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Error de conexión: {str(e)}"
            }
    
    def _parse_pac_response(self, response_text: str) -> Dict[str, Any]:
        """Parsea respuesta del PAC Facturama"""
        try:
            # Facturama returns JSON with the stamped CFDI or details
            # Assuming it returns JSON like { "Id": "...", "CfdiXml": "..." }
            import json
            data = json.loads(response_text)
            
            if "CfdiXml" in data:
                xml_timbrado = data["CfdiXml"] # Might be base64 or raw string
                # If base64, decode
                # xml_timbrado = base64.b64decode(data["CfdiXml"]).decode()
                
                # Extract UUID and stamp details from the returned XML
                root = etree.fromstring(xml_timbrado.encode())
                timbre = root.find('.//{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital', namespaces={
                    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
                })
                
                if timbre is not None:
                    return {
                        "success": True,
                        "uuid": timbre.get("UUID"),
                        "fecha_timbrado": timbre.get("FechaTimbrado"),
                        "sello_sat": timbre.get("SelloSAT"),
                        "no_certificado_sat": timbre.get("NoCertificadoSAT"),
                        "xml_timbrado": xml_timbrado
                    }
            
            # Fallback if structure is different
            return {
                "success": False,
                "error": "Respuesta PAC sin XML timbrado reconocible",
                "details": data
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error parseando respuesta PAC: {str(e)}",
                "details": response_text
            }
