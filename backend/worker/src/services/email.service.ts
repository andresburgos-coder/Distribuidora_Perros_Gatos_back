import nodemailer from 'nodemailer';
import { config } from '../config';
import logger from '../utils/logger';

const transporter = nodemailer.createTransport({
  host: config.smtp.host,
  port: config.smtp.port,
  secure: false, // true for 465, false for other ports
  auth: {
    user: config.smtp.user,
    pass: config.smtp.pass,
  },
});

export const sendEmail = async (to: string, subject: string, html: string) => {
  try {
    await transporter.sendMail({
      from: '"Distribuidora Perros y Gatos" <no-reply@example.com>',
      to,
      subject,
      html,
    });
    logger.info('Email sent successfully');
  } catch (error) {
    logger.error('Error sending email:', error);
  }
};
