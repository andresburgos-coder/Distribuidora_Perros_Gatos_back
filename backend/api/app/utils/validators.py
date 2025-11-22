"""
Validation utilities for product, category, and inventory data
"""
import re
import logging
from typing import Tuple
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class ValidatorUtils:
    """Utilities for data validation"""
    
    @staticmethod
    def validate_product_name(nombre: str) -> bool:
        """Validate product name (3-100 characters)"""
        return 3 <= len(nombre) <= 100
    
    @staticmethod
    def validate_price(precio: float) -> bool:
        """Validate product price (must be positive)"""
        return precio > 0
    
    @staticmethod
    def validate_weight(peso_gramos: int) -> bool:
        """Validate product weight (must be positive)"""
        return peso_gramos > 0
    
    @staticmethod
    def validate_quantity(cantidad: int) -> bool:
        """Validate quantity (must be non-negative)"""
        return cantidad >= 0
    
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_cedula(cedula: str) -> bool:
        """Validate cedula format (6-12 digits)"""
        return re.match(r'^\d{6,12}$', cedula) is not None
    
    @staticmethod
    def validate_phone(telefono: str) -> bool:
        """Validate phone number format (7-15 digits)"""
        return re.match(r'^\d{7,15}$', telefono) is not None
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        Validate password strength
        Requirements: 10+ chars, uppercase, digit, special char
        Returns: (is_valid, error_message)
        """
        if len(password) < 10:
            return False, "Password must be at least 10 characters"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain uppercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain digit"
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return False, "Password must contain special character"
        
        return True, ""
    
    @staticmethod
    def validate_category_name(nombre: str) -> bool:
        """Validate category name (2-100 characters)"""
        return 2 <= len(nombre) <= 100
    
    @staticmethod
    def validate_subcategory_name(nombre: str) -> bool:
        """Validate subcategory name (2-100 characters)"""
        return 2 <= len(nombre) <= 100
    
    @staticmethod
    def validate_carousel_order(orden: int) -> bool:
        """Validate carousel image order (1-5)"""
        return 1 <= orden <= 5
    
    @staticmethod
    def validate_carousel_url(url: str) -> bool:
        """Validate carousel image URL"""
        pattern = r'https?://[^\s]+'
        return re.match(pattern, url) is not None if url else True
    
    @staticmethod
    def validate_address(direccion: str) -> bool:
        """Validate address (minimum 10 characters)"""
        return len(direccion) >= 10
    
    @staticmethod
    def validate_verification_code(code: str) -> bool:
        """Validate verification code (6 digits)"""
        return re.match(r'^\d{6}$', code) is not None
    
    @staticmethod
    def validate_order_status(status: str) -> bool:
        """Validate order status"""
        valid_statuses = {"Pendiente", "Enviado", "Entregado", "Cancelado"}
        return status in valid_statuses
    
    @staticmethod
    def raise_validation_error(detail: str, error_code: str = "VALIDATION_ERROR"):
        """Raise HTTP validation exception"""
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


validator_utils = ValidatorUtils()
