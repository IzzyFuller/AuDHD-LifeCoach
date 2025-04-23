"""
Messaging adapters package.

This package contains adapters for different messaging systems
like RabbitMQ, Apache Kafka, etc.
"""
from audhd_lifecoach.adapters.messaging.rabbitmq_message_consumer import RabbitMQMessageConsumer

__all__ = ["RabbitMQMessageConsumer"]