/**
 * Categories Service - EXACT implementation per HU_MANAGE_CATEGORIES
 * Handles business logic for categories and subcategories operations
 */
import mssql from 'mssql';
import pool, { ensureConnection } from '../database';
import logger from '../utils/logger';

interface CreateCategoriaPayload {
  nombre: string;
}

interface UpdateCategoriaPayload {
  id: string;
  nombre: string;
}

interface CreateSubcategoriaPayload {
  categoriaId: string;
  nombre: string;
}

interface UpdateSubcategoriaPayload {
  id: string;
  nombre: string;
}

interface DeleteCategoriaPayload {
  id: string;
}

interface DeleteSubcategoriaPayload {
  id: string;
}

interface ServiceResponse {
  status: 'success' | 'error';
  message: string;
  data?: any;
}

/**
 * Create a new category
 * Validates uniqueness (case-insensitive) and inserts into database
 */
export async function createCategoria(payload: CreateCategoriaPayload): Promise<ServiceResponse> {
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
    
    const nombre = payload.nombre.trim();
    
    // Validación: nombre obligatorio
    if (!nombre) {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'Por favor, completa todos los campos obligatorios.'
      };
    }
    
    // Validación: min 2 caracteres
    if (nombre.length < 2) {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'El nombre debe tener al menos 2 caracteres.'
      };
    }
    
    // Validación: unicidad case-insensitive
    const checkRequest = new mssql.Request(transaction);
    checkRequest.input('nombre', mssql.VarChar, nombre);
    const checkQuery = `
      SELECT id FROM Categorias 
      WHERE LOWER(LTRIM(RTRIM(nombre))) = LOWER(LTRIM(RTRIM(@nombre)))
    `;
    const existing = await checkRequest.query(checkQuery);
    
    if (existing.recordset.length > 0) {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'Ya existe una categoría con ese nombre.'
      };
    }
    
    // Insertar categoría - Intentar primero con created_at/updated_at
    let insertQuery = `
      INSERT INTO Categorias (nombre, created_at, updated_at)
      OUTPUT INSERTED.id, INSERTED.nombre, INSERTED.created_at, INSERTED.updated_at
      VALUES (@nombre, GETUTCDATE(), GETUTCDATE())
    `;
    
    let result;
    try {
      const insertRequest = new mssql.Request(transaction);
      insertRequest.input('nombre', mssql.VarChar, nombre);
      result = await insertRequest.query(insertQuery);
    } catch (columnError: any) {
      // Si las columnas created_at/updated_at no existen, intentar con fecha_creacion/fecha_actualizacion
      if (columnError.number === 207 || columnError.message.includes('Invalid column name')) {
        logger.warn('Columns created_at/updated_at not found, trying fecha_creacion/fecha_actualizacion');
        insertQuery = `
          INSERT INTO Categorias (nombre, fecha_creacion, fecha_actualizacion)
          OUTPUT INSERTED.id, INSERTED.nombre, INSERTED.fecha_creacion, INSERTED.fecha_actualizacion
          VALUES (@nombre, GETUTCDATE(), GETUTCDATE())
        `;
        const insertRequest2 = new mssql.Request(transaction);
        insertRequest2.input('nombre', mssql.VarChar, nombre);
        result = await insertRequest2.query(insertQuery);
      } else {
        throw columnError;
      }
    }
    
    await transaction.commit();
    
    logger.info(`✅ Category created successfully: ID=${result.recordset[0].id}, nombre=${nombre}`);
    
    return {
      status: 'success',
      message: 'Categoría creada exitosamente',
      data: result.recordset[0]
    };
    
  } catch (error: any) {
    try {
      await transaction.rollback();
    } catch (rollbackError) {
      logger.error('Error rolling back transaction:', rollbackError);
    }
    
    // Manejar violación de índice único (condición de carrera)
    if (error.number === 2601 || error.number === 2627) {
      logger.warn(`Duplicate category name detected: ${payload.nombre}`);
      return {
        status: 'error',
        message: 'Ya existe una categoría con ese nombre.'
      };
    }
    
    logger.error(`❌ Error creating category: ${error.message}`, {
      error: error.message,
      errorNumber: error.number,
      errorCode: error.code,
      stack: error.stack,
      nombre: payload.nombre
    });
    return {
      status: 'error',
      message: `Error al crear la categoría: ${error.message}. Por favor, intente nuevamente.`
    };
  }
}

