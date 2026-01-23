import os
import cv2
import pytesseract
import pandas as pd
import re
import numpy as np
from fuzzywuzzy import fuzz
from pdf2image import convert_from_path
import pdfplumber
import time


def debe_omitir_factura(texto: str) -> bool:
    return "HERRERA MOTORS DE AGUASCALIENTES" in texto.upper()


def ordenar_facturas_por_fecha(df: pd.DataFrame) -> pd.DataFrame:
    df["Fecha_dt"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
    df = df.sort_values(by="Fecha_dt")
    return df.drop(columns=["Fecha_dt"])


carpeta = "imagenes"

empresas_conocidas = list(
    set(
        [
            "UNIDAD DE GASOLINERAS",
            "MEXICANA DE TECNICOS EN AUTOPISTAS",
            "DELCASA FERRETERA",
            "DELCASA FERRETERIA",
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
            "FIX FERRETERIAS",
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
        ]
    )
)


# --- Clasificación empresas ---
def obtener_empresas_por_clasificacion():
    return {
        "ferreteria": [
            "ACEROS ALCALDE",
            "ACEROS Y MATERIALES SAN JORGE",
            "DELCASA FERRETERA",
            "DELCASA FERRETERIA",
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
        ],
        "material electrico": [
            "COMERCIAL ELECTRICA",
            "DISTRIBUIDORA TAMEX",
            "DISTRIBUIDORA TAMEX SAPI DE CV",
            "EUROELECTRICA",
            "EUGENIA MARIA ELENA VILLALPANDO",
        ],
        "plomeria": [
            "LA INDUSTRIAL MEXICANA",
            "LIMSA SA DE CV",
            "PLOMERIA SELECTA",
            "PLASTICOS RUSSELL",
        ],
        "maquinaria": [
            "RAUL SALAZAR MARTINEZ",
            "SERVICIO Y MAQUINARIA DE AGUASCALIENTES",
        ],
        "refaccion": ["AUTO ZONE DE MEXICO"],
        "limpieza": ["DON PULCRO"],
        "voz y datos": ["STEREN", "TECNOTIENDAS AGUASCALIENTES"],
        "papeleria": ["ANTONIO PADILLA RAMIREZ", "OFFICE DEPOT"],
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
    }


datos = []

meses_map = {
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
}

regex_fechas = [
    r"\d{1,2}/\d{1,2}/\d{4}",
    r"\d{1,2}-\d{1,2}-\d{4}",
    r"\d{4}-\d{1,2}-\d{1,2}",
]
regex_fecha_texto = r"(\d{1,2})/([a-z0-9]{3})\.?/(\d{4})(?:\s+\d{1,2}:\d{2}:\d{2})?"


def convertir_fecha_texto(fecha_str):
    m = re.match(regex_fecha_texto, fecha_str, re.IGNORECASE)
    if not m:
        return None
    dia, mes_abrev, anio = m.groups()
    mes_abrev = mes_abrev.lower().replace("0", "o").replace("sept", "sep")
    mes_num = meses_map.get(mes_abrev[:3])
    if not mes_num:
        return None
    return f"{int(dia):02d}/{mes_num}/{anio}"


def procesar_texto(texto):
    if debe_omitir_factura(texto):
        return
    fecha, folio, subtotal = "", "", 0.0

    # --- Fecha ---
    match_texto = re.search(regex_fecha_texto, texto, re.IGNORECASE)
    if match_texto:
        fecha = convertir_fecha_texto(match_texto.group())
    else:
        for patron in regex_fechas:
            match = re.search(patron, texto)
            if match:
                fecha = match.group()
                break

    # --- Folio ---
    match_folio = re.search(r"fol(?!.*SAT).*:\s*([A-Z0-9-]+)", texto, re.IGNORECASE)
    if match_folio:
        folio = match_folio.group(1)

    # --- Subtotal ---
    match_subtotal = re.search(
        r"sub\s*total[:\s]*([\d,]+\.\d{2})", texto, re.IGNORECASE
    )
    if match_subtotal:
        subtotal = float(match_subtotal.group(1).replace(",", ""))

    iva = round(subtotal * 0.16, 2) if subtotal > 0 else 0.0
    total = round(subtotal + iva, 2)

    # --- Proveedor ---
    proveedor, tipo, max_ratio = "DESCONOCIDA", "DESCONOCIDA", 0
    texto_upper = texto.upper()
    for emp in empresas_conocidas:
        ratio = fuzz.partial_ratio(emp, texto_upper)
        if ratio > max_ratio:
            max_ratio, proveedor = ratio, emp
    if max_ratio >= 50:
        for cat, emps in obtener_empresas_por_clasificacion().items():
            if proveedor in emps:
                tipo = cat.upper()
                break

    datos.append(
        {
            "Fecha": fecha,
            "Proveedor": proveedor,
            "Concepto": tipo,
            "Folio": folio,
            "Subtotal": subtotal,
            "IVA": iva,
            "Total": total,
        }
    )


# --- Procesar PDFs ---
for archivo in os.listdir(carpeta):
    if archivo.endswith(".pdf"):
        ruta = os.path.join(carpeta, archivo)
        print(f"📄 Procesando: {archivo}")
        try:
            texto = ""
            with pdfplumber.open(ruta) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        texto += page_text + "\n"
            if len(texto.strip()) > 0:
                procesar_texto(texto)
            else:
                print("➡ No hay texto, usando OCR...")
                for img in convert_from_path(ruta):
                    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    texto = pytesseract.image_to_string(img_cv, lang="spa")
                    procesar_texto(texto)
        except Exception as e:
            print(f"❌ Error en {archivo}: {e}")

# --- Guardar resultados ---
df = pd.DataFrame(datos)
if not df.empty:
    df = ordenar_facturas_por_fecha(df)
    orden = ["Fecha", "Proveedor", "Concepto", "Folio", "Subtotal", "IVA", "Total"]
    df = df[orden]

    os.makedirs("output", exist_ok=True)
    excel_path, lock_path = "output/facturas_procesadas.xlsx", "output/excel_lock.lock"

    while os.path.exists(lock_path):
        time.sleep(0.1)
    with open(lock_path, "w") as f:
        f.write("locked")

    try:
        if os.path.exists(excel_path):
            existing_df = pd.read_excel(excel_path)
            combined_df = ordenar_facturas_por_fecha(
                pd.concat([existing_df, df], ignore_index=True)
            )
            combined_df.to_excel(excel_path, index=False)
        else:
            df.to_excel(excel_path, index=False)
    finally:
        os.remove(lock_path)

    print("✅ Proceso completado. Archivo guardado en output/facturas_procesadas.xlsx")
else:
    print("⚠ No se extrajeron datos de los PDFs")
