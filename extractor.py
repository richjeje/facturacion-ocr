import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
import pdfplumber
from PIL import Image
import os
import logging
import time
from .utils import ExtractionError

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path):
    """Extrae texto de un PDF usando pdfplumber, con fallback a OCR si no hay texto."""
    try:
        with pdfplumber.open(file_path) as pdf:
            texto = ""
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                texto += page_text + "\n"
        if texto.strip():
            logger.info(f"Texto extraído exitosamente de PDF: {file_path}")
            return texto, "Texto"
        else:
            logger.info(f"No texto en PDF {file_path}, intentando OCR...")
            # Fallback a OCR con reintentos
            return _ocr_from_pdf(file_path)
    except Exception as e:
        logger.error(f"Error extrayendo texto de PDF {file_path}: {e}")
        raise ExtractionError(f"Error en PDF {file_path}: {e}")

def _ocr_from_pdf(file_path):
    """Realiza OCR en PDF con reintentos."""
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            images = convert_from_path(file_path)
            texto = ""
            for img in images:
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
                img_cv = cv2.threshold(img_cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                texto += pytesseract.image_to_string(img_cv, lang="spa+eng") + "\n"
            if texto.strip():
                logger.info(f"OCR exitoso en PDF {file_path} en intento {attempt + 1}")
                return texto, "OCR"
            else:
                logger.warning(f"OCR sin texto en PDF {file_path}, intento {attempt + 1}")
        except Exception as e:
            logger.warning(f"Error en OCR de PDF {file_path}, intento {attempt + 1}: {e}")
            if attempt < max_retries:
                time.sleep(1 * (attempt + 1))  # Backoff
    logger.error(f"OCR falló definitivamente en PDF {file_path}")
    raise ExtractionError(f"OCR falló en PDF {file_path} tras {max_retries + 1} intentos")

def extract_text_from_image(file_path):
    """Extrae texto de una imagen usando OCR con reintentos y optimización."""
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            img_pil = Image.open(file_path)
            # Optimizar: redimensionar si es muy grande (>2000px en algún lado)
            if img_pil.width > 2000 or img_pil.height > 2000:
                ratio = min(2000 / img_pil.width, 2000 / img_pil.height)
                new_size = (int(img_pil.width * ratio), int(img_pil.height * ratio))
                img_pil = img_pil.resize(new_size, Image.Resampling.LANCZOS)
                logger.debug(f"Imagen redimensionada a {new_size} para {file_path}")

            img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            img_cv = cv2.threshold(img_cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            texto = pytesseract.image_to_string(img_cv, lang="spa+eng")
            if texto.strip():
                logger.info(f"OCR exitoso en imagen {file_path} en intento {attempt + 1}")
                return texto, "OCR"
            else:
                logger.warning(f"OCR sin texto en imagen {file_path}, intento {attempt + 1}")
        except Exception as e:
            logger.warning(f"Error en OCR de imagen {file_path}, intento {attempt + 1}: {e}")
            if attempt < max_retries:
                time.sleep(1 * (attempt + 1))  # Backoff
    logger.error(f"OCR falló definitivamente en imagen {file_path}")
    raise ExtractionError(f"OCR falló en imagen {file_path} tras {max_retries + 1} intentos")

def extract_text(file_path):
    """Función principal para extraer texto según tipo de archivo."""
    # Validación básica
    if not os.path.exists(file_path):
        raise ExtractionError(f"Archivo no existe: {file_path}")
    file_size = os.path.getsize(file_path)
    if file_size > 50 * 1024 * 1024:  # 50MB límite
        raise ExtractionError(f"Archivo demasiado grande: {file_path} ({file_size} bytes)")
    if not file_path.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
        raise ExtractionError(f"Tipo de archivo no soportado: {file_path}")

    logger.info(f"Iniciando extracción de texto para {file_path}")
    try:
        if file_path.lower().endswith('.pdf'):
            return extract_text_from_pdf(file_path)
        else:
            return extract_text_from_image(file_path)
    except ExtractionError as e:
        logger.error(f"Falló extracción de texto para {file_path}: {e}")
        raise