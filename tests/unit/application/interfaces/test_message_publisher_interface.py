"""
Unit tests for the message publisher interface.
"""
import pytest
from unittest.mock import MagicMock
from typing import Dict, Any

from audhd_lifecoach.application.interfaces.message_publisher_interface import MessagePublisherInterface


class ConcreteMessagePublisher:
    """Concrete implementation of MessagePublisherInterface for testing."""
    
    def connect(self) -> bool:
        """Connect implementation for testing."""
        return True
    
    def disconnect(self) -> bool:
        """Disconnect implementation for testing."""
        return True
    
    def publish_message(self, 
                      exchange: str,
                      routing_key: str, 
                      message: Dict[str, Any],
                      content_type: str = "application/json",
                      persistent: bool = True) -> bool:
        """Publish message implementation for testing."""
        return True


class TestMessagePublisherInterface:
    """Test case for the message publisher interface."""
    
    def test_interface_implementation(self):
        """Test that we can implement and use the interface."""
        # Arrange
        publisher = ConcreteMessagePublisher()
        
        # Act & Assert - no exceptions should be raised
        assert publisher.connect() is True
        assert publisher.disconnect() is True
        assert publisher.publish_message("test-exchange", "test.key", {"test": "message"}) is True
        
        # Verify the object satisfies the Protocol
        assert isinstance(publisher, MessagePublisherInterface)
    
    def test_partial_implementation_fails_runtime_check(self):
        """Test that a partial implementation fails the runtime check."""
        # Arrange - create a class missing some methods
        class PartialImplementation:
            def connect(self) -> bool:
                return True
                
            # Missing disconnect and publish_message methods
        
        # Act
        partial = PartialImplementation()
        
        # Assert - should not be recognized as implementing the protocol
        assert not isinstance(partial, MessagePublisherInterface)
    
    def test_duck_typing_compatibility(self):
        """Test that any object with correct method signatures satisfies the protocol."""
        # Arrange - create a completely separate class with compatible methods
        class RandomPublisherLike:
            def connect(self) -> bool:
                return False
                
            def disconnect(self) -> bool:
                return False
                
            def publish_message(self, 
                              exchange: str,
                              routing_key: str, 
                              message: Dict[str, Any],
                              content_type: str = "application/json",
                              persistent: bool = True) -> bool:
                return False
        
        # Act
        random_obj = RandomPublisherLike()
        
        # Assert - should be recognized as implementing the protocol
        assert isinstance(random_obj, MessagePublisherInterface)