import { Channel, ConsumeMessage } from 'amqplib';
import { sendEmail } from '../services/email.service';
import logger from '../utils/logger';
import path from 'path';
import fs from 'fs';
import handlebars from 'handlebars';

// Cargar plantilla
const loadTemplate = (templateName: string): string => {
  try {
    const templatePath = path.join(__dirname, `../../templates/emails/${templateName}.hbs`);
    return fs.readFileSync(templatePath, 'utf8');
  } catch (error) {
    logger.error(`Error cargando la plantilla ${templateName}:`, error);
    throw new Error(`Plantilla ${templateName} no encontrada`);
  }
};

// Registrar ayudantes de Handlebars
handlebars.registerHelper('formatDate', (dateString: string) => {
  return new Date(dateString).toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
});

export const consumeEmailMessages = async (channel: Channel) => {
  const queue = 'email.notifications';
  await channel.assertQueue(queue, { durable: true });

  logger.info(`[Email Consumer] Esperando mensajes en ${queue}`);
  
  channel.consume(
    queue,
    async (msg: ConsumeMessage | null) => {
      if (!msg) return;

      try {
        const message = JSON.parse(msg.content.toString());
        logger.info(`[Email Consumer] Procesando mensaje: ${message.requestId}`);
        
        // Cargar la plantilla
        const templateSource = loadTemplate(message.template);
        const template = handlebars.compile(templateSource);
        const html = template(message.context);

        // Enviar el correo
        await sendEmail({
          to: message.to,
          subject: message.subject,
          html,
        });

        // Confirmar el procesamiento
        channel.ack(msg);
        logger.info(`[Email Consumer] Correo enviado exitosamente: ${message.requestId}`);
      } catch (error) {
        logger.error('[Email Consumer] Error procesando mensaje:', error);
        
        // Reintentar más tarde
        if (msg.fields.redelivered) {
          // Si ya se reintentó, descartar el mensaje
          channel.ack(msg);
          logger.warn('[Email Consumer] Mensaje descartado después de reintento');
        } else {
          // Reintentar
          channel.nack(msg, false, true);
        }
      }
    },
    { noAck: false }
  );
};