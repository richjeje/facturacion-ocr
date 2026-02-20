"""Entry point de compatibilidad — Servidor Web FastAPI.

Uso:
    python web_app.py
    # o directamente con uvicorn:
    uvicorn backend.api.main:app --reload
"""

from backend.api.main import app  # noqa: F401

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
