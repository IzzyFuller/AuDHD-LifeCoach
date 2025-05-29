"""
RabbitMQ Message Consumer Adapter.

This adapter implements the MessageConsumerInterface for RabbitMQ.
"""

import json
import logging
from typing import Any, Callable, Dict, Optional

import pika

from audhd_lifecoach.adapters.messaging.rabbitmq_settings import RabbitMQSettings
from audhd_lifecoach.application.interfaces.message_consumer_interface import (
    MessageConsumerInterface,
)

logger = logging.getLogger(__name__)


class RabbitMQMessageConsumer(MessageConsumerInterface):
    """
    RabbitMQ implementation of the MessageConsumerInterface.

    This class provides methods to connect to RabbitMQ, consume messages
    from a queue, and handle acknowledgments/rejections.
    """

    def __init__(self, settings: RabbitMQSettings):
        """
        Initialize the RabbitMQ message consumer with settings.

        Args:
            settings: RabbitMQ configuration settings
        """
        self.settings = settings
        self._connection = None
        self._channel = None
        self._consumer_tag = None
        self._callback = None

    def connect(self) -> bool:
        """
        Connect to the RabbitMQ server using configured settings.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create connection parameters from settings
            credentials = pika.PlainCredentials(
                self.settings.username, self.settings.password
            )
            parameters = pika.ConnectionParameters(
                host=self.settings.host,
                port=self.settings.port,
                virtual_host=self.settings.host,
                credentials=credentials,
                connection_attempts=self.settings.connection_attempts,
                retry_delay=self.settings.retry_delay,
                socket_timeout=self.settings.connection_timeout,
                heartbeat=self.settings.heartbeat,
            )

            # Connect to RabbitMQ
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()

            logger.info(
                f"Connected to RabbitMQ at {self.settings.host}:{self.settings.port}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Disconnect from the RabbitMQ server.

        Returns:
            bool: True if disconnection successful, False otherwise
        """
        # Cancel consumer if it exists
        if self._channel and self._consumer_tag:
            self._channel.basic_cancel(self._consumer_tag)
            self._consumer_tag = None

        # Close channel and connection
        if self._channel:
            self._channel.close()
            self._channel = None

        if self._connection:
            self._connection.close()
            self._connection = None

        logger.info("Disconnected from RabbitMQ")
        return True

    def consume_messages(self, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """
        Start consuming messages from the configured queue.

        Args:
            callback: Function to call when a message is received
        """
        if not self._channel:
            raise RuntimeError("Not connected to RabbitMQ")

        # Store the callback function
        self._callback = callback

        # Start consuming from the configured queue (no queue declaration)
        self._consumer_tag = self._channel.basic_consume(
            queue=self.settings.consume_queue_name,
            on_message_callback=self._on_message,
            auto_ack=False,
        )

        logger.info(
            f"Started consuming messages from queue '{self.settings.consume_queue_name}'"
        )

        # Start the IO loop to process messages
        self._channel.start_consuming()

    def _on_message(self, channel, method, properties, body) -> None:
        """
        Callback function for RabbitMQ message delivery.

        This function is called by pika when a message is received.
        It parses the message body and calls the user-provided callback.

        Args:
            channel: The pika channel
            method: The pika method frame
            properties: The pika properties
            body: The message body
        """
        try:
            # Parse the message body
            message_data = json.loads(body)

            # Store the delivery tag for acknowledgment
            message_data["message_id"] = method.delivery_tag

            # Call the user-provided callback
            if self._callback:
                self._callback(message_data)

        except json.JSONDecodeError as e:
            logger.exception(f"Failed to parse message body: {e}")
            # Reject invalid JSON messages
            channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            # Reject and requeue on other errors
            channel.basic_reject(delivery_tag=method.delivery_tag, requeue=True)

    def acknowledge_message(self, message_id: str) -> bool:
        """
        Acknowledge a message.

        Args:
            message_id: ID of the message to acknowledge

        Returns:
            bool: True if successful, False otherwise
        """
        if not self._channel:
            raise RuntimeError("Not connected to RabbitMQ")

        # In RabbitMQ, the message_id is the delivery tag
        delivery_tag = int(message_id)
        self._channel.basic_ack(delivery_tag=delivery_tag)
        return True

    def reject_message(self, message_id: str, requeue: bool = False) -> bool:
        """
        Reject a message.

        Args:
            message_id: ID of the message to reject
            requeue: Whether to requeue the message

        Returns:
            bool: True if successful, False otherwise
        """
        if not self._channel:
            raise RuntimeError("Not connected to RabbitMQ")

        # In RabbitMQ, the message_id is the delivery tag
        delivery_tag = int(message_id)
        self._channel.basic_reject(delivery_tag=delivery_tag, requeue=requeue)
        return True
