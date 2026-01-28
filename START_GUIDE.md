# Opciones para ejecutar frontend y backend simultáneamente

## 🚀 Scripts Disponibles

### 1. Script Python (Recomendado)
```bash
python start.py
```
- Muestra salida en tiempo real de ambos procesos
- Maneja Ctrl+C graceful
- Monitorea el estado de los servicios

### 2. Script Batch (Windows)
```bash
start.bat
```
- Abre ventanas separadas para cada servicio
- Fácil para desarrollo en Windows
- No requiere dependencias adicionales

### 3. Script PowerShell
```powershell
.\start.ps1
```
- Moderno y más potente
- Mejor manejo de procesos
- Requiere PowerShell 5.1+

## 📡 URLs de Acceso

- **Frontend**: http://localhost:8000
- **Backend API**: http://localhost:8000/api
- **Documentación API**: http://localhost:8000/docs

## 🛑 Detener Servicios

- **Script Python**: Ctrl+C
- **Script Batch**: Cierra las ventanas abiertas
- **Script PowerShell**: Ctrl+C o cierra la terminal

## 🔧 Requisitos Previos

1. Python 3.8+ instalado
2. Dependencias instaladas: `pip install -r requirements.txt`
3. Base de datos PostgreSQL disponible
4. Opcional: Redis para tareas asíncronas

## 🐛 Solución de Problemas

### Si el puerto 8000 está ocupado:
```bash
# Ver qué usa el puerto
netstat -ano | findstr :8000

# Matar el proceso (reemplazar PID)
taskkill /PID <PID> /F
```

### Si Python no está en PATH:
1. Busca la instalación de Python
2. Agrega al PATH de Windows
3. Reinicia la terminal

### Si hay errores de dependencias:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 📝 Notas

- El frontend usa el servidor integrado de FastAPI para desarrollo
- Para producción, considera usar un servidor WSGI como Gunicorn
- El script Python es el más robusto para desarrollo continuo