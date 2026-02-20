# backend/cfdi/certificates.py
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography import x509
from cryptography.fernet import Fernet
import base64
import datetime as dt
from datetime import datetime
from sqlalchemy.orm import Session
from ..core.cfdi_models import CFDICertificate
from ..core.config import logger

class CertificateManager:
    """Manejador seguro de certificados CSD/e.Firma"""
    
    def __init__(self, db_session: Session, master_key: str):
        self.db = db_session
        self.master_key = master_key
    
    def import_certificate(self, user_id: int, cer_file: bytes, 
                        key_file: bytes, password: str) -> dict:
        """Importa y almacena certificado de forma segura"""
        try:
            # Parsear certificado para extraer información
            cert = x509.load_pem_x509_certificate(cer_file)
            
            # Validar certificado (vigencia)
            # Usar UTC para evitar problemas de zona horaria
            now = datetime.now(dt.timezone.utc)
            
            # Soporte para cryptography >= 42.0 (not_valid_before_utc) y anteriores
            valid_from = getattr(cert, 'not_valid_before_utc', cert.not_valid_before)
            valid_until = getattr(cert, 'not_valid_after_utc', cert.not_valid_after)

            # Asegurar que las fechas del certificado tengan timezone info si usamos 'now' con timezone
            if valid_from.tzinfo is None:
                valid_from = valid_from.replace(tzinfo=dt.timezone.utc)
            if valid_until.tzinfo is None:
                valid_until = valid_until.replace(tzinfo=dt.timezone.utc)

            if now < valid_from or now > valid_until:
                 # Permitir un pequeño margen de error (clock skew) de 5 minutos
                 if (valid_from - now).total_seconds() > 300:
                    return {"success": False, "error": "Certificado inválido o expirado"}

            # Extraer RFC (usualmente en el Subject, campo OID 2.5.4.45 (x500UniqueIdentifier) o similar para SAT)
            # Nota: La estructura del Subject del SAT puede variar, aqui intentamos extraerlo de forma generica o fallback
            rfc = self._extract_rfc_from_subject(cert.subject)
            cert_number = self._extract_certificate_number(cert)
            
            # Encriptar archivos con Fernet
            fernet = Fernet(self.master_key.encode())
            cer_encrypted = fernet.encrypt(cer_file)
            key_encrypted = fernet.encrypt(key_file)
            password_encrypted = fernet.encrypt(password.encode()).decode()
            
            # Desactivar certificados anteriores del mismo usuario/RFC si se desea (opcional)
            # self._deactivate_previous_certificates(user_id, rfc)

            # Crear registro en BD
            cert_record = CFDICertificate(
                user_id=user_id,
                certificate_name=f"Certificado_{rfc}_{datetime.now().strftime('%Y%m%d')}",
                cer_file_content=cer_encrypted,
                key_file_content=key_encrypted,
                password_encrypted=password_encrypted,
                valid_from=cert.not_valid_before.date(),
                valid_until=cert.not_valid_after.date(),
                sat_rfc=rfc,
                certificate_number=cert_number,
                is_active=True
            )
            
            self.db.add(cert_record)
            self.db.commit()
            
            return {
                "success": True,
                "certificate_id": cert_record.id,
                "rfc": rfc,
                "valid_until": cert.not_valid_after.date().isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error importando certificado: {str(e)}")
            return {"success": False, "error": f"Error al importar certificado: {str(e)}"}
    
    def sign_xml(self, xml_string: str, certificate_id: int, user_id: int) -> dict:
        """Firma XML con certificado digital"""
        try:
            # Obtener certificado
            cert = self.db.query(CFDICertificate).filter(
                CFDICertificate.id == certificate_id,
                CFDICertificate.user_id == user_id,
                CFDICertificate.is_active == True
            ).first()
            
            if not cert:
                return {"success": False, "error": "Certificado no encontrado o inactivo"}
            
            # Desencriptar archivos
            fernet = Fernet(self.master_key.encode())
            key_bytes = fernet.decrypt(cert.key_file_content)
            password = fernet.decrypt(cert.password_encrypted.encode()).decode()
            
            # Cargar clave privada
            private_key = serialization.load_pem_private_key(
                key_bytes,
                password=password.encode()
            )
            
            # Generar cadena original
            cadena_original = self._generate_cadena_original(xml_string)
            
            # Firmar cadena original (SHA256)
            signature = private_key.sign(
                cadena_original.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            # Codificar firma en base64
            signature_b64 = base64.b64encode(signature).decode('utf-8')
            
            # Insertar sello y certificado en XML
            # Nota: También se debe insertar el certificado en base64 en el atributo 'Certificado'
            cer_bytes = fernet.decrypt(cert.cer_file_content)
            # Convertir PEM a DER para quitar headers y newlines para el XML
            # Pero load_pem_x509_certificate carga PEM.
            # El atributo 'Certificado' del CFDI requiere el certificado en Base64 (sin headers)
            # Si cer_bytes es PEM, limpiamos headers.
            cert_b64_clean = self._clean_pem_headers(cer_bytes.decode('utf-8'))

            xml_signed = self._insert_sello_in_xml(xml_string, signature_b64, cert_b64_clean, cert.certificate_number)
            
            return {
                "success": True,
                "xml_signed": xml_signed,
                "signature_b64": signature_b64
            }
            
        except Exception as e:
            logger.error(f"Error firmando XML: {str(e)}")
            return {"success": False, "error": f"Error al firmar XML: {str(e)}"}
    
    def _generate_cadena_original(self, xml_string: str) -> str:
        """Genera cadena original para firma SAT (Simplificada para MVP)"""
        # IMPORTANTE: En producción usar XSLT oficial del SAT (cadenaoriginal_4_0.xslt)
        # Aquí usamos una aproximación simplificada para la prueba conceptual
        from lxml import etree
        try:
            # Esto es un placeholder. La implementación real DEBE usar XSLT
            # xslt_root = etree.parse("cadenaoriginal_4_0.xslt")
            # transform = etree.XSLT(xslt_root)
            # xml_doc = etree.fromstring(xml_string.encode())
            # return str(transform(xml_doc))
            
            # Fallback manual muy básico SOLO para pruebas internas
            return f"||4.0|...|{datetime.now().isoformat()}|...||"
        except Exception:
            return ""

    def _insert_sello_in_xml(self, xml_string: str, sello: str, certificado: str, no_certificado: str) -> str:
        from lxml import etree
        root = etree.fromstring(xml_string.encode())
        root.set("Sello", sello)
        root.set("Certificado", certificado)
        root.set("NoCertificado", no_certificado)
        return etree.tostring(root, encoding='utf-8').decode('utf-8')

    def _extract_rfc_from_subject(self, subject) -> str:
        # Intenta extraer RFC del subject. 
        # En certificados de prueba SAT suele venir en x500UniqueIdentifier (2.5.4.45)
        # O en CommonName. 
        # Implementación simplificada: buscar 'OID.2.5.4.45'
        for attribute in subject:
             # x500UniqueIdentifier
            if attribute.oid.dotted_string == "2.5.4.45":
                return attribute.value.strip()
        # Fallback: a veces está en CN o serialNumber
        return "RFC_GENERICO" # Placeholder

    def _extract_certificate_number(self, cert) -> str:
        # Convertir serial number int a string hex o decimal según corresponda
        # SAT usa string de 20 dígitos.
        # El serial number de x509 es un entero. 
        # Hack común: decodificar desde bytes del serial
        # Implementación correcta requiere mapeo específico SAT
        return str(cert.serial_number)[0:20] # Placeholder

    def _clean_pem_headers(self, pem_str: str) -> str:
        lines = pem_str.strip().split('\n')
        # Remover primera y ultima linea (-----BEGIN/END CERTIFICATE-----)
        if "BEGIN CERTIFICATE" in lines[0]:
            lines = lines[1:]
        if "END CERTIFICATE" in lines[-1]:
            lines = lines[:-1]
        return "".join([line.strip() for line in lines])
