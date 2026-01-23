import pytest
from processor import process_invoice_text

def test_process_valid_invoice():
    texto = """Factura de prueba
Fecha: 15/08/2024
Proveedor: TIENDAS FIX
Folio: 12345
Subtotal: $100.00
IVA: $16.00
Total: $116.00
URL: https://example.com"""

    resultado = process_invoice_text(texto, "Texto")

    assert resultado is not None
    assert resultado["Fecha"] == "15/08/2024"
    assert resultado["Proveedor"] == "TIENDAS FIX"
    assert resultado["Folio"] == "12345"
    assert resultado["Subtotal"] == 100.0
    assert resultado["IVA"] == 16.0
    assert resultado["Total"] == 116.0
    assert "example.com" in resultado["URL"]

def test_process_invalid_invoice():
    texto = "Texto sin datos válidos"

    resultado = process_invoice_text(texto, "Texto")

    assert resultado is None  # Debería omitirse por falta de datos

def test_process_omit_herrera():
    texto = "HERRERA MOTORS DE AGUASCALIENTES Factura"

    resultado = process_invoice_text(texto, "Texto")

    assert resultado is None  # Debería omitirse

def test_process_low_confidence():
    texto = "Proveedor desconocido XYZ"

    resultado = process_invoice_text(texto, "Texto")

    assert resultado is None  # Confianza baja