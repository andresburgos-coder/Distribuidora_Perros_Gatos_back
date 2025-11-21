import { Channel } from 'amqplib';
import { config } from '../config';
import { processUserRegistration } from '../services/user.service';
import logger from '../utils/logger';

export const consumeUserRegistrationMessages = async (channel: Channel) => {
  const queue = config.rabbitMQ.queues.userRegistration;
  await channel.assertQueue(queue, { durable: true });

  logger.info(`Waiting for messages in ${queue}`);
  channel.consume(
    queue,
    async (msg) => {
      if (msg) {
        try {
          const user = JSON.parse(msg.content.toString());
          await processUserRegistration(user);
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
