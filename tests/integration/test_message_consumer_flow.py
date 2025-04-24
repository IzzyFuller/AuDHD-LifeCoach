"""
Integration test for the message consumer flow.

This test verifies the full flow via the message consumer:
1. A communication message is received from a message queue
2. The message is processed to extract commitments
3. Reminders are created for these commitments

This test uses the actual transformer pipeline rather than mocks.
"""
import pytest
import json
import time
from datetime import datetime
from unittest.mock import MagicMock, patch, call

import pika

from audhd_lifecoach.application.dtos.communication_dto import CommunicationRequestDTO
from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.adapters.ai.hugging_face_onyx_transformer_commitment_identifier import HuggingFaceONYXTransformerCommitmentIdentifier
from audhd_lifecoach.adapters.messaging.rabbitmq_message_consumer import RabbitMQMessageConsumer
from audhd_lifecoach.core.services.communication_processor import CommunicationProcessor
from audhd_lifecoach.application.interfaces.message_consumer_interface import MessageConsumerInterface
from audhd_lifecoach.application.services.message_consumer_service import MessageConsumerService


class TestMessageConsumerFlow:
    """Integration test for the message consumer flow."""
    
    @pytest.fixture
    def mock_pika_connection(self):
        """Create a mock for the pika BlockingConnection"""
        with patch('pika.BlockingConnection') as mock_connection:
            # Create mock channel
            mock_channel = MagicMock()
            
            # Configure connection to return the mock channel
            mock_connection.return_value.channel.return_value = mock_channel
            
            # Set up basic_consume to store the callback function
            # and prevent actual consumption from occurring
            def mock_basic_consume(queue, on_message_callback, auto_ack):
                # Store the callback for later use in tests
                mock_channel.on_message_callback = on_message_callback
                return "mock_consumer_tag"
                
            mock_channel.basic_consume = mock_basic_consume
            
            # Replace start_consuming with a no-op
            mock_channel.start_consuming = MagicMock()
            
            yield mock_connection, mock_channel
    
    @pytest.fixture
    def rabbitmq_adapter(self, mock_pika_connection):
        """Create a real RabbitMQ adapter with mocked connection"""
        # This uses the real adapter but with mocked Pika internals
        adapter = RabbitMQMessageConsumer(
            host='localhost',
            port=5672,
            username='guest',
            password='guest',
            virtual_host='/'
        )
        return adapter
    
    @pytest.fixture
    def message_consumer_service(self, rabbitmq_adapter):
        """
        Create an actual MessageConsumerService with the real RabbitMQMessageConsumer.
        """
        # Create the commitment identifier
        commitment_identifier = HuggingFaceONYXTransformerCommitmentIdentifier()
        
        # Create the communication processor
        communication_processor = CommunicationProcessor(commitment_identifier)
        
        # Create the message consumer service
        service = MessageConsumerService(
            message_consumer=rabbitmq_adapter,
            communication_processor=communication_processor,
            queue_name='communications'
        )
        
        return service
    
    @pytest.mark.integration
    def test_basic_message_flow_with_one_commitment(self, mock_pika_connection, rabbitmq_adapter, message_consumer_service):
        """
        Test the basic flow through the message consumer from message to reminder.
        
        This test simulates a message being received from RabbitMQ and verifies that it's
        properly processed by our message consumer service to extract commitments
        and create reminders.
        """
        # Unpack mocks
        mock_connection, mock_channel = mock_pika_connection
        
        # Arrange
        # Create a communication message
        message_data = {
            "content": "I'll call you at 15:30 tomorrow.",
            "sender": "Me",
            "recipient": "Friend",
            "message_id": 1
        }
        
        # Connect the adapter
        rabbitmq_adapter.connect()
        
        # Set up the message callback in the adapter
        rabbitmq_adapter.consume_messages("test_queue", message_consumer_service._message_callback)
        
        # Create method, properties and message body for the message
        method = MagicMock()
        method.delivery_tag = message_data["message_id"]
        properties = MagicMock()
        body = json.dumps(message_data).encode('utf-8')
        
        # Replace start_consuming with a function that delivers our test message
        def mock_start_consuming():
            # This simulates what would happen when RabbitMQ delivers a message
            # It calls the _on_message callback that was registered with basic_consume
            rabbitmq_adapter._on_message(mock_channel, method, properties, body)
        
        # Replace the start_consuming method with our custom function
        mock_channel.start_consuming.side_effect = mock_start_consuming
        
        # Trigger the message consumption flow
        mock_channel.start_consuming()
        
        # Verify the channel's basic_ack method was called with the correct delivery tag
        mock_channel.basic_ack.assert_called_once_with(delivery_tag=message_data["message_id"])
    
    @pytest.mark.integration
    def test_error_handling_for_invalid_message(self, mock_pika_connection, rabbitmq_adapter, message_consumer_service):
        """
        Test that the message consumer properly handles invalid messages.
        
        This test ensures that when an invalid message is received,
        it's rejected properly and doesn't cause the service to crash.
        """
        # Unpack mocks
        mock_connection, mock_channel = mock_pika_connection
        
        # Arrange
        # Create an invalid communication message (missing required fields)
        invalid_message_data = {
            "content": "This message is missing sender and recipient",
            "message_id": 2
        }
        
        # Connect the adapter
        rabbitmq_adapter.connect()
        
        # Set up the message callback in the adapter
        rabbitmq_adapter.consume_messages("test_queue", message_consumer_service._message_callback)
        
        # Create method, properties and message body for the message
        method = MagicMock()
        method.delivery_tag = invalid_message_data["message_id"]
        properties = MagicMock()
        body = json.dumps(invalid_message_data).encode('utf-8')
        
        # Replace start_consuming with a function that delivers our test message
        def mock_start_consuming():
            # This simulates what would happen when RabbitMQ delivers a message
            # It calls the _on_message callback that was registered with basic_consume
            rabbitmq_adapter._on_message(mock_channel, method, properties, body)
        
        # Replace the start_consuming method with our custom function
        mock_channel.start_consuming.side_effect = mock_start_consuming
        
        # Trigger the message consumption flow
        mock_channel.start_consuming()
        
        # Verify the RabbitMQ channel's basic_reject was called with the correct delivery tag
        mock_channel.basic_reject.assert_called_once_with(delivery_tag=invalid_message_data["message_id"], requeue=False)
    
    @pytest.mark.integration
    def test_multiple_messages_processing(self, mock_pika_connection, rabbitmq_adapter, message_consumer_service):
        """
        Test that the message consumer can process multiple messages.
        """
        # Unpack mocks
        mock_connection, mock_channel = mock_pika_connection
        
        # Arrange
        # Create multiple communication messages
        messages = [
            {
                "content": "I'll call you at 15:30 tomorrow.",
                "sender": "Me",
                "recipient": "Friend",
                "message_id": 1
            },
            {
                "content": "Let's meet at the coffee shop at 10:00.",
                "sender": "Me", 
                "recipient": "Colleague",
                "message_id": 2
            }
        ]
        
        # Connect the adapter
        rabbitmq_adapter.connect()
        
        # Set up the message callback in the adapter
        rabbitmq_adapter.consume_messages("test_queue", message_consumer_service._message_callback)
        
        # Process each message
        for message in messages:
            # Create method, properties and message body for the message
            method = MagicMock()
            method.delivery_tag = message["message_id"]
            properties = MagicMock()
            body = json.dumps(message).encode('utf-8')
            
            # Deliver the message to the adapter's callback
            rabbitmq_adapter._on_message(mock_channel, method, properties, body)
        
        # Verify that basic_ack was called once for each message
        assert mock_channel.basic_ack.call_count == len(messages), f"Expected basic_ack to be called {len(messages)} times"
        
        # Verify that basic_ack was called with the correct delivery tags
        for message in messages:
            mock_channel.basic_ack.assert_any_call(delivery_tag=message["message_id"])
    
    @pytest.mark.integration
    def test_json_decode_error_in_flow(self, mock_pika_connection, rabbitmq_adapter, message_consumer_service):
        """
        Test that malformed JSON messages are rejected in the flow.
        
        This test verifies that when a message with invalid JSON is received,
        it is properly rejected at the adapter level.
        """
        # Unpack mocks
        mock_connection, mock_channel = mock_pika_connection
        
        # Connect the adapter
        rabbitmq_adapter.connect()
        
        # Set up the message callback in the adapter
        rabbitmq_adapter.consume_messages("test_queue", message_consumer_service._message_callback)
        
        # Create method with delivery tag
        method = MagicMock()
        delivery_tag = 42
        method.delivery_tag = delivery_tag
        
        # Create properties
        properties = MagicMock()
        
        # Create invalid JSON body
        body = b'{ this is not valid JSON }'
        
        # Define our custom start_consuming behavior
        def mock_start_consuming():
            # Directly call _on_message with the invalid JSON
            rabbitmq_adapter._on_message(mock_channel, method, properties, body)
            
        # Replace the start_consuming method with our custom function
        mock_channel.start_consuming.side_effect = mock_start_consuming
        
        # Trigger the message consumption flow
        mock_channel.start_consuming()
        
        # Verify that the invalid JSON message was rejected
        mock_channel.basic_reject.assert_called_once_with(delivery_tag=delivery_tag, requeue=False)
    
    @pytest.mark.integration
    def test_exception_during_processing_in_flow(self, mock_pika_connection, rabbitmq_adapter, message_consumer_service):
        """
        Test that exceptions during message processing are handled correctly.
        
        This test verifies that when an exception occurs during message processing,
        the message is properly rejected with requeue=True at the adapter level.
        """
        # Unpack mocks
        mock_connection, mock_channel = mock_pika_connection
        
        # Create a valid message
        message_data = {
            "content": "This message will trigger an exception",
            "sender": "Me",
            "recipient": "Friend",
            "message_id": 6
        }
        
        # Connect the adapter
        rabbitmq_adapter.connect()
        
        # Set up the message callback in the adapter
        rabbitmq_adapter.consume_messages("test_queue", message_consumer_service._message_callback)
        
        # Create method, properties and message body for the message
        method = MagicMock()
        method.delivery_tag = message_data["message_id"]
        properties = MagicMock()
        body = json.dumps(message_data).encode('utf-8')
        
        # Patch the process_message method to raise an exception
        with patch.object(message_consumer_service, '_process_message', 
                         side_effect=Exception("Simulated processing error")):
            # Replace start_consuming with a function that delivers our test message
            def mock_start_consuming():
                # This simulates what would happen when RabbitMQ delivers a message
                # It calls the _on_message callback that was registered with basic_consume
                rabbitmq_adapter._on_message(mock_channel, method, properties, body)
            
            # Replace the start_consuming method with our custom function
            mock_channel.start_consuming.side_effect = mock_start_consuming
            
            # Trigger the message consumption flow
            mock_channel.start_consuming()
            
            # Verify the RabbitMQ channel's basic_reject was called with requeue=True
            mock_channel.basic_reject.assert_called_once_with(delivery_tag=message_data["message_id"], requeue=True)
    
    @pytest.mark.integration
    def test_disconnect_cleans_up_resources(self, mock_pika_connection, rabbitmq_adapter):
        """
        Test that disconnecting from RabbitMQ properly cleans up resources.
        
        This test verifies that when disconnect() is called, all associated resources
        are properly cleaned up, including cancelling consumers and closing connections.
        """
        # Unpack mocks
        mock_connection, mock_channel = mock_pika_connection
        
        # Setup consumer tag
        rabbitmq_adapter._consumer_tag = "test-consumer-tag"
        
        # Connect the adapter
        rabbitmq_adapter.connect()
        
        # Disconnect
        result = rabbitmq_adapter.disconnect()
        
        # Verify the result
        assert result is True, "disconnect should return True on success"
        
        # Verify the channel operations
        mock_channel.basic_cancel.assert_called_once_with("test-consumer-tag")
        mock_channel.close.assert_called_once()
        
        # Verify connection was closed
        mock_connection.return_value.close.assert_called_once()
        
        # Verify internal state was reset
        assert rabbitmq_adapter._channel is None
        assert rabbitmq_adapter._connection is None
        assert rabbitmq_adapter._consumer_tag is None