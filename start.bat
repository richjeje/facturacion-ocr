@echo off
echo 🎯 Iniciando Facturacion OCR - Frontend + Backend
echo ========================================

REM Verificar que Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python no está instalado o no está en el PATH
    pause
    exit /b 1
)

REM Verificar que estamos en el directorio correcto
if not exist "backend\app\main.py" (
    echo ❌ Error: No se encuentra el archivo backend\app\main.py
    echo Ejecuta este script desde el directorio raíz del proyecto
    pause
    exit /b 1
)

REM Iniciar backend en una nueva ventana
echo 🚀 Iniciando backend FastAPI...
start "Backend FastAPI" cmd /k "cd /d %~dp0 && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Esperar un momento
timeout /t 3 /nobreak >nul

REM Iniciar frontend en una nueva ventana
echo 🌐 Iniciando servidor frontend...
start "Frontend" cmd /k "cd /d %~dp0 && python backend\app\main.py"

REM Esperar un momento
timeout /t 2 /nobreak >nul

echo ✅ Servicios iniciados:
echo    📡 Backend: http://localhost:8000
echo    🌍 Frontend: http://localhost:8000
echo    📚 API Docs: http://localhost:8000/docs
echo.
echo 🔄 Las ventanas de backend y frontend se han abierto en ventanas separadas
echo    Puedes cerrar esta ventana o mantenerla abierta
echo.
echo 🛑 Para detener todos los servicios, cierra las ventanas abiertas
echo    o presiona Ctrl+C en cada ventana

pause