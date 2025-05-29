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
from audhd_lifecoach.adapters.messaging.rabbitmq_settings import RabbitMQSettings
from audhd_lifecoach.application.interfaces.message_publisher_interface import MessagePublisherInterface


logger = logging.getLogger(__name__)


class RabbitMQMessagePublisher:
    """
    RabbitMQ implementation of the message publisher interface.
    
    This implementation assumes all infrastructure (exchanges, queues, bindings)
    has been pre-provisioned externally (e.g., by Terraform).
    """
    
    def __init__(self, settings: RabbitMQSettings):
        """
        Initialize the RabbitMQ message publisher with settings.
        
        Args:
            settings: RabbitMQ configuration settings
        """
        self.settings = settings
        
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
                username=self.settings.username, 
                password=self.settings.password
            )
            
            parameters = pika.ConnectionParameters(
                host=self.settings.host,
                port=self.settings.port,
                virtual_host=self.settings.virtual_host,
                credentials=credentials,
                connection_attempts=self.settings.connection_attempts,
                retry_delay=self.settings.retry_delay,
                socket_timeout=self.settings.connection_timeout,
                heartbeat=self.settings.heartbeat
            )
            
            # Connect to RabbitMQ
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            
            logger.info(f"Connected to RabbitMQ at {self.settings.host}:{self.settings.port}")
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
    
    def publish_message(
        self,
        routing_key: str,
        message: Dict[str, Any],
        content_type: str = "application/json",
        persistent: bool = True
    ) -> bool:
        """
        Publish a message to the configured exchange.
        
        Assumes the exchange has been pre-provisioned externally.
        
        Args:
            routing_key: The routing key for the message
            message: The message to publish (will be serialized to JSON)
            content_type: The content type of the message
            persistent: Whether the message should be persisted by the broker
            
        Returns:
            bool: True if the message was published successfully, False otherwise
        """
        if not self._channel:
            return False
        
        try:
            # Convert message to JSON
            message_body = json.dumps(message).encode('utf-8')
            
            # Create message properties
            properties = pika.BasicProperties(
                content_type=content_type,
                delivery_mode=2 if persistent else 1  # 2 = persistent, 1 = non-persistent
            )
            
            # Publish message to the configured exchange
            self._channel.basic_publish(
                exchange=self.settings.publish_exchange_name,  # Use configured exchange
                routing_key=routing_key,
                body=message_body,
                properties=properties
            )
            
            logger.debug(f"Published message to exchange '{self.settings.publish_exchange_name}' with routing key '{routing_key}'")
            return True
            
        except AMQPError as e:
            logger.error(f"Failed to publish message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing message: {e}")
            return False