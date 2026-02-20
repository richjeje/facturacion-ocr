import os

from pathlib import Path
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional

# Load DATABASE_URL, etc. from .env by default
try:
    from dotenv import load_dotenv # type: ignore

    _backend_dir = Path(__file__).resolve().parents[1]  # backend/
    _env_path = _backend_dir / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except Exception:
    # If python-dotenv isn't installed, fall back to OS env
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./facturacion_ocr.db")
_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

# Avoid table-name clashes on shared Postgres databases by using a dedicated schema.
_metadata = None
if not DATABASE_URL.startswith("sqlite"):
    _schema = os.getenv("DB_SCHEMA", "mistica")
    _metadata = MetaData(schema=_schema)
else:
    _metadata = MetaData()

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base(metadata=_metadata)

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
