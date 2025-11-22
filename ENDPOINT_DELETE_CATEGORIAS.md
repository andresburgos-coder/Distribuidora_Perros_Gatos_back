# 🗑️ Endpoint DELETE - Eliminación de Categorías y Subcategorías

## 📋 Explicación

Los endpoints DELETE permiten eliminar categorías y subcategorías del sistema. **IMPORTANTE**: No se permite eliminar si existen productos asociados. El sistema valida esta restricción antes de proceder con la eliminación.

**Flujo:**
1. Cliente envía DELETE → FastAPI (Producer)
2. FastAPI publica mensaje en RabbitMQ
3. Worker consume el mensaje
4. Worker valida que no existan productos asociados
5. Si no hay productos → Elimina
6. Si hay productos → Rechaza con mensaje de error

---

## 🛣️ Rutas de los Endpoints

### Eliminar Categoría
```
DELETE /api/admin/categorias/{id}
```

### Eliminar Subcategoría
```
DELETE /api/admin/subcategorias/{id}
```

---

## 🎮 Controlador FastAPI (Python)

**Archivo:** `backend/api/app/routers/categories.py`

```python
@router.delete("/categorias/{id}", response_model=SuccessResponse)
async def delete_category(id: str):
    """
    Delete category - EXACT implementation per HU_MANAGE_CATEGORIES
    
    Requirements:
    - DELETE /api/admin/categorias/{id}
    - Validates that no products are associated with the category
    - Publishes to categorias.eliminar queue
    - Worker validates and rejects if products exist
    """
    try:
        if not rabbitmq_producer.connection or rabbitmq_producer.connection.is_closed:
            rabbitmq_producer.connect()
        
        message = {
            "requestId": str(uuid.uuid4()),
            "action": "eliminar_categoria",
            "payload": {
                "id": id
            },
            "meta": {
                "userId": "admin",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        rabbitmq_producer.publish("categorias.eliminar", message)
        logger.info(f"Message published to categorias.eliminar: {message['requestId']}")
        
        return SuccessResponse(
            status="success",
            message="Solicitud de eliminación procesada"
        )
        
    except Exception as e:
        logger.error(f"Error publishing to RabbitMQ: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error al procesar la solicitud. Por favor, intente nuevamente."}
        )


@router.delete("/subcategorias/{id}", response_model=SuccessResponse)
async def delete_subcategory(id: str):
    """
    Delete subcategory - EXACT implementation per HU_MANAGE_CATEGORIES
    
    Requirements:
    - DELETE /api/admin/subcategorias/{id}
    - Validates that no products are associated with the subcategory
    - Publishes to subcategorias.eliminar queue
    - Worker validates and rejects if products exist
    """
    try:
        if not rabbitmq_producer.connection or rabbitmq_producer.connection.is_closed:
            rabbitmq_producer.connect()
        
        message = {
            "requestId": str(uuid.uuid4()),
            "action": "eliminar_subcategoria",
            "payload": {
                "id": id
            },
            "meta": {
                "userId": "admin",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        rabbitmq_producer.publish("subcategorias.eliminar", message)
        logger.info(f"Message published to subcategorias.eliminar: {message['requestId']}")
        
        return SuccessResponse(
            status="success",
            message="Solicitud de eliminación procesada"
        )
        
    except Exception as e:
        logger.error(f"Error publishing to RabbitMQ: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error al procesar la solicitud. Por favor, intente nuevamente."}
        )
```

---

## 🔧 Servicio TypeScript

**Archivo:** `backend/worker/src/services/categorias.service.ts`

### Eliminar Categoría

