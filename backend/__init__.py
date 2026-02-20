"""Backend package for Facturación OCR.

Sub-paquetes:
- ``api``     — Aplicación FastAPI (web/REST).
- ``cli``     — Procesador CLI por lotes.
- ``core``    — Configuración, modelos, base de datos y utilidades.
- ``ocr``     — Extracción de texto (OCR + pdfplumber).
- ``parsing`` — Parseo y validación de facturas.
- ``worker``  — Tareas asíncronas con Celery.
"""
