from __future__ import annotations

from typing import Iterable, Mapping, List

from .config import setup_logging
from .database import SessionLocal
from .models import Invoice

logger = setup_logging()


def save_to_database(rows: Iterable[Mapping]) -> None:
    """Persist parsed invoice rows into the database."""
    materialized: List[Mapping] = list(rows)

    db = SessionLocal()
    try:
        for row in materialized:
            db.add(Invoice(**row))
        db.commit()
        logger.info(f"Datos guardados en BD: {len(materialized)} registros")
    except Exception as e:
        db.rollback()
        logger.error(f"Error guardando en BD: {e}")
    finally:
        db.close()
