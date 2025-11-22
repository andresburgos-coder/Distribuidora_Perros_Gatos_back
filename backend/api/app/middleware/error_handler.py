"""
Error handler middleware for FastAPI
Handles global exception handlers for common errors
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, DatabaseError
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


def setup_error_handlers(app: FastAPI):
    """
    Setup global exception handlers for the FastAPI application
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Handle Pydantic validation errors
        Returns 422 with field-specific error details
        """
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })
        
        logger.warning(f"Validation error on {request.url.path}: {errors}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "message": "Validation error",
                "errors": errors
            }
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        """
        Handle database errors
        Returns 500 with generic error message (don't expose DB details)
        """
        logger.error(f"Database error on {request.url.path}: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Database error occurred"
            }
        )
    
    @app.exception_handler(DatabaseError)
    async def generic_database_exception_handler(request: Request, exc: DatabaseError):
        """
        Handle generic database errors
        """
        logger.error(f"Database error on {request.url.path}: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Database error occurred"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        Handle all other unhandled exceptions
        Returns 500 with generic error message
        """
        logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Internal server error"
            }
        )

