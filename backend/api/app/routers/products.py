"""
Products router: Create, Read, Update products for admin
Handles HU_CREATE_PRODUCT
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.schemas import ProductoCreate, ProductoResponse, ProductoUpdate
from app.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/productos",
    tags=["products"]
)


@router.post("", response_model=ProductoResponse)
async def create_product(
    request: ProductoCreate,
    db: Session = Depends(get_db)
):
    """
    Create new product with details
    
    Requirements (HU_CREATE_PRODUCT):
    - Validates product name, price, weight, category, subcategory
    - Price > 0, weight > 0
    - Category and subcategory must exist
    - Publishes productos.crear queue message
    - Handles image uploads separately
    """
    # TODO: Implement create product logic
    # 1. Validate product data (name, price, weight, category exists)
    # 2. Check subcategory belongs to category
    # 3. Create Producto in DB with cantidad_disponible
    # 4. Publish productos.crear queue message
    # 5. Return created product
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("", response_model=List[ProductoResponse])
async def list_products(
    categoria_id: int = Query(None, ge=1),
    subcategoria_id: int = Query(None, ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List products with optional filtering by category/subcategory
    
    Requirements:
    - Filter by category_id and/or subcategory_id
    - Pagination support
    - Return active products
    """
    # TODO: Implement list products logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{producto_id}", response_model=ProductoResponse)
async def get_product(producto_id: int, db: Session = Depends(get_db)):
    """
    Get product details
    
    Requirements:
    - Return full product information
    - Include images, category, subcategory
    """
    # TODO: Implement get product logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.put("/{producto_id}", response_model=ProductoResponse)
async def update_product(
    producto_id: int,
    request: ProductoUpdate,
    db: Session = Depends(get_db)
):
    """
    Update product information
    
    Requirements (HU_CREATE_PRODUCT):
    - Update name, price, weight, category, subcategory
    - Validates all fields
    - Publishes productos.actualizar queue message
    """
    # TODO: Implement update product logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/{producto_id}/images")
async def upload_product_image(
    producto_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload product image
    
    Requirements (HU_CREATE_PRODUCT):
    - Max 10 MB file size
    - Allowed formats: jpg, jpeg, png, svg, webp
    - Stores in uploads/productos/{producto_id}/
    - Publishes productos.imagen.crear queue message
    """
    # TODO: Implement image upload logic
    # 1. Validate product exists
    # 2. Validate file size (max 10 MB)
    # 3. Validate file extension
    # 4. Save file to uploads/productos/{producto_id}/
    # 5. Create ProductoImagen record
    # 6. Publish productos.imagen.crear queue message
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.delete("/{producto_id}/images/{imagen_id}")
async def delete_product_image(
    producto_id: int,
    imagen_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete product image
    
    Requirements (HU_CREATE_PRODUCT):
    - Delete image file and database record
    - Publishes productos.imagen.eliminar queue message
    """
    # TODO: Implement delete image logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.delete("/{producto_id}")
async def delete_product(producto_id: int, db: Session = Depends(get_db)):
    """
    Soft delete product (mark as inactive)
    
    Requirements:
    - Set activo=False instead of deleting
    - Publishes productos.eliminar queue message
    """
    # TODO: Implement delete product logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