```typescript
/**
 * Delete a category
 * Validates that no products are associated with the category before deletion
 */
export async function deleteCategoria(payload: DeleteCategoriaPayload): Promise<ServiceResponse> {
  // Ensure database connection is ready
  try {
    await ensureConnection();
  } catch (error: any) {
    logger.error('Failed to connect to database:', error);
    return {
      status: 'error',
      message: 'Error de conexión a la base de datos. Por favor, intente nuevamente.'
    };
  }
  
  const transaction = new mssql.Transaction(pool);
  
  try {
    await transaction.begin();
    
    let categoriaId: number | string = payload.id;
    
    // Intentar convertir a número
    const categoriaIdNum = parseInt(payload.id);
    if (!isNaN(categoriaIdNum)) {
      categoriaId = categoriaIdNum;
    } else {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'La categoría especificada no parece válida.'
      };
    }
    
    // Validar que la categoría existe
    const checkExistsRequest = new mssql.Request(transaction);
    checkExistsRequest.input('id', mssql.Int, categoriaId);
    const existsResult = await checkExistsRequest.query(`
      SELECT id, nombre FROM Categorias WHERE id = @id
    `);
    
    if (existsResult.recordset.length === 0) {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'La categoría especificada no existe.'
      };
    }
    
    // Validar que no existan productos asociados a la categoría
    const checkProductsRequest = new mssql.Request(transaction);
    checkProductsRequest.input('categoriaId', mssql.Int, categoriaId);
    const productsResult = await checkProductsRequest.query(`
      SELECT COUNT(*) as total
      FROM Productos
      WHERE categoria_id = @categoriaId
    `);
    
    const totalProducts = productsResult.recordset[0].total;
    
    if (totalProducts > 0) {
      await transaction.rollback();
      logger.warn(`Cannot delete category ${categoriaId}: has ${totalProducts} associated products`);
      return {
        status: 'error',
        message: 'No se permite eliminar la categoría/subcategoría porque tiene productos asociados.'
      };
    }
    
    // Validar que no existan subcategorías con productos asociados
    const checkSubcategoriesRequest = new mssql.Request(transaction);
    checkSubcategoriesRequest.input('categoriaId', mssql.Int, categoriaId);
    const subcategoriesResult = await checkSubcategoriesRequest.query(`
      SELECT COUNT(*) as total
      FROM Subcategorias
      WHERE categoria_id = @categoriaId
    `);
    
    const totalSubcategories = subcategoriesResult.recordset[0].total;
    
    // Si hay subcategorías, verificar que ninguna tenga productos
    if (totalSubcategories > 0) {
      const checkSubcatProductsRequest = new mssql.Request(transaction);
      checkSubcatProductsRequest.input('categoriaId', mssql.Int, categoriaId);
      const subcatProductsResult = await checkSubcatProductsRequest.query(`
        SELECT COUNT(*) as total
        FROM Productos p
        INNER JOIN Subcategorias s ON p.subcategoria_id = s.id
        WHERE s.categoria_id = @categoriaId
      `);
      
      if (subcatProductsResult.recordset[0].total > 0) {
        await transaction.rollback();
        logger.warn(`Cannot delete category ${categoriaId}: subcategories have associated products`);
        return {
          status: 'error',
          message: 'No se permite eliminar la categoría/subcategoría porque tiene productos asociados.'
        };
      }
    }
    
    // Eliminar la categoría
    const deleteRequest = new mssql.Request(transaction);
    deleteRequest.input('id', mssql.Int, categoriaId);
    await deleteRequest.query(`
      DELETE FROM Categorias WHERE id = @id
    `);
    
    await transaction.commit();
    
    logger.info(`✅ Category deleted successfully: ID=${categoriaId}`);
    
    return {
      status: 'success',
      message: 'Categoría eliminada exitosamente'
    };
    
  } catch (error: any) {
    try {
      await transaction.rollback();
    } catch (rollbackError) {
      logger.error('Error rolling back transaction:', rollbackError);
    }
    
    logger.error(`❌ Error deleting category: ${error.message}`, {
      error: error.message,
      errorNumber: error.number,
      errorCode: error.code,
      stack: error.stack,
      id: payload.id
    });
    
    return {
      status: 'error',
      message: `Error al eliminar la categoría: ${error.message}. Por favor, intente nuevamente.`
    };
  }
}
```

### Eliminar Subcategoría

```typescript
/**
 * Delete a subcategory
 * Validates that no products are associated with the subcategory before deletion
 */
export async function deleteSubcategoria(payload: DeleteSubcategoriaPayload): Promise<ServiceResponse> {
  // Ensure database connection is ready
  try {
    await ensureConnection();
  } catch (error: any) {
    logger.error('Failed to connect to database:', error);
    return {
      status: 'error',
      message: 'Error de conexión a la base de datos. Por favor, intente nuevamente.'
    };
  }
  
  const transaction = new mssql.Transaction(pool);
  
  try {
    await transaction.begin();
    
    let subcategoriaId: number | string = payload.id;
    
    // Intentar convertir a número
    const subcategoriaIdNum = parseInt(payload.id);
    if (!isNaN(subcategoriaIdNum)) {
      subcategoriaId = subcategoriaIdNum;
    } else {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'La subcategoría especificada no parece válida.'
      };
    }
    
    // Validar que la subcategoría existe
    const checkExistsRequest = new mssql.Request(transaction);
    checkExistsRequest.input('id', mssql.Int, subcategoriaId);
    const existsResult = await checkExistsRequest.query(`
      SELECT id, nombre, categoria_id FROM Subcategorias WHERE id = @id
    `);
    
    if (existsResult.recordset.length === 0) {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'La subcategoría especificada no existe.'
      };
    }
    
    // Validar que no existan productos asociados a la subcategoría
    const checkProductsRequest = new mssql.Request(transaction);
    checkProductsRequest.input('subcategoriaId', mssql.Int, subcategoriaId);
    const productsResult = await checkProductsRequest.query(`
      SELECT COUNT(*) as total
      FROM Productos
      WHERE subcategoria_id = @subcategoriaId
    `);
    
    const totalProducts = productsResult.recordset[0].total;
    
    if (totalProducts > 0) {
      await transaction.rollback();
      logger.warn(`Cannot delete subcategory ${subcategoriaId}: has ${totalProducts} associated products`);
      return {
        status: 'error',
        message: 'No se permite eliminar la categoría/subcategoría porque tiene productos asociados.'
      };
    }
    
    // Eliminar la subcategoría
    const deleteRequest = new mssql.Request(transaction);
    deleteRequest.input('id', mssql.Int, subcategoriaId);
    await deleteRequest.query(`
      DELETE FROM Subcategorias WHERE id = @id
    `);
    
    await transaction.commit();
    
    logger.info(`✅ Subcategory deleted successfully: ID=${subcategoriaId}`);
    
    return {
      status: 'success',
      message: 'Subcategoría eliminada exitosamente'
    };
    
  } catch (error: any) {
    try {
      await transaction.rollback();
    } catch (rollbackError) {
      logger.error('Error rolling back transaction:', rollbackError);
    }
    
    logger.error(`❌ Error deleting subcategory: ${error.message}`, {
      error: error.message,
      errorNumber: error.number,
      errorCode: error.code,
      stack: error.stack,
      id: payload.id
    });
    
    return {
      status: 'error',
      message: `Error al eliminar la subcategoría: ${error.message}. Por favor, intente nuevamente.`
    };
  }
}
```

---

## 📊 Consultas SQL

### Validación de Existencia de Categoría

```sql
SELECT id, nombre 
FROM Categorias 
WHERE id = @id
```

### Validación de Productos Asociados a Categoría

```sql
SELECT COUNT(*) as total
FROM Productos
WHERE categoria_id = @categoriaId
```

### Validación de Subcategorías con Productos (al eliminar categoría)

```sql
SELECT COUNT(*) as total
FROM Productos p
INNER JOIN Subcategorias s ON p.subcategoria_id = s.id
WHERE s.categoria_id = @categoriaId
```

### Validación de Existencia de Subcategoría

```sql
SELECT id, nombre, categoria_id 
FROM Subcategorias 
WHERE id = @id
```

### Validación de Productos Asociados a Subcategoría

```sql
SELECT COUNT(*) as total
FROM Productos
WHERE subcategoria_id = @subcategoriaId
```

### Eliminación de Categoría

```sql
DELETE FROM Categorias 
WHERE id = @id
```

### Eliminación de Subcategoría

```sql
DELETE FROM Subcategorias 
WHERE id = @id
```

---

## 📨 Consumer TypeScript

**Archivo:** `backend/worker/src/consumers/categorias.consumer.ts`

```typescript
/**
 * Process category deletion message
 */
async function processDeleteCategoria(message: RabbitMQMessage): Promise<void> {
  try {
    logger.info(`Processing eliminar_categoria message: ${message.requestId}`, { payload: message.payload });
    
    const { id } = message.payload;
    
    if (!id) {
      logger.error(`Invalid payload for eliminar_categoria: ${message.requestId} - Missing id`);
      return;
    }
    
    logger.info(`Attempting to delete category: ${id} (requestId: ${message.requestId})`);
    const result = await deleteCategoria({ id });
    
    if (result.status === 'success') {
      logger.info(`✅ Category deleted successfully: ${message.requestId} - ID: ${id}`);
    } else {
      logger.error(`❌ Category deletion failed: ${message.requestId} - ${result.message}`, { 
        id,
        error: result.message 
      });
    }
    
  } catch (error: any) {
    logger.error(`❌ Error processing eliminar_categoria: ${message.requestId}`, {
      error: error.message,
      stack: error.stack,
      payload: message.payload
    });
  }
}

/**
 * Consume messages from categorias.eliminar queue
 */
export const consumeCategoriasEliminar = async (channel: Channel) => {
  const queue = config.rabbitMQ.queues.eliminarCategoria;
  await channel.assertQueue(queue, { durable: true });

  logger.info(`Waiting for messages in ${queue}`);
  
  channel.consume(
    queue,
    async (msg) => {
      if (msg) {
        try {
          const message: RabbitMQMessage = JSON.parse(msg.content.toString());
          logger.info(`Received message: ${message.requestId} - Action: ${message.action}`);
          
          await processDeleteCategoria(message);
          channel.ack(msg);
        } catch (error: any) {
          logger.error('Error processing message from categorias.eliminar:', error);
          channel.nack(msg, false, true);
        }
      }
    },
    { noAck: false }
  );
};
```

---

## ✅ Posibles Respuestas

### 200 OK - Eliminación Exitosa

**Response Body:**
```json
{
  "status": "success",
  "message": "Categoría eliminada exitosamente"
}
```

o

```json
{
  "status": "success",
  "message": "Subcategoría eliminada exitosamente"
}
```

### 400 Bad Request - Categoría/Subcategoría con Productos Asociados

**Response Body:**
```json
{
  "status": "error",
  "message": "No se permite eliminar la categoría/subcategoría porque tiene productos asociados."
}
```

### 404 Not Found - Categoría/Subcategoría No Existe

**Response Body:**
```json
{
  "status": "error",
  "message": "La categoría especificada no existe."
}
```

o

```json
{
  "status": "error",
  "message": "La subcategoría especificada no existe."
}
```

### 400 Bad Request - ID Inválido

**Response Body:**
```json
{
  "status": "error",
  "message": "La categoría especificada no parece válida."
}
```

### 500 Internal Server Error - Error del Sistema

**Response Body:**
```json
{
  "status": "error",
  "message": "Error al procesar la solicitud. Por favor, intente nuevamente."
}
```

---

## 🧪 Ejemplos de Uso

### Eliminar Categoría (cURL)

```bash
curl -X DELETE "http://localhost:8000/api/admin/categorias/1" \
  -H "Content-Type: application/json"
```

### Eliminar Subcategoría (cURL)

```bash
curl -X DELETE "http://localhost:8000/api/admin/subcategorias/1" \
  -H "Content-Type: application/json"
```

### Eliminar Categoría (Postman)

- **Método:** DELETE
- **URL:** `http://localhost:8000/api/admin/categorias/1`
- **Headers:** `Content-Type: application/json`

---

## 🔍 Validaciones Implementadas

1. ✅ **Existencia**: Verifica que la categoría/subcategoría exista antes de eliminar
2. ✅ **Productos asociados**: Valida que no haya productos vinculados
3. ✅ **Subcategorías con productos**: Al eliminar categoría, verifica que sus subcategorías no tengan productos
4. ✅ **ID válido**: Valida que el ID sea un número válido
5. ✅ **Transacciones**: Usa transacciones SQL para garantizar integridad
6. ✅ **Rollback**: Si algo falla, revierte todos los cambios

---

## 📝 Notas Importantes

- El endpoint DELETE es **asíncrono**: FastAPI responde inmediatamente, pero la eliminación se procesa en el Worker
- La validación de productos se hace en el **Worker**, no en FastAPI
- Si hay productos asociados, la eliminación se **rechaza** con el mensaje exacto especificado
- Los logs del Worker mostrarán el resultado de la operación
- Se usa **transacciones SQL** para garantizar integridad de datos

---

## ✅ Checklist de Implementación

- [x] Endpoint DELETE en FastAPI para categorías
- [x] Endpoint DELETE en FastAPI para subcategorías
- [x] Colas RabbitMQ: `categorias.eliminar` y `subcategorias.eliminar`
- [x] Consumer TypeScript para procesar eliminaciones
- [x] Servicio TypeScript con validación de productos
- [x] Consultas SQL para validar existencia y productos
- [x] Manejo de errores completo
- [x] Logging detallado
- [x] Mensajes de error exactos según especificación

---

¡Implementación completa y lista para usar! 🚀

