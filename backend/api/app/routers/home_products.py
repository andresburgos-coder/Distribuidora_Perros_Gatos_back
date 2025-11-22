"""
Home/Products router: Public product browsing and cart management
Handles HU_HOME_PRODUCTS
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas import ProductoResponse, CartResponse, CartItemCreate, CartItemResponse
from app.database import get_db
from app.utils.security import security_utils
import logging
from sqlalchemy import text
import uuid
from app.utils.rabbitmq import rabbitmq_producer
import time

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["home-products"]
)


@router.get("/home/productos", response_model=List[ProductoResponse])
async def browse_products(
    categoria_id: int = Query(None),
    subcategoria_id: int = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Browse products by category/subcategory

    Requirements (HU_HOME_PRODUCTS):
    - Return hierarchical structure: Category -> Subcategory -> Products
    - Filter by categoria_id and/or subcategoria_id
    - Only return active products with stock > 0
    - Pagination support
    - Default limit 12 (typical grid layout)
    """
    params = {"skip": int(skip), "limit": int(limit)}
    where = ["p.activo = 1", "p.cantidad_disponible > 0"]
    if categoria_id:
        where.append("p.categoria_id = :categoria_id")
        params["categoria_id"] = int(categoria_id)
    if subcategoria_id:
        where.append("p.subcategoria_id = :subcategoria_id")
        params["subcategoria_id"] = int(subcategoria_id)

    where_sql = " AND ".join(where)
    try:
        q = text(
            f"SELECT p.id, p.nombre, p.descripcion, p.precio, p.peso_gramos, p.cantidad_disponible, p.categoria_id, p.subcategoria_id, p.activo, p.fecha_creacion FROM Productos p WHERE {where_sql} ORDER BY p.fecha_creacion DESC OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY"
        )
        rows = db.execute(q, params).fetchall()
    except Exception as e:
        logger.exception("Error querying home products: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al listar productos.")

    products = []
    if not rows:
        return []

    # collect ids for batch fetch
    prod_ids = [r.id for r in rows]
    cat_ids = set(r.categoria_id for r in rows if r.categoria_id)
    subcat_ids = set(r.subcategoria_id for r in rows if r.subcategoria_id)

    cats = {}
    subcats = {}
    try:
        if cat_ids:
            qcat = text(
                f"SELECT id, nombre FROM Categorias WHERE id IN ({', '.join([str(int(x)) for x in cat_ids])})"
            )
            for c in db.execute(qcat).fetchall():
                cats[c.id] = {"id": c.id, "nombre": c.nombre}
        if subcat_ids:
            qsub = text(
                f"SELECT id, nombre FROM Subcategorias WHERE id IN ({', '.join([str(int(x)) for x in subcat_ids])})"
            )
            for s in db.execute(qsub).fetchall():
                subcats[s.id] = {"id": s.id, "nombre": s.nombre}
    except Exception:
        logger.exception("Error fetching category/subcategory names")

    # images map
    images_map = {}
    try:
        if prod_ids:
            qimg = text(
                f"SELECT producto_id, ruta_imagen FROM ProductoImagenes WHERE producto_id IN ({', '.join([str(int(x)) for x in prod_ids])}) ORDER BY orden ASC"
            )
            for img in db.execute(qimg).fetchall():
                images_map.setdefault(img.producto_id, []).append(img.ruta_imagen)
    except Exception:
        logger.exception("Error fetching product images")

    for r in rows:
        products.append(
            {
                "id": int(r.id),
                "nombre": r.nombre,
                "descripcion": r.descripcion,
                "precio": float(r.precio),
                "peso_gramos": int(r.peso_gramos),
                "cantidad_disponible": int(r.cantidad_disponible or 0),
                "categoria_id": int(r.categoria_id) if r.categoria_id is not None else None,
                "subcategoria_id": int(r.subcategoria_id) if r.subcategoria_id is not None else None,
                "activo": bool(r.activo),
                "fecha_creacion": r.fecha_creacion,
                "categoria": cats.get(r.categoria_id),
                "subcategoria": subcats.get(r.subcategoria_id),
                "imagenes": images_map.get(r.id, []),
            }
        )

    return products


