import os
import pika
import json

RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))


class RabbitMQAdmin:
    def __init__(self):
        self.channel = self.create_rabbit_connection()
        
    @staticmethod
    def create_rabbit_connection():
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
        )
        channel = connection.channel()
        return channel

    def publish_message(self, queue_name, task, priority=None):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            )
        )
        channel = connection.channel()
        if priority is None:
            channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(task), properties=pika.BasicProperties(delivery_mode=2))
        else:
            channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(task), properties=pika.BasicProperties(priority=priority, delivery_mode=2))
        connection.close()
