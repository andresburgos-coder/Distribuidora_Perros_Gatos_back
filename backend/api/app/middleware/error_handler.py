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
        Returns appropriate status with field-specific error details
        Matches HU specifications for exact error messages
        """
        errors = []
        main_message = "Por favor, completa todos los campos obligatorios."
        
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            error_msg = error.get("msg", "")
            error_type = error.get("type", "")
            
            # Check for specific error messages from HU specifications
            if "password" in field.lower() and any(keyword in error_msg.lower() for keyword in ["mayúscula", "uppercase", "número", "digit", "especial", "special", "caracteres", "characters"]):
                main_message = "La contraseña debe tener al menos 10 caracteres, incluir una mayúscula, un número y un carácter especial."
                break
            elif "email" in field.lower() and "value is not a valid email address" in error_msg.lower():
                main_message = "El correo electrónico no tiene un formato válido."
                break
            elif error_type == "value_error.missing" or "field required" in error_msg.lower():
                main_message = "Por favor, completa todos los campos obligatorios."
            
            errors.append({
                "field": field,
                "message": error_msg,
                "type": error_type
            })
        
        logger.warning(f"Validation error on {request.url.path}: {errors}")
        
        # Return 400 for validation errors to match HU specifications
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "error",
                "message": main_message
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