/**
 * Update an existing category
 * Validates uniqueness (case-insensitive) and updates in database
 */
export async function updateCategoria(payload: UpdateCategoriaPayload): Promise<ServiceResponse> {
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
    
    const nombre = payload.nombre.trim();
    let categoriaId: number | string = payload.id;
    
    // Intentar convertir a número
    const categoriaIdNum = parseInt(payload.id);
    if (!isNaN(categoriaIdNum)) {
      categoriaId = categoriaIdNum;
    }
    
    // Validación: nombre obligatorio
    if (!nombre) {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'Por favor, completa todos los campos obligatorios.'
      };
    }
    
    // Validación: min 2 caracteres
    if (nombre.length < 2) {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'El nombre debe tener al menos 2 caracteres.'
      };
    }
    
    // Validar que la categoría existe
    if (typeof categoriaId === 'number') {
      const checkExistsRequest = new mssql.Request(transaction);
      checkExistsRequest.input('id', mssql.Int, categoriaId);
      const existsResult = await checkExistsRequest.query(
        'SELECT id FROM Categorias WHERE id = @id'
      );
      
      if (existsResult.recordset.length === 0) {
        await transaction.rollback();
        return {
          status: 'error',
          message: 'La categoría especificada no existe.'
        };
      }
      
      // Validación: unicidad case-insensitive (excluyendo la categoría actual)
      const checkUniqueRequest = new mssql.Request(transaction);
      checkUniqueRequest.input('nombre', mssql.VarChar, nombre);
      checkUniqueRequest.input('id', mssql.Int, categoriaId);
      const uniqueResult = await checkUniqueRequest.query(`
        SELECT id FROM Categorias 
        WHERE LOWER(LTRIM(RTRIM(nombre))) = LOWER(LTRIM(RTRIM(@nombre)))
        AND id != @id
      `);
      
      if (uniqueResult.recordset.length > 0) {
        await transaction.rollback();
        return {
          status: 'error',
          message: 'Ya existe una categoría con ese nombre.'
        };
      }
      
      // Actualizar categoría
      const updateRequest = new mssql.Request(transaction);
      updateRequest.input('nombre', mssql.VarChar, nombre);
      updateRequest.input('id', mssql.Int, categoriaId);
      await updateRequest.query(`
        UPDATE Categorias 
        SET nombre = @nombre, updated_at = GETUTCDATE()
        WHERE id = @id
      `);
      
      await transaction.commit();
      
      logger.info(`Category updated successfully: ${categoriaId}`);
      
      return {
        status: 'success',
        message: 'Actualización realizada correctamente'
      };
    } else {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'La categoría especificada no parece válida.'
      };
    }
    
  } catch (error: any) {
    try {
      await transaction.rollback();
    } catch (rollbackError) {
      logger.error('Error rolling back transaction:', rollbackError);
    }
    
    if (error.number === 2601 || error.number === 2627) {
      return {
        status: 'error',
        message: 'Ya existe una categoría con ese nombre.'
      };
    }
    
    logger.error(`Error updating category: ${error.message}`, error);
    return {
      status: 'error',
      message: 'Error al actualizar la categoría. Por favor, intente nuevamente.'
    };
  }
}

/**
 * Create a new subcategory
 * Validates category existence and uniqueness within category (case-insensitive)
 */
