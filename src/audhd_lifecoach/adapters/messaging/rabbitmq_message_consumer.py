"""
RabbitMQ Message Consumer Adapter.

This adapter implements the MessageConsumerInterface for RabbitMQ.
"""
import json
import logging
from typing import Any, Callable, Dict, Optional

# The pika library is used for RabbitMQ communication
import pika

from audhd_lifecoach.application.interfaces.message_consumer_interface import MessageConsumerInterface


logger = logging.getLogger(__name__)


class RabbitMQMessageConsumer(MessageConsumerInterface):
    """
    RabbitMQ implementation of the MessageConsumerInterface.
    
    This class provides methods to connect to RabbitMQ, consume messages
    from a queue, and handle acknowledgments/rejections.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 5672, 
                 username: str = 'guest', password: str = 'guest',
                 virtual_host: str = '/'):
        """
        Initialize the RabbitMQ message consumer.
        
        Args:
            host: RabbitMQ host
            port: RabbitMQ port
            username: RabbitMQ username
            password: RabbitMQ password
            virtual_host: RabbitMQ virtual host
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.virtual_host = virtual_host
        
        self._connection = None
        self._channel = None
        self._consumer_tag = None
        self._callback = None
    
    def connect(self) -> bool:
        """
        Connect to the RabbitMQ server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create connection parameters
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.virtual_host,
                credentials=credentials
            )
            
            # Connect to RabbitMQ
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            
            logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to connect to RabbitMQ: {e}")
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from the RabbitMQ server.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        try:
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
            
        except Exception as e:
            logger.exception(f"Failed to disconnect from RabbitMQ: {e}")
            return False
    
    def consume_messages(self, queue_name: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """
        Start consuming messages from the specified queue.
        
        Args:
            queue_name: Name of the queue to consume from
            callback: Function to call when a message is received
        """
        if not self._channel:
            logger.error("Not connected to RabbitMQ. Call connect() first")
            return
        
        try:
            # Store the callback function
            self._callback = callback
            
            # Declare the queue (ensures it exists)
            self._channel.queue_declare(queue=queue_name, durable=True)
            
            # Start consuming messages
            self._consumer_tag = self._channel.basic_consume(
                queue=queue_name,
                on_message_callback=self._on_message,
                auto_ack=False
            )
            
            logger.info(f"Started consuming messages from queue '{queue_name}'")
            
            # Start the IO loop to process messages
            self._channel.start_consuming()
            
        except Exception as e:
            logger.exception(f"Error consuming messages: {e}")
            self.disconnect()
    
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
            logger.error("Not connected to RabbitMQ. Call connect() first")
            return False
        
        try:
            # In RabbitMQ, the message_id is the delivery tag
            delivery_tag = int(message_id)
            self._channel.basic_ack(delivery_tag=delivery_tag)
            return True
            
        except Exception as e:
            logger.exception(f"Failed to acknowledge message {message_id}: {e}")
            return False
    
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
            logger.error("Not connected to RabbitMQ. Call connect() first")
            return False
        
        try:
            # In RabbitMQ, the message_id is the delivery tag
            delivery_tag = int(message_id)
            self._channel.basic_reject(delivery_tag=delivery_tag, requeue=requeue)
            return True
            
        except Exception as e:
            logger.exception(f"Failed to reject message {message_id}: {e}")
            return False