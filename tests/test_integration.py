import pytest
import os
from main import process_files  # Assuming we can call a function from main, but since it's script, maybe mock

# For integration, perhaps test the processor with extractor

from extractor import extract_text
from processor import process_invoice_text

def test_integration_full_process():
    # Simulate reading a text file as if extracted
    with open("tests/sample_invoice.txt", "r", encoding="utf-8") as f:
        texto = f.read()

    resultado = process_invoice_text(texto, "Texto")

    assert resultado is not None
    assert resultado["Proveedor"] == "TIENDAS FIX"
    assert resultado["Concepto"] == "FERRETERIA"