
import 'reflect-metadata';
import { connect } from 'amqplib';
import { consumeEmailMessages } from './consumers/email.consumer';
import { config } from './config';
import { consumeInventoryMessages } from './consumers/inventory.consumer';
import { consumeOrderMessages } from './consumers/order.consumer';
import { consumeUserRegistrationMessages } from './consumers/user.consumer';
import { consumeProductCreateMessages } from './consumers/product.consumer';
import logger from './utils/logger';

async function startWorker() {
  try {
    logger.info('Starting email worker...');
    
    // Conectar a RabbitMQ
    const connection = await connect(config.rabbitMQ.url);
    const channel = await connection.createChannel();
    
    // Configurar el prefetch para evitar sobrecargar el worker
    await channel.prefetch(1);
    
    // Iniciar consumidores
    await consumeEmailMessages(channel);
    
    logger.info('Worker started successfully');
    
    // Manejar cierre limpio
    const shutdown = async () => {
      logger.info('Shutting down worker...');
      try {
        await channel.close();
        await connection.close();
        logger.info('Worker stopped successfully');
        process.exit(0);
      } catch (error) {
        logger.error('Error during shutdown:', error);
        process.exit(1);
      }
    };

    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
    consumeEmailMessages(channel);
    consumeOrderMessages(channel);
    consumeInventoryMessages(channel);
    consumeUserRegistrationMessages(channel);
    consumeProductCreateMessages(channel);
    
  } catch (error) {
    logger.error('Failed to start worker:', error);
    process.exit(1);
  }
}

startWorker();