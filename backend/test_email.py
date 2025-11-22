# test_email.py
import json
import pika
import uuid
from datetime import datetime

# Configuración de RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declarar la cola
channel.queue_declare(queue='email.notifications', durable=True)

# Crear mensaje de prueba
message = {
    "requestId": str(uuid.uuid4()),
    "to": "burgosgusman@gmail.com",  # Reemplaza con un correo real para probar
    "subject": "Prueba de correo",
    "template": "verification",  # Nombre del archivo de plantilla sin extensión
    "context": {
        "name": "Usuario de Prueba",
        "code": "123456",
        "year": datetime.now().year
    },
    "timestamp": datetime.utcnow().isoformat()
}

# Publicar mensaje
channel.basic_publish(
    exchange='',
    routing_key='email.notifications',
    body=json.dumps(message),
    properties=pika.BasicProperties(
        delivery_mode=2,  # Hacer el mensaje persistente
        content_type='application/json'
    )
)

print(f" [x] Mensaje enviado: {message['requestId']}")
connection.close()