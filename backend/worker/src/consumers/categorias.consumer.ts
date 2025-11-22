/**
 * Categories Consumer - EXACT implementation per HU_MANAGE_CATEGORIES
 * Consumes messages from categorias.crear and categorias.actualizar queues
 */
import { Channel } from 'amqplib';
import { config } from '../config';
import {
  createCategoria,
  updateCategoria,
  deleteCategoria,
  createSubcategoria,
  updateSubcategoria,
  deleteSubcategoria
} from '../services/categorias.service';
import logger from '../utils/logger';

interface RabbitMQMessage {
  requestId: string;
  action: string;
  payload: any;
  meta?: {
    userId?: string;
    timestamp?: string;
  };
}

/**
 * Process category creation message
 */
async function processCreateCategoria(message: RabbitMQMessage): Promise<void> {
  try {
    logger.info(`Processing crear_categoria message: ${message.requestId}`, { payload: message.payload });
    
    const { nombre } = message.payload;
    
    if (!nombre) {
      logger.error(`Invalid payload for crear_categoria: ${message.requestId} - Missing nombre`);
      return;
    }
    
    logger.info(`Attempting to create category: ${nombre} (requestId: ${message.requestId})`);
    const result = await createCategoria({ nombre });
    
    if (result.status === 'success') {
      logger.info(`✅ Category created successfully: ${message.requestId} - ${nombre} - ID: ${result.data?.id || 'N/A'}`);
    } else {
      logger.error(`❌ Category creation failed: ${message.requestId} - ${result.message}`, { 
        nombre,
        error: result.message 
      });
    }
    
  } catch (error: any) {
    logger.error(`❌ Error processing crear_categoria: ${message.requestId}`, {
      error: error.message,
      stack: error.stack,
      payload: message.payload
    });
  }
}

/**
 * Process category update message
 */
async function processUpdateCategoria(message: RabbitMQMessage): Promise<void> {
  try {
    const { id, nombre } = message.payload;
    
    if (!id || !nombre) {
      logger.error(`Invalid payload for actualizar_categoria: ${message.requestId}`);
      return;
    }
    
    const result = await updateCategoria({ id, nombre });
    
    if (result.status === 'success') {
      logger.info(`Category updated successfully: ${message.requestId} - ${id}`);
    } else {
      logger.warn(`Category update failed: ${message.requestId} - ${result.message}`);
    }
    
  } catch (error: any) {
    logger.error(`Error processing actualizar_categoria: ${message.requestId}`, error);
  }
}

/**
 * Process subcategory creation message
 */
async function processCreateSubcategoria(message: RabbitMQMessage): Promise<void> {
  try {
    const { categoriaId, nombre } = message.payload;
    
    if (!categoriaId || !nombre) {
      logger.error(`Invalid payload for crear_subcategoria: ${message.requestId}`);
      return;
    }
    
    const result = await createSubcategoria({ categoriaId, nombre });
    
    if (result.status === 'success') {
      logger.info(`Subcategory created successfully: ${message.requestId} - ${nombre}`);
    } else {
      logger.warn(`Subcategory creation failed: ${message.requestId} - ${result.message}`);
    }
    
  } catch (error: any) {
    logger.error(`Error processing crear_subcategoria: ${message.requestId}`, error);
  }
}

/**
 * Process subcategory update message
 */
async function processUpdateSubcategoria(message: RabbitMQMessage): Promise<void> {
  try {
    const { id, nombre } = message.payload;
    
    if (!id || !nombre) {
      logger.error(`Invalid payload for actualizar_subcategoria: ${message.requestId}`);
      return;
    }
    
    const result = await updateSubcategoria({ id, nombre });
    
    if (result.status === 'success') {
      logger.info(`Subcategory updated successfully: ${message.requestId} - ${id}`);
    } else {
      logger.warn(`Subcategory update failed: ${message.requestId} - ${result.message}`);
    }
    
  } catch (error: any) {
    logger.error(`Error processing actualizar_subcategoria: ${message.requestId}`, error);
  }
}

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
 * Process subcategory deletion message
 */
async function processDeleteSubcategoria(message: RabbitMQMessage): Promise<void> {
  try {
    logger.info(`Processing eliminar_subcategoria message: ${message.requestId}`, { payload: message.payload });
    
    const { id } = message.payload;
    
    if (!id) {
      logger.error(`Invalid payload for eliminar_subcategoria: ${message.requestId} - Missing id`);
      return;
    }
    
    logger.info(`Attempting to delete subcategory: ${id} (requestId: ${message.requestId})`);
    const result = await deleteSubcategoria({ id });
    
    if (result.status === 'success') {
      logger.info(`✅ Subcategory deleted successfully: ${message.requestId} - ID: ${id}`);
    } else {
      logger.error(`❌ Subcategory deletion failed: ${message.requestId} - ${result.message}`, { 
        id,
        error: result.message 
      });
    }
    
  } catch (error: any) {
    logger.error(`❌ Error processing eliminar_subcategoria: ${message.requestId}`, {
      error: error.message,
      stack: error.stack,
      payload: message.payload
    });
  }
}

