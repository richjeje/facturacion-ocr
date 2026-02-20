"""Tareas Celery para procesamiento asíncrono de facturas."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from celery import Celery

from backend.core.config import setup_logging
from backend.core.persistence import save_to_database
from backend.ocr.extractor import extract_text
from backend.parsing.processor import process_invoice_text

setup_logging()
logger = logging.getLogger(__name__)

celery_app = Celery("tasks")
celery_app.config_from_object("backend.worker.celeryconfig")


@celery_app.task(bind=True, max_retries=3)
def process_file_task(
    self,
    file_path: str,
    filename: str,
    client_name: str,
):
    """Procesa un archivo de factura de forma asíncrona.

    Args:
        file_path: Ruta temporal del archivo subido.
        filename: Nombre original del archivo.
        client_name: Identificador del cliente que realizó la llamada.
    """
    try:
        logger.info(
            "Procesando archivo async: %s para cliente: %s", filename, client_name
        )
        texto, metodo = extract_text(file_path)
        if not texto.strip():
            logger.warning("Texto vacío en archivo async: %s", filename)
            return None

        resultado = process_invoice_text(texto, metodo)
        if resultado:
            resultado["cliente"] = client_name
            save_to_database([resultado])
            logger.info(
                "Factura procesada async: %s — %s",
                resultado["Proveedor"],
                resultado["Folio"],
            )
            return resultado

        logger.warning("No se pudo procesar archivo async: %s", filename)
        return None
    except Exception as exc:
        logger.error("Error en tarea async para %s: %s", filename, exc)
        self.retry(countdown=60, exc=exc)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@celery_app.task
def cleanup_temp_files() -> None:
    """Elimina archivos temporales con prefijo ``temp_`` de más de 24 horas."""
    temp_dir = Path(".")
    cutoff = time.time() - 86_400  # 24 h
    for path in temp_dir.glob("temp_*"):
        if path.is_file() and path.stat().st_mtime < cutoff:
            path.unlink()
            logger.info("Limpiado archivo temp: %s", path.name)
