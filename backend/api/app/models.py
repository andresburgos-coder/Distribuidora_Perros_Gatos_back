"""
SQLAlchemy models for the application
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


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
