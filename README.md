# Facturacion OCR

Sistema para automatizar la extracción de datos de facturas mexicanas en PDFs e imágenes usando OCR.

## Instalación

1. Clona el repositorio:
   ```bash
   git clone <repo-url>
   cd facturacion_ocr
   ```

2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Instala Tesseract OCR:
   - Windows: Descarga de [GitHub Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
   - Asegúrate de que esté en PATH.

## Uso

1. Coloca facturas en la carpeta `imagenes/` (PDFs, JPG, PNG).

2. Ejecuta:
   ```bash
   python main.py
   ```

3. Opcional: Limita archivos con input (presiona Enter para todos).

4. Resultados en `output/facturas_procesadas.xlsx`.

## Configuración

- **Empresas**: Edita `companies.json` para agregar/eliminar proveedores.
- **Patrones**: Edita `patterns.json` para regex de fechas/folios.
- **Logs**: En `logs/processing.log`.

## Estructura

- `main.py`: Orquestación principal.
- `config.py`: Configuraciones.
- `extractor.py`: Extracción de texto.
- `processor.py`: Parsing de datos.
- `utils.py`: Utilidades.
- `tests/`: Tests unitarios.

## Ejemplos

Factura de muestra:
```
Fecha: 15/08/2024
Proveedor: TIENDAS FIX
Folio: 12345
Subtotal: $100.00
Total: $116.00
```

Resultado en Excel con columnas: Fecha, Proveedor, Concepto, Folio, Subtotal, IVA, Total, etc.

## Logs y Errores

- Logs en `logs/processing.log`.
- Errores comunes: Instala Tesseract, verifica dependencias.

## Despliegue

### Local con Docker Compose
1. Asegúrate de tener Docker y Docker Compose instalados.
2. Crea un archivo `.env` con:
   ```
   DATABASE_URL=postgresql://user:pass@db:5432/facturacion
   SECRET_KEY=your-secret-key
   ```
3. Ejecuta:
   ```bash
   docker-compose up --build
   ```
4. Accede a http://localhost:8000.

### Producción en Vercel + Neon + Redis
1. Configura Neon PostgreSQL (neon.tech) y obtén DATABASE_URL.
2. Configura Redis (ej. Upstash) y obtén REDIS_URL.
3. En Vercel, conecta el repo GitHub, agrega env vars (DATABASE_URL, SECRET_KEY, REDIS_URL).
4. Despliega: Vercel maneja automáticamente.
5. Para Celery workers: Usa Railway o similar para `celery -A tasks worker`.

### Scripts de Deploy
- `deploy.sh`: Script para deploy manual en VPS.
- Docker Compose: Para desarrollo local.

## Monitoreo
- Logs en `logs/processing.log`.
- Agregado Sentry para error tracking (configura DSN en env).

## Tests

```bash
pytest tests/
```

## Contribución

1. Fork y branch.
2. Tests para cambios.
3. PR con descripción.