import amqplib from 'amqplib';
import { config } from './config';
import { consumeEmailMessages } from './consumers/email.consumer';
import { consumeInventoryMessages } from './consumers/inventory.consumer';
import { consumeOrderMessages } from './consumers/order.consumer';
import { consumeUserRegistrationMessages } from './consumers/user.consumer';
import logger from './utils/logger';

const consumeMessages = async () => {
  try {
    const connection = await amqplib.connect(config.rabbitMQ.url);
    const channel = await connection.createChannel();

    consumeEmailMessages(channel);
    consumeOrderMessages(channel);
    consumeInventoryMessages(channel);
    consumeUserRegistrationMessages(channel);
    
  } catch (error) {
    logger.error('Error connecting to RabbitMQ:', error);
  }
};

consumeMessages();
