"""Configuración centralizada del sistema de facturación OCR.

Carga valores desde variables de entorno y archivos JSON externos,
con fallbacks a valores por defecto.
"""

from __future__ import annotations

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rutas base
# ---------------------------------------------------------------------------
# Directorio raíz del repositorio (dos niveles arriba de este archivo)
_ROOT_DIR = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT_DIR / "data"


def _load_json(filename: str) -> dict:
    """Carga un archivo JSON desde ``data/``, con fallback silencioso."""
    path = _DATA_DIR / filename
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("No se pudo leer %s: %s", path, exc)
    else:
        logger.warning("%s no encontrado, usando fallbacks.", path)
    return {}


_companies_data = _load_json("companies.json")
_patterns_data = _load_json("patterns.json")

# ---------------------------------------------------------------------------
# Configuración de empresas
# ---------------------------------------------------------------------------
EMPRESAS_CONOCIDAS: list[str] = _companies_data.get(
    "empresas_conocidas",
    [
        "UNIDAD DE GASOLINERAS",
        "MEXICANA DE TECNICOS EN AUTOPISTAS",
        "DELCASA FERRETERA",
        "WIZARD ZONE MEXICO",
        "DISTRIBUIDORA TAMEX",
        "JULIETA CAMPOS GONZALEZ",
        "STEREN",
        "PLOMERIA SELECTA",
        "FERRETERIA PROGRESO",
        "AUTO ZONE DE MEXICO",
        "TIENDAS FIX",
        "EDUARDO RODRIGUEZ LOPEZ",
        "EUROELECTRICA",
        "ACEROS ALCALDE",
        "DON PULCRO",
        "PLASTICOS RUSSELL",
        "TECNOTIENDAS AGUASCALIENTES",
        "ACEROS Y MATERIALES SAN JORGE",
        "MULTIHERRAMIENTAS DEL BAJIO",
        "SERVICIO Y MAQUINARIA DE AGUASCALIENTES",
        "LA INDUSTRIAL MEXICANA",
        "LIDIA MONTSERRAT MENDOZA NIETO",
        "KALISCH FIERRO Y ACERO",
        "ANTONIO PADILLA RAMIREZ",
        "EUGENIA MARIA ELENA VILLALPANDO",
        "LIMSA SA DE CV",
        "FRANCISCO JAVIER MARTINEZ GONZALEZ",
        "PLAFORAMA",
        "EDUARDO RODRIGUEZ LOPEZ DE LARA",
        "HOME DEPOT MEXICO",
        "SOLUCIONES EN ALUMINIO",
        "COMEX",
        "OFFICE DEPOT",
        "MASTER DEPOT",
        "PINTURAS Y COMPLEMENTOS ORLOP SA DE CV",
        "PINTURAS MUÑOZ",
        "ADRIANA ANGELA ROMERO ANDRADE",
        "COMERCIAL ELECTRICA",
        "IMPERMEABILIZANTES Y MATERIALES DEL CENTRO",
        "LAURA CENTENO JIMENEZ",
        "RAUL SALAZAR MARTINEZ",
        "DISTRIBUIDORA TAMEX SAPI DE CV",
        "TAISA ACABADOS",
        "PISOS Y CERAMICOS DE AGUASCALIENTES",
        "FARMACIAS",
        "SERVICIO MAPRO SA DE CV",
        "FIX",
        "OPERADORA OMX",
        "MERCEDES ALEJANDRA LOPEZ MORALES",
        "OSCAR DELGADO CASAS",
        "ROBERTO BRAVO GUTIERREZ",
        "ISRAEL HERRERA SUBIAS",
        "LUIS FERNANDO MACIAS AVILA",
        "SURTIDORA DE ALAMBRES Y ACEROS DEL CENTRO",
        "AUTOZONE",
        "FC FACIL DE CONTRUIR",
        "TAISA CONSTRUCCIONES",
        "MARTIN ORTEGA MATINEZ",
        "NATALIE MACIAS CAMARILLO",
        "GERSA",
        "ANA CECILIA ESQUIVEL COSSIO",
        "CHELECTRONICA",
        "MARIA ISIDORA SOTO RAMIRES",
        "INDUSTRIAL ELECTRICA",
        "HUMBERTO PALOS LOMELI",
    ],
)

