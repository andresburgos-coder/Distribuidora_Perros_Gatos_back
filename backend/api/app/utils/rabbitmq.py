"""
RabbitMQ producer for publishing messages to message queues
"""
import pika
import json
import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class RabbitMQProducer:
    """Publisher for RabbitMQ messages"""
    
    def __init__(self):
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
    
    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
            parameters = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                virtual_host=settings.RABBITMQ_VHOST,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise
    
    def declare_queue(self, queue_name: str, durable: bool = True):
        """Declare a queue"""
        try:
            self.channel.queue_declare(queue=queue_name, durable=durable)
        except Exception as e:
            logger.error(f"Failed to declare queue {queue_name}: {str(e)}")
            raise
    
    def publish(self, queue_name: str, message: Dict[str, Any], durable: bool = True):
        """Publish message to queue"""
        try:
            # Ensure connection is established
            if not self.connection or self.connection.is_closed:
                self.connect()
            
            self.declare_queue(queue_name, durable)
            
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2 if durable else 1,  # 2 = persistent
                    content_type='application/json'
                )
            )
            logger.info(f"Message published to queue: {queue_name}, requestId: {message.get('requestId', 'N/A')}")
        except Exception as e:
            logger.error(f"Failed to publish message to {queue_name}: {str(e)}")
            # Try to reconnect once
            try:
                self.connect()
                self.declare_queue(queue_name, durable)
                self.channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2 if durable else 1,
                        content_type='application/json'
                    )
                )
                logger.info(f"Message published to queue after reconnect: {queue_name}")
            except Exception as retry_error:
                logger.error(f"Failed to publish after reconnect: {str(retry_error)}")
            raise
    
    def close(self):
        """Close connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {str(e)}")


# Global RabbitMQ producer instance
rabbitmq_producer = RabbitMQProducer()


async def get_rabbitmq_producer() -> RabbitMQProducer:
    """Dependency for RabbitMQ producer"""
    return rabbitmq_producer


async def send_email_notification(
    to_email: str,
    subject: str,
    template_name: str,
    context: dict,
    request_id: str = None
) -> bool:
    """
    Publica una notificación de correo electrónico en la cola de RabbitMQ.
    
    Args:
        to_email: Correo electrónico del destinatario
        subject: Asunto del correo
        template_name: Nombre de la plantilla a utilizar
        context: Diccionario con las variables para la plantilla
        request_id: ID opcional para seguimiento
        
    Returns:
        bool: True si el mensaje se publicó correctamente, False en caso contrario
    """
    from datetime import datetime
    import uuid
    
    message = {
        "requestId": request_id or str(uuid.uuid4()),
        "to": to_email,
        "subject": subject,
        "template": template_name,
        "context": context,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        rabbitmq_producer.publish("email.notifications", message)
        logger.info(f"Email notification queued for {to_email}, template: {template_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to queue email notification: {str(e)}")
        return False