"""
Carousel router: Manage homepage carousel images
Handles HU_MANAGE_CAROUSEL
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas import CarruselImagenCreate, CarruselImagenResponse, CarruselImagenUpdate
from app.database import get_db
from app import models
from app.config import settings
from app.utils.rabbitmq import rabbitmq_producer
import logging
import os
import uuid
from datetime import datetime

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
    images = db.query(models.CarruselImagen).filter(models.CarruselImagen.activo == True).order_by(models.CarruselImagen.orden.asc()).limit(5).all()
    return images


@router.post("", response_model=CarruselImagenResponse)
async def add_carousel_image(
    orden: int = Form(..., ge=1, le=5),
    link_url: Optional[str] = Form(None),
    created_by: Optional[str] = Form(None),
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
    # Basic presence validation
    if not file:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "Por favor, completa todos los campos obligatorios."})

    # Validate extension
    filename = file.filename or ""
    _, ext = os.path.splitext(filename.lower())
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "Formato o tamaño de imagen no válido."})

    # Read bytes and validate size
    contents = await file.read()
    if not contents or len(contents) == 0 or len(contents) > settings.MAX_FILE_SIZE:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "Formato o tamaño de imagen no válido."})

    # Check active images limit
    active_count = db.query(models.CarruselImagen).filter(models.CarruselImagen.activo == True).count()
    if active_count >= 5:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "El carrusel ya tiene el número máximo de imágenes."})

    # Prepare upload directory
    upload_dir = os.path.abspath(os.path.join(settings.UPLOAD_DIR, "carrusel"))
    os.makedirs(upload_dir, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}{ext}"
    saved_path = os.path.join(upload_dir, unique_name)
    # Save file to disk
    try:
        with open(saved_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        logger.error(f"Failed saving uploaded file: {str(e)}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Formato o tamaño de imagen no válido."})

    # Normalize created_by
    created_by = created_by or "unknown"

    # Insert into DB and handle orden uniqueness (shift existing >= orden)
    try:
        # Shift existing orders >= orden up by 1
        db.query(models.CarruselImagen).filter(models.CarruselImagen.activo == True, models.CarruselImagen.orden >= orden).update({models.CarruselImagen.orden: models.CarruselImagen.orden + 1})
        new_img = models.CarruselImagen(
            imagen_url=saved_path,
            orden=orden,
            link_url=link_url,
            created_by=created_by,
            activo=True
        )
        db.add(new_img)
        db.commit()
        db.refresh(new_img)
    except Exception as e:
        logger.error(f"DB error creating carousel image: {str(e)}")
        db.rollback()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Formato o tamaño de imagen no válido."})

    # Publish message to RabbitMQ (non-blocking best-effort)
    try:
        rabbitmq_producer.connect()
        request_id = uuid.uuid4().hex
        message = {
            "requestId": request_id,
            "action": "crear_imagen",
            "payload": {
                "imagenPath": saved_path,
                "linkUrl": link_url,
                "created_by": created_by
            },
            "meta": {"timestamp": datetime.utcnow().isoformat()}
        }
        rabbitmq_producer.publish("carrusel.imagen.crear", message)
    except Exception as e:
        logger.warning(f"Could not publish RabbitMQ message: {str(e)}")
    finally:
        try:
            rabbitmq_producer.close()
        except Exception:
            pass

    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"status": "success", "message": "Imagen agregada al carrusel"})


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
    img = db.query(models.CarruselImagen).filter(models.CarruselImagen.id == imagen_id, models.CarruselImagen.activo == True).first()
    if not img:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "error", "message": "Imagen no encontrada."})

    # Update orden if provided
    if request.orden is not None:
        new_orden = int(request.orden)
        if new_orden < 1 or new_orden > 5:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "El orden debe ser un número entero positivo y único."})
        if new_orden != img.orden:
            # Shift others accordingly
            if new_orden > img.orden:
                # decrement those between img.orden+1 .. new_orden
                db.query(models.CarruselImagen).filter(models.CarruselImagen.activo == True, models.CarruselImagen.orden > img.orden, models.CarruselImagen.orden <= new_orden).update({models.CarruselImagen.orden: models.CarruselImagen.orden - 1})
            else:
                # increment those between new_orden .. img.orden-1
                db.query(models.CarruselImagen).filter(models.CarruselImagen.activo == True, models.CarruselImagen.orden >= new_orden, models.CarruselImagen.orden < img.orden).update({models.CarruselImagen.orden: models.CarruselImagen.orden + 1})
            img.orden = new_orden

    if request.link_url is not None:
        img.link_url = request.link_url

    try:
        db.add(img)
        db.commit()
        db.refresh(img)
    except Exception as e:
        logger.error(f"DB error updating carousel image: {str(e)}")
        db.rollback()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Formato o tamaño de imagen no válido."})

    # Publish update message
    try:
        rabbitmq_producer.connect()
        message = {
            "requestId": uuid.uuid4().hex,
            "action": "actualizar_imagen",
            "payload": {"id": imagen_id, "orden": img.orden, "linkUrl": img.link_url},
            "meta": {"timestamp": datetime.utcnow().isoformat()}
        }
        rabbitmq_producer.publish("carrusel.imagen.actualizar", message)
    except Exception as e:
        logger.warning(f"Could not publish RabbitMQ update message: {str(e)}")
    finally:
        try:
            rabbitmq_producer.close()
        except Exception:
            pass

    return img


@router.delete("/{imagen_id}")
async def delete_carousel_image(imagen_id: int, db: Session = Depends(get_db)):
    """
    Delete carousel image
    
    Requirements (HU_MANAGE_CAROUSEL):
    - Delete image file and database record
    - Reorder remaining images to maintain 1-5 sequence
    - Publishes carrusel.imagen.eliminar queue message
    """
    img = db.query(models.CarruselImagen).filter(models.CarruselImagen.id == imagen_id, models.CarruselImagen.activo == True).first()
    if not img:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "error", "message": "Imagen no encontrada."})

    # Mark as inactive
    try:
        img.activo = False
        db.add(img)
        db.commit()
    except Exception as e:
        logger.error(f"DB error deleting carousel image: {str(e)}")
        db.rollback()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Imagen no encontrada."})

    # Reindex remaining active images to be consecutive starting from 1
    try:
        active_images = db.query(models.CarruselImagen).filter(models.CarruselImagen.activo == True).order_by(models.CarruselImagen.orden.asc()).all()
        for idx, item in enumerate(active_images, start=1):
            if item.orden != idx:
                item.orden = idx
                db.add(item)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to reindex after delete: {str(e)}")
        db.rollback()

    # Publish delete message
    try:
        rabbitmq_producer.connect()
        message = {
            "requestId": uuid.uuid4().hex,
            "action": "eliminar_imagen",
            "payload": {"id": imagen_id},
            "meta": {"timestamp": datetime.utcnow().isoformat()}
        }
        rabbitmq_producer.publish("carrusel.imagen.eliminar", message)
    except Exception as e:
        logger.warning(f"Could not publish RabbitMQ delete message: {str(e)}")
    finally:
        try:
            rabbitmq_producer.close()
        except Exception:
            pass

    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "success", "message": "Imagen eliminada exitosamente"})


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
    img = db.query(models.CarruselImagen).filter(models.CarruselImagen.id == imagen_id, models.CarruselImagen.activo == True).first()
    if not img:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "error", "message": "Imagen no encontrada."})

    new_orden = int(nueva_orden)
    if new_orden < 1 or new_orden > 5:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "El orden debe ser un número entero positivo y único."})

    try:
        if new_orden > img.orden:
            db.query(models.CarruselImagen).filter(models.CarruselImagen.activo == True, models.CarruselImagen.orden > img.orden, models.CarruselImagen.orden <= new_orden).update({models.CarruselImagen.orden: models.CarruselImagen.orden - 1})
        elif new_orden < img.orden:
            db.query(models.CarruselImagen).filter(models.CarruselImagen.activo == True, models.CarruselImagen.orden >= new_orden, models.CarruselImagen.orden < img.orden).update({models.CarruselImagen.orden: models.CarruselImagen.orden + 1})
        img.orden = new_orden
        db.add(img)
        db.commit()
        db.refresh(img)
    except Exception as e:
        logger.error(f"DB error reordering carousel image: {str(e)}")
        db.rollback()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "El orden debe ser un número entero positivo y único."})

    # Publish reorder message with current ordering snapshot
    try:
        rabbitmq_producer.connect()
        active_images = db.query(models.CarruselImagen).filter(models.CarruselImagen.activo == True).order_by(models.CarruselImagen.orden.asc()).all()
        ordenes = [{"id": item.id, "orden": item.orden} for item in active_images]
        message = {
            "requestId": uuid.uuid4().hex,
            "action": "reordenar",
            "payload": {"ordenes": ordenes},
            "meta": {"timestamp": datetime.utcnow().isoformat()}
        }
        rabbitmq_producer.publish("carrusel.imagen.reordenar", message)
    except Exception as e:
        logger.warning(f"Could not publish RabbitMQ reorder message: {str(e)}")
    finally:
        try:
            rabbitmq_producer.close()
        except Exception:
            pass

    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "success", "message": "Orden actualizado exitosamente"})


@router.put("/reordenar")
async def bulk_reorder(payload: dict = Body(...), db: Session = Depends(get_db)):
    """Bulk reorder endpoint: accepts payload {"ordenes": [{"id":..., "orden":...}, ...]}"""
    ordenes = payload.get("ordenes")
    if not ordenes or not isinstance(ordenes, list):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "Por favor, completa todos los campos obligatorios."})

    # Validate uniqueness and range
    seen = set()
    for o in ordenes:
        if not isinstance(o, dict) or "id" not in o or "orden" not in o:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "Por favor, completa todos los campos obligatorios."})
        try:
            num = int(o["orden"])
        except Exception:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "El orden debe ser un número entero positivo y único."})
        if num < 1 or num > 5 or num in seen:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "El orden debe ser un número entero positivo y único."})
        seen.add(num)

    # Validate all ids exist
    ids = [o["id"] for o in ordenes]
    db_items = db.query(models.CarruselImagen).filter(models.CarruselImagen.id.in_(ids), models.CarruselImagen.activo == True).all()
    if len(db_items) != len(ids):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "error", "message": "Imagen no encontrada."})

    # Apply updates in transaction
    try:
        for o in ordenes:
            item = next(filter(lambda x: x.id == o["id"], db_items), None)
            if item:
                item.orden = int(o["orden"])
                db.add(item)
        db.commit()
    except Exception as e:
        logger.error(f"DB error bulk reordering: {str(e)}")
        db.rollback()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "El orden debe ser un número entero positivo y único."})

    # Publish message
    try:
        rabbitmq_producer.connect()
        message = {
            "requestId": uuid.uuid4().hex,
            "action": "reordenar",
            "payload": {"ordenes": ordenes},
            "meta": {"timestamp": datetime.utcnow().isoformat()}
        }
        rabbitmq_producer.publish("carrusel.imagen.reordenar", message)
    except Exception as e:
        logger.warning(f"Could not publish RabbitMQ bulk reorder message: {str(e)}")
    finally:
        try:
            rabbitmq_producer.close()
        except Exception:
            pass

    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "success", "message": "Orden actualizado exitosamente"})