CLASIFICACIONES_EMPRESAS: dict[str, list[str]] = _companies_data.get(
    "clasificaciones_empresas",
    {
        "ferreteria": [
            "ACEROS ALCALDE",
            "ACEROS Y MATERIALES SAN JORGE",
            "DELCASA FERRETERA",
            "DELCASA FERRETERIA",
            "EDUARDO RODRIGUEZ LOPEZ",
            "FIX FERRETERIAS",
            "HOME DEPOT MEXICO",
            "JULIETA CAMPOS GONZALEZ",
            "KALISCH FIERRO Y ACERO",
            "LAURA CENTENO JIMENEZ",
            "LIDIA MONTSERRAT MENDOZA NIETO",
            "MASTER DEPOT",
            "MULTIHERRAMIENTAS DEL BAJIO",
            "PLAFORAMA",
            "SOLUCIONES EN ALUMINIO",
            "TAISA ACABADOS",
            "WIZARD ZONE MEXICO",
            "IMPERMEABILIZANTES Y MATERIALES DEL CENTRO",
            "SERVICIO MAPRO SA DE CV",
            "MERCEDES ALEJANDRA LOPEZ MORALES",
            "OSCAR DELGADO CASAS",
            "ROBERTO BRAVO GUTIERREZ",
            "ISRAEL HERRERA SUBIAS",
            "LUIS FERNANDO MACIAS AVILA",
            "SURTIDORA DE ALAMBRES Y ACEROS DEL CENTRO",
            "AUTOZONE",
            "TIENDAS FIX",
            "FC FACIL DE CONTRUIR",
            "TAISA CONSTRUCCIONES",
            "MARTIN ORTEGA MATINEZ",
            "NATALIE MACIAS CAMARILLO",
            "GERSA",
        ],
        "material electrico": [
            "COMERCIAL ELECTRICA",
            "DISTRIBUIDORA TAMEX",
            "DISTRIBUIDORA TAMEX SAPI DE CV",
            "EUROELECTRICA",
            "EUGENIA MARIA ELENA VILLALPANDO",
            "INDUSTRIAL ELECTRICA",
        ],
        "plomeria": [
            "LA INDUSTRIAL MEXICANA",
            "LIMSA SA DE CV",
            "PLOMERIA SELECTA",
            "PLASTICOS RUSSELL",
            "ANA CECILIA ESQUIVEL COSSIO",
        ],
        "maquinaria": [
            "RAUL SALAZAR MARTINEZ",
            "SERVICIO Y MAQUINARIA DE AGUASCALIENTES",
        ],
        "refaccion": ["AUTO ZONE DE MEXICO"],
        "limpieza": ["DON PULCRO"],
        "voz y datos": ["STEREN", "TECNOTIENDAS AGUASCALIENTES", "CHELECTRONICA"],
        "papeleria": [
            "ANTONIO PADILLA RAMIREZ",
            "OFFICE DEPOT",
            "MARIA ISIDORA SOTO RAMIRES",
            "OPERADORA OMX",
        ],
        "tornilleria": ["EDUARDO RODRIGUEZ LOPEZ DE LARA"],
        "pintura": [
            "COMEX",
            "PINTURAS MUÑOZ",
            "PINTURAS Y COMPLEMENTOS ORLOP SA DE CV",
        ],
        "casetas": ["MEXICANA DE TECNICOS EN AUTOPISTAS"],
        "gasolina": ["UNIDAD DE GASOLINERAS"],
        "seguridad": ["ADRIANA ANGELA ROMERO ANDRADE"],
        "farmacias": ["FARMACIAS"],
        "material para pisos": ["PISOS Y CERAMICOS DE AGUASCALIENTES"],
        "reparacion de herramienta": ["FRANCISCO JAVIER MARTINEZ GONZALEZ"],
    },
)

# ---------------------------------------------------------------------------
# Configuración de fechas
# ---------------------------------------------------------------------------
MESES_MAP: dict[str, str] = _patterns_data.get(
    "meses_map",
    {
        "ene": "01",
        "feb": "02",
        "mar": "03",
        "abr": "04",
        "may": "05",
        "jun": "06",
        "jul": "07",
        "ago": "08",
        "sep": "09",
        "oct": "10",
        "nov": "11",
        "dic": "12",
        "nev": "11",
    },
)

REGEX_FECHAS: list[str] = _patterns_data.get(
    "regex_fechas",
    [
        r"\d{1,2}/\d{1,2}/\d{4}",
        r"\d{1,2}-\d{1,2}-\d{4}",
        r"\d{4}-\d{1,2}-\d{1,2}",
        r"\d{1,2}/\d{1,2}/\d{2}",
        r"(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})",
    ],
)

