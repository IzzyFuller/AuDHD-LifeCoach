"""
Test the MessageConsumerInterface.

This module contains tests for ensuring proper implementation of the MessageConsumerInterface.
"""
import pytest
from typing import List, Dict, Any, Optional, Callable
from unittest.mock import MagicMock

from audhd_lifecoach.application.interfaces.message_consumer_interface import MessageConsumerInterface


class TestMessageConsumerInterface:
    """Tests to verify the protocol can be used as expected."""
    
    def test_interface_compliance(self):
        """Test that an object implementing all required methods is recognized as compliant."""
        # Arrange
        class MockConsumer:
            """Mock implementation that should match the interface."""
            
            def connect(self) -> bool:
                return True
                
            def disconnect(self) -> bool:
                return True
            
            def consume_messages(self, queue_name: str, callback: Callable[[dict], Any]) -> None:
                pass
            
            def acknowledge_message(self, message_id: str) -> bool:
                return True
            
            def reject_message(self, message_id: str, requeue: bool = False) -> bool:
                return True
        
        # Act
        mock_consumer = MockConsumer()
        
        # Assert
        assert isinstance(mock_consumer, MessageConsumerInterface)
    
    def test_interface_non_compliance(self):
        """Test that an object missing required methods is not recognized as compliant."""
        # Arrange
        class IncompleteMockConsumer:
            """Mock implementation missing required methods."""
            
            def connect(self) -> bool:
                return True
                
            def disconnect(self) -> bool:
                return True
            
            # Missing consume_messages method
            
            def acknowledge_message(self, message_id: str) -> bool:
                return True
            
            def reject_message(self, message_id: str, requeue: bool = False) -> bool:
                return True
        
        # Act
        incomplete_mock = IncompleteMockConsumer()
        
        # Assert
        assert not isinstance(incomplete_mock, MessageConsumerInterface)
    
    def test_connect_disconnect_lifecycle(self):
        """Test the basic connect/disconnect lifecycle."""
        # Arrange - Note: We're using a concrete class now instead of MagicMock
        class MockConsumer:
            def connect(self) -> bool:
                return True
                
            def disconnect(self) -> bool:
                return True
            
            def consume_messages(self, queue_name: str, callback: Callable[[dict], Any]) -> None:
                pass
            
            def acknowledge_message(self, message_id: str) -> bool:
                return True
            
            def reject_message(self, message_id: str, requeue: bool = False) -> bool:
                return True
        
        mock_consumer = MockConsumer()
        
        # Act & Assert
        assert mock_consumer.connect()
        assert mock_consumer.disconnect()
    
    def test_message_consumption_callback(self):
        """Test that message consumption invokes the callback."""
        # Arrange
        queue_name = "test_queue"
        callback_called = False
        callback_data = None
        
        class MockConsumer:
            def connect(self) -> bool:
                return True
                
            def disconnect(self) -> bool:
                return True
            
            def consume_messages(self, queue_name: str, callback: Callable[[dict], Any]) -> None:
                # Simulate calling the callback with a test message
                nonlocal callback_called, callback_data
                message_data = {"content": "Test message"}
                callback(message_data)
                callback_called = True
                callback_data = message_data
            
            def acknowledge_message(self, message_id: str) -> bool:
                return True
            
            def reject_message(self, message_id: str, requeue: bool = False) -> bool:
                return True
        
        mock_consumer = MockConsumer()
        
        # Define a real callback function
        def test_callback(data: dict) -> None:
            assert data["content"] == "Test message"
        
        # Act
        mock_consumer.consume_messages(queue_name, test_callback)
        
        # Assert
        assert callback_called
        assert callback_data is not None
        assert callback_data["content"] == "Test message"
    
    def test_message_acknowledgment(self):
        """Test message acknowledgment."""
        # Arrange
        message_id = "message123"
        acknowledge_called = False
        acknowledge_id = None
        
        class MockConsumer:
            def connect(self) -> bool:
                return True
                
            def disconnect(self) -> bool:
                return True
            
            def consume_messages(self, queue_name: str, callback: Callable[[dict], Any]) -> None:
                pass
            
            def acknowledge_message(self, message_id: str) -> bool:
                nonlocal acknowledge_called, acknowledge_id
                acknowledge_called = True
                acknowledge_id = message_id
                return True
            
            def reject_message(self, message_id: str, requeue: bool = False) -> bool:
                return True
        
        mock_consumer = MockConsumer()
        
        # Act
        result = mock_consumer.acknowledge_message(message_id)
        
        # Assert
        assert result is True
        assert acknowledge_called
        assert acknowledge_id == message_id
    
    def test_message_rejection(self):
        """Test message rejection with and without requeuing."""
        # Arrange
        message_id = "message123"
        reject_called = False
        reject_id = None
        reject_requeue = None
        
        class MockConsumer:
            def connect(self) -> bool:
                return True
                
            def disconnect(self) -> bool:
                return True
            
            def consume_messages(self, queue_name: str, callback: Callable[[dict], Any]) -> None:
                pass
            
            def acknowledge_message(self, message_id: str) -> bool:
                return True
            
            def reject_message(self, message_id: str, requeue: bool = False) -> bool:
                nonlocal reject_called, reject_id, reject_requeue
                reject_called = True
                reject_id = message_id
                reject_requeue = requeue
                return True
        
        mock_consumer = MockConsumer()
        
        # Act & Assert - Without requeue (using default)
        result = mock_consumer.reject_message(message_id)
        assert result is True
        assert reject_called
        assert reject_id == message_id
        assert reject_requeue is False
        
        # Reset tracking variables
        reject_called = False
        reject_id = None
        reject_requeue = None
        
        # Act & Assert - With requeue=True
        result = mock_consumer.reject_message(message_id, requeue=True)
        assert result is True
        assert reject_called
        assert reject_id == message_id
        assert reject_requeue is True