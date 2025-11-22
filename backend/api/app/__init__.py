"""
__init__.py for app package
"""
from app.config import settings, Settings
from app.database import init_db, close_db, get_db, SessionLocal, Base

# Import models to ensure they're registered with Base
from app import models  # noqa: F401

__all__ = [
    'settings',
    'Settings',
    'init_db',
    'close_db',
    'get_db',
    'SessionLocal',
    'Base',
]
