import dotenv from 'dotenv';

dotenv.config();

export const config = {
  rabbitMQ: {
    url: process.env.RABBITMQ_URL || 'amqp://localhost',
    queues: {
      sendEmail: 'send_email_queue',
      processOrder: 'process_order_queue',
      updateInventory: 'update_inventory_queue',
      userRegistration: 'user_registration_queue',
    },
  },
  smtp: {
    host: process.env.SMTP_HOST,
    port: parseInt(process.env.SMTP_PORT || '587', 10),
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
  },
};
