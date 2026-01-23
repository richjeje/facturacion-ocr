import os
import pandas as pd
import time
import datetime
import tempfile
import shutil
import logging
import concurrent.futures
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from extractor import extract_text
from processor import process_invoice_text
from utils import (
    ordenar_facturas_por_fecha,
    ExtractionError,
    ProcessingError,
    ValidationError,
)
from config import setup_logging

# DB PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@host/db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    fecha = Column(String, index=True)
    proveedor = Column(String, index=True)
    concepto = Column(String)
    folio = Column(String)
    subtotal = Column(Float)
    iva = Column(Float)
    total = Column(Float)
    metodo_extraccion = Column(String)
    confianza_proveedor = Column(Float)
    url = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)


Base.metadata.create_all(bind=engine)

# --- Configurar logging ---
logger = setup_logging()

# --- Carpetas ---
carpeta = "imagenes"
output_dir = "output"
os.makedirs(carpeta, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

# --- Procesamiento ---
datos = []
rename_counter = 0


def save_to_database(datos):
    """Guarda datos en PostgreSQL DB."""
    db = SessionLocal()
    try:
        for dato in datos:
            invoice = Invoice(**dato)
            db.add(invoice)
        db.commit()
        logger.info(f"Datos guardados en BD: {len(datos)} registros")
    except Exception as e:
        db.rollback()
        logger.error(f"Error guardando en BD: {e}")
    finally:
        db.close()


def _rename_failed_file(ruta, archivo):
    global rename_counter
    now = datetime.datetime.now()
    ext = archivo.split(".")[-1]
    new_name = f"procesado_{now.strftime('%d_%m_%Y')}_{rename_counter}.{ext}"
    new_path = os.path.join(carpeta, new_name)
    try:
        os.rename(ruta, new_path)
        logger.info(f"Archivo renombrado a {new_name}")
        rename_counter += 1
    except Exception as rename_e:
        logger.error(f"Error renombrando {archivo}: {rename_e}")


def process_single_file(archivo):
    """Procesa un archivo individual y devuelve resultado o None."""
    ruta = os.path.join(carpeta, archivo)
    logger.info(f"Procesando archivo: {archivo}")
    try:
        texto, metodo = extract_text(ruta)
        logger.debug(f"Texto extraído: {texto[:500]}...")
        if texto.strip():
            resultado = process_invoice_text(texto, metodo)
            if resultado:
                logger.info(
                    "Factura procesada exitosamente: "
                    f"{resultado['Proveedor']} - {resultado['Folio']}"
                )
                return resultado
        else:
            logger.warning(f"Texto vacío extraído de {archivo}")
    except ExtractionError as e:
        logger.error(f"Error de extracción en {archivo}: {e}")
        # Renombrar si es imagen
        if not archivo.lower().endswith(".pdf"):
            _rename_failed_file(ruta, archivo)
    except ProcessingError as e:
        logger.error(f"Error de procesamiento en {archivo}: {e}")
    except ValidationError as e:
        logger.error(f"Error de validación en {archivo}: {e}")
    except Exception as e:
        logger.error(f"Error inesperado en {archivo}: {e}")
    return None


# --- Configuración de procesamiento ---
max_files_input = input(
    "¿Cuántos archivos deseas procesar? (presiona Enter para todos): "
).strip()
if max_files_input.isdigit():
    max_files = int(max_files_input)
else:
    max_files = None

# --- Main loop ---
archivos = os.listdir(carpeta)
archivos_filtrados = sorted(
    [f for f in archivos if f.lower().endswith((".pdf", ".jpg", ".jpeg", ".png"))]
)
if max_files is not None:
    archivos_filtrados = archivos_filtrados[:max_files]

# Procesamiento paralelo
with concurrent.futures.ThreadPoolExecutor(
    max_workers=min(4, len(archivos_filtrados))
) as executor:
    futures = {
        executor.submit(process_single_file, archivo): archivo
        for archivo in archivos_filtrados
    }
    for future in concurrent.futures.as_completed(futures):
        archivo = futures[future]
        try:
            resultado = future.result()
            if resultado:
                datos.append(resultado)
        except Exception as e:
            logger.error(f"Error en future para {archivo}: {e}")

# --- Guardar resultados ---
if datos:
    # Guardar en BD
    save_to_database(datos)

    # También guardar en Excel para compatibilidad
    df = pd.DataFrame(datos)
    orden = [
        "Fecha",
        "Proveedor",
        "Concepto",
        "Folio",
        "Subtotal",
        "IVA",
        "Total",
        "Metodo_Extraccion",
        "Confianza_Proveedor",
        "URL",
    ]
    df = ordenar_facturas_por_fecha(df[orden])
    df = df.drop_duplicates()

    excel_path = os.path.join(output_dir, "facturas_procesadas.xlsx")
    lock_path = os.path.join(output_dir, "excel_lock.lock")

    while os.path.exists(lock_path):
        time.sleep(0.1)
    open(lock_path, "w").close()

    try:
        if os.path.exists(excel_path):
            existing_df = pd.read_excel(excel_path)
            combined_df = ordenar_facturas_por_fecha(
                pd.concat([existing_df, df], ignore_index=True)
            )
            combined_df = combined_df.drop_duplicates()
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".xlsx", dir=output_dir
            ) as tmp:
                combined_df.to_excel(tmp.name, index=False)
                temp_path = tmp.name
            shutil.move(temp_path, excel_path)
        else:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".xlsx", dir=output_dir
            ) as tmp:
                df.to_excel(tmp.name, index=False)
                temp_path = tmp.name
            shutil.move(temp_path, excel_path)
    finally:
        if os.path.exists(lock_path):
            os.remove(lock_path)

    logger.info(f"Proceso completado. Datos en BD y Excel: {excel_path}")
else:
    logger.warning("No se extrajo información de los archivos")
