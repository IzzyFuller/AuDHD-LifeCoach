"""
Message Consumer Interface for handling message-based communication.

This module defines the protocol for message consumer adapters to interact with the application.
"""
from typing import Protocol, runtime_checkable, Any, Callable


@runtime_checkable
class MessageConsumerInterface(Protocol):
    """
    Protocol for message consumer adapters.
    
    This interface defines how the application interacts with different message broker
    implementations (RabbitMQ, SQS, etc.) for consuming messages.
    """
    
    def connect(self) -> bool:
        """
        Connect to the message broker.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        ...
        
    def disconnect(self) -> bool:
        """
        Disconnect from the message broker.
        
        Returns:
            bool: True if disconnect was successful, False otherwise
        """
        ...
    
    def consume_messages(self, queue_name: str, callback: Callable[[dict], Any]) -> None:
        """
        Start consuming messages from the specified queue.
        
        This method typically starts a blocking loop that calls the callback
        function whenever a new message is received.
        
        Args:
            queue_name: The name of the queue to consume from
            callback: Function to call when a message is received.
                     The callback should accept a dict parameter containing the message data.
        """
        ...
    
    def acknowledge_message(self, message_id: str) -> bool:
        """
        Acknowledge that a message has been processed successfully.
        
        Args:
            message_id: The ID of the message to acknowledge
            
        Returns:
            bool: True if the acknowledgment was successful, False otherwise
        """
        ...
    
    def reject_message(self, message_id: str, requeue: bool = False) -> bool:
        """
        Reject a message that could not be processed.
        
        Args:
            message_id: The ID of the message to reject
            requeue: Whether to requeue the message for later processing
            
        Returns:
            bool: True if the rejection was successful, False otherwise
        """
        ...