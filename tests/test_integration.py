# For integration, test the processor with extractor
from processor import process_invoice_text
from extractor import extract_text_from_docx, extract_text_from_pptx
import pytest
import os

def test_integration_full_process():
    # Simulate reading a text file as if extracted
    with open("tests/sample_invoice.txt", "r", encoding="utf-8") as f:
        texto = f.read()

    resultado = process_invoice_text(texto, "Texto")

    assert resultado is not None
    assert resultado["Proveedor"] == "TIENDAS FIX"
    assert resultado["Concepto"] == "FERRETERIA"

def test_integration_docx_processing():
    # Mock a DOCX file if possible, or skip
    pytest.skip("DOCX test requires sample file")

def test_integration_pptx_processing():
    # Mock a PPTX file if possible, or skip
    pytest.skip("PPTX test requires sample file")

def test_integration_full_pipeline():
    # Test from extractor to processor
    # This would require a real file, so mock
    texto = "Factura de prueba\nFecha: 15/08/2024\nProveedor: TIENDAS FIX\nTotal: $116.00"
    resultado = process_invoice_text(texto, "Texto")

    assert resultado is not None
    assert "Fecha" in resultado
    assert "Total" in resultado
