from processor import process_invoice_text
from extractor import extract_text
import pytest
import os
from unittest.mock import patch, MagicMock

def test_integration_full_process():
    # Simulate reading a text file as if extracted
    with open("tests/sample_invoice.txt", "r", encoding="utf-8") as f:
        texto = f.read()

    resultado = process_invoice_text(texto, "Texto")

    assert resultado is not None
    assert resultado["Proveedor"] == "TIENDAS FIX"
    assert resultado["Concepto"] == "FERRETERIA"

@patch("backend.ocr.extractor.pdfplumber.open")
def test_integration_pdf_to_processor(mock_pdf_open):
    # Mock PDF extraction
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Factura\nFecha: 01/01/2024\nProveedor: TIENDAS FIX\nTotal: $200.00"
    mock_pdf.pages = [mock_page]
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf
    
    # Create a dummy file path
    dummy_pdf = "dummy.pdf"
    with open(dummy_pdf, "w") as f:
        f.write("dummy")
    
    try:
        texto, metodo = extract_text(dummy_pdf)
        resultado = process_invoice_text(texto, metodo)
        
        assert resultado is not None
        assert resultado["Proveedor"] == "TIENDAS FIX"
        assert resultado["Total"] == 200.0
    finally:
        if os.path.exists(dummy_pdf):
            os.remove(dummy_pdf)

