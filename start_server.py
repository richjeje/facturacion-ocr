import uvicorn

# Load env from .env automatically like in production
try:
    from dotenv import load_dotenv
    load_dotenv()  # type: ignore
except Exception:
    pass  # If dotenv not available, continue (fallback to os.getenv)

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)