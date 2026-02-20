"""Utilidades compartidas: excepciones personalizadas y helpers de texto."""

from __future__ import annotations

import re
from typing import Optional, TYPE_CHECKING

from .config import MESES_MAP, REGEX_FECHA_TEXTO

if TYPE_CHECKING:
    import pandas as pd


# ---------------------------------------------------------------------------
# Excepciones personalizadas
# ---------------------------------------------------------------------------
class ExtractionError(Exception):
    """Error durante la extracción de texto desde un archivo."""


class ProcessingError(Exception):
    """Error durante el procesamiento / parsing de una factura."""


class ValidationError(Exception):
    """Error de validación de datos de factura."""


# ---------------------------------------------------------------------------
# Helpers de texto
# ---------------------------------------------------------------------------
def debe_omitir_factura(texto: str) -> bool:
    """Devuelve ``True`` si la factura corresponde a un proveedor excluido."""
    return "HERRERA MOTORS DE AGUASCALIENTES" in texto.upper()


def ordenar_facturas_por_fecha(df: "pd.DataFrame") -> "pd.DataFrame":
    """Ordena un DataFrame de facturas por la columna ``Fecha`` (dd/mm/yyyy)."""
    import pandas as pd  # import local para no hacer pandas obligatorio en imports

    df = df.copy()
    df["_fecha_dt"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
    df = df.sort_values(by="_fecha_dt").drop(columns=["_fecha_dt"])
    return df


def clean_date(fecha_str: str) -> str:
    """Limpia y estandariza una cadena de fecha a ``dd/mm/yyyy``.

    Args:
        fecha_str: Cadena de fecha cruda.

    Returns:
        Fecha en formato ``dd/mm/yyyy``.
    """
    match = re.match(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", fecha_str)
    if not match:
        return fecha_str

    cleaned = match.group(1).replace("-", "/")
    parts = cleaned.split("/")
    if len(parts) == 3:
        a, b, c = (int(p) for p in parts)
        if a > 12 and b <= 12 and c <= 31:
            # Formato yy/mm/dd
            year, month, day = 2000 + a, b, c
        else:
            # Formato dd/mm/yy
            day, month, year = a, b, c
        if year < 100:
            year += 2000
        if year > 2030 or year < 2000:
            year = 2024
        return f"{day:02d}/{month:02d}/{year}"
    return cleaned


def clean_amount(amount_str: str) -> str:
    """Elimina todo excepto dígitos y punto de una cadena de monto.

    Las comas se tratan como separadores de miles (formato mexicano).

    Args:
        amount_str: Cadena de monto cruda.

    Returns:
        Cadena con sólo dígitos y punto decimal.
    """
    return re.sub(r"[^\d.]", "", amount_str)


def convertir_fecha_texto(fecha_str: str) -> Optional[str]:
    """Convierte una fecha textual tipo ``15/ago/2024`` a ``dd/mm/yyyy``.

    Args:
        fecha_str: Fecha en formato textual.

    Returns:
        Fecha en formato ``dd/mm/yyyy`` o ``None`` si no se puede convertir.
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
