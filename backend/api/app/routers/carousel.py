"""
Carousel router: Manage homepage carousel images
Handles HU_MANAGE_CAROUSEL
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.schemas import CarruselImagenCreate, CarruselImagenResponse, CarruselImagenUpdate
from app.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/carrusel",
    tags=["carousel"]
)


@router.get("", response_model=List[CarruselImagenResponse])
async def list_carousel_images(db: Session = Depends(get_db)):
    """
    List all carousel images ordered by position
    
    Requirements (HU_MANAGE_CAROUSEL):
    - Return max 5 images
    - Sorted by orden (1-5)
    - Include ruta_imagen and link_url
    - Only active images
    """
    # TODO: Implement list carousel images logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("", response_model=CarruselImagenResponse)
async def add_carousel_image(
    orden: int = Form(..., ge=1, le=5),
    link_url: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Add new carousel image
    
    Requirements (HU_MANAGE_CAROUSEL):
    - Max 5 images allowed (error if trying to exceed)
    - orden must be unique and 1-5
    - File max 10 MB
    - Allowed formats: jpg, jpeg, png, svg, webp
    - Stores in uploads/carrusel/
    - Publishes carrusel.imagen.crear queue message
    """
    # TODO: Implement add carousel image logic
    # 1. Check max 5 images limit
    # 2. Validate orden (1-5) is unique
    # 3. Validate file size and format
    # 4. Save file to uploads/carrusel/
    # 5. Create CarruselImagen record
    # 6. Publish carrusel.imagen.crear queue message
    # 7. Return created image
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.put("/{imagen_id}", response_model=CarruselImagenResponse)
async def update_carousel_image(
    imagen_id: int,
    request: CarruselImagenUpdate,
    db: Session = Depends(get_db)
):
    """
    Update carousel image order or link
    
    Requirements (HU_MANAGE_CAROUSEL):
    - Update orden (1-5, must remain unique)
    - Update link_url
    - Publishes carrusel.imagen.actualizar queue message
    """
    # TODO: Implement update carousel image logic
    # 1. Validate imagen exists
    # 2. If updating orden, check uniqueness
    # 3. Update CarruselImagen
    # 4. Publish carrusel.imagen.actualizar queue message
    # 5. Return updated image
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.delete("/{imagen_id}")
async def delete_carousel_image(imagen_id: int, db: Session = Depends(get_db)):
    """
    Delete carousel image
    
    Requirements (HU_MANAGE_CAROUSEL):
    - Delete image file and database record
    - Reorder remaining images to maintain 1-5 sequence
    - Publishes carrusel.imagen.eliminar queue message
    """
    # TODO: Implement delete carousel image logic
    # 1. Validate imagen exists
    # 2. Delete image file from uploads/carrusel/
    # 3. Delete CarruselImagen record
    # 4. Reorder remaining images (adjust orden)
    # 5. Publish carrusel.imagen.eliminar queue message
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/{imagen_id}/reorder")
async def reorder_carousel(
    imagen_id: int,
    nueva_orden: int = Form(..., ge=1, le=5),
    db: Session = Depends(get_db)
):
    """
    Reorder carousel image position
    
    Requirements (HU_MANAGE_CAROUSEL):
    - Move image to new position (1-5)
    - Adjust other images' positions accordingly
    - Publishes carrusel.imagen.reordenar queue message
    """
    # TODO: Implement reorder logic
    # 1. Validate imagen exists
    # 2. Validate nueva_orden (1-5)
    # 3. If moving to occupied position, shift others
    # 4. Update order in database
    # 5. Publish carrusel.imagen.reordenar queue message
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
