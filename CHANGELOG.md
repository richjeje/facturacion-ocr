# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-XX

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