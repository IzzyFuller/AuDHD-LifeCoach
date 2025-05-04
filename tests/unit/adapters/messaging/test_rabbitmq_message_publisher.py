"""
Unit tests for the RabbitMQ message publisher adapter.

This test module verifies that the RabbitMQ adapter correctly implements the
message publisher interface and interacts with pika as expected.
"""
import json
import pytest
from unittest.mock import MagicMock, patch, call
from typing import Dict, Any

import pika
from pika.exceptions import AMQPError

# The interface that the adapter should implement
from audhd_lifecoach.application.interfaces.message_publisher_interface import MessagePublisherInterface

# Import the adapter class (which doesn't exist yet - this will fail until implemented)
# This follows TDD - test first, then implement
from audhd_lifecoach.adapters.messaging.rabbitmq_message_publisher import RabbitMQMessagePublisher


class TestRabbitMQMessagePublisher:
    """Test case for the RabbitMQ message publisher adapter."""
    
    @pytest.fixture
    def mock_pika_connection(self):
        """Create a mock for the pika BlockingConnection."""
        with patch('pika.BlockingConnection') as mock_connection:
            # Create mock channel
            mock_channel = MagicMock()
            
            # Configure connection to return the mock channel
            mock_connection.return_value.channel.return_value = mock_channel
            
            yield mock_connection, mock_channel
    
    def test_implements_interface(self):
        """Test that the RabbitMQ adapter implements the MessagePublisherInterface."""
        # Arrange
        publisher = RabbitMQMessagePublisher(
            host='localhost',
            port=5672,
            username='guest',
            password='guest'
        )
        
        # Assert
        assert isinstance(publisher, MessagePublisherInterface)
    
    def test_connect_success(self, mock_pika_connection):
        """Test successful connection to RabbitMQ."""
        # Arrange
        mock_connection, mock_channel = mock_pika_connection
        
        publisher = RabbitMQMessagePublisher(
            host='localhost',
            port=5672,
            username='guest',
            password='guest'
        )
        
        # Act
        result = publisher.connect()
        
        # Assert
        assert result is True
        mock_connection.assert_called_once()
        
        # Verify connection parameters
        args, kwargs = mock_connection.call_args
        connection_params = args[0]
        assert connection_params.host == 'localhost'
        assert connection_params.port == 5672
        assert connection_params.credentials.username == 'guest'
        assert connection_params.credentials.password == 'guest'
    
    def test_connect_failure(self):
        """Test connection failure to RabbitMQ."""
        # Arrange
        with patch('pika.BlockingConnection', side_effect=AMQPError("Connection failed")):
            publisher = RabbitMQMessagePublisher(
                host='localhost',
                port=5672,
                username='guest',
                password='guest'
            )
            
            # Act
            result = publisher.connect()
            
            # Assert
            assert result is False
    
    def test_disconnect_success(self, mock_pika_connection):
        """Test successful disconnection from RabbitMQ."""
        # Arrange
        mock_connection, mock_channel = mock_pika_connection
        
        publisher = RabbitMQMessagePublisher(
            host='localhost',
            port=5672,
            username='guest',
            password='guest'
        )
        
        # Connect first
        publisher.connect()
        
        # Act
        result = publisher.disconnect()
        
        # Assert
        assert result is True
        mock_channel.close.assert_called_once()
        mock_connection.return_value.close.assert_called_once()
    
    def test_disconnect_already_disconnected(self):
        """Test disconnection when already disconnected."""
        # Arrange
        publisher = RabbitMQMessagePublisher(
            host='localhost',
            port=5672,
            username='guest',
            password='guest'
        )
        
        # Act - without connecting first
        result = publisher.disconnect()
        
        # Assert
        assert result is True  # Should return True when already disconnected
    
    def test_disconnect_failure(self, mock_pika_connection):
        """Test failure during disconnection."""
        # Arrange
        mock_connection, mock_channel = mock_pika_connection
        mock_channel.close.side_effect = AMQPError("Close failed")
        
        publisher = RabbitMQMessagePublisher(
            host='localhost',
            port=5672,
            username='guest',
            password='guest'
        )
        
        # Connect first
        publisher.connect()
        
        # Act
        result = publisher.disconnect()
        
        # Assert
        assert result is False
    
    def test_publish_message_success(self, mock_pika_connection):
        """Test successful message publishing."""
        # Arrange
        mock_connection, mock_channel = mock_pika_connection
        
        publisher = RabbitMQMessagePublisher(
            host='localhost',
            port=5672,
            username='guest',
            password='guest'
        )
        
        # Connect first
        publisher.connect()
        
        # Test message
        exchange = "test-exchange"
        routing_key = "test.key"
        message = {"test": "message"}
        
        # Act
        result = publisher.publish_message(exchange, routing_key, message)
        
        # Assert
        assert result is True
        
        # Verify message published
        mock_channel.basic_publish.assert_called_once()
        args, kwargs = mock_channel.basic_publish.call_args
        
        assert kwargs["exchange"] == exchange
        assert kwargs["routing_key"] == routing_key
        assert kwargs["body"] == json.dumps(message).encode('utf-8')
        
        # Verify properties
        properties = kwargs["properties"]
        assert properties.content_type == "application/json"
        assert properties.delivery_mode == 2  # persistent
    
    def test_publish_message_not_connected(self):
        """Test publishing message when not connected."""
        # Arrange
        publisher = RabbitMQMessagePublisher(
            host='localhost',
            port=5672,
            username='guest',
            password='guest'
        )
        
        # Act - without connecting first
        result = publisher.publish_message("test-exchange", "test.key", {"test": "message"})
        
        # Assert
        assert result is False
    
    def test_publish_message_with_publish_failure(self, mock_pika_connection):
        """Test publishing with basic_publish failure."""
        # Arrange
        mock_connection, mock_channel = mock_pika_connection
        mock_channel.basic_publish.side_effect = AMQPError("Publish failed")
        
        publisher = RabbitMQMessagePublisher(
            host='localhost',
            port=5672,
            username='guest',
            password='guest'
        )
        
        # Connect first
        publisher.connect()
        
        # Act
        result = publisher.publish_message("test-exchange", "test.key", {"test": "message"})
        
        # Assert
        assert result is False
    
    def test_publish_message_non_persistent(self, mock_pika_connection):
        """Test publishing non-persistent message."""
        # Arrange
        mock_connection, mock_channel = mock_pika_connection
        
        publisher = RabbitMQMessagePublisher(
            host='localhost',
            port=5672,
            username='guest',
            password='guest'
        )
        
        # Connect first
        publisher.connect()
        
        # Act - with persistent=False
        result = publisher.publish_message(
            "test-exchange", 
            "test.key", 
            {"test": "message"}, 
            persistent=False
        )
        
        # Assert
        assert result is True
        
        # Verify properties - delivery_mode should be 1 (non-persistent)
        args, kwargs = mock_channel.basic_publish.call_args
        properties = kwargs["properties"]
        assert properties.delivery_mode == 1  # non-persistent