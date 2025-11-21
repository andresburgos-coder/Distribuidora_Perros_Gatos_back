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
            logger.info(f"Message published to queue: {queue_name}")
        except Exception as e:
            logger.error(f"Failed to publish message to {queue_name}: {str(e)}")
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
