import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

export const config = {
  nodeEnv: process.env.NODE_ENV || 'development',  // Añadido nodeEnv
  rabbitMQ: {
    url: process.env.RABBITMQ_URL || 'amqp://localhost',
    queues: {
      emailNotifications: 'email.notifications',
      sendEmail: 'send_email_queue',  // Mantenido para compatibilidad
      processOrder: 'process_order_queue',
      updateInventory: 'update_inventory_queue',
      userRegistration: 'user_registration_queue',
      productosCrear: process.env.RABBITMQ_QUEUE_PRODUCTOS_CREAR || 'productos.crear',
    },
  },
  smtp: {
    host: process.env.SMTP_HOST || 'smtp.gmail.com',
    port: parseInt(process.env.SMTP_PORT || '587', 10),
    user: process.env.SMTP_USER || '',
    pass: process.env.SMTP_PASS || '',
    from: process.env.SMTP_FROM || 'no-reply@distribuidora.com'  // Añadido from
  },
};