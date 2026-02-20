import re
import logging
from typing import Optional, Dict, Any
from fuzzywuzzy import fuzz
from core.config import (
    EMPRESAS_CONOCIDAS,
    obtener_empresas_por_clasificacion,
    REGEX_FECHAS,
    REGEX_FECHA_TEXTO,
    FOLIO_PATTERNS,
    FOLIO_PATTERNS_GENERAL,
    FIX_ADDRESSES,
    REGEX_SUBTOTALS,
    REGEX_TOTALS,
)
from core.utils import (
    clean_date,
    clean_amount,
    convertir_fecha_texto,
    debe_omitir_factura,
    ValidationError,
)

logger = logging.getLogger(__name__)


def process_invoice_text(texto: str, metodo_extraccion: str) -> Optional[Dict[str, Any]]:
    """Procesa el texto extraído de una factura y devuelve un diccionario
    con los datos parseados."""
    if debe_omitir_factura(texto):
        return None

    fecha, folio, subtotal, total, iva = "", "", 0.0, 0.0, 0.0

    # --- Extraer Fecha ---
    match_texto = re.search(REGEX_FECHA_TEXTO, texto, re.IGNORECASE)
    if match_texto:
        fecha = convertir_fecha_texto(match_texto.group())
        fecha = clean_date(fecha) if fecha else ""
    else:
        for patron in REGEX_FECHAS:
            match = re.search(patron, texto)
            if match:
                fecha = match.group()
                if patron == r"\d{1,2}-\d{1,2}-\d{4}":
                    fecha = fecha.replace("-", "/")
                elif patron == r"\d{4}-\d{1,2}-\d{1,2}":
                    parts = fecha.split("-")
                    fecha = f"{parts[2].zfill(2)}/{parts[1].zfill(2)}/{parts[0]}"
                fecha = clean_date(fecha)
                break

    # --- Extraer Folio ---
    # Primero, patrones específicos por proveedor
    proveedor_temp = None
    texto_upper = texto.upper()
    for emp in EMPRESAS_CONOCIDAS:
        ratio = fuzz.partial_ratio(emp, texto_upper)
        if ratio > 50:
            proveedor_temp = emp
            break
    if proveedor_temp == "PLOMERIA SELECTA":
        match_folio = re.search(r"Fo.*Intern.*:\s*([A-Z0-9\s-]+)", texto, re.IGNORECASE)
        if match_folio:
            folio_raw = match_folio.group(1)
            folio = re.sub(r"[^A-Z0-9-]", "", folio_raw).strip()
            if len(folio) > 8:
                folio = folio[:8]
    elif proveedor_temp == "SERVICIO MAPRO SA DE CV":
        match_folio = re.search(r"Folio:\s*([A-Z0-9?]+)", texto, re.IGNORECASE)
        if match_folio:
            folio = match_folio.group(1).replace("?", "2")
    elif proveedor_temp in ["TIENDAS FIX", "FIX", "MULTIHERRAMIENTAS DEL BAJIO"]:
        match_folio = re.search(r"Folio[^f]*(\d{5})", texto, re.IGNORECASE)
        if match_folio:
            folio = match_folio.group(1)
        else:
            matches = re.findall(r"\b\d{5}\b", texto)
            if matches:
                folio = matches[0]
    elif proveedor_temp == "LA INDUSTRIAL MEXICANA":
        match_folio = re.search(r"Folio[^f]*(\d{6})", texto, re.IGNORECASE)
        if match_folio:
            folio = match_folio.group(1)
        else:
            matches = re.findall(r"\b\d{6}\b", texto)
            if matches:
                folio = matches[0]
    elif proveedor_temp in FOLIO_PATTERNS:
        match_folio = re.search(FOLIO_PATTERNS[proveedor_temp], texto)
        if match_folio:
            folio = match_folio.group(1)

    if not folio:
        for patron in FOLIO_PATTERNS_GENERAL:
            matches = re.findall(patron, texto, re.IGNORECASE)
            for m in matches:
                full_match_str = (
                    patron.replace("([0-9]+)", re.escape(m))
                    if "([0-9]+)" in patron
                    else patron.replace("(\\d{5,10})", re.escape(m))
                )
                full_match = re.search(full_match_str, texto, re.IGNORECASE)
                if full_match:
                    start = max(0, full_match.start() - 50)
                    end = min(len(texto), full_match.end() + 50)
                    context = texto[start:end].lower()
                    if (
                        "c.p." in context
                        or "codigo postal" in context
                        or "código postal" in context
                        or "cp" in context
                        or "postal" in context
                    ):
                        continue
                    if (
                        "fiscal" not in full_match.group(0).lower()
                        and "serle" not in full_match.group(0).lower()
                        and "flacal" not in full_match.group(0).lower()
                        and len(m) > 2
                        and m.lower()
                        not in [
                            "no",
                            "folio",
                            "fecha",
                            "de",
                            "fc",
                            "serie",
                            "cag",
                            "fao",
                            "fa",
                            "a",
                            "fpn",
                            "sla",
                            "00007104",
                            "2024",
                            "2023",
                            "2025",
                        ]
                        and not m.startswith("0000")
                    ):
                        if re.match(r"\d{1,2}/\d{1,2}/\d{4}", m) or re.match(
                            r"\d{4}-\d{1,2}-\d{1,2}", m
                        ):
                            continue
                        folio = m
                        break
            if folio:
                break

    # --- Extraer Subtotal ---
    for patron in REGEX_SUBTOTALS:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            subtotal = float(clean_amount(match.group(1)))
            break

    # --- Extraer Total ---
    for patron in REGEX_TOTALS:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            total = float(clean_amount(match.group(1)))
            break

    # --- Calcular IVA y Totales ---
    if subtotal > 0:
        iva = round(subtotal * 0.16, 2)
        total = round(subtotal + iva, 2)
    elif total > 0:
        subtotal = round(total / 1.16, 2)
        iva = round(total - subtotal, 2)
    else:
        iva = 0.0
        total = 0.0

    # --- Identificar Proveedor ---
    proveedor, tipo, max_ratio = "DESCONOCIDA", "DESCONOCIDA", 0
    for emp in EMPRESAS_CONOCIDAS:
        ratio = fuzz.partial_ratio(emp, texto_upper)
        if ratio > max_ratio:
            max_ratio, proveedor = ratio, emp
    if max_ratio >= 50:
        clasificaciones = obtener_empresas_por_clasificacion()
        for cat, emps in clasificaciones.items():
            if proveedor in emps:
                tipo = cat.upper()
                break

    # Merge FIX
    if proveedor == "FIX":
        proveedor = "TIENDAS FIX"

    # Override FIX
    for addr in FIX_ADDRESSES:
        if addr in texto_upper:
            proveedor = "TIENDAS FIX"
            tipo = "FERRETERIA"
            max_ratio = 100
            break

    if max_ratio < 60:
        logger.warning(
            f"Confianza baja en proveedor ({max_ratio}%): {proveedor}, omitiendo factura."
        )
        return None
    if max_ratio < 70:
        logger.warning(f"Baja confianza en proveedor ({max_ratio}%): {proveedor}")

    # --- Extraer URL ---
    url_match = re.search(r"https?://[^\s]+", texto)
    url = url_match.group(0) if url_match else ""

    # --- Validaciones ---
    if not fecha:
        raise ValidationError("Fecha no encontrada o inválida")
    if subtotal <= 0 and total <= 0:
        raise ValidationError("Subtotal y total inválidos o cero")
    if not folio:
        logger.warning("Folio no encontrado, pero continuando")
    if proveedor == "DESCONOCIDA":
        raise ValidationError("Proveedor no identificado")

    logger.info(
        f"Procesamiento exitoso: Proveedor {proveedor}, Folio {folio}, Total {total}"
    )

    return {
        "Fecha": fecha,
        "Proveedor": proveedor,
        "Concepto": tipo,
        "Folio": folio,
        "Subtotal": subtotal,
        "IVA": iva,
        "Total": total,
        "Metodo_Extraccion": metodo_extraccion,
        "Confianza_Proveedor": max_ratio,
        "URL": url,
    }
