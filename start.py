#!/usr/bin/env python3
"""
Script para iniciar frontend y backend simultáneamente
"""

import subprocess
import sys
import os
import signal
import time
from pathlib import Path

# Directorio raíz del proyecto
ROOT_DIR = Path(__file__).parent

class ProcessManager:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def start_backend(self):
        """Iniciar el backend FastAPI"""
        print("Iniciando backend FastAPI...")
        backend_cmd = [
            sys.executable, "-m", "uvicorn", 
            "backend.api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ]
        
        # Cambiar al directorio backend para imports relativos
        backend_process = subprocess.Popen(
            backend_cmd,
            cwd=ROOT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        self.processes.append(("Backend", backend_process))
        return backend_process
    
    def start_frontend(self):
        """Iniciar el servidor frontend"""
        print("Iniciando servidor frontend...")
        frontend_cmd = [
            sys.executable, "start_server.py"
        ]
        
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd=ROOT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        self.processes.append(("Frontend", frontend_process))
        return frontend_process
    
    def monitor_processes(self):
        """Monitorear procesos y mostrar salida"""
        try:
            while self.running and any(p.poll() is None for _, p in self.processes):
                for name, process in self.processes:
                    if process.poll() is None:
                        # Leer salida sin bloquear
                        try:
                            line = process.stdout.readline()
                            if line:
                                print(f"[{name}] {line.strip()}")
                        except:
                            pass
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nInterrumpiendo procesos...")
            self.stop_all()
    
    def stop_all(self):
        """Detener todos los procesos"""
        self.running = False
        for name, process in self.processes:
            if process.poll() is None:
                print(f"Deteniendo {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

def main():
    print("Iniciando Facturacion OCR - Frontend + Backend")
    print("=" * 50)
    
    manager = ProcessManager()
    
    try:
        # Verificar que estamos en el directorio correcto
        if not (ROOT_DIR / "backend" / "api" / "main.py").exists():
            print("Error: No se encuentra el archivo backend/api/main.py")
            print("Ejecuta este script desde el directorio raíz del proyecto")
            sys.exit(1)
        
        # Iniciar procesos
        backend_process = manager.start_backend()
        time.sleep(2)  # Dar tiempo al backend a iniciar
        
        frontend_process = manager.start_frontend()
        time.sleep(1)  # Dar tiempo al frontend a iniciar
        
        print("\nServicios iniciados:")
        print("   Backend: http://localhost:8000")
        print("   Frontend: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        print("\nPresiona Ctrl+C para detener todos los servicios")
        print("=" * 50)
        
        # Monitorear procesos
        manager.monitor_processes()
        
    except KeyboardInterrupt:
        manager.stop_all()
    except Exception as e:
        print(f"Error: {e}")
        manager.stop_all()
        sys.exit(1)
    
    print("\nTodos los servicios han sido detenidos")

if __name__ == "__main__":
    main()