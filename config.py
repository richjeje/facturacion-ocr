import json
import os
import logging
from logging.handlers import RotatingFileHandler


# --- Cargar configuración ---
def load_config():
    """Carga configuraciones desde JSON con fallbacks a valores por defecto.

    Returns:
        dict: Diccionario con configuraciones cargadas.
    """
    config_data = {}
    try:
        with open("companies.json", "r", encoding="utf-8") as f:
            config_data.update(json.load(f))
    except FileNotFoundError:
        print("companies.json no encontrado, usando fallbacks")

    try:
        with open("patterns.json", "r", encoding="utf-8") as f:
            config_data.update(json.load(f))
    except FileNotFoundError:
        print("patterns.json no encontrado, usando fallbacks")

    return config_data


_config = load_config()

# --- Configuración de empresas ---
EMPRESAS_CONOCIDAS = _config.get(
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

CLASIFICACIONES_EMPRESAS = _config.get(
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

# --- Configuración de fechas ---
MESES_MAP = _config.get(
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

REGEX_FECHAS = _config.get(
    "regex_fechas",
    [
        r"\d{1,2}/\d{1,2}/\d{4}",
        r"\d{1,2}-\d{1,2}-\d{4}",
        r"\d{4}-\d{1,2}-\d{1,2}",
        r"\d{1,2}/\d{1,2}/\d{2}",  # Short year
        r"(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})",  # e.g., 15 de agosto de 2024
    ],
)
REGEX_FECHA_TEXTO = _config.get(
    "regex_fecha_texto",
    r"(\d{1,2})/([a-z0-9]{3})\.?/(\d{4})(?:\s+\d{1,2}:\d{2}:\d{2})?",
)

# --- Configuración de folios ---
FOLIO_PATTERNS = _config.get(
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

FOLIO_PATTERNS_GENERAL = _config.get(
    "folio_patterns_general",
    [
        r"Folio:\s*([0-9]+)",
        r"Folio[^f]*([0-9]+)",
        r"No\.?\s*Folio[^f]*([0-9]+)",
        r"Número\s*de\s*Folio[^f]*([0-9]+)",
        r"Num\.?\s*Folio[^f]*([0-9]+)",
        r"Folio\s+Fiscal[^f]*([0-9]+)",  # Sometimes "Folio Fiscal"
        r"(\d{5,10})",  # General 5-10 digit numbers, but filter carefully
    ],
)

# --- Configuración de FIX ---
FIX_ADDRESSES = _config.get(
    "fix_addresses",
    [
        "BLVD. ZACATECAS 204 ,EL PLATEADO 20137, AGUASCALIENTES AGUASCALIENTES, MEXICO",
        "AVENIDA SIGLO XXI 5021, OJOCALIENTE 20196 AGUASCALIENTES AGUASCALIENTES, MEXICO",
        "AVENIDA JOSE MARIA CHAVEZ 710.CP 20270, AGUASCALIENTES MEXICO, MEXICO AGUASCALIENTES",
    ],
)

# --- Regex adicionales ---
REGEX_SUBTOTALS = _config.get(
    "regex_subtotals",
    [
        r"sub\s*total[^\d]*\$?(\d+(?:[,.]\d+)*)",
        r"subtotal\s*:\s*\$?(\d+(?:[,.]\d+)*)",
        r"sub\s*total\s*\$?(\d+(?:[,.]\d+)*)",
        r"sub-?tot[^\d]*\$?(\d+(?:[,.]\d+)*)",
        r"importe\s*subtotal[^\d]*\$?(\d+(?:[,.]\d+)*)",
    ],
)

REGEX_TOTALS = _config.get(
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
REGEX_FECHA_TEXTO = r"(\d{1,2})/([a-z0-9]{3})\.?/(\d{4})(?:\s+\d{1,2}:\d{2}:\d{2})?"

# --- Configuración de folios ---
FOLIO_PATTERNS = {
    "WIZARD ZONE MEXICO": r"F(\d{4})",
    "PLOMERIA SELECTA": r"(\d{6}-[A-Z])",
    "OPERADORA OMX": r"OPERADORA OMX\s*([0-9]+)",
    "ROBERTO BRAVO GUTIERREZ": r"ROBERTO BRAVO GUTIERREZ\s*([0-9]+)",
    "HOME DEPOT MEXICO": r"HOME DEPOT MEXICO\s*([0-9]+)",
    "COMERCIAL ELECTRICA": r"([A-Z]{2}\d{8})",
}

FOLIO_PATTERNS_GENERAL = [
    r"Folio:\s*([0-9]+)",
    r"Folio[^f]*([0-9]+)",
    r"No\.?\s*Folio[^f]*([0-9]+)",
    r"Número\s*de\s*Folio[^f]*([0-9]+)",
    r"Num\.?\s*Folio[^f]*([0-9]+)",
    r"Folio\s+Fiscal[^f]*([0-9]+)",
    r"(\d{5,10})",  # General 5-10 digit numbers, but filter carefully
]

# --- Configuración de FIX ---
FIX_ADDRESSES = [
    "BLVD. ZACATECAS 204 ,EL PLATEADO 20137, AGUASCALIENTES AGUASCALIENTES, MEXICO",
    "AVENIDA SIGLO XXI 5021, OJOCALIENTE 20196 AGUASCALIENTES AGUASCALIENTES, MEXICO",
    "AVENIDA JOSE MARIA CHAVEZ 710.CP 20270, AGUASCALIENTES MEXICO, MEXICO AGUASCALIENTES",
]


# --- Funciones de configuración ---
def obtener_empresas_por_clasificacion():
    return CLASIFICACIONES_EMPRESAS


def setup_logging():
    """Configura logging centralizado con archivo rotativo y console.

    Returns:
        Logger: Instancia del logger configurado.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Formato
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Handler para archivo con rotación
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "processing.log"), maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
