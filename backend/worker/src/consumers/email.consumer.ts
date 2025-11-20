import { Channel } from 'amqplib';
import { config } from '../config';
import { sendEmail } from '../services/email.service';
import logger from '../utils/logger';

export const consumeEmailMessages = async (channel: Channel) => {
  const queue = config.rabbitMQ.queues.sendEmail;
  await channel.assertQueue(queue, { durable: true });

  logger.info(`Waiting for messages in ${queue}`);
  channel.consume(
    queue,
    async (msg) => {
      if (msg) {
        try {
          const { to, subject, html } = JSON.parse(msg.content.toString());
          await sendEmail(to, subject, html);
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
