import pytest
from unittest.mock import patch, MagicMock
from extractor import (
    extract_text_from_pdf,
    extract_text_from_image,
    extract_text,
    extract_text_from_docx,
    extract_text_from_pptx,
)


@patch("extractor.pdfplumber")
def test_extract_pdf_with_text(mock_pdfplumber):
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Texto de la factura"
    mock_pdf.pages = [mock_page]
    mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

    texto, metodo = extract_text_from_pdf("test.pdf")

    assert texto == "Texto de la factura\n"
    assert metodo == "Texto"


@patch("extractor.convert_from_path")
@patch("extractor.pdfplumber")
def test_extract_pdf_ocr_fallback(mock_pdfplumber, mock_convert):
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = None
    mock_pdf.pages = [mock_page]
    mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

    mock_img = MagicMock()
    mock_convert.return_value = [mock_img]

    with patch("extractor.pytesseract.image_to_string", return_value="Texto OCR"):
        texto, metodo = extract_text_from_pdf("test.pdf")

        assert "Texto OCR" in texto
        assert metodo == "OCR"


@patch("extractor.easyocr.Reader")
def test_extract_image_easyocr(mock_reader):
    mock_reader_instance = MagicMock()
    mock_reader_instance.readtext.return_value = ["Texto EasyOCR"]
    mock_reader.return_value = mock_reader_instance

    with patch("extractor.Image.open") as mock_open, patch(
        "extractor.np.array"
    ) as mock_array:
        mock_img = MagicMock()
        mock_open.return_value = mock_img
        mock_array.return_value = "img_array"

        texto, metodo = extract_text_from_image("test.jpg")

        assert "Texto EasyOCR" in texto
        assert metodo == "EasyOCR"


@patch("extractor.Document")
def test_extract_docx(mock_document):
    mock_doc = MagicMock()
    mock_para = MagicMock()
    mock_para.text = "Texto de prueba"
    mock_doc.paragraphs = [mock_para]
    mock_document.return_value = mock_doc

    texto, metodo = extract_text_from_docx("test.docx")

    assert texto == "Texto de prueba\n"
    assert metodo == "DOCX"


@patch("extractor.Presentation")
def test_extract_pptx(mock_presentation):
    mock_prs = MagicMock()
    mock_slide = MagicMock()
    mock_shape = MagicMock()
    mock_shape.text = "Texto PPT"
    mock_slide.shapes = [mock_shape]
    mock_prs.slides = [mock_slide]
    mock_presentation.return_value = mock_prs

    texto, metodo = extract_text_from_pptx("test.pptx")

    assert texto == "Texto PPT\n"
    assert metodo == "PPTX"
