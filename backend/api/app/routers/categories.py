"""
Categories router: Create, Read, Update categories and subcategories
Handles HU_MANAGE_CATEGORIES - EXACT implementation per specifications
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app.schemas import (
    CategoriaCreateRequest,
    SubcategoriaCreateRequest,
    CategoriaUpdateRequest,
    SubcategoriaUpdateRequest,
    CategoriaResponse,
    SubcategoriaResponse,
    SuccessResponse,
    ErrorResponse
)
from app.database import get_db
from app.utils.rabbitmq import rabbitmq_producer
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["Categories"]
)


@router.post("/categorias", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_category(request: CategoriaCreateRequest):
    """
    Create new category - EXACT implementation per HU_MANAGE_CATEGORIES
    
    Requirements:
    - POST /api/admin/categorias
    - Body: { "nombre": "NombreCategoria" }
    - Validations: nombre obligatorio, min 2 chars, no espacios vacíos
    - Publishes to categorias.crear queue
    """
    # Validación inicial en Producer (FastAPI)
    nombre = request.nombre.strip() if request.nombre else ""
    
    # Validación: nombre obligatorio
    if not nombre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": "Por favor, completa todos los campos obligatorios."}
        )
    
    # Validación: min 2 caracteres
    if len(nombre) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": "El nombre de la categoría debe tener al menos 2 caracteres."}
        )
    
    # Publicar mensaje en cola RabbitMQ
    try:
        # Conectar a RabbitMQ si no está conectado
        if not rabbitmq_producer.connection or rabbitmq_producer.connection.is_closed:
            rabbitmq_producer.connect()
        
        # Crear mensaje según especificación
        message = {
            "requestId": str(uuid.uuid4()),
            "action": "crear_categoria",
            "payload": {
                "nombre": nombre
            },
            "meta": {
                "userId": "admin",  # TODO: obtener del token JWT
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        # Publicar en cola categorias.crear
        rabbitmq_producer.publish("categorias.crear", message)
        logger.info(f"Message published to categorias.crear: {message['requestId']}")
        
        # Retornar respuesta de éxito (el worker procesará y persistirá)
        return SuccessResponse(
            status="success",
            message="Categoría creada exitosamente"
        )
        
    except Exception as e:
        logger.error(f"Error publishing to RabbitMQ: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error al procesar la solicitud. Por favor, intente nuevamente."}
        )


@router.post("/subcategorias", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_subcategory(request: SubcategoriaCreateRequest):
    """
    Create new subcategory - EXACT implementation per HU_MANAGE_CATEGORIES
    
    Requirements:
    - POST /api/admin/subcategorias
    - Body: { "categoriaId": "<id>", "nombre": "NombreSubcategoria" }
    - Validations: categoriaId obligatorio y válido, nombre obligatorio y min 2 chars
    - Publishes to subcategorias.crear queue
    """
    # Validación inicial en Producer
    nombre = request.nombre.strip() if request.nombre else ""
    categoria_id = request.categoriaId.strip() if request.categoriaId else ""
    
    # Validación: campos obligatorios
    if not categoria_id or not nombre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": "Por favor, completa todos los campos obligatorios."}
        )
    
    # Validación: nombre min 2 caracteres
    if len(nombre) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": "El nombre debe tener al menos 2 caracteres."}
        )
    
    # Validación: categoriaId formato válido (puede ser int o GUID)
    try:
        # Intentar convertir a int (bigint)
        categoria_id_int = int(categoria_id)
    except ValueError:
        # Si no es int, validar formato GUID básico
        if not (len(categoria_id) == 36 and categoria_id.count('-') == 4):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": "La categoría especificada no parece válida."}
            )
    
    # Publicar mensaje en cola RabbitMQ
    try:
        if not rabbitmq_producer.connection or rabbitmq_producer.connection.is_closed:
            rabbitmq_producer.connect()
        
        message = {
            "requestId": str(uuid.uuid4()),
            "action": "crear_subcategoria",
            "payload": {
                "categoriaId": categoria_id,
                "nombre": nombre
            },
            "meta": {
                "userId": "admin",  # TODO: obtener del token JWT
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        rabbitmq_producer.publish("subcategorias.crear", message)
        logger.info(f"Message published to subcategorias.crear: {message['requestId']}")
        
        return SuccessResponse(
            status="success",
            message="Subcategoría creada exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing to RabbitMQ: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error al procesar la solicitud. Por favor, intente nuevamente."}
        )


@router.put("/categorias/{id}", response_model=SuccessResponse)
async def update_category(id: str, request: CategoriaUpdateRequest):
    """
    Update category name - EXACT implementation per HU_MANAGE_CATEGORIES
    
    Requirements:
    - PUT /api/admin/categorias/{id}
    - Body: { "nombre": "NuevoNombre" }
    - Publishes to categorias.actualizar queue
    """
    nombre = request.nombre.strip() if request.nombre else ""
    
    # Validación: nombre obligatorio
    if not nombre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": "Por favor, completa todos los campos obligatorios."}
        )
    
    # Validación: min 2 caracteres
    if len(nombre) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": "El nombre debe tener al menos 2 caracteres."}
        )
    
    try:
        if not rabbitmq_producer.connection or rabbitmq_producer.connection.is_closed:
            rabbitmq_producer.connect()
        
        message = {
            "requestId": str(uuid.uuid4()),
            "action": "actualizar_categoria",
            "payload": {
                "id": id,
                "nombre": nombre
            },
            "meta": {
                "userId": "admin",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        rabbitmq_producer.publish("categorias.actualizar", message)
        logger.info(f"Message published to categorias.actualizar: {message['requestId']}")
        
        return SuccessResponse(
            status="success",
            message="Actualización realizada correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error publishing to RabbitMQ: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error al procesar la solicitud. Por favor, intente nuevamente."}
        )


@router.put("/subcategorias/{id}", response_model=SuccessResponse)
async def update_subcategory(id: str, request: SubcategoriaUpdateRequest):
    """
    Update subcategory name - EXACT implementation per HU_MANAGE_CATEGORIES
    
    Requirements:
    - PUT /api/admin/subcategorias/{id}
    - Body: { "nombre": "NuevoNombre" }
    - Publishes to subcategorias.actualizar queue
    """
    nombre = request.nombre.strip() if request.nombre else ""
    
    # Validación: nombre obligatorio
    if not nombre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": "Por favor, completa todos los campos obligatorios."}
        )
    
    # Validación: min 2 caracteres
    if len(nombre) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": "El nombre debe tener al menos 2 caracteres."}
        )
    
    try:
        if not rabbitmq_producer.connection or rabbitmq_producer.connection.is_closed:
            rabbitmq_producer.connect()
        
        message = {
            "requestId": str(uuid.uuid4()),
            "action": "actualizar_subcategoria",
            "payload": {
                "id": id,
                "nombre": nombre
            },
            "meta": {
                "userId": "admin",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        rabbitmq_producer.publish("subcategorias.actualizar", message)
        logger.info(f"Message published to subcategorias.actualizar: {message['requestId']}")
        
        return SuccessResponse(
            status="success",
            message="Actualización realizada correctamente"
        )
        
    except Exception as e:
        logger.error(f"Error publishing to RabbitMQ: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error al procesar la solicitud. Por favor, intente nuevamente."}
        )


@router.get("/categorias", response_model=List[CategoriaResponse])
async def get_categories(db: Session = Depends(get_db)):
    """
    Get complete category structure with subcategories - EXACT implementation per HU_MANAGE_CATEGORIES
    
    Requirements:
    - GET /api/admin/categorias
    - Returns tree structure: categories with their subcategories
    - Producer can read directly from DB (synchronous read)
    """
    try:
        # Query directa a la base de datos (lectura síncrona)
        from sqlalchemy import text
        
        # Query para obtener todas las categorías con sus subcategorías
        query = text("""
            SELECT 
                c.id,
                c.nombre,
                c.created_at,
                c.updated_at,
                s.id as subcategoria_id,
                s.nombre as subcategoria_nombre,
                s.created_at as subcategoria_created_at,
                s.updated_at as subcategoria_updated_at
            FROM Categorias c
            LEFT JOIN Subcategorias s ON c.id = s.categoria_id
            ORDER BY c.id, s.id
        """)
        
        result = db.execute(query)
        rows = result.fetchall()
        
        # Agrupar por categoría
        categorias_dict = {}
        for row in rows:
            categoria_id = row.id
            if categoria_id not in categorias_dict:
                categorias_dict[categoria_id] = {
                    "id": categoria_id,
                    "nombre": row.nombre,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                    "subcategorias": []
                }
            
            # Agregar subcategoría si existe
            if row.subcategoria_id:
                categorias_dict[categoria_id]["subcategorias"].append({
                    "id": row.subcategoria_id,
                    "categoria_id": categoria_id,
                    "nombre": row.subcategoria_nombre,
                    "created_at": row.subcategoria_created_at,
                    "updated_at": row.subcategoria_updated_at
                })
        
        # Convertir a lista de CategoriaResponse
        categorias_list = []
        for cat_data in categorias_dict.values():
            subcategorias = [
                SubcategoriaResponse(**sub) for sub in cat_data["subcategorias"]
            ]
            categoria = CategoriaResponse(
                id=cat_data["id"],
                nombre=cat_data["nombre"],
                created_at=cat_data["created_at"],
                updated_at=cat_data["updated_at"],
                subcategorias=subcategorias
            )
            categorias_list.append(categoria)
        
        return categorias_list
        
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error al obtener las categorías."}
        )


@router.delete("/categorias/{id}", response_model=SuccessResponse)
async def delete_category(id: str, sync: bool = Query(True, description="Ejecutar eliminación de forma síncrona en la BD (True por defecto para pruebas)"), db: Session = Depends(get_db)):
    """
    Delete category - EXACT implementation per HU_MANAGE_CATEGORIES
    
    Requirements:
    - DELETE /api/admin/categorias/{id}
    - Validates that no products are associated with the category
    - Publishes to categorias.eliminar queue
    - Worker validates and rejects if products exist
    """
    # Modo síncrono: por defecto True para que Swagger elimine realmente la fila en la BD
    if sync:
        try:
            try:
                categoria_id = int(id)
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail={"status": "error", "message": "El id de categoría no es válido."})

            with db.begin():
                exists_q = text("SELECT id FROM Categorias WHERE id = :id")
                exists_res = db.execute(exists_q, {"id": categoria_id}).fetchall()
                if not exists_res:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                        detail={"status": "error", "message": "La categoría especificada no existe."})

                prod_q = text("SELECT COUNT(*) as total FROM Productos WHERE categoria_id = :id")
                prod_res = db.execute(prod_q, {"id": categoria_id}).fetchone()
                total_products = prod_res.total if prod_res is not None else 0
                if total_products > 0:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail={"status": "error", "message": "No se permite eliminar la categoría porque tiene productos asociados."})

                sub_q = text("SELECT COUNT(*) as total FROM Subcategorias WHERE categoria_id = :id")
                sub_res = db.execute(sub_q, {"id": categoria_id}).fetchone()
                total_subs = sub_res.total if sub_res is not None else 0
                if total_subs > 0:
                    subprod_q = text("SELECT COUNT(*) as total FROM Productos p INNER JOIN Subcategorias s ON p.subcategoria_id = s.id WHERE s.categoria_id = :id")
                    subprod_res = db.execute(subprod_q, {"id": categoria_id}).fetchone()
                    if subprod_res and subprod_res.total > 0:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                            detail={"status": "error", "message": "No se permite eliminar la categoría porque sus subcategorías tienen productos asociados."})

                del_q = text("DELETE FROM Categorias WHERE id = :id")
                res = db.execute(del_q, {"id": categoria_id})

            return SuccessResponse(status="success", message="Categoría eliminada correctamente (síncrono)")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error ejecutando eliminación síncrona de categoría: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail={"status": "error", "message": "Error al eliminar la categoría de forma síncrona."})

    # Modo asíncrono: encolar para procesamiento por el worker
    try:
        if not rabbitmq_producer.connection or rabbitmq_producer.connection.is_closed:
            rabbitmq_producer.connect()

        message = {
            "requestId": str(uuid.uuid4()),
            "action": "eliminar_categoria",
            "payload": {"id": id},
            "meta": {"userId": "admin", "timestamp": datetime.utcnow().isoformat() + "Z"}
        }

        rabbitmq_producer.publish("categorias.eliminar", message)
        logger.info(f"Message published to categorias.eliminar: {message['requestId']}")

        return SuccessResponse(status="success", message="Solicitud de eliminación encolada; se procesará en background")
    except Exception as e:
        logger.error(f"Error publishing to RabbitMQ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"status": "error", "message": "Error al procesar la solicitud. Por favor, intente nuevamente."})


@router.delete("/subcategorias/{id}", response_model=SuccessResponse)
async def delete_subcategory(id: str, sync: bool = Query(True, description="Ejecutar eliminación de forma síncrona en la BD (True por defecto para pruebas)"), db: Session = Depends(get_db)):
    """
    Delete subcategory - EXACT implementation per HU_MANAGE_CATEGORIES
    
    Requirements:
    - DELETE /api/admin/subcategorias/{id}
    - Validates that no products are associated with the subcategory
    - Publishes to subcategorias.eliminar queue
    - Worker validates and rejects if products exist
    """
    if sync:
        try:
            try:
                sub_id = int(id)
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail={"status": "error", "message": "El id de subcategoría no es válido."})

            with db.begin():
                exists_q = text("SELECT id FROM Subcategorias WHERE id = :id")
                exists_res = db.execute(exists_q, {"id": sub_id}).fetchall()
                if not exists_res:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                        detail={"status": "error", "message": "La subcategoría especificada no existe."})

                prod_q = text("SELECT COUNT(*) as total FROM Productos WHERE subcategoria_id = :id")
                prod_res = db.execute(prod_q, {"id": sub_id}).fetchone()
                total_products = prod_res.total if prod_res is not None else 0
                if total_products > 0:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail={"status": "error", "message": "No se permite eliminar la subcategoría porque tiene productos asociados."})

                del_q = text("DELETE FROM Subcategorias WHERE id = :id")
                res = db.execute(del_q, {"id": sub_id})

            return SuccessResponse(status="success", message="Subcategoría eliminada correctamente (síncrono)")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error ejecutando eliminación síncrona de subcategoría: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail={"status": "error", "message": "Error al eliminar la subcategoría de forma síncrona."})

    try:
        if not rabbitmq_producer.connection or rabbitmq_producer.connection.is_closed:
            rabbitmq_producer.connect()

        message = {
            "requestId": str(uuid.uuid4()),
            "action": "eliminar_subcategoria",
            "payload": {"id": id},
            "meta": {"userId": "admin", "timestamp": datetime.utcnow().isoformat() + "Z"}
        }

        rabbitmq_producer.publish("subcategorias.eliminar", message)
        logger.info(f"Message published to subcategorias.eliminar: {message['requestId']}")

        return SuccessResponse(status="success", message="Solicitud de eliminación encolada; se procesará en background")
    except Exception as e:
        logger.error(f"Error publishing to RabbitMQ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"status": "error", "message": "Error al procesar la solicitud. Por favor, intente nuevamente."})
