"""Database engine and session management for Kisaan Dost."""

from __future__ import annotations

import logging
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings
from app.db.models import Base

logger = logging.getLogger(__name__)


def _get_database_url() -> str:
    if settings.database_url:
        # Handle postgres:// vs postgresql://
        url = settings.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    # Default to local SQLite fallback if PostgreSQL URL is not provided
    db_path = settings.project_root / "data" / "processed" / "kisaan_dost.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"


def create_db_engine(url: Optional[str] = None) -> Engine:
    db_url = url or _get_database_url()
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        return create_engine(db_url, connect_args=connect_args)

    return create_engine(
        db_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


engine: Engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(target_engine: Optional[Engine] = None) -> None:
    """Initialize database tables according to Base metadata."""
    eng = target_engine or engine
    try:
        Base.metadata.create_all(bind=eng)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_db_connected(target_engine: Optional[Engine] = None) -> bool:
    """Check if the database engine can execute a test query."""
    eng = target_engine or engine
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database connectivity check failed: {e}")
        return False
