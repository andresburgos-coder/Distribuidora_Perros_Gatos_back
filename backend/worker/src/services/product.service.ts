import fs from 'fs';
import path from 'path';
import mssql from 'mssql';
import pool from '../database';
import logger from '../utils/logger';

const UPLOAD_DIR = process.env.UPLOAD_DIR || path.join(__dirname, '../../uploads');

export const processProductCreate = async (payload: any) => {
  const { nombre, descripcion, precio, peso_gramos, categoria_id, subcategoria_id, cantidad_disponible, imagen_filename, imagen_b64, sku } = payload;

  const trx = pool;
  try {
    // Ensure pool is connected before making requests (avoid race at startup)
    if (!trx.connected) {
      await trx.connect();
      logger.info('DB pool connected from product.service');
    }
    // Check name uniqueness (case-insensitive)
    const nameCheck = await trx.request()
      .input('nombre', mssql.NVarChar(100), nombre)
      .query('SELECT TOP 1 id FROM Productos WHERE LOWER(nombre) = LOWER(@nombre)');

    if (nameCheck.recordset && nameCheck.recordset.length > 0) {
      throw new Error('Ya existe un producto con ese nombre.');
    }

    // Validate category
    const catRes = await trx.request()
      .input('categoria_id', mssql.Int, categoria_id)
      .query('SELECT id FROM Categorias WHERE id = @categoria_id AND activo = 1');
    if (!catRes.recordset || catRes.recordset.length === 0) {
      throw new Error('Categoría no encontrada.');
    }

    // Validate subcategory belongs to category
    const subcatRes = await trx.request()
      .input('subcategoria_id', mssql.Int, subcategoria_id)
      .input('categoria_id', mssql.Int, categoria_id)
      .query('SELECT id FROM Subcategorias WHERE id = @subcategoria_id AND categoria_id = @categoria_id AND activo = 1');
    if (!subcatRes.recordset || subcatRes.recordset.length === 0) {
      throw new Error('Subcategoría no encontrada o no pertenece a la categoría indicada.');
    }

    // Ensure SKU exists (some migrations add a unique SKU constraint)
    const finalSku = (sku && String(sku).trim()) || `SKU-${Date.now()}-${Math.floor(Math.random() * 10000)}`;

    // Insert product (include sku to avoid UNIQUE constraint on nullable sku)
    const insertRes = await trx.request()
      .input('nombre', mssql.NVarChar(100), nombre)
      .input('descripcion', mssql.NVarChar(500), descripcion)
      .input('precio', mssql.Decimal(10, 2), precio)
      .input('peso_gramos', mssql.Int, peso_gramos)
      .input('cantidad_disponible', mssql.Int, cantidad_disponible || 0)
      .input('categoria_id', mssql.Int, categoria_id)
      .input('subcategoria_id', mssql.Int, subcategoria_id)
      .input('sku', mssql.NVarChar(50), finalSku)
      .query(`INSERT INTO Productos (nombre, descripcion, precio, peso_gramos, cantidad_disponible, categoria_id, subcategoria_id, sku)
             OUTPUT INSERTED.id
             VALUES (@nombre, @descripcion, @precio, @peso_gramos, @cantidad_disponible, @categoria_id, @subcategoria_id, @sku)`);

    const newId = insertRes.recordset && insertRes.recordset[0] && insertRes.recordset[0].id;
    if (!newId) throw new Error('No se pudo crear el producto.');

    // If image provided, decode and store
    if (imagen_b64 && imagen_filename) {
      const productDir = path.join(UPLOAD_DIR, 'productos', String(newId));
      fs.mkdirSync(productDir, { recursive: true });
      const safeName = `${Date.now()}_${imagen_filename.replace(/[^a-zA-Z0-9_.-]/g, '_')}`;
      const filePath = path.join(productDir, safeName);
      const buffer = Buffer.from(imagen_b64, 'base64');
      fs.writeFileSync(filePath, buffer as any);

      // Save image record
      await trx.request()
        .input('producto_id', mssql.Int, newId)
        .input('ruta_imagen', mssql.NVarChar(mssql.MAX), filePath)
        .query('INSERT INTO ProductoImagenes (producto_id, ruta_imagen, es_principal, orden) VALUES (@producto_id, @ruta_imagen, 1, 0)');
    }

    logger.info(`Producto creado con id=${newId}`);
    return { success: true, id: newId };
  } catch (err: any) {
    logger.error('Error processing product create:', err.message || err);
    throw err;
  }
};
