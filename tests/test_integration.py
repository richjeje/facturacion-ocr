# For integration, test the processor with extractor
from processor import process_invoice_text


def test_integration_full_process():
    # Simulate reading a text file as if extracted
    with open("tests/sample_invoice.txt", "r", encoding="utf-8") as f:
        texto = f.read()

    resultado = process_invoice_text(texto, "Texto")

    assert resultado is not None
    assert resultado["Proveedor"] == "TIENDAS FIX"
    assert resultado["Concepto"] == "FERRETERIA"