/**
 * Consume messages from categorias.crear queue
 */
export const consumeCategoriasCrear = async (channel: Channel) => {
  const queue = config.rabbitMQ.queues.crearCategoria;
  await channel.assertQueue(queue, { durable: true });

  logger.info(`Waiting for messages in ${queue}`);
  
  channel.consume(
    queue,
    async (msg) => {
      if (msg) {
        try {
          const message: RabbitMQMessage = JSON.parse(msg.content.toString());
          logger.info(`Received message: ${message.requestId} - Action: ${message.action}`);
          
          await processCreateCategoria(message);
          channel.ack(msg);
        } catch (error: any) {
          logger.error('Error processing message from categorias.crear:', error);
          // Requeue message on error (will retry)
          channel.nack(msg, false, true);
        }
      }
    },
    { noAck: false }
  );
};

/**
 * Consume messages from categorias.actualizar queue
 */
export const consumeCategoriasActualizar = async (channel: Channel) => {
  const queue = config.rabbitMQ.queues.actualizarCategoria;
  await channel.assertQueue(queue, { durable: true });

  logger.info(`Waiting for messages in ${queue}`);
  
  channel.consume(
    queue,
    async (msg) => {
      if (msg) {
        try {
          const message: RabbitMQMessage = JSON.parse(msg.content.toString());
          logger.info(`Received message: ${message.requestId} - Action: ${message.action}`);
          
          await processUpdateCategoria(message);
          channel.ack(msg);
        } catch (error: any) {
          logger.error('Error processing message from categorias.actualizar:', error);
          channel.nack(msg, false, true);
        }
      }
    },
    { noAck: false }
  );
};

/**
 * Consume messages from subcategorias.crear queue
 */
export const consumeSubcategoriasCrear = async (channel: Channel) => {
  const queue = config.rabbitMQ.queues.crearSubcategoria;
  await channel.assertQueue(queue, { durable: true });

  logger.info(`Waiting for messages in ${queue}`);
  
  channel.consume(
    queue,
    async (msg) => {
      if (msg) {
        try {
          const message: RabbitMQMessage = JSON.parse(msg.content.toString());
          logger.info(`Received message: ${message.requestId} - Action: ${message.action}`);
          
          await processCreateSubcategoria(message);
          channel.ack(msg);
        } catch (error: any) {
          logger.error('Error processing message from subcategorias.crear:', error);
          channel.nack(msg, false, true);
        }
      }
    },
    { noAck: false }
  );
};

/**
 * Consume messages from subcategorias.actualizar queue
 */
export const consumeSubcategoriasActualizar = async (channel: Channel) => {
  const queue = config.rabbitMQ.queues.actualizarSubcategoria;
  await channel.assertQueue(queue, { durable: true });

  logger.info(`Waiting for messages in ${queue}`);
  
  channel.consume(
    queue,
    async (msg) => {
      if (msg) {
        try {
          const message: RabbitMQMessage = JSON.parse(msg.content.toString());
          logger.info(`Received message: ${message.requestId} - Action: ${message.action}`);
          
          await processUpdateSubcategoria(message);
          channel.ack(msg);
        } catch (error: any) {
          logger.error('Error processing message from subcategorias.actualizar:', error);
          channel.nack(msg, false, true);
        }
      }
    },
    { noAck: false }
  );
};

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

/**
 * Consume messages from subcategorias.eliminar queue
 */
export const consumeSubcategoriasEliminar = async (channel: Channel) => {
  const queue = config.rabbitMQ.queues.eliminarSubcategoria;
  await channel.assertQueue(queue, { durable: true });

  logger.info(`Waiting for messages in ${queue}`);
  
  channel.consume(
    queue,
    async (msg) => {
      if (msg) {
        try {
          const message: RabbitMQMessage = JSON.parse(msg.content.toString());
          logger.info(`Received message: ${message.requestId} - Action: ${message.action}`);
          
          await processDeleteSubcategoria(message);
          channel.ack(msg);
        } catch (error: any) {
          logger.error('Error processing message from subcategorias.eliminar:', error);
          channel.nack(msg, false, true);
        }
      }
    },
    { noAck: false }
  );
};

