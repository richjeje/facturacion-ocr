# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-01-27
### Added
- **Fase 5: Optimizaciones y Rendimiento**
  - Carga perezosa (lazy loading) de EasyOCR para reducir consumo de RAM inicial.
  - Procesamiento paralelo de páginas en PDF OCR con `ThreadPoolExecutor`.
  - Paginación (skip/limit) en `/api/results` y conteo total de registros.
  - Tarea programada (Celery Beat) para limpieza diaria de archivos temporales.
  - Reciclaje automático de workers para mitigar fugas de memoria.
- **Fase 4: Calidad y CI/CD**
  - Nueva suite de tests `tests/test_api_v2.py` con cobertura completa.
  - Tests de integración real usando mocks para extractor y base de datos.
  - Workflow de GitHub Actions actualizado para Python 3.12 con servicios Postgres/Redis.
  - Archivo `requirements-dev.txt` para estandarizar el entorno de desarrollo.

### Fixed
- Corregidos errores de LSP en `backend/core/database.py` y `backend/app/main.py`.
- Solucionado error en `FileResponse` con buffers en memoria (migrado a `StreamingResponse`).
- Saneamiento de nombres de archivos y gestión de tipos en la API.
- Actualización de dependencias críticas en `requirements.txt`.

## [1.1.0] - 2026-01-25
### Added

- **Modularización Completa**: Código dividido en módulos (config, utils, extractor, processor, web_app).
- **Interfaz Web**: FastAPI con autenticación JWT, uploads drag-and-drop, dashboard con Plotly.
- **API REST**: Endpoints para uploads, results, status con API keys para múltiples clientes.
- **Mejora OCR**: Soporte EasyOCR, DOCX/PPTX, entrenamientos custom, métricas.
- **Colas Asíncronas**: Celery + Redis para procesamiento paralelo (6 workers).
- **BD PostgreSQL**: Migración de SQLite, índices para rendimiento.
- **Tests y CI/CD**: Pytest con coverage, GitHub Actions, linting (Black, Flake8, MyPy).
- **Seguridad**: Rate limiting, sanitización de inputs, encriptación básica.
- **Monitoreo**: Sentry para errores, caching Redis, logs estructurados.
- **Deploy**: Docker Compose, Vercel ready, scripts de deploy.

### Changed
- Reemplazado prints con logging.
- Optimizadas queries y agregados índices.
- UI mejorada con real-time updates.

### Fixed
- Errores de linting y type hints.
- Dependencias y compatibilidad.

### Technical Debt
- Entrenamiento OCR custom requiere dataset adicional.
- Tests pasan en CI, fallan local sin deps.