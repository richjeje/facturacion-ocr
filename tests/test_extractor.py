import pytest
from unittest.mock import patch, MagicMock
from extractor import extract_text_from_pdf, extract_text_from_image, extract_text

@patch('extractor.pdfplumber')
def test_extract_pdf_with_text(mock_pdfplumber):
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Texto de la factura"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

    texto, metodo = extract_text_from_pdf("test.pdf")

    assert texto == "Texto de la factura\n"
    assert metodo == "Texto"

@patch('extractor.convert_from_path')
@patch('extractor.pdfplumber')
def test_extract_pdf_ocr_fallback(mock_pdfplumber, mock_convert):
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = None
    mock_pdf.pages = [mock_page]
    mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

    mock_img = MagicMock()
    mock_convert.return_value = [mock_img]

    with patch('extractor.pytesseract.image_to_string', return_value="Texto OCR"):
        texto, metodo = extract_text_from_pdf("test.pdf")

        assert "Texto OCR" in texto
        assert metodo == "OCR"

@patch('extractor.PIL.Image.open')
@patch('extractor.cv2.cvtColor')
@patch('extractor.cv2.threshold')
def test_extract_image(mock_threshold, mock_cvtColor, mock_open):
    mock_img = MagicMock()
    mock_open.return_value = mock_img
    mock_cvtColor.return_value = "gray_img"
    mock_threshold.return_value = ("thresh", "thresh_img")

    with patch('extractor.pytesseract.image_to_string', return_value="Texto imagen"):
        texto, metodo = extract_text_from_image("test.jpg")

        assert texto == "Texto imagen"
        assert metodo == "OCR"