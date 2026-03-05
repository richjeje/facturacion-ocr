# AGENTS.md — Facturación OCR

Documento central del proyecto. Combina guía de uso, arquitectura, historial de cambios y notas del asistente de IA.

---

## Índice

1. [¿Qué es este proyecto?](#qué-es-este-proyecto)
2. [Instalación](#instalación)
3. [Uso](#uso)
4. [Estructura del proyecto](#estructura-del-proyecto)
5. [Configuración](#configuración)
6. [Despliegue](#despliegue)
7. [Solución de problemas](#solución-de-problemas)
8. [Base de datos — Neon PostgreSQL](#base-de-datos--neon-postgresql)
9. [Frontend / UI](#frontend--ui)
10. [Tests](#tests)
11. [Changelog](#changelog)
12. [Pendientes](#pendientes)
13. [Registro del asistente IA](#registro-del-asistente-ia)

---

## ¿Qué es este proyecto?

Sistema para automatizar la extracción de datos de facturas mexicanas en PDFs e imágenes usando OCR.
Soporta dos modos de operación:

- **CLI** (`python main.py`) — procesamiento por lotes desde la carpeta `imagenes/`, exporta a Excel y BD.
- **Web / API** (`uvicorn backend.api.main:app`) — FastAPI con auth JWT, uploads drag-and-drop, dashboard con Plotly, WebSocket real-time y API REST para integraciones.

---

## Instalación

```bash
# 1. Clonar
git clone <repo-url>
cd facturacion-ocr

# 2. Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Edita .env con tus valores (SECRET_KEY, DATABASE_URL, REDIS_URL)

# 5. Instalar Tesseract OCR (solo para modo OCR imagen)
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# Asegúrate de que esté en PATH
```

---

## Uso

### CLI — Procesamiento en lote

```bash
# Coloca facturas en imagenes/ (PDF, JPG, PNG, DOCX, PPTX)
python -m backend.cli.main
# Ingresa cuántos archivos procesar (Enter = todos)
# Resultado: output/facturas_procesadas.xlsx + base de datos
```

### Web / API

```bash
# Opcion A: script todo-en-uno (backend + frontend)
python start.py

# Opcion B: solo servidor web
python start_server.py
# o directamente:
uvicorn backend.api.main:app --reload

# Worker Celery (en otra terminal)
celery -A backend.worker.tasks worker --loglevel=info
```

Endpoints disponibles:

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/login` | Obtener token JWT |
| `POST` | `/api/upload` | Subir factura (requiere API key) |
| `GET` | `/api/status/{task_id}` | Estado de tarea |
| `GET` | `/api/results` | Listar facturas procesadas |
| `GET` | `/dashboard` | Dashboard con gráficos (JWT) |
| `GET` | `/export/pdf` | Exportar reporte PDF (JWT) |
| `WS` | `/ws` | Actualizaciones en tiempo real |

---

## Estructura del proyecto

```
facturacion-ocr/
├── backend/
│   ├── api/              # FastAPI — rutas, auth, dashboard, WebSocket
│   │   └── main.py
│   ├── cli/              # Procesador por lotes (entrada: imagenes/)
│   │   └── main.py
│   ├── core/             # Configuración, modelos, BD, utilidades
│   │   ├── config.py     # Config central (env + data/*.json)
│   │   ├── database.py   # SQLAlchemy engine + session
│   │   ├── models.py     # ORM: User, APIKey, Invoice
│   │   ├── all_models.py # Modelos extendidos (CFDI, CSF, etc.)
│   │   ├── persistence.py# save_to_database()
│   │   └── utils.py      # Excepciones custom + helpers de texto
│   ├── ocr/              # Extracción de texto
│   │   └── extractor.py  # pdfplumber + EasyOCR + pytesseract
│   ├── parsing/          # Parsing y validación de facturas
│   │   └── processor.py  # process_invoice_text()
│   └── worker/           # Celery
│       ├── celeryconfig.py
│       └── tasks.py
├── data/                 # Configuración externa (companies.json, patterns.json)
├── frontend/
│   ├── templates/        # HTML servido por FastAPI
│   └── static/           # CSS, JS, assets
├── tests/                # Tests con pytest
│   ├── test_extractor.py
│   ├── test_processor.py
│   ├── test_integration.py
│   ├── test_api.py
│   ├── test_api_v2.py
│   ├── test_cfdi_core.py
│   ├── test_cfdi_routes.py
│   ├── test_cfdi_setup.py
│   ├── test_csf_integration.py
│   ├── test_csf_profile_integration.py
│   ├── test_csf_validator.py
│   └── sample_invoice.txt
├── .env.example          # Variables de entorno documentadas
├── docker-compose.yml    # Orquestación local (web + worker + db + redis)
├── Dockerfile
├── requirements.txt
├── start.py              # Entry point: arranca backend + frontend simultaneamente
├── start_server.py       # Entry point: solo servidor web (uvicorn)
└── test_server.py        # Script de prueba de servidor
```

---

## Configuración

### Variables de entorno (`.env`)

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `SECRET_KEY` | **Sí** | Clave para firmar JWT. Genera con `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | No | `sqlite:///./facturacion_ocr.db` (default) o PostgreSQL |
| `REDIS_URL` | No | `redis://localhost:6379/0` (default) |
| `SENTRY_DSN` | No | DSN de Sentry para monitoreo de errores |

### Empresas y patrones (`data/`)

- **`data/companies.json`** — Lista de empresas conocidas y sus clasificaciones por categoría.
- **`data/patterns.json`** — Regex de fechas, folios, subtotales y totales.

Edita estos archivos para agregar/modificar proveedores sin tocar el código fuente.

---

## Despliegue

### Local con Docker Compose

```bash
# Crea .env desde .env.example y ajusta
cp .env.example .env

docker-compose up --build
# Accede en http://localhost:8000
```

### Producción: Vercel + Neon + Upstash Redis

1. Configura Neon PostgreSQL (neon.tech) → obtén `DATABASE_URL`.
2. Configura Upstash Redis → obtén `REDIS_URL`.
3. En Vercel: conecta el repo, agrega env vars (`DATABASE_URL`, `SECRET_KEY`, `REDIS_URL`).
4. Para Celery workers: usa Railway o similar con `celery -A backend.worker.tasks worker`.

### VPS manual

```bash
bash deploy.sh
```

---

## Solución de problemas

### Puerto 8000 ocupado

```bash
# Ver qué proceso usa el puerto
netstat -ano | findstr :8000
# Matar el proceso (reemplaza PID)
taskkill /PID <PID> /F
```

### Python no está en PATH (Windows)

1. Busca la instalación de Python en el sistema.
2. Agrégala al PATH en Variables de Entorno.
3. Reinicia la terminal.

### Errores de dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Errores SQLAlchemy — relaciones cíclicas

- **Síntoma**: `User` con relaciones a `CSFDocument`/`CSFRecord` que no están disponibles al inicio.
- **Solución**: Las relaciones deben definirse en sus modelos propios, no en `User`. Ver `backend/core/all_models.py`.
- **Causa original**: importación circular entre modelos; resuelta al separar `all_models.py`.

### Módulo `qrcode` no encontrado

```bash
pip install "qrcode[pil]"
```

---

## Base de datos — Neon PostgreSQL

### Tablas creadas en producción

| Tabla | Propósito |
|---|---|
| `Users` | Gestión de usuarios y roles |
| `APIKeys` | Claves de API por cliente |
| `Invoices` | Facturas OCR procesadas |
| `CFDICertificates` | Certificados digitales CFDI 4.0 |
| `CFDIInvoice` | Facturas CFDI generadas |
| `CFDICatalogs` | Catálogos SAT |
| `CFDISettings` | Configuración PAC y features |
| `CSFRecord` | Registros CSF principales |
| `CSFValidationCache` | Caché de validaciones CSF |
| `CSFHistory` | Historial de cambios CSF |
| `CSFDocument` | Documentos CSF subidos |
| `CSFProfileHistory` | Historial de aplicación CSF |

### Estado de la migración

- Conexión SSL configurada correctamente (endpoint `ep-misty-morning-ahjog2u0-pooler`).
- Usuarios de base: `admin` / `admin123` y `vanta`.
- Backup automático provisto por Neon; datos persistentes entre reinicios.
- Configuración en `.env` → variable `DATABASE_URL`.

### Seguridad

- SSL requerido en todas las conexiones a Neon.
- No almacenar credenciales en el código; usar `.env` (ver `.env.example`).

---

## Frontend / UI

- Los templates HTML son servidos directamente por FastAPI (carpeta `frontend/templates/`).
- Los assets estáticos (CSS, JS) están en `frontend/static/`.
- El directorio `frontend/static/js/` contiene los archivos JavaScript del dashboard.

### Rutas del frontend

| Ruta | Vista |
|---|---|
| `/` | Redirect a login o dashboard |
| `/login` | Formulario de login |
| `/dashboard` | Dashboard principal con gráficos |
| `/negocio/emitir-factura` | Emisión de facturas CFDI |
| `/negocio/facturar-gastos` | Registro de gastos |
| `/negocio/mis-facturas` | Listado de facturas |
| `/negocio/mis-clientes` | Gestión de clientes |
| `/configuracion/perfil` | Perfil CSF y configuración |

### Notas de UI

- Header condicional: oculto en la pantalla de login, visible en el resto.
- Notificaciones: placeholder activo, integración real pendiente.
- Mocks dinámicos activos en rutas de Negocio mientras se completa la integración backend.

---

## Tests

```bash
pytest tests/ -v

# Con coverage
pytest tests/ --cov=backend --cov-report=term-missing
```

Los tests se ejecutan automáticamente en GitHub Actions (`.github/workflows/ci.yml`) con PostgreSQL y Redis efímeros.

---

## Changelog

### [1.2.0] — 2026-02-20 _(Merge con remote + correcciones)_

#### Integrado del remote
- Nuevos tests: `test_api_v2.py`, `test_cfdi_core.py`, `test_cfdi_routes.py`, `test_cfdi_setup.py`.
- Nuevos tests de integración CSF: `test_csf_integration.py`, `test_csf_profile_integration.py`, `test_csf_validator.py`.
- Scripts de arranque: `start.py` (orquestador), `start_server.py` (uvicorn), `test_server.py`.
- `backend/core/all_models.py` — modelos extendidos para CFDI/CSF.

#### Corregido
- `start.py` y `start_server.py` actualizados a `backend.api.main` (antes apuntaban a `backend.app.main`).
- Entry points en AGENTS.md actualizados: `start.py` / `start_server.py` reemplazan a `main.py` / `web_app.py`.

### [1.1.0] — 2026-02-20 _(Reestructuración)_

#### Cambiado
- `backend/app/` renombrado a `backend/api/` (convención estándar).
- `companies.json` y `patterns.json` movidos a `data/` (separación datos/código).
- `backend/core/config.py` reescrito: sin duplicados, paths con `pathlib`, `setup_logging()` idempotente.
- `backend/core/utils.py` limpiado: eliminado código muerto duplicado, `ordenar_facturas_por_fecha` no muta el DataFrame del caller.
- `backend/api/main.py`: `SECRET_KEY` falla rápido si no está configurado, imports al tope del archivo.
- `docker-compose.yml`: usa `uvicorn` correctamente, carga `.env`.

#### Eliminado
- Stubs/proxies redundantes en raíz: `extractor.py`, `processor.py`, `utils.py`, `config.py`, `celeryconfig.py`, `tasks.py`, `pdf_processor.py`, `check_excel.py`.
- Scripts de debug temporales: `test_pdf.py`, `tests/temp_extract.py`, `tests/temp_extract_ocr.py`, `tests/debug_folio.py`.
- `backend/ocr/pdf_processor.py` (versión monolítica obsoleta).

#### Agregado
- `.env.example` con documentación de todas las variables de entorno.
- `.gitignore` actualizado: `temp_*`, `facturacion_ocr.db`.

---

### [1.0.0] — 2025-01-27

#### Agregado
- **Modularización completa**: código dividido en módulos (`config`, `utils`, `extractor`, `processor`).
- **Interfaz Web**: FastAPI con autenticación JWT, uploads drag-and-drop, dashboard con Plotly.
- **API REST**: endpoints `/api/upload`, `/api/results`, `/api/status` con API keys por cliente.
- **OCR mejorado**: soporte EasyOCR, DOCX/PPTX, fallbacks y métricas.
- **Colas asíncronas**: Celery + Redis (6 workers simultáneos, timeouts 10-15 min).
- **Base de datos**: PostgreSQL con SQLAlchemy, índices en `fecha`, `proveedor`, `uploaded_at`.
- **Tests y CI/CD**: pytest con coverage, GitHub Actions, linting (Black, Flake8, MyPy).
- **Seguridad**: rate limiting (slowapi), sanitización de filenames, encriptación bcrypt.
- **Monitoreo**: Sentry para errores, caching Redis (5 min TTL) en dashboard.
- **Deploy**: Docker Compose, Vercel-ready, `deploy.sh` para VPS.

#### Deuda técnica conocida
- Entrenamiento OCR custom requiere dataset adicional.
- Tests de integración requieren servicios externos (PostgreSQL, Redis); pasan en CI, pueden fallar en local sin deps.

---

## Pendientes

- [ ] Migrar manejo de BD de `create_all` a Alembic (migraciones versionadas)
- [ ] Agregar endpoint `POST /api/keys` para auto-provisionar API keys
- [ ] Expandir tests de integración con mocks de Celery
- [ ] Agregar entrenamiento OCR custom (requiere dataset de facturas mexicanas etiquetado)
- [ ] WebSocket: enviar datos reales de progreso en lugar de mensaje genérico

---

## Registro del asistente IA

### Sesión 1 — Análisis y planificación inicial

**Problemas identificados originalmente:**
- Código monolítico en `main.py` (477 líneas).
- Sin manejo de errores ni logging.
- Configuraciones hardcodeadas.
- Sin tests.
- Rendimiento limitado.
- Sin interfaz ni APIs.

**Plan de 7 pasos ejecutado:**
1. Modularizar código → separar en `config`, `utils`, `extractor`, `processor`.
2. Agregar manejo de errores y logging → excepciones custom, reintentos, logs con rotación.
3. Configuración externa → `companies.json`, `patterns.json`.
4. Tests unitarios e integración → pytest con mocks.
5. Rendimiento → procesamiento paralelo con `ThreadPoolExecutor`.
6. Documentación → README, docstrings.
7. Escalabilidad y seguridad → PostgreSQL, Docker, validaciones.

**Features adicionales implementadas:**
- Interfaz Web con FastAPI y auth JWT.
- API REST con API keys por cliente.
- Soporte DOCX/PPTX en extractor.
- Sistema de colas con Celery + Redis.
- Dashboard con Plotly y WebSockets.
- Rate limiting, sanitización, Sentry.
- GitHub Actions CI/CD.

### Sesión 2 — Reestructuración con buenas prácticas (2026-02-20)

**Problemas identificados:**
- 8 archivos proxy/stub en la raíz sin contenido real.
- `backend/core/config.py` con variables definidas dos veces.
- `backend/core/utils.py` con función `debe_omitir_factura` duplicada (código muerto).
- `backend/ocr/pdf_processor.py` era la versión monolítica anterior, ya reemplazada.
- `companies.json`/`patterns.json` en la raíz mezclados con código.
- Scripts de debug sueltos en raíz y `tests/`.
- `SECRET_KEY` con valor por defecto silencioso (riesgo de seguridad).
- Imports inline dentro de funciones en `backend/app/main.py`.
- `docker-compose.yml` con `SECRET_KEY` hardcodeado y sin `env_file`.

**Acciones tomadas:**
- Eliminados todos los stubs/proxies de la raíz.
- Renombrado `backend/app/` → `backend/api/`.
- Creado `data/` y movidos los JSON de configuración.
- Reescrito `config.py` con `pathlib`, sin duplicados.
- Limpiado `utils.py`, corregida mutación de DataFrame.
- Refactorizado `backend/api/main.py` con seguridad y estructura correcta.
- Actualizado `docker-compose.yml` con `uvicorn` y `env_file`.
- Creado `.env.example`.
- Consolidados todos los `.md` en este archivo.

### Sesión 3 — Migración Neon + features CFDI/CSF (remote, antes del merge)

**Situación encontrada:**
El remote (`origin/main`) tenía 14 commits nuevos con features de CFDI/CSF, nuevos tests y scripts de arranque (`start.py`, `start_server.py`). Conflictos en `AGENTS.md`, `.gitignore`, `config.py`, `tasks.py`. El remote había eliminado `main.py` y `web_app.py` (reemplazados por `start*.py`).

**Resolución de conflictos:**
- Tomada versión local para: `AGENTS.md`, `.gitignore`, `config.py`, `tasks.py` (contienen la reestructuración).
- Eliminados `main.py` y `web_app.py` (el remote los removió, se adopta su convención de `start*.py`).
- Integrados sin conflicto: nuevos tests CFDI/CSF, `start.py`, `start_server.py`, `all_models.py`.
- Corregidas referencias a `backend.app.main` → `backend.api.main` en `start.py` y `start_server.py`.

**Commits creados:**
1. `refactor: reestructuracion con buenas practicas` — 33 archivos, 863 inserciones, 1223 eliminaciones.
2. `merge: integrar cambios remotos conservando reestructuracion local` — merge commit.
3. `fix: corregir referencias backend.app → backend.api en start.py y start_server.py`.

### Sesión 4 — Fusión de .md restantes (2026-02-20)

**Archivos fusionados y eliminados:**
- `FINAL_SOLUTION.md` → errores SQLAlchemy resueltos, estado servidor → sección «Solución de problemas».
- `MIGRACION_COMPLETA.md` → estado migración Neon → sección «Base de datos — Neon PostgreSQL».
- `MIGRATION_NEON_COMPLETE.md` → tablas creadas, conexión SSL, usuarios → misma sección.
- `START_GUIDE.md` → scripts de arranque, troubleshooting → secciones «Uso» y «Solución de problemas».
- `docs/CHANGELOG.md` → notas de limpieza UI y rutas Negocio → sección «Frontend / UI».
- `docs/README.md` → descripción general → absorbida por sección «¿Qué es este proyecto?».
- `frontend/static/js/README.md` → nota de directorio → sección «Frontend / UI».

### Sesión 5 — Migración de index.html a Vue SPA (2026-03-02)

**Situación encontrada:**
- El archivo `frontend/templates/index.html` manejaba el inicio de sesión como una plantilla HTML autónoma usando Vue 3 vía CDN y Tailwind vía CDN.
- Se requería migrar esta vista al nuevo proyecto frontend (Vue SFC con TypeScript y Composition API).

**Acciones tomadas:**
- Se migró el contenido de `frontend/templates/index.html` al componente SFC `frontend/facturacion ocr/src/views/iniciar_sesion.vue`.
- Se reemplazaron los delimitadores adaptados para backend (`[[ ... ]]`) por la sintaxis estándar de Vue (`{{ ... }}`).
- Se refactorizó la lógica en la sección `<script setup lang="ts">` importando Composition API nativa y aprovechando vue-router.
- Se reemplazó la recarga completa (`window.location.href`) por la navegación en cliente (`router.push`) y los links nativos por `<router-link>`.
- Se encapsularon los estilos CSS en `.glass-card` y condicionales auxiliares usando la directiva `<style scoped>`.

---

### Sesión 6 — Migración de signup.html a Vue SPA (2026-03-02)

**Sitación encontrada:**
- El archivo `frontend/templates/signup.html` manejaba el registro como una plantilla HTML autónoma usando Vue 3 y Tailwind vía CDN.
- Se requería migrar esta vista a `registrarse.vue` en el nuevo proyecto de Vue.

**Acciones tomadas:**
- Se migró el contenido de `frontend/templates/signup.html` al componente SFC `frontend/facturacion ocr/src/views/registrarse.vue`.
- Se reemplazaron los delimitadores adaptados para backend (`[[ ... ]]`) por la sintaxis estándar de Vue (`{{ ... }}`).
- Se refactorizó la lógica en la sección `<script setup lang="ts">` importando la API nativa y aprovechando `vue-router`.
- Se reemplazó la recarga local en la redirección por la navegación con `router.push('/iniciar-sesion')` y los enlaces con `<router-link>`.
- Se añadieron estilos CSS locales en la directiva `<style scoped>`.

---

### Sesión 7 — Migración de admin_dashboard.html a Vue SPA (2026-03-03)

**Situación encontrada:**
- El archivo `frontend/templates/admin_dashboard.html` manejaba el panel de administración como una vista autónoma. Se necesitaba mover a `admin_dashboard.vue` para continuar con la adopción completa del framework Vue 3.

**Acciones tomadas:**
- Se migró el contenido HTML al componente Vue `<template>`, y se reemplazaron los engarces de datos (`[[ ]]` a `{{ }}`).
- Se refactorizó la lógica de control a Composition API bajo `<script setup lang="ts">`.
- Las fuentes personalizadas y estilos (fuentes, glass-card, utilidades generadas) se importaron directamente en un `<style scoped>`.
- Se implementaron las navegaciones entre vistas con `<router-link>`.

### Sesión 8 — Migración de business_profile.html a Vue SPA (2026-03-03)

**Situación encontrada:**
- El archivo `frontend/templates/business_profile.html` manejaba el perfil de negocio y la subida de Constancias de Situación Fiscal (CSF) de forma autónoma con Jinja2, Tailwind vía CDN y JS inline.
- Se requería migrar esta vista al componente Vue `business_profile.vue` preservando todas las variables visuales, fuentes y clases CSS de utilidad.

**Acciones tomadas:**
- Se migró toda la estructura a `frontend/facturacion ocr/src/views/business_profile.vue`.
- Se reimplementaron las utilidades exclusivas de Tailwind definidas en la cabecera original del HTML (`colors: primary, charcoal` etc.) con clases aplicables directamente en el bloque `<style scoped>`, así como las fuentes `Sora`, `Bebas Neue` y `Space Mono`.
- La lógica de subida y lectura provista antes por un archivo JS nativo fue abstraída directamente a Composition API simulando el backend original para cargar los datos en tabla dinámicamente y mostrar el modal del _preview_ del CSF con barra fluida.

### Sesión 9 — Migración de config_perfil.html a Vue SPA (2026-03-03)

**Situación encontrada:**
- El archivo `frontend/templates/config_perfil.html` manejaba el perfil de configuración de forma autónoma con Jinja2, Tailwind vía CDN y estilos nativos.
- Se requería migrar esta vista al componente Vue `config_perfil.vue` preservando todas las variables visuales, fuentes y estilos neon/gradient.

**Acciones tomadas:**
- Se migró toda la estructura a `frontend/facturacion ocr/src/views/config_perfil.vue`.
- Se reimplementaron las utilidades exclusivas de estilos (como `neon-border`, `gradient-btn`, fuentes personalizadas como `Sora`, `Bebas Neue`, etc.) con un bloque `<style scoped>`.
- El manejo del formulario en Jinja (`{{ user.business_name }}`) fue adaptado a propiedades reactivas con Vue `reactive()` y enlazadas a los campos con directivas `v-model`. 
- Se establecieron las acciones de clic de los botones (e.g. `resetForm`, `saveProfile`, navegación vía `vue-router`).

### Sesión 10 — Migración de negocio_emitir_factura.html a Vue SPA (2026-03-03)

**Situación encontrada:**
- El archivo `frontend/templates/negocio_emitir_factura.html` manejaba el formulario de emisión de factura de forma autónoma con Jinja2, Tailwind vía CDN y Vue 3 vía CDN.
- Se requería migrar esta vista al componente Vue `negocio_emitir_factura.vue` en el proyecto SPA, preservando estilos y fuentes personalizadas.

**Acciones tomadas:**
- Se migró toda la estructura a `frontend/facturacion ocr/src/views/negocio_emitir_factura.vue`.
- Se transpiló la lógica de Options API basada en CDN hacia Composition API usando `<script setup lang="ts">`.
- Las configuraciones custom de Tailwind se adaptaron a variables de estilos aplicadas a clases dentro del bloque `<style scoped>`.
- Las llamadas de Jinja (`[[ ]]`) se convirtieron a la interpolación habitual de Vue (`{{ }}`).

### Sesión 11 — Migración de negocio_facturar_gastos.html a Vue SPA (2026-03-03)

**Situación encontrada:**
- El archivo `frontend/templates/negocio_facturar_gastos.html` manejaba el facturador de gastos de forma autónoma con Jinja2, Tailwind vía CDN y Vue 3 vía CDN.
- Se requería migrar esta vista al componente Vue `negocio_facturar_gastos.vue` en el proyecto SPA, asegurando compatibilidad completa con el framework Vue y Tailwind preconfigurado, además de mantener fuentes.

**Acciones tomadas:**
- Se migró toda la estructura a `frontend/facturacion ocr/src/views/negocio_facturar_gastos.vue`.
- Se transpiló la lógica adaptada con Options API y `createApp` basada en CDN a Composition API usando `<script setup lang="ts">` importando propiedades como `ref` y `reactive` para mantener la reactividad en el progreso de OCR.
- Los estilos y fuentes personalizadas (`Bebas Neue`, `Space Grotesk`, `Space Mono`) así como clases custom que hacían override fueron aplicados directamente en etiquetas o como clases dentro del bloque `<style scoped>`. Clases personalizadas de Tailwind (`bg-background-dark`, `border-border-dark`) fueron reemplazadas en línea por sintaxis de valor arbitrario (`bg-[#050508]`, `border-[#1f1f2e]`) para mantener su exactitud de colores.
- Las interpolaciones originadas de Jinja (`[[ ]]`) se convirtieron a convenciones estandarizadas de Vue (`{{ }}`).

### Sesión 12 — Migración de negocio_mis_clientes.html a Vue SPA con diseño Stitch (2026-03-03)

**Situación encontrada:**
- Se proporcionó un diseño en Stitch (ID: 311803ef9acf4939a92ca968ff2e14d7) para la vista "Mis Clientes".
- Era necesario implementar este diseño exacto en el componente Vue `negocio_mis_clientes.vue` de la SPA, preservando la paleta de colores, gradientes, tipografías personalizadas (`Space Grotesk`, `Bebas Neue`, `Space Mono`) y estilos.

**Acciones tomadas:**
- Se descargó el código fuente HTML/CSS del mock generado por Stitch.
- Se migró toda la estructura y la tabla de clientes a `frontend/facturacion ocr/src/views/negocio_mis_clientes.vue`.
- La lógica de renderización estática para iterar clientes se movió a variables reactivas utilizando Composition API bajo `<script setup lang="ts">` importando la función `ref` y usando un bucle `v-for`.
- Las utilidades personalizadas de Tailwind definidas en la configuración del diseño (e.g., .text-primary, gradientes custom, configuraciones dark-mode) fueron transcritas a CSS puro dentro de un bloque `<style scoped>` del componente.
- Los iconos, navegaciones con Vue Router y fuentes fueron referenciados explícitamente para mantener total fidelidad con la interfaz visual.

_Última actualización: 2026-03-03_