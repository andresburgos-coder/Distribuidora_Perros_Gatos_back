import amqplib from 'amqplib';
import { config } from './config';
import { consumeEmailMessages } from './consumers/email.consumer';
import { consumeInventoryMessages } from './consumers/inventory.consumer';
import { consumeOrderMessages } from './consumers/order.consumer';
import { consumeUserRegistrationMessages } from './consumers/user.consumer';
import {
  consumeCategoriasCrear,
  consumeCategoriasActualizar,
  consumeCategoriasEliminar,
  consumeSubcategoriasCrear,
  consumeSubcategoriasActualizar,
  consumeSubcategoriasEliminar
} from './consumers/categorias.consumer';
import logger from './utils/logger';

const consumeMessages = async () => {
  try {
    const connection = await amqplib.connect(config.rabbitMQ.url);
    const channel = await connection.createChannel();

    // Existing consumers
    consumeEmailMessages(channel);
    consumeOrderMessages(channel);
    consumeInventoryMessages(channel);
    consumeUserRegistrationMessages(channel);
    
    // HU_MANAGE_CATEGORIES consumers - EXACT as per specification
    consumeCategoriasCrear(channel);
    consumeCategoriasActualizar(channel);
    consumeCategoriasEliminar(channel);
    consumeSubcategoriasCrear(channel);
    consumeSubcategoriasActualizar(channel);
    consumeSubcategoriasEliminar(channel);
    
    logger.info('All consumers registered and waiting for messages');
    
  } catch (error) {
    logger.error('Error connecting to RabbitMQ:', error);
    process.exit(1);
  }
};

consumeMessages();
