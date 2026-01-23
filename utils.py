import re
import pandas as pd
from .config import MESES_MAP, REGEX_FECHA_TEXTO


# Custom exceptions
class ExtractionError(Exception):
    """Error durante la extracción de texto."""

    pass


class ProcessingError(Exception):
    """Error durante el procesamiento de datos."""

    pass


class ValidationError(Exception):
    """Error de validación de datos."""

    pass


def debe_omitir_factura(texto: str) -> bool:
    """Verifica si la factura debe omitirse (ej. proveedores excluidos).

    Args:
        texto (str): Texto de la factura.

    Returns:
        bool: True si debe omitirse.
    """
    return "HERRERA MOTORS DE AGUASCALIENTES" in texto.upper()


def ordenar_facturas_por_fecha(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena el DataFrame de facturas por fecha.

    Args:
        df (pd.DataFrame): DataFrame con columna 'Fecha'.

    Returns:
        pd.DataFrame: DataFrame ordenado.
    """
    df["Fecha_dt"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
    df = df.sort_values(by="Fecha_dt").drop(columns=["Fecha_dt"])
    return df


def clean_date(fecha_str):
    """Limpia y estandariza una cadena de fecha.

    Args:
        fecha_str (str): Cadena de fecha cruda.

    Returns:
        str: Fecha en formato dd/mm/yyyy.
    """
    # Remove any trailing non-date characters
    match = re.match(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", fecha_str)
    if match:
        cleaned = match.group(1).replace("-", "/")
        # Detect format: if first number >12, assume yy/mm/dd, else dd/mm/yy
        parts = cleaned.split("/")
        if len(parts) == 3:
            a, b, c = map(int, parts)
            if a > 12 and b <= 12 and c <= 31:
                # yy/mm/dd
                year = 2000 + a
                month = b
                day = c
            else:
                # dd/mm/yy
                day = a
                month = b
                year = c
            if year < 100:
                year += 2000
            if year > 2030 or year < 2000:
                year = 2024
            cleaned = f"{day:02d}/{month:02d}/{year}"
        return cleaned
    return fecha_str


def clean_amount(amount_str):
    """Limpia una cadena de monto, removiendo caracteres no numéricos.

    Args:
        amount_str (str): Cadena de monto cruda.

    Returns:
        str: Monto limpio con solo dígitos y punto.
    """
    # Remove all non-digit except dots
    # (commas are thousands separators in Mexican format, so remove them)
    cleaned = re.sub(r"[^\d.]", "", amount_str)
    return cleaned


def convertir_fecha_texto(fecha_str):
    """Convierte fecha en texto (ej. '15 de agosto de 2024') a formato dd/mm/yyyy.

    Args:
        fecha_str (str): Fecha en texto.

    Returns:
        str or None: Fecha convertida o None si falla.
    """
    m = re.match(REGEX_FECHA_TEXTO, fecha_str, re.IGNORECASE)
    if not m:
        return None
    dia, mes_abrev, anio = m.groups()
    mes_abrev = mes_abrev.lower().replace("0", "o")
    mes_num = MESES_MAP.get(mes_abrev[:3])
    if not mes_num:
        return None
    return f"{int(dia):02d}/{mes_num}/{anio}"
