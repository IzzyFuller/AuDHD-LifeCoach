"""
RabbitMQ Message Publisher.

This adapter implements the message publisher interface for RabbitMQ.
"""
import json
import logging
from typing import Any, Dict, Optional

import pika
from pika.exceptions import AMQPError

# The publisher interface is defined as a Protocol - no need to inherit
from audhd_lifecoach.application.interfaces.message_publisher_interface import MessagePublisherInterface


logger = logging.getLogger(__name__)


class RabbitMQMessagePublisher:
    """
    RabbitMQ implementation of the message publisher interface.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5672,
        username: str = "guest",
        password: str = "guest",
        virtual_host: str = "/",
        connection_attempts: int = 3,
        retry_delay: int = 5
    ):
        """
        Initialize the RabbitMQ message publisher.
        
        Args:
            host: RabbitMQ host
            port: RabbitMQ port
            username: RabbitMQ username
            password: RabbitMQ password
            virtual_host: RabbitMQ virtual host
            connection_attempts: Number of connection attempts
            retry_delay: Delay between connection attempts in seconds
        """
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._virtual_host = virtual_host
        self._connection_attempts = connection_attempts
        self._retry_delay = retry_delay
        
        # Connection state
        self._connection = None
        self._channel = None
        
    def connect(self) -> bool:
        """
        Connect to RabbitMQ.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create connection parameters with credentials
            credentials = pika.PlainCredentials(
                username=self._username, 
                password=self._password
            )
            
            parameters = pika.ConnectionParameters(
                host=self._host,
                port=self._port,
                virtual_host=self._virtual_host,
                credentials=credentials,
                connection_attempts=self._connection_attempts,
                retry_delay=self._retry_delay
            )
            
            # Connect to RabbitMQ
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            
            logger.info(f"Connected to RabbitMQ at {self._host}:{self._port}")
            return True
            
        except AMQPError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from RabbitMQ.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        try:
            if self._connection and self._connection.is_open:
                # Close channel first if it exists
                if self._channel and self._channel.is_open:
                    self._channel.close()
                
                # Close connection
                self._connection.close()
                
                # Reset connection state
                self._connection = None
                self._channel = None
                
                logger.info("Disconnected from RabbitMQ")
                return True
            return True  # Already disconnected
            
        except AMQPError as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")
            return False
    
    def _ensure_exchange_exists(self, exchange: str, exchange_type: str = "topic") -> bool:
        """
        Ensure that the exchange exists.
        
        Args:
            exchange: The exchange name
            exchange_type: The exchange type (topic, direct, fanout, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self._channel:
                logger.error("Not connected to RabbitMQ")
                return False
                
            self._channel.exchange_declare(
                exchange=exchange,
                exchange_type=exchange_type,
                durable=True,  # Survive broker restarts
                auto_delete=False  # Don't delete when no queues are bound
            )
            return True
            
        except AMQPError as e:
            logger.error(f"Failed to declare exchange '{exchange}': {e}")
            return False
    
    def publish_message(
        self,
        exchange: str,
        routing_key: str,
        message: Dict[str, Any],
        content_type: str = "application/json",
        persistent: bool = True
    ) -> bool:
        """
        Publish a message to RabbitMQ.
        
        Args:
            exchange: The exchange to publish to
            routing_key: The routing key for the message
            message: The message to publish (will be serialized to JSON)
            content_type: The content type of the message
            persistent: Whether the message should be persisted by the broker
            
        Returns:
            bool: True if the message was published successfully, False otherwise
        """
        try:
            if not self._channel:
                logger.error("Not connected to RabbitMQ")
                return False
            
            # Ensure the exchange exists (topic exchange by default)
            if not self._ensure_exchange_exists(exchange):
                return False
                
            # Convert message to JSON
            message_body = json.dumps(message).encode('utf-8')
            
            # Create message properties
            properties = pika.BasicProperties(
                content_type=content_type,
                delivery_mode=2 if persistent else 1  # 2 = persistent, 1 = non-persistent
            )
            
            # Publish message
            self._channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=message_body,
                properties=properties
            )
            
            logger.debug(f"Published message to exchange '{exchange}' with routing key '{routing_key}'")
            return True
            
        except AMQPError as e:
            logger.error(f"Failed to publish message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing message: {e}")
            return False