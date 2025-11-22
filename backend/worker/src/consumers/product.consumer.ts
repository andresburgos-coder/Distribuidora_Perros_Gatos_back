import { Channel } from 'amqplib';
import { config } from '../config';
import logger from '../utils/logger';
import { processProductCreate } from '../services/product.service';

export const consumeProductCreateMessages = async (channel: Channel) => {
  const queue = config.rabbitMQ.queues.productosCrear || 'productos.crear';
  await channel.assertQueue(queue, { durable: true });

  logger.info(`Waiting for messages in ${queue}`);
  channel.consume(
    queue,
    async (msg) => {
      if (msg) {
        try {
          const payload = JSON.parse(msg.content.toString());
          await processProductCreate(payload);
          channel.ack(msg);
        } catch (error) {
          logger.error('Error processing product.create message:', error);
          // Do not requeue (could be poisoned); nack without requeue
          channel.nack(msg, false, false);
        }
      }
    },
    { noAck: false }
  );
};
