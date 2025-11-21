"""
Admin Users router: View customer profiles and order history
Handles HU_MANAGE_USERS
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.schemas import UsuarioDetailResponse, PedidoResponse
from app.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/usuarios",
    tags=["admin-users"]
)


@router.get("", response_model=List[UsuarioDetailResponse])
async def list_users(
    nombre: str = Query(None),
    email: str = Query(None),
    cedula: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all customers with optional search
    
    Requirements (HU_MANAGE_USERS):
    - Search by nombre, email, or cedula (case-insensitive)
    - Sort by fecha_registro DESC (newest first)
    - Return user details but NO password
    - Pagination support
    - Database indexes on email, cedula, nombre for performance
    """
    # TODO: Implement list users logic
    # 1. Query Usuarios table
    # 2. Apply search filters (nombre LIKE, email LIKE, cedula exact)
    # 3. Sort by fecha_registro DESC
    # 4. Apply pagination
    # 5. Do NOT include password_hash
    # 6. Return users
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{usuario_id}", response_model=UsuarioDetailResponse)
async def get_user(usuario_id: int, db: Session = Depends(get_db)):
    """
    Get customer profile details
    
    Requirements (HU_MANAGE_USERS):
    - Return full user information
    - Include fecha_registro and ultimo_login
    - Do NOT include password
    - Return 404 if user not found
    """
    # TODO: Implement get user logic
    # 1. Query usuario by id
    # 2. Return details without password
    # 3. Raise 404 if not found
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{usuario_id}/pedidos", response_model=List[PedidoResponse])
async def get_user_orders(
    usuario_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get order history for customer
    
    Requirements (HU_MANAGE_USERS):
    - Return all pedidos for usuario_id
    - Sort by fecha_creacion DESC (newest first)
    - Include all pedido items
    - Pagination support
    """
    # TODO: Implement get user orders logic
    # 1. Validate usuario exists
    # 2. Query Pedidos for usuario_id
    # 3. Include PedidoItems
    # 4. Sort by fecha_creacion DESC
    # 5. Apply pagination
    # 6. Return orders
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.get("/{usuario_id}/stats")
async def get_user_stats(usuario_id: int, db: Session = Depends(get_db)):
    """
    Get customer statistics
    
    Requirements:
    - Total orders count
    - Total spent (sum of pedido totals)
    - Last order date
    - Preferred category (most purchased)
    """
    # TODO: Implement user stats logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
