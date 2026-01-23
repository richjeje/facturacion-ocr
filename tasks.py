from celery import Celery
from extractor import extract_text
from processor import process_invoice_text
from config import setup_logging
from main import save_to_database

logger = setup_logging()

celery_app = Celery('tasks')
celery_app.config_from_object('celeryconfig')

@celery_app.task(bind=True, max_retries=3)
def process_file_task(self, file_path, filename, client_name):
    """Tarea Celery para procesar archivo asíncronamente."""
    try:
        logger.info(f"Procesando archivo async: {filename} para cliente: {client_name}")
        texto, metodo = extract_text(file_path)
        if texto.strip():
            resultado = process_invoice_text(texto, metodo)
            if resultado:
                # Agregar client_name al resultado
                resultado['cliente'] = client_name
                # Guardar en BD
                save_to_database([resultado])
                logger.info(f"Factura procesada async: {resultado['Proveedor']} - {resultado['Folio']}")
                return resultado
        logger.warning(f"No se pudo procesar archivo async: {filename}")
        return None
    except Exception as e:
        logger.error(f"Error en tarea async para {filename}: {e}")
        self.retry(countdown=60, exc=e)  # Reintentar en 1 min
    finally:
        # Limpiar archivo temp si existe
        import os
        if os.path.exists(file_path):
            os.remove(file_path)