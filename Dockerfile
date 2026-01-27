# Dockerfile básico para facturacion_ocr
FROM python:3.9-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libsm6 libxext6 libxrender-dev libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copiar proyecto
WORKDIR /app
COPY . .

# Instalar Python deps
RUN pip install -r requirements.txt

# Crear directorios
RUN mkdir -p imagenes output logs

# Comando (API Web por defecto)
CMD ["python", "backend/app/main.py"]