export async function createSubcategoria(payload: CreateSubcategoriaPayload): Promise<ServiceResponse> {
  const transaction = new mssql.Transaction(pool);
  
  try {
    await transaction.begin();
    
    const nombre = payload.nombre.trim();
    let categoriaId: number | string = payload.categoriaId;
    
    // Intentar convertir a número
    const categoriaIdNum = parseInt(payload.categoriaId);
    if (!isNaN(categoriaIdNum)) {
      categoriaId = categoriaIdNum;
    }
    
    // Validación: campos obligatorios
    if (!categoriaId || !nombre) {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'Por favor, completa todos los campos obligatorios.'
      };
    }
    
    // Validación: nombre min 2 caracteres
    if (nombre.length < 2) {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'El nombre debe tener al menos 2 caracteres.'
      };
    }
    
    // Validación: categoría existe
    if (typeof categoriaId === 'number') {
      const checkCategoriaRequest = new mssql.Request(transaction);
      checkCategoriaRequest.input('categoriaId', mssql.Int, categoriaId);
      const categoriaExists = await checkCategoriaRequest.query(
        'SELECT id FROM Categorias WHERE id = @categoriaId'
      );
      
      if (categoriaExists.recordset.length === 0) {
        await transaction.rollback();
        return {
          status: 'error',
          message: 'La categoría seleccionada no existe.'
        };
      }
      
      // Validación: unicidad case-insensitive dentro de la misma categoría
      const checkUniqueRequest = new mssql.Request(transaction);
      checkUniqueRequest.input('nombre', mssql.VarChar, nombre);
      checkUniqueRequest.input('categoriaId', mssql.Int, categoriaId);
      const uniqueResult = await checkUniqueRequest.query(`
        SELECT id FROM Subcategorias 
        WHERE categoria_id = @categoriaId
        AND LOWER(LTRIM(RTRIM(nombre))) = LOWER(LTRIM(RTRIM(@nombre)))
      `);
      
      if (uniqueResult.recordset.length > 0) {
        await transaction.rollback();
        return {
          status: 'error',
          message: 'Ya existe una subcategoría con ese nombre en la categoría seleccionada.'
        };
      }
      
      // Insertar subcategoría
      const insertRequest = new mssql.Request(transaction);
      insertRequest.input('nombre', mssql.VarChar, nombre);
      insertRequest.input('categoriaId', mssql.Int, categoriaId);
      const result = await insertRequest.query(`
        INSERT INTO Subcategorias (categoria_id, nombre, created_at, updated_at)
        OUTPUT INSERTED.id, INSERTED.categoria_id, INSERTED.nombre, INSERTED.created_at, INSERTED.updated_at
        VALUES (@categoriaId, @nombre, GETUTCDATE(), GETUTCDATE())
      `);
      
      await transaction.commit();
      
      logger.info(`Subcategory created successfully: ${result.recordset[0].id}`);
      
      return {
        status: 'success',
        message: 'Subcategoría creada exitosamente',
        data: result.recordset[0]
      };
    } else {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'La categoría especificada no parece válida.'
      };
    }
    
  } catch (error: any) {
    try {
      await transaction.rollback();
    } catch (rollbackError) {
      logger.error('Error rolling back transaction:', rollbackError);
    }
    
    // Manejar violación de índice único
    if (error.number === 2601 || error.number === 2627) {
      return {
        status: 'error',
        message: 'Ya existe una subcategoría con ese nombre en la categoría seleccionada.'
      };
    }
    
    logger.error(`Error creating subcategory: ${error.message}`, error);
    return {
      status: 'error',
      message: 'Error al crear la subcategoría. Por favor, intente nuevamente.'
    };
  }
}

/**
 * Update an existing subcategory
 * Validates uniqueness within category (case-insensitive) and updates in database
 */
