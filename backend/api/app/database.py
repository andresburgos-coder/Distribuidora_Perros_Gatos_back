"""
Database connection and session management using SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Verify connection health before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to inject database session
    Ensures proper session cleanup after request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database by creating all tables"""
    try:
        # Only create tables if there are models registered
        if Base.metadata.tables:
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized successfully")
        else:
            logger.info("No database models found, skipping table creation")
    except Exception as e:
        logger.warning(f"Could not initialize database: {str(e)}")
        logger.warning("Application will continue without database connection")
        # Don't raise - allow app to start without DB for development


def close_db():
    """Close database engine connection"""
    engine.dispose()
    logger.info("Database connection closed")
