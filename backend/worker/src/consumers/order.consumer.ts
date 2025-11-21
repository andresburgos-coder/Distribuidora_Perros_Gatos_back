import { Channel } from 'amqplib';
import { config } from '../config';
import { processOrder } from '../services/order.service';
import logger from '../utils/logger';

export const consumeOrderMessages = async (channel: Channel) => {
  const queue = config.rabbitMQ.queues.processOrder;
  await channel.assertQueue(queue, { durable: true });

  logger.info(`Waiting for messages in ${queue}`);
  channel.consume(
    queue,
    async (msg) => {
      if (msg) {
        try {
          const order = JSON.parse(msg.content.toString());
          await processOrder(order);
          channel.ack(msg);
        } catch (error) {
          logger.error('Error processing message:', error);
          channel.nack(msg, false, false); // Requeue the message
        }
      }
    },
    { noAck: false }
  );
};
