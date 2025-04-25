"""
Message Publisher Interface.

This interface defines the contract for message publishing adapters.
"""
from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class MessagePublisherInterface(Protocol):
    """
    Interface for message publisher adapters that publish messages to a message broker.
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
            bool: True if disconnection was successful, False otherwise
        """
        ...
    
    def publish_message(self, 
                        exchange: str,
                        routing_key: str, 
                        message: Dict[str, Any],
                        content_type: str = "application/json",
                        persistent: bool = True) -> bool:
        """
        Publish a message to the message broker.
        
        Args:
            exchange: The exchange to publish to
            routing_key: The routing key for the message
            message: The message to publish
            content_type: The content type of the message
            persistent: Whether the message should be persisted by the broker
            
        Returns:
            bool: True if the message was published successfully, False otherwise
        """
        ...