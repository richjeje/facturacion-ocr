import pdfplumber

pdf = pdfplumber.open("imagenes/PFIX.pdf")
print(f"Pages: {len(pdf.pages)}")
texto = ""
for i, page in enumerate(pdf.pages):
    page_text = page.extract_text() or ""
    print(f"Page {i+1} text: {page_text[:200]}...")
    texto += page_text + "\n"
print("Full text:")
print(texto)
