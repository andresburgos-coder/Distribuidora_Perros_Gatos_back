"""
Categories router: Create, Read, Update categories and subcategories
Handles HU_MANAGE_CATEGORIES
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.schemas import CategoriaCreate, CategoriaResponse, CategoriaUpdate
from app.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/categorias",
    tags=["categories"]
)


@router.get("", response_model=List[CategoriaResponse])
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all categories with subcategories
    
    Requirements (HU_MANAGE_CATEGORIES):
    - Returns hierarchical structure: Categorias -> Subcategorias
    - Supports pagination (skip, limit)
    """
    # TODO: Implement list categories logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("", response_model=CategoriaResponse)
async def create_category(request: CategoriaCreate, db: Session = Depends(get_db)):
    """
    Create new category with subcategories
    
    Requirements (HU_MANAGE_CATEGORIES):
    - Category name must be unique (case-insensitive)
    - Can create subcategories in same request
    - Publishes categorias.crear queue message
    - Returns created category
    """
    # TODO: Implement create category logic
    # 1. Validate category name (2-100 chars)
    # 2. Check uniqueness (case-insensitive)
    # 3. Create Categoria in DB
    # 4. Create Subcategorias if provided
    # 5. Publish categorias.crear queue message
    # 6. Return created category
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{categoria_id}", response_model=CategoriaResponse)
async def get_category(categoria_id: int, db: Session = Depends(get_db)):
    """
    Get category details with subcategories
    
    Requirements:
    - Return full category with all subcategories
    """
    # TODO: Implement get category logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.put("/{categoria_id}", response_model=CategoriaResponse)
async def update_category(
    categoria_id: int,
    request: CategoriaUpdate,
    db: Session = Depends(get_db)
):
    """
    Update category name
    
    Requirements (HU_MANAGE_CATEGORIES):
    - Update category name (case-insensitive uniqueness check)
    - Publishes categorias.actualizar queue message
    - Cannot delete category if products exist
    """
    # TODO: Implement update category logic
    # 1. Validate category exists
    # 2. Validate new name (if provided) for uniqueness
    # 3. Update Categoria in DB
    # 4. Publish categorias.actualizar queue message
    # 5. Return updated category
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/{categoria_id}/subcategorias")
async def add_subcategory(categoria_id: int, nombre: str, db: Session = Depends(get_db)):
    """
    Add subcategory to existing category
    
    Requirements:
    - Subcategory name must be unique within category
    - Max 5 images for carousel per category
    """
    # TODO: Implement add subcategory logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.delete("/{categoria_id}")
async def delete_category(categoria_id: int, db: Session = Depends(get_db)):
    """
    Delete category if no products exist
    
    Requirements (HU_MANAGE_CATEGORIES):
    - Can only delete if no products in category/subcategories
    - Returns error if category has products
    """
    # TODO: Implement delete category logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
