import nodemailer from 'nodemailer';
import { config } from '../config';
import logger from '../utils/logger';

interface EmailOptions {
  to: string;
  subject: string;
  html: string;
  text?: string;
}

const transporter = nodemailer.createTransport({
  host: config.smtp.host,
  port: config.smtp.port,
  secure: config.smtp.port === 465, // true para puerto 465, false para otros
  auth: {
    user: config.smtp.user,
    pass: config.smtp.pass,
  },
  tls: {
    // No fallar en certificados inválidos en desarrollo
    rejectUnauthorized: config.nodeEnv === 'production',
  },
});

// Verificar la conexión al inicio
transporter.verify((error) => {
  if (error) {
    logger.error('Error al conectar con el servidor SMTP:', error);
  } else {
    logger.info('Conexión con el servidor SMTP establecida correctamente');
  }
});

export const sendEmail = async (options: EmailOptions) => {
  const mailOptions = {
    from: config.smtp.from,  // Usamos el from de la configuración
    to: options.to,
    subject: options.subject,
    html: options.html,
    text: options.text || options.subject, // Versión de texto plano
  };

  try {
    const info = await transporter.sendMail(mailOptions);
    logger.info(`Correo enviado a ${options.to} con ID: ${info.messageId}`);
    return info;
  } catch (error) {
    logger.error('Error al enviar el correo:', {
      to: options.to,
      subject: options.subject,
      error: error instanceof Error ? error.message : 'Error desconocido',
    });
    throw error; // Relanzar para manejar reintentos
  }
};