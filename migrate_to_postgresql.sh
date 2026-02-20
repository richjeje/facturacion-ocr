#!/bin/bash
# Script de migración a PostgreSQL - Facturación OCR

echo "🚀 Iniciando migración a PostgreSQL..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor instala Docker primero."
    exit 1
fi

# Verificar si contenedor ya existe
if docker ps -a --format 'table {{.Names}}' | grep -q "postgres-facturacion"; then
    echo "📦 Contenedor PostgreSQL ya existe. Iniciando..."
    docker start postgres-facturacion
else
    echo "📦 Creando contenedor PostgreSQL..."
    docker run -d --name postgres-facturacion \
        -e POSTGRES_PASSWORD=micontraseña \
        -e POSTGRES_USER=facturacion_user \
        -e POSTGRES_DB=facturacion_ocr \
        -p 5432:5432 \
        -v postgres_data:/var/lib/postgresql/data \
        postgres:15
fi

# Esperar a que PostgreSQL inicie
echo "⏳ Esperando a que PostgreSQL inicie..."
sleep 30

# Verificar conexión
echo "🔍 Verificando conexión a PostgreSQL..."
if docker exec postgres-facturacion pg_isready -U facturacion_user -d facturacion_ocr; then
    echo "✅ PostgreSQL está listo!"
else
    echo "❌ No se pudo conectar a PostgreSQL"
    exit 1
fi

# Configurar variables de entorno
echo "⚙️ Configurando variables de entorno..."
if [ ! -f .env ]; then
    echo "# Base de Datos PostgreSQL" > .env
    echo "DATABASE_URL=postgresql://facturacion_user:micontraseña@localhost:5432/facturacion_ocr" >> .env
    echo "DB_SCHEMA=public" >> .env
    echo "✅ Archivo .env creado"
else
    echo "⚠️  Archivo .env ya existe. Por favor agrega:"
    echo "   DATABASE_URL=postgresql://facturacion_user:micontraseña@localhost:5432/facturacion_ocr"
    echo "   DB_SCHEMA=public"
fi

# Ejecutar migración
echo "🔄 Ejecutando migración de tablas..."
if python add_cfdi_tables.py; then
    echo "✅ Migración completada exitosamente!"
else
    echo "❌ Error en migración. Revisa los logs."
    exit 1
fi

echo ""
echo "🎉 Migración a PostgreSQL completada!"
echo ""
echo "📋 Resumen:"
echo "   - PostgreSQL corriendo en localhost:5432"
echo "   - Base de datos: facturacion_ocr"
echo "   - Usuario: facturacion_user"
echo "   - Tablas migradas: CFDI, CSF, Invoices"
echo ""
echo "🚀 Para iniciar la aplicación:"
echo "   python -m backend.app.main"
echo ""
echo "🔄 Para volver a SQLite:"
echo "   - Detén PostgreSQL: docker stop postgres-facturacion"
echo "   - Elimina DATABASE_URL del .env"
echo ""