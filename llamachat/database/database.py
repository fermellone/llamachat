from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from llamachat.config import AppConfig
import logging

logger = logging.getLogger(__name__)

def get_engine():
    """Get SQLAlchemy engine with proper configuration."""
    return create_engine(
        AppConfig.database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )

engine = None

def init_db():
    """Initialize database connection and create schema."""
    global engine
    try:
        engine = get_engine()
        SQLModel.metadata.create_all(engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def get_session() -> Generator[Session, None, None]:
    """Get database session."""
    if engine is None:
        init_db()
    with Session(engine) as session:
        yield session 