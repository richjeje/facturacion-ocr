# Facturación OCR SaaS

Sistema avanzado de extracción de datos de facturas (PDF, Imágenes, DOCX, PPTX) utilizando OCR (EasyOCR/Tesseract) y procesamiento asíncrono.

## 🚀 Características (Fases 1-6)

- **Extracción Multi-formato**: Soporte para PDF (texto y OCR), JPG, PNG, DOCX y PPTX.
- **Procesamiento Inteligente**: 
  - Carga perezosa de modelos OCR para ahorro de RAM.
  - Procesamiento paralelo de páginas en PDF.
  - Paginación de resultados y caching con Redis.
- **Arquitectura Robusta**:
  - Backend modular con FastAPI.
  - Colas de trabajo con Celery + Redis.
  - Persistencia en PostgreSQL (soporta esquemas personalizados).
- **Dashboard & API**:
  - Interfaz web con diseño "Mistica" (oscuro/moderno).
  - Dashboard interactivo con Plotly.
  - API REST protegida por API Keys y JWT.
- **Calidad & DevOps**:
  - Cobertura de tests >80% con Pytest.
  - CI/CD automatizado con GitHub Actions.
  - Contenerización completa con Docker Compose.

## 🛠️ Instalación y Desarrollo

### Requisitos
- Python 3.12+
- Docker y Docker Compose
- Tesseract OCR (`sudo apt install tesseract-ocr`)

### Configuración Local
1. Clonar el repositorio.
2. Crear un entorno virtual: `python -m venv venv`.
3. Instalar dependencias: `pip install -r requirements.txt -r requirements-dev.txt`.
4. Configurar `.env` (ver sección Variables).
5. Ejecutar la app: `uvicorn backend.app.main:app --reload`.

### Testing y Calidad
```bash
# Ejecutar tests con cobertura
pytest --cov=.

# Linting
black .
flake8 .
mypy .
```

## 🐳 Despliegue con Docker

```bash
# Iniciar stack completo (API, Worker, Beat, Redis, DB)
docker-compose up -d
```

### Variables de Entorno (.env)
```ini
DATABASE_URL=postgresql://user:pass@localhost:5432/facturacion
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=tu_clave_secreta_aqui
DB_SCHEMA=public
```

## 📄 Documentación de API
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---
**Desarrollado con opencode - Enero 2026**
