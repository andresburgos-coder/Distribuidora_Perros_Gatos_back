import { Channel } from 'amqplib';
import { config } from '../config';
import { updateInventory } from '../services/inventory.service';
import logger from '../utils/logger';

export const consumeInventoryMessages = async (channel: Channel) => {
  const queue = config.rabbitMQ.queues.updateInventory;
  await channel.assertQueue(queue, { durable: true });

  logger.info(`Waiting for messages in ${queue}`);
  channel.consume(
    queue,
    async (msg) => {
      if (msg) {
        try {
          const item = JSON.parse(msg.content.toString());
          await updateInventory(item);
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
