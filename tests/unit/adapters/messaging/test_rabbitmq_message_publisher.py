"""
Unit tests for the RabbitMQ message publisher adapter.

This test module verifies that the RabbitMQ adapter correctly implements the
message publisher interface and interacts with pika as expected.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from pika.exceptions import AMQPError

# Import the adapter class and settings
from audhd_lifecoach.adapters.messaging.rabbitmq_message_publisher import (
    RabbitMQMessagePublisher,
)
from audhd_lifecoach.adapters.messaging.rabbitmq_settings import RabbitMQSettings

# The interface that the adapter should implement
from audhd_lifecoach.application.interfaces.message_publisher_interface import (
    MessagePublisherInterface,
)


class TestRabbitMQMessagePublisher:
    """Test case for the RabbitMQ message publisher adapter."""

    @pytest.fixture
    def test_settings(self):
        """Create test RabbitMQ settings."""
        return RabbitMQSettings(
            host="localhost",
            port=5672,
            username="guest",
            password="guest",
            virtual_host="/",
            consume_queue_name="test_queue",
            publish_exchange_name="test_exchange",
            connection_attempts=3,
            retry_delay=2,
            connection_timeout=30,
            heartbeat=600,
            use_ssl=False,
            ssl_ca_cert_path=None,
            ssl_cert_path=None,
            ssl_key_path=None,
        )

    @pytest.fixture
    def mock_pika_connection(self):
        """Create a mock for the pika BlockingConnection."""
        with patch("pika.BlockingConnection") as mock_connection:
            # Create mock channel
            mock_channel = MagicMock()

            # Configure connection to return the mock channel
            mock_connection.return_value.channel.return_value = mock_channel

            yield mock_connection, mock_channel

    def test_implements_interface(self, test_settings):
        """Test that the RabbitMQ adapter implements the MessagePublisherInterface."""
        # Arrange
        publisher = RabbitMQMessagePublisher(test_settings)

        # Assert
        assert isinstance(publisher, MessagePublisherInterface)

    def test_connect_success(self, mock_pika_connection, test_settings):
        """Test successful connection to RabbitMQ."""
        # Arrange
        mock_connection, mock_channel = mock_pika_connection

        publisher = RabbitMQMessagePublisher(test_settings)

        # Act
        result = publisher.connect()

        # Assert
        assert result is True
        mock_connection.assert_called_once()

        # Verify connection parameters
        args, kwargs = mock_connection.call_args
        connection_params = args[0]
        assert connection_params.host == "localhost"
        assert connection_params.port == 5672
        assert connection_params.credentials.username == "guest"
        assert connection_params.credentials.password == "guest"

    def test_connect_failure(self, test_settings):
        """Test connection failure to RabbitMQ."""
        # Arrange
        with patch(
            "pika.BlockingConnection", side_effect=AMQPError("Connection failed")
        ):
            publisher = RabbitMQMessagePublisher(test_settings)

            # Act
            result = publisher.connect()

            # Assert
            assert result is False

    def test_disconnect_success(self, mock_pika_connection, test_settings):
        """Test successful disconnection from RabbitMQ."""
        # Arrange
        mock_connection, mock_channel = mock_pika_connection

        publisher = RabbitMQMessagePublisher(test_settings)

        # Connect first
        publisher.connect()

        # Act
        result = publisher.disconnect()

        # Assert
        assert result is True
        mock_channel.close.assert_called_once()
        mock_connection.return_value.close.assert_called_once()

    def test_disconnect_already_disconnected(self, test_settings):
        """Test disconnection when already disconnected."""
        # Arrange
        publisher = RabbitMQMessagePublisher(test_settings)

        # Act - without connecting first
        result = publisher.disconnect()

        # Assert
        assert result is True  # Should return True when already disconnected

    def test_disconnect_failure(self, mock_pika_connection, test_settings):
        """Test failure during disconnection."""
        # Arrange
        mock_connection, mock_channel = mock_pika_connection
        mock_channel.close.side_effect = AMQPError("Close failed")

        publisher = RabbitMQMessagePublisher(test_settings)

        # Connect first
        publisher.connect()

        # Act
        result = publisher.disconnect()

        # Assert
        assert result is False

    def test_publish_message_success(self, mock_pika_connection, test_settings):
        """Test successful message publishing."""
        # Arrange
        mock_connection, mock_channel = mock_pika_connection

        publisher = RabbitMQMessagePublisher(test_settings)

        # Connect first
        publisher.connect()

        # Test message
        routing_key = "test.key"
        message = {"test": "message"}

        # Act
        result = publisher.publish_message(routing_key, message)

        # Assert
        assert result is True

        # Verify message published
        mock_channel.basic_publish.assert_called_once()
        args, kwargs = mock_channel.basic_publish.call_args

        assert kwargs["exchange"] == test_settings.publish_exchange_name
        assert kwargs["routing_key"] == routing_key
        assert kwargs["body"] == json.dumps(message).encode("utf-8")

        # Verify properties
        properties = kwargs["properties"]
        assert properties.content_type == "application/json"
        assert properties.delivery_mode == 2  # persistent

    def test_publish_message_not_connected(self, test_settings):
        """Test publishing message when not connected."""
        # Arrange
        publisher = RabbitMQMessagePublisher(test_settings)

        # Act - without connecting first
        result = publisher.publish_message("test.key", {"test": "message"})

        # Assert
        assert result is False

    def test_publish_message_with_publish_failure(
        self, mock_pika_connection, test_settings
    ):
        """Test publishing with basic_publish failure."""
        # Arrange
        mock_connection, mock_channel = mock_pika_connection
        mock_channel.basic_publish.side_effect = AMQPError("Publish failed")

        publisher = RabbitMQMessagePublisher(test_settings)

        # Connect first
        publisher.connect()

        # Act
        result = publisher.publish_message("test.key", {"test": "message"})

        # Assert
        assert result is False

    def test_publish_message_non_persistent(self, mock_pika_connection, test_settings):
        """Test publishing non-persistent message."""
        # Arrange
        mock_connection, mock_channel = mock_pika_connection

        publisher = RabbitMQMessagePublisher(test_settings)

        # Connect first
        publisher.connect()

        # Act - with persistent=False
        result = publisher.publish_message(
            "test.key", {"test": "message"}, persistent=False
        )

        # Assert
        assert result is True

        # Verify properties - delivery_mode should be 1 (non-persistent)
        args, kwargs = mock_channel.basic_publish.call_args
        properties = kwargs["properties"]
        assert properties.delivery_mode == 1  # non-persistent

    def test_publish_message_custom_content_type(
        self, mock_pika_connection, test_settings
    ):
        """Test publishing message with custom content type."""
        # Arrange
        mock_connection, mock_channel = mock_pika_connection

        publisher = RabbitMQMessagePublisher(test_settings)

        # Connect first
        publisher.connect()

        # Act - with custom content type
        result = publisher.publish_message(
            "test.key", {"test": "message"}, content_type="application/custom"
        )

        # Assert
        assert result is True

        # Verify properties
        args, kwargs = mock_channel.basic_publish.call_args
        properties = kwargs["properties"]
        assert properties.content_type == "application/custom"

    def test_settings_validation_invalid_port(self):
        """Test that invalid port raises ValueError."""
        with pytest.raises(ValueError, match="Invalid port number"):
            RabbitMQSettings(
                host="localhost",
                port=-1,  # Invalid port
                username="guest",
                password="guest",
                consume_queue_name="test_queue",
                publish_exchange_name="test_exchange",
            )

    def test_settings_validation_empty_queue_name(self):
        """Test that empty queue name raises ValueError."""
        with pytest.raises(ValueError, match="Consume queue name cannot be empty"):
            RabbitMQSettings(
                host="localhost",
                port=5672,
                username="guest",
                password="guest",
                consume_queue_name="",  # Empty queue name
                publish_exchange_name="test_exchange",
            )

    def test_settings_validation_empty_exchange_name(self):
        """Test that empty exchange name raises ValueError."""
        with pytest.raises(ValueError, match="Publish exchange name cannot be empty"):
            RabbitMQSettings(
                host="localhost",
                port=5672,
                username="guest",
                password="guest",
                consume_queue_name="test_queue",
                publish_exchange_name="",  # Empty exchange name
            )
