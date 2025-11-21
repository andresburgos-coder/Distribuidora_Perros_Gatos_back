"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime


# Auth Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=10)


class RegisterRequest(BaseModel):
    nombre_completo: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=10)
    cedula: str = Field(..., pattern=r"^\d{6,12}$")
    
    @field_validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain special character')
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class VerificationCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., pattern=r"^\d{6}$")


# Category Schemas
class SubcategoriaCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)


class CategoriaCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    subcategorias: List[SubcategoriaCreate] = []


class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)


class SubcategoriaResponse(BaseModel):
    id: int
    nombre: str
    
    class Config:
        from_attributes = True


class CategoriaResponse(BaseModel):
    id: int
    nombre: str
    subcategorias: List[SubcategoriaResponse] = []
    
    class Config:
        from_attributes = True


# Product Schemas
class ProductoCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    precio: float = Field(..., gt=0)
    peso_gramos: int = Field(..., gt=0)
    categoria_id: int
    subcategoria_id: int
    cantidad_disponible: int = Field(default=0, ge=0)
    sku: Optional[str] = Field(None, max_length=50)


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    precio: Optional[float] = Field(None, gt=0)
    peso_gramos: Optional[int] = Field(None, gt=0)
    categoria_id: Optional[int] = None
    subcategoria_id: Optional[int] = None
    cantidad_disponible: Optional[int] = Field(None, ge=0)
    activo: Optional[bool] = None


class ProductoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    precio: float
    peso_gramos: int
    cantidad_disponible: int
    sku: Optional[str]
    categoria_id: int
    subcategoria_id: int
    activo: bool
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True


# Inventory Schemas
class ReabastecimientoRequest(BaseModel):
    cantidad: int = Field(..., gt=0)
    referencia: Optional[str] = Field(None, max_length=200)


class InventarioHistorialResponse(BaseModel):
    id: int
    producto_id: int
    cantidad_anterior: int
    cantidad_nueva: int
    tipo_movimiento: str
    referencia: Optional[str]
    usuario_id: Optional[int]
    fecha: datetime
    
    class Config:
        from_attributes = True


# Cart Schemas
class CartItemCreate(BaseModel):
    producto_id: int
    cantidad: int = Field(..., gt=0)


class CartItemResponse(BaseModel):
    id: int
    producto_id: int
    cantidad: int
    precio_unitario: float
    
    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    id: int
    usuario_id: Optional[int]
    session_id: Optional[str]
    items: List[CartItemResponse] = []
    total: float
    
    class Config:
        from_attributes = True


# Order Schemas
class PedidoCreate(BaseModel):
    direccion_entrega: str = Field(..., min_length=10)
    telefono_contacto: str = Field(..., pattern=r"^\d{7,15}$")
    nota_especial: Optional[str] = Field(None, max_length=500)


class PedidoEstadoUpdate(BaseModel):
    estado: str = Field(..., pattern="^(Pendiente|Enviado|Entregado|Cancelado)$")
    nota: Optional[str] = Field(None, max_length=300)


class PedidoItemResponse(BaseModel):
    id: int
    producto_id: int
    cantidad: int
    precio_unitario: float
    
    class Config:
        from_attributes = True


class PedidoResponse(BaseModel):
    id: int
    usuario_id: int
    estado: str
    total: float
    fecha_creacion: datetime
    items: List[PedidoItemResponse] = []
    
    class Config:
        from_attributes = True


# Carousel Schemas
class CarruselImagenCreate(BaseModel):
    orden: int = Field(..., ge=1, le=5)
    link_url: Optional[str] = Field(None, max_length=500)


class CarruselImagenUpdate(BaseModel):
    orden: Optional[int] = Field(None, ge=1, le=5)
    link_url: Optional[str] = Field(None, max_length=500)


class CarruselImagenResponse(BaseModel):
    id: int
    orden: int
    ruta_imagen: str
    link_url: Optional[str]
    activo: bool
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True


# User Schemas
class UsuarioPublicResponse(BaseModel):
    id: int
    nombre_completo: str
    email: str
    
    class Config:
        from_attributes = True


class UsuarioDetailResponse(BaseModel):
    id: int
    nombre_completo: str
    email: str
    cedula: str
    fecha_registro: datetime
    ultimo_login: Optional[datetime]
    
    class Config:
        from_attributes = True


# Error Response
class ErrorResponse(BaseModel):
    error: str
    detalle: Optional[str] = None
    codigo: str
