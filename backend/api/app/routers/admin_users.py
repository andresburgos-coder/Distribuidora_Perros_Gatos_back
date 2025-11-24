"""
Admin Users router: View customer profiles and order history
Handles HU_MANAGE_USERS
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, text
from typing import List, Optional
from app.schemas import (
    UsuarioDetailResponse,
    PedidoResponse,
    UsuariosListResponse,
    UsuarioDetailWrapper,
    PedidosListResponse,
)
from app.database import get_db
from app.models import Usuario, Pedido, PedidoItem
from app.utils import security_utils
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/usuarios",
    tags=["admin-users"]
)


def require_admin(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """
    Dependency that verifies JWT and that the user is admin.
    Raises 401/403 accordingly.
    """
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"status": "error", "message": "No autenticado"})
    token = auth_header.split(" ", 1)[1]
    try:
        payload = security_utils.verify_jwt_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"status": "error", "message": "Token inválido"})
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"status": "error", "message": "Token inválido"})
    usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if not usuario or not usuario.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"status": "error", "message": "Cuenta no activa"})
    if not usuario.es_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"status": "error", "message": "Acceso denegado"})
    return usuario


@router.get("", response_model=UsuariosListResponse)
async def list_users(
    q: Optional[str] = Query(None, description="Búsqueda libre por id, nombre, cedula o email"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    sort: str = Query("fecha_registro", description="Campo para ordenar: nombre o fecha_registro"),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin)
):
    """
    List all customers with optional search and pagination.
    Returns shape matching `UsuariosListResponse`.
    """
    try:
        query = db.query(Usuario)

        # Apply free-text search
        if q:
            q_lower = q.lower()
            filters = []
            if q.isdigit():
                filters.append(Usuario.id == int(q))
            filters.append(func.lower(Usuario.nombre_completo).like(f"%{q_lower}%"))
            filters.append(func.lower(Usuario.email).like(f"%{q_lower}%"))
            filters.append(func.lower(Usuario.cedula).like(f"%{q_lower}%"))
            query = query.filter(or_(*filters))

        total = query.count()

        # Sorting
        if sort == "nombre":
            query = query.order_by(Usuario.nombre_completo.asc())
        else:
            query = query.order_by(Usuario.fecha_registro.desc())

        # Pagination
        offset = (page - 1) * pageSize
        users = query.offset(offset).limit(pageSize).all()

        data = []
        for u in users:
            data.append({
                "id": u.id,
                "nombre_completo": u.nombre_completo,
                "cedula": u.cedula,
                "email": u.email,
                "direccion_envio": u.direccion_envio,
                "fecha_registro": u.fecha_registro,
            })

        return {"status": "success", "data": data, "meta": {"page": page, "pageSize": pageSize, "total": total}}
    except Exception:
        logger.exception("Error listing users")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"status": "error", "message": "Error al listar usuarios."})


@router.get("/{usuario_id}", response_model=UsuarioDetailWrapper)
async def get_user(usuario_id: int, db: Session = Depends(get_db), _admin: Usuario = Depends(require_admin)):
    """
    Get full user profile and a pedidosResumen summary.
    """
    try:
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"status": "error", "message": "Usuario no encontrado."})

        # pedidosResumen
        pedidos_query = db.query(Pedido).filter(Pedido.usuario_id == usuario.id)
        total_pedidos = pedidos_query.count()
        ultimo = pedidos_query.order_by(Pedido.fecha_creacion.desc()).first()
        ultimo_pedido = None
        if ultimo:
            ultimo_pedido = {"id": ultimo.id, "fecha": ultimo.fecha_creacion, "total": float(ultimo.total), "estado": ultimo.estado}

        result = {
            "id": usuario.id,
            "nombre_completo": usuario.nombre_completo,
            "email": usuario.email,
            "cedula": usuario.cedula,
            "telefono": usuario.telefono,
            "direccion_envio": usuario.direccion_envio,
            "preferencia_mascotas": usuario.preferencia_mascotas,
            "fecha_registro": usuario.fecha_registro,
            "ultimo_login": usuario.ultimo_login,
            "rol": "admin" if usuario.es_admin else "cliente",
            "pedidosResumen": {"totalPedidos": total_pedidos, "ultimoPedido": ultimo_pedido}
        }

        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching user %s", usuario_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"status": "error", "message": "Error al obtener el usuario."})


@router.get("/{usuario_id}/pedidos", response_model=PedidosListResponse)
async def get_user_orders(
    usuario_id: int,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin)
):
    """
    Get paginated order history for a customer.
    """
    try:
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"status": "error", "message": "Usuario no encontrado."})

        query = db.query(Pedido).filter(Pedido.usuario_id == usuario_id)
        if estado:
            query = query.filter(Pedido.estado == estado)

        total = query.count()
        offset = (page - 1) * pageSize
        pedidos = query.order_by(Pedido.fecha_creacion.desc()).offset(offset).limit(pageSize).all()

        data = []
        for p in pedidos:
            items = db.query(PedidoItem).filter(PedidoItem.pedido_id == p.id).all()
            items_list = []
            for it in items:
                items_list.append({
                    "id": it.id,
                    "producto_id": it.producto_id,
                    "cantidad": it.cantidad,
                    "precio_unitario": float(it.precio_unitario)
                })

            data.append({
                "id": p.id,
                "usuario_id": p.usuario_id,
                "estado": p.estado,
                "total": float(p.total),
                "fecha_creacion": p.fecha_creacion,
                "items": items_list
            })

        return {"status": "success", "data": data, "meta": {"page": page, "pageSize": pageSize, "total": total}}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching orders for user %s", usuario_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"status": "error", "message": "Error al obtener los pedidos del usuario."})


@router.get("/{usuario_id}/stats")
async def get_user_stats(usuario_id: int, db: Session = Depends(get_db), _admin: Usuario = Depends(require_admin)):
    """
    Compute summary statistics for a user: total orders, total spent, last order date, preferred category.
    """
    try:
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"status": "error", "message": "Usuario no encontrado."})

        # Total orders and total spent
        total_pedidos = db.query(func.count(Pedido.id)).filter(Pedido.usuario_id == usuario_id).scalar() or 0
        total_gastado = db.query(func.coalesce(func.sum(Pedido.total), 0)).filter(Pedido.usuario_id == usuario_id).scalar() or 0.0
        ultimo_pedido = db.query(func.max(Pedido.fecha_creacion)).filter(Pedido.usuario_id == usuario_id).scalar()

        # Preferred category (most spent) - using raw SQL for simplicity
        pref_q = text("""
            SELECT TOP 1 c.id as categoria_id, c.nombre as categoria_nombre, SUM(pi.cantidad * pi.precio_unitario) as total_spent
            FROM PedidoItems pi
            INNER JOIN Pedidos p ON pi.pedido_id = p.id
            INNER JOIN Productos prod ON pi.producto_id = prod.id
            INNER JOIN Categorias c ON prod.categoria_id = c.id
            WHERE p.usuario_id = :id
            GROUP BY c.id, c.nombre
            ORDER BY total_spent DESC
        """)
        pref_res = db.execute(pref_q, {"id": usuario_id}).fetchone()

        return {
            "total_pedidos": int(total_pedidos),
            "total_gastado": float(total_gastado),
            "ultimo_pedido": ultimo_pedido,
            "preferida": {"categoria_id": pref_res.categoria_id, "nombre": pref_res.categoria_nombre} if pref_res else None
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error computing stats for user %s", usuario_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"status": "error", "message": "Error al calcular estadísticas del usuario."})
