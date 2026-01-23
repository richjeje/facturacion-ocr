import cv2
import pytesseract
from PIL import Image
import re
import numpy as np
from fuzzywuzzy import fuzz

# Load image
img_pil = Image.open('imagenes/Img_20251003180404_008.jpeg')
img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
img_cv = cv2.threshold(img_cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
texto = pytesseract.image_to_string(img_cv, lang="spa+eng")
print("Extracted text:")
print(texto)

# Identify provider
empresas_conocidas = [
    "LA INDUSTRIAL MEXICANA",
    # Add others if needed
]
proveedor, max_ratio = "DESCONOCIDA", 0
texto_upper = texto.upper()
for emp in empresas_conocidas:
    ratio = fuzz.partial_ratio(emp, texto_upper)
    if ratio > max_ratio:
        max_ratio, proveedor = ratio, emp

print(f"Identified provider: {proveedor} with ratio {max_ratio}")

# Extract folio based on provider
folio = ""
if proveedor == "LA INDUSTRIAL MEXICANA":
    match_folio = re.search(r"Folio[^f]*(\d{6})", texto, re.IGNORECASE)
    if match_folio:
        folio = match_folio.group(1)
        print(f"Found 6-digit folio: {folio}")
    else:
        # Buscar números de 6 dígitos independientes
        matches = re.findall(r"\b\d{6}\b", texto)
        if matches:
            folio = matches[0]
            print(f"Found standalone 6-digit folio: {folio}")
else:
    # General patterns
    folio_patterns_general = [
        r"Folio:\s*([0-9]+)",
        r"Folio[^f]*([0-9]+)",
        r"No\.?\s*Folio[^f]*([0-9]+)",
        r"Número\s*de\s*Folio[^f]*([0-9]+)",
        r"Num\.?\s*Folio[^f]*([0-9]+)",
    ]

    for patron in folio_patterns_general:
        matches = re.findall(patron, texto, re.IGNORECASE)
        print(f"Pattern {patron}: matches {matches}")
        for m in matches:
            full_match_str = patron.replace("([0-9]+)", re.escape(m))
            full_match = re.search(full_match_str, texto, re.IGNORECASE)
            if full_match and "fiscal" not in full_match.group(0).lower() and "serle" not in full_match.group(0).lower() and "flacal" not in full_match.group(0).lower() and len(m) > 2 and m.lower() not in ["no", "folio", "fecha", "de", "fc", "serie", "cag", "fao", "fa", "a", "fpn", "sla", "00007104"]:
                folio = m
                print(f"Found folio: {folio}")
                break
        if folio: break

print(f"Final folio: {folio}")
