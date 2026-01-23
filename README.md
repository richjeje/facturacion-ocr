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

## Tests

```bash
pytest tests/
```

## Contribución

1. Fork y branch.
2. Tests para cambios.
3. PR con descripción.