export async function updateSubcategoria(payload: UpdateSubcategoriaPayload): Promise<ServiceResponse> {
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
    
    const nombre = payload.nombre.trim();
    let subcategoriaId: number | string = payload.id;
    
    // Intentar convertir a número
    const subcategoriaIdNum = parseInt(payload.id);
    if (!isNaN(subcategoriaIdNum)) {
      subcategoriaId = subcategoriaIdNum;
    }
    
    // Validación: nombre obligatorio
    if (!nombre) {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'Por favor, completa todos los campos obligatorios.'
      };
    }
    
    // Validación: min 2 caracteres
    if (nombre.length < 2) {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'El nombre debe tener al menos 2 caracteres.'
      };
    }
    
    // Validar que la subcategoría existe y obtener categoria_id
    if (typeof subcategoriaId === 'number') {
      const checkExistsRequest = new mssql.Request(transaction);
      checkExistsRequest.input('id', mssql.Int, subcategoriaId);
      const existsResult = await checkExistsRequest.query(`
        SELECT categoria_id FROM Subcategorias WHERE id = @id
      `);
      
      if (existsResult.recordset.length === 0) {
        await transaction.rollback();
        return {
          status: 'error',
          message: 'La subcategoría especificada no existe.'
        };
      }
      
      const categoriaId = existsResult.recordset[0].categoria_id;
      
      // Validación: unicidad case-insensitive dentro de la misma categoría
      const checkUniqueRequest = new mssql.Request(transaction);
      checkUniqueRequest.input('nombre', mssql.VarChar, nombre);
      checkUniqueRequest.input('categoriaId', mssql.Int, categoriaId);
      checkUniqueRequest.input('id', mssql.Int, subcategoriaId);
      const uniqueResult = await checkUniqueRequest.query(`
        SELECT id FROM Subcategorias 
        WHERE categoria_id = @categoriaId
        AND LOWER(LTRIM(RTRIM(nombre))) = LOWER(LTRIM(RTRIM(@nombre)))
        AND id != @id
      `);
      
      if (uniqueResult.recordset.length > 0) {
        await transaction.rollback();
        return {
          status: 'error',
          message: 'Ya existe una subcategoría con ese nombre en la categoría seleccionada.'
        };
      }
      
      // Actualizar subcategoría
      const updateRequest = new mssql.Request(transaction);
      updateRequest.input('nombre', mssql.VarChar, nombre);
      updateRequest.input('id', mssql.Int, subcategoriaId);
      await updateRequest.query(`
        UPDATE Subcategorias 
        SET nombre = @nombre, updated_at = GETUTCDATE()
        WHERE id = @id
      `);
      
      await transaction.commit();
      
      logger.info(`Subcategory updated successfully: ${subcategoriaId}`);
      
      return {
        status: 'success',
        message: 'Actualización realizada correctamente'
      };
    } else {
      await transaction.rollback();
      return {
        status: 'error',
        message: 'La subcategoría especificada no parece válida.'
      };
    }
    
  } catch (error: any) {
    try {
      await transaction.rollback();
    } catch (rollbackError) {
      logger.error('Error rolling back transaction:', rollbackError);
    }
    
    if (error.number === 2601 || error.number === 2627) {
      return {
        status: 'error',
        message: 'Ya existe una subcategoría con ese nombre en la categoría seleccionada.'
      };
    }
    
    logger.error(`Error updating subcategory: ${error.message}`, error);
    return {
      status: 'error',
      message: 'Error al actualizar la subcategoría. Por favor, intente nuevamente.'
    };
  }
}

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
    
    // Validar que no existan subcategorías asociadas (opcional, según requerimiento)
    // Si se permite eliminar categoría con subcategorías, comentar este bloque
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
    
    // Eliminar la categoría (las subcategorías se eliminarán en cascada si hay FK CASCADE)
    const deleteRequest = new mssql.Request(transaction);
    deleteRequest.input('id', mssql.Int, categoriaId);
    const deleteResult = await deleteRequest.query(`
      DELETE FROM Categorias WHERE id = @id
    `);

    if (!deleteResult.rowsAffected || deleteResult.rowsAffected[0] === 0) {
      await transaction.rollback();
      logger.warn(`No rows deleted for category ${categoriaId}`);
      return {
        status: 'error',
        message: 'No se pudo eliminar la categoría (no encontrada o no afectada).'
      };
    }

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
    const deleteResult = await deleteRequest.query(`
      DELETE FROM Subcategorias WHERE id = @id
    `);

    if (!deleteResult.rowsAffected || deleteResult.rowsAffected[0] === 0) {
      await transaction.rollback();
      logger.warn(`No rows deleted for subcategory ${subcategoriaId}`);
      return {
        status: 'error',
        message: 'No se pudo eliminar la subcategoría (no encontrada o no afectada).'
      };
    }

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
