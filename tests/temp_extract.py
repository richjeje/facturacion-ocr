import pdfplumber

with pdfplumber.open('imagenes/MAPRO.pdf') as pdf:
    texto = ""
    for page in pdf.pages:
        page_text = page.extract_text() or ""
        texto += page_text + "\n"
    print(texto)
