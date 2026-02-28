# AGENTS.md — Facturación OCR

Guía de referencia para agentes automatizados y desarrolladores sobre el estado,
convenciones y cambios recientes del proyecto.

---

## Stack Tecnológico

| Capa       | Tecnología                                      |
|------------|-------------------------------------------------|
| Backend    | Python / FastAPI                                |
| Frontend   | Jinja2 templates + Vue 3 (CDN)                  |
| CSS        | Sistema propio `mistica.css` + `header.css`     |
| Fuentes    | Google Fonts — DM Sans                          |
| Iconos     | Font Awesome 6                                  |
| Auth       | JWT en `localStorage` (`token`)                 |

---

## Convenciones

- Los templates extienden `base.html` con `{% extends "base.html" %}`.
- Estilos específicos de pantalla van en `{% block head_extra %}`.
- Scripts de Vue 3 van en `{% block scripts %}` (si existe) o al final del `{% block content %}`.
- La autenticación se verifica en `base.html`; páginas privadas redirigen a `/` si no hay token.
- Los endpoints de la API esperan el header `Authorization: Bearer <token>`.
- En modo desarrollo se usan datos de demostración cuando la API no responde.

---

## Pantallas y cambios recientes

### `index.html` — Inicio / Login
- Diseño Stitch integrado: dark mode con gradiente, glassmorphism.
- Vue 3 Composition API para manejo de formulario de login.
- Llamada a `POST /api/login` y almacenamiento de JWT.

### `signup.html` — Registro de Usuario
- Diseño Stitch: "Registro - Facturación OCR".
- Vue 3 para validación y envío de formulario de registro.
- Llamada a `POST /api/signup`.
- Incluye paso de datos de negocio (diseño "Registro de Negocio").

### `dashboard.html` — Dashboard Principal
- Diseño Stitch integrado: sidebar con KPIs, tabla de historial paginada.
- Vue 3 Composition API: KPIs con indicadores de tendencia, paginación funcional.
- Carga dinámica de: facturas emitidas (`/api/issued`), historial OCR (`/api/results`).
- Bloque `head_extra` para CSS y librerías propias de la pantalla.
- `base.html` fue actualizado para incluir `{% block head_extra %}`.

### `negocio_mis_clientes.html` — Mis Clientes  *(Actualizado 2026-02-28)*
- **Diseño Stitch integrado**: `Mis Clientes - Facturación OCR` (ID: `311803ef9acf4939a92ca968ff2e14d7`, Proyecto: `5204995489370135169`).
- **Layout**: sidebar izquierdo con navegación e información de usuario + área principal.
- **Tabla enriquecida**: columnas Nombre/Razón Social, RFC, Teléfono, Email, Acciones.
  - Avatares de color generados determinísticamente desde nombre+RFC.
  - Botón "Ver" estilizado por fila.
- **Barra de herramientas**: input de búsqueda filtrada en tiempo real (nombre, RFC, email) + botón Filtros + botón Exportar CSV.
- **Paginación**: 5 registros por página, controles con elipsis inteligente.
- **Tarjetas KPI**: Total Clientes, Nuevos (Mes), RFCs Verificados.
- **Modal "Nuevo Cliente"**: formulario con campos Nombre, RFC, Teléfono, Email → `POST /api/clientes`.
- **Exportar CSV**: genera archivo descargable con los registros filtrados actualmente visibles.
- **Vue 3 CDN** (Composition API): toda la lógica reactiva en el bloque `{% block scripts %}`.
- **Fallback de demostración**: si `/api/clientes` falla, muestra 5 clientes de ejemplo y KPIs simulados para no bloquear el desarrollo.
- **Responsive**: sidebar oculto en pantallas < 900 px.

### `config_perfil.html` — Configuración de Perfil
- *(Sin cambios documentados aún)*

### `business_profile.html` — Perfil del Negocio
- *(Sin cambios documentados aún)*

### `admin_dashboard.html` — Panel de Administración
- *(Sin cambios documentados aún)*

---

## Endpoints de API relevantes

| Método | Ruta                   | Descripción                          |
|--------|------------------------|--------------------------------------|
| POST   | `/api/login`           | Autenticación, devuelve JWT          |
| POST   | `/api/signup`          | Registro de usuario                  |
| GET    | `/api/clientes`        | Lista de clientes del negocio        |
| POST   | `/api/clientes`        | Crear nuevo cliente                  |
| GET    | `/api/issued`          | Facturas emitidas                    |
| GET    | `/api/results`         | Historial OCR                        |
| GET    | `/api/business/profile`| Perfil del negocio                   |
| POST   | `/api/business/profile`| Actualizar perfil del negocio        |
| GET    | `/api/notifications`   | Notificaciones (polling 30 s)        |

---

## Diseño Stitch — Proyecto

- **Título**: Facturación OCR Main Dashboard  
- **Project ID**: `5204995489370135169`

| Pantalla                        | Screen ID                            |
|---------------------------------|--------------------------------------|
| Iniciar Sesión                  | *(ver conversación 23e8b2c7)*        |
| Registro                        | *(ver conversación 40e4dcd3)*        |
| Registro de Negocio             | *(ver conversación 40e4dcd3)*        |
| Dashboard Principal             | *(ver conversación c2fe03cf)*        |
| **Mis Clientes**                | `311803ef9acf4939a92ca968ff2e14d7`   |