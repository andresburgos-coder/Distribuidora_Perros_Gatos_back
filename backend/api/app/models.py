"""
SQLAlchemy models for database tables
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Usuario(Base):
    """
    Modelo para la tabla Usuarios
    Almacena información de los usuarios/clientes
    """
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre_completo = Column(String(100), nullable=False)
    cedula = Column(String(20), nullable=True, index=True)
    telefono = Column(String(20), nullable=True)
    direccion_envio = Column(String(500), nullable=True)
    preferencia_mascotas = Column(String(20), nullable=True)  # Perros, Gatos, Ambos, Ninguno
    is_active = Column(Boolean, default=False, nullable=False)  # False hasta verificar email
    
    # Campos para bloqueo de cuenta
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.getdate(), nullable=False)
    updated_at = Column(DateTime, server_default=func.getdate(), onupdate=func.getdate(), nullable=False)
    ultimo_login = Column(DateTime, nullable=True)
    
    # Relationships
    verification_codes = relationship("VerificationCode", back_populates="usuario", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="usuario", cascade="all, delete-orphan")
    
    # Note: Email uniqueness is enforced at application level with case-insensitive comparison
    # SQL Server collation can be set to case-insensitive, or we use LOWER() in queries
    
    def __repr__(self):
        return f"<Usuario(id={self.id}, email={self.email}, is_active={self.is_active})>"


class VerificationCode(Base):
    """
    Modelo para la tabla VerificationCodes
    Almacena códigos de verificación de email (solo hash, nunca texto plano)
    """
    __tablename__ = "verification_codes"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(255), nullable=False)  # Hash del código, nunca texto plano
    expires_at = Column(DateTime, nullable=False, index=True)
    attempts = Column(Integer, default=0, nullable=False)  # Intentos de verificación
    sent_count = Column(Integer, default=0, nullable=False)  # Cantidad de reenvíos
    created_at = Column(DateTime, server_default=func.getdate(), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)  # Si ya fue usado para verificar
    
    # Relationships
    usuario = relationship("Usuario", back_populates="verification_codes")
    
    def __repr__(self):
        return f"<VerificationCode(id={self.id}, usuario_id={self.usuario_id}, expires_at={self.expires_at})>"


class RefreshToken(Base):
    """
    Modelo para la tabla RefreshTokens
    Almacena los refresh tokens de los usuarios para la persistencia de sesión
    """
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.getdate(), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    ip = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    # Relationships
    usuario = relationship("Usuario", back_populates="refresh_tokens")
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, usuario_id={self.usuario_id}, revoked={self.revoked})>"


class CarruselImagen(Base):
    __tablename__ = 'carrusel_imagenes'

    id = Column(Integer, primary_key=True, index=True)
    imagen_url = Column(String(1024), nullable=False)
    thumbnail_url = Column(String(1024), nullable=True)
    orden = Column(Integer, nullable=False, index=True)
    link_url = Column(String(2048), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    activo = Column(Boolean, nullable=False, default=True)