@router.get("/cart")
async def get_cart(
    session_id: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get current cart (anonymous or authenticated)
    
    Requirements (HU_HOME_PRODUCTS):
    - For anonymous users: use session_id from header/cookie
    - For authenticated users: use user_id from JWT
    - Return cart with items and total
    """
    # Determine usuario_id from JWT if provided
    usuario_id = None
    if authorization:
        try:
            token = authorization.split(" ")[-1]
            payload = security_utils.verify_token(token)
            usuario_id = payload.get('user_id') or payload.get('sub')
        except Exception:
            usuario_id = None

    cart_row = None
    try:
        if usuario_id:
            cart_row = db.execute(text("SELECT id, usuario_id, session_id FROM Carts WHERE usuario_id = :usuario_id"), {"usuario_id": usuario_id}).first()
        else:
            # anonymous flow: use session_id header to identify cart
            if not session_id:
                return {"id": None, "usuario_id": None, "session_id": None, "items": [], "total": 0.0}
            cart_row = db.execute(text("SELECT id, usuario_id, session_id FROM Carts WHERE session_id = :session_id"), {"session_id": session_id}).first()
    except Exception as e:
        logger.exception("Error querying cart: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener el carrito.")

    if not cart_row:
        return {"id": None, "usuario_id": None, "session_id": session_id, "items": [], "total": 0.0}

    cart_id = cart_row.id
    items = []
    total = 0.0
    try:
        q = text("SELECT ci.id, ci.producto_id, ci.cantidad, p.precio FROM CartItems ci JOIN Productos p ON p.id = ci.producto_id WHERE ci.cart_id = :cart_id")
        for it in db.execute(q, {"cart_id": cart_id}).fetchall():
            subtotal = float(it.precio) * int(it.cantidad)
            total += subtotal
            items.append({"id": int(it.id), "producto_id": int(it.producto_id), "cantidad": int(it.cantidad), "precio_unitario": float(it.precio)})
    except Exception as e:
        logger.exception("Error fetching cart items: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener los items del carrito.")

    return {"id": int(cart_id), "usuario_id": getattr(cart_row, 'usuario_id', None), "session_id": session_id, "items": items, "total": float(total)}


@router.post("/cart/add", response_model=CartResponse)
async def add_to_cart(
    request: CartItemCreate,
    session_id: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Add product to cart (anonymous or authenticated)
    
    Requirements (HU_HOME_PRODUCTS):
    - For anonymous: create cart if not exists, use session_id
    - For authenticated: use user cart
    - Validate product exists and stock available
    - If product already in cart: add to quantity (check stock limit)
    - Publishes cart.item.agregar queue message
    """
    # Validate input
    producto_id = int(request.producto_id)
    cantidad = int(request.cantidad)

    # 1. Validate producto exists and stock
    try:
        p = db.execute(text("SELECT id, precio, cantidad_disponible FROM Productos WHERE id = :id AND activo = 1"), {"id": producto_id}).first()
    except Exception as e:
        logger.exception("Error querying producto for cart add: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al validar producto.")

    if not p:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "error", "message": "Producto no encontrado."})

    if cantidad <= 0:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "La cantidad debe ser un número entero positivo."})

    if int(p.cantidad_disponible) < cantidad:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"status": "error", "message": "Sin existencias"})

    # 2. Determine cart owner: prefer authenticated usuario_id from JWT
    usuario_id = None
    if authorization:
        try:
            token = authorization.split(" ")[-1]
            payload = security_utils.verify_token(token)
            usuario_id = payload.get('user_id') or payload.get('sub')
        except Exception:
            usuario_id = None

    # If authenticated, find or create cart for usuario_id
    if usuario_id:
        try:
            cart = db.execute(text("SELECT id FROM Carts WHERE usuario_id = :usuario_id"), {"usuario_id": usuario_id}).first()
            if not cart:
                db.execute(text("INSERT INTO Carts (usuario_id, created_at, updated_at) VALUES (:usuario_id, GETUTCDATE(), GETUTCDATE())"), {"usuario_id": usuario_id})
                db.commit()
                cart = db.execute(text("SELECT id FROM Carts WHERE usuario_id = :usuario_id"), {"usuario_id": usuario_id}).first()
        except Exception as e:
            logger.exception("Error creating/fetching cart for usuario: %s", e)
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener carrito.")
        session_id = getattr(cart, 'session_id', None)
    else:
        # anonymous flow: create or use session_id
        if not session_id:
            session_id = str(uuid.uuid4())
            try:
                db.execute(text("INSERT INTO Carts (session_id, created_at, updated_at) VALUES (:session_id, GETUTCDATE(), GETUTCDATE())"), {"session_id": session_id})
                db.commit()
            except Exception as e:
                logger.exception("Error creating cart: %s", e)
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al crear carrito.")
        try:
            cart = db.execute(text("SELECT id FROM Carts WHERE session_id = :session_id"), {"session_id": session_id}).first()
        except Exception as e:
            logger.exception("Error querying cart after create: %s", e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener carrito.")

    if not cart:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al obtener carrito"})

    cart_id = int(cart.id)

    # 3. Check if product already in cart
    try:
        ci = db.execute(text("SELECT id, cantidad FROM CartItems WHERE cart_id = :cart_id AND producto_id = :producto_id"), {"cart_id": cart_id, "producto_id": producto_id}).first()
    except Exception as e:
        logger.exception("Error querying cart item: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al procesar carrito.")

    try:
        if ci:
            new_total = int(ci.cantidad) + cantidad
            if new_total > int(p.cantidad_disponible):
                return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"status": "error", "message": "Sin existencias"})
            db.execute(text("UPDATE CartItems SET cantidad = :cantidad WHERE id = :id"), {"cantidad": new_total, "id": int(ci.id)})
        else:
            db.execute(text("INSERT INTO CartItems (cart_id, producto_id, cantidad) VALUES (:cart_id, :producto_id, :cantidad)"), {"cart_id": cart_id, "producto_id": producto_id, "cantidad": cantidad})
        db.commit()
    except Exception as e:
        logger.exception("Error inserting/updating cart item: %s", e)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al actualizar carrito.")

    # Publish cart event (optional)
    try:
        message = {"requestId": str(uuid.uuid4()), "action": "cart_add", "payload": {"cartId": cart_id, "productoId": producto_id, "cantidad": cantidad, "userId": None}, "meta": {"timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ')}}
        rabbitmq_producer.connect()
        rabbitmq_producer.publish(queue_name="cart.events", message=message)
    except Exception:
        logger.exception("Failed to publish cart.events - continuing")
    finally:
        try:
            rabbitmq_producer.close()
        except Exception:
            pass

    # Return updated cart
    # reuse get_cart logic
    return await get_cart(session_id=session_id, db=db)


@router.put("/cart/items/{item_id}")
async def update_cart_item(
    item_id: int,
    cantidad: int = Query(..., gt=0),
    session_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Update quantity of cart item
    
    Requirements (HU_HOME_PRODUCTS):
    - Validate new cantidad doesn't exceed stock
    - Publishes cart.item.actualizar queue message
    """
    # TODO: Implement update cart item logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.delete("/cart/items/{item_id}")
async def remove_from_cart(
    item_id: int,
    session_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Remove item from cart
    
    Requirements (HU_HOME_PRODUCTS):
    - Delete CartItem record
    - Publishes cart.item.eliminar queue message
    """
    # TODO: Implement remove from cart logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.delete("/cart")
async def clear_cart(
    session_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Clear entire cart
    
    Requirements:
    - Delete all CartItems for cart
    - Publishes cart.vaciar queue message
    """
    # TODO: Implement clear cart logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
