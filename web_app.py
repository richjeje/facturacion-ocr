"""Backward-compatible entrypoint.

The FastAPI app lives in `backend/app/main.py`.
"""

from backend.app.main import *  # noqa: F403


if __name__ == "__main__":
    from backend.app.main import app
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