REGEX_FECHA_TEXTO: str = _patterns_data.get(
    "regex_fecha_texto",
    r"(\d{1,2})/([a-z0-9]{3})\.?/(\d{4})(?:\s+\d{1,2}:\d{2}:\d{2})?",
)

# ---------------------------------------------------------------------------
# Configuración de folios
# ---------------------------------------------------------------------------
FOLIO_PATTERNS: dict[str, str] = _patterns_data.get(
    "folio_patterns",
    {
        "WIZARD ZONE MEXICO": r"F(\d{4})",
        "PLOMERIA SELECTA": r"(\d{6}-[A-Z])",
        "OPERADORA OMX": r"OPERADORA OMX\s*([0-9]+)",
        "ROBERTO BRAVO GUTIERREZ": r"ROBERTO BRAVO GUTIERREZ\s*([0-9]+)",
        "HOME DEPOT MEXICO": r"HOME DEPOT MEXICO\s*([0-9]+)",
        "COMERCIAL ELECTRICA": r"([A-Z]{2}\d{8})",
    },
)

FOLIO_PATTERNS_GENERAL: list[str] = _patterns_data.get(
    "folio_patterns_general",
    [
        r"Folio:\s*([0-9]+)",
        r"Folio[^f]*([0-9]+)",
        r"No\.?\s*Folio[^f]*([0-9]+)",
        r"Número\s*de\s*Folio[^f]*([0-9]+)",
        r"Num\.?\s*Folio[^f]*([0-9]+)",
        r"Folio\s+Fiscal[^f]*([0-9]+)",
        r"(\d{5,10})",
    ],
)

# ---------------------------------------------------------------------------
# Configuración de FIX
# ---------------------------------------------------------------------------
FIX_ADDRESSES: list[str] = _patterns_data.get(
    "fix_addresses",
    [
        "BLVD. ZACATECAS 204 ,EL PLATEADO 20137, AGUASCALIENTES AGUASCALIENTES, MEXICO",
        "AVENIDA SIGLO XXI 5021, OJOCALIENTE 20196 AGUASCALIENTES AGUASCALIENTES, MEXICO",
        "AVENIDA JOSE MARIA CHAVEZ 710.CP 20270, AGUASCALIENTES MEXICO, MEXICO AGUASCALIENTES",
    ],
)

# ---------------------------------------------------------------------------
# Regex de montos
# ---------------------------------------------------------------------------
REGEX_SUBTOTALS: list[str] = _patterns_data.get(
    "regex_subtotals",
    [
        r"sub\s*total[^\d]*\$?(\d+(?:[,.]\d+)*)",
        r"subtotal\s*:\s*\$?(\d+(?:[,.]\d+)*)",
        r"sub\s*total\s*\$?(\d+(?:[,.]\d+)*)",
        r"sub-?tot[^\d]*\$?(\d+(?:[,.]\d+)*)",
        r"importe\s*subtotal[^\d]*\$?(\d+(?:[,.]\d+)*)",
    ],
)

REGEX_TOTALS: list[str] = _patterns_data.get(
    "regex_totals",
    [
        r"total[^\d]*\$?\s*(\d+(?:[,.]\d+)*)",
        r"total\s*:\s*\$?\s*(\d+(?:[,.]\d+)*)",
        r"total\s+a\s+pagar[^\d]*\$?\s*(\d+(?:[,.]\d+)*)",
        r"importe\s+total[^\d]*\$?\s*(\d+(?:[,.]\d+)*)",
        r"gran\s+total[^\d]*\$?\s*(\d+(?:[,.]\d+)*)",
        r"total\s+final[^\d]*\$?\s*(\d+(?:[,.]\d+)*)",
    ],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def obtener_empresas_por_clasificacion() -> dict[str, list[str]]:
    """Devuelve el mapa de clasificaciones → empresas."""
    return CLASIFICACIONES_EMPRESAS


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    """Configura logging centralizado con archivo rotativo y consola.

    Idempotente: si el root logger ya tiene handlers no los duplica.

    Returns:
        Logger: Logger raíz configurado.
    """
    root = logging.getLogger()
    if root.handlers:
        return root

    root.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_dir = _ROOT_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / "processing.log", maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    return root
