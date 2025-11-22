"""
Middleware package for FastAPI application
"""
from app.middleware.error_handler import setup_error_handlers

__all__ = ['setup_error_handlers']

