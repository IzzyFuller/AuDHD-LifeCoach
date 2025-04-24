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
from unittest.mock import MagicMock, patch

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
    
    def simulate_message_received(self, mock_channel, message_data):
        """Helper method to simulate a message being received from RabbitMQ"""
        # Create a method frame object with delivery tag
        method = MagicMock()
        method.delivery_tag = message_data.get("message_id", "test-message-1")
        
        # Create properties object
        properties = MagicMock()
        
        # Convert message data to bytes
        body = json.dumps(message_data).encode('utf-8')
        
        # Get the callback that was registered with basic_consume
        callback = mock_channel.on_message_callback
        
        # Call the callback directly as if RabbitMQ had called it
        callback(mock_channel, method, properties, body)
        
        return method.delivery_tag
    
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
            "message_id": "test-message-1"
        }
        
        # Helper class to capture results
        results = []
        
        # Define a mock callback to capture results
        def capture_callback(message_data):
            result = message_consumer_service._process_message(message_data)
            results.append(result)
            return result
        
        # Patch the message_callback method to use our capturing callback
        with patch.object(message_consumer_service, '_message_callback', side_effect=capture_callback):
            # Start the message consumer service in non-blocking mode
            message_consumer_service.start(block=False)
            
            # Simulate a message being received
            self.simulate_message_received(mock_channel, message_data)
            
            # Stop the service
            message_consumer_service.stop()
        
        # Assert that the message was processed and produced a result
        assert len(results) > 0, "Message was not processed"
        result = results[0]
        
        # Assert that reminders were created
        assert result is not None, "Message processing should return a result"
        reminders = result["reminders"]
        assert len(reminders) > 0, "No reminders were created from the communication"
        
        # Get the first reminder and verify its details
        reminder = reminders[0]
        
        # Verify reminder commitment details
        assert "Friend" == reminder["commitment_who"], f"Expected recipient 'Friend', got '{reminder['commitment_who']}'"
        assert "Meeting or appointment" in reminder["commitment_what"] or "call" in reminder["commitment_what"].lower(), \
               f"Unexpected commitment type: {reminder['commitment_what']}"
        
        # Using 15:30 as the expected time from our message
        commitment_start = datetime.fromisoformat(reminder["commitment_start_time"])
        commitment_end = datetime.fromisoformat(reminder["commitment_end_time"])
        
        assert commitment_start.hour == 15, f"Expected start hour 15, got {commitment_start.hour}"
        assert commitment_start.minute == 30, f"Expected start minute 30, got {commitment_start.minute}"
        
        # Make sure end_time is after start_time
        assert commitment_end > commitment_start, "Commitment end time should be after start time"
        
        # Verify reminder time and acknowledgment
        reminder_when = datetime.fromisoformat(reminder["when"])
        assert reminder_when < commitment_start, "Reminder time should be before commitment start time"
        assert reminder["acknowledged"] is False, "New reminder should not be acknowledged"
    
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
            "message_id": "test-invalid-message"
        }
        
        # Helper lists to track results
        results = []
        rejected_message_ids = []
        
        # Define a mock callback to capture results
        def capture_callback(message_data):
            result = message_consumer_service._process_message(message_data)
            results.append(result)
            if result is None:
                rejected_message_ids.append(message_data.get("message_id", "unknown"))
            return result
        
        # Patch the message_callback method to use our capturing callback
        with patch.object(message_consumer_service, '_message_callback', side_effect=capture_callback):
            # Start the message consumer service in non-blocking mode
            message_consumer_service.start(block=False)
            
            # Simulate an invalid message being received
            self.simulate_message_received(mock_channel, invalid_message_data)
            
            # Stop the service
            message_consumer_service.stop()
        
        # Assert that the message was processed but resulted in None (rejected)
        assert len(results) > 0, "Message was not processed"
        assert results[0] is None, "Invalid message should result in None"
        assert len(rejected_message_ids) > 0, "Invalid message ID should be captured as rejected"
    
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
                "message_id": "test-message-1"
            },
            {
                "content": "Let's meet at the coffee shop at 10:00.",
                "sender": "Me", 
                "recipient": "Colleague",
                "message_id": "test-message-2"
            }
        ]
        
        # Helper lists to track results
        results = []
        message_ids_processed = []
        
        # Define a mock callback to capture results
        def capture_callback(message_data):
            message_ids_processed.append(message_data.get("message_id", "unknown"))
            result = message_consumer_service._process_message(message_data)
            results.append(result)
            return result
        
        # Patch the message_callback method to use our capturing callback
        with patch.object(message_consumer_service, '_message_callback', side_effect=capture_callback):
            # Start the message consumer service in non-blocking mode
            message_consumer_service.start(block=False)
            
            # Simulate multiple messages being received
            for message in messages:
                self.simulate_message_received(mock_channel, message)
            
            # Stop the service
            message_consumer_service.stop()
        
        # Assert that all messages were processed
        assert len(message_ids_processed) == len(messages), "All messages should be processed"
        
        # Assert that all messages produced results with reminders
        assert len(results) == len(messages), "All messages should return results"
        assert all(result is not None for result in results), "All messages should return non-None results"
        assert all(len(result["reminders"]) > 0 for result in results), "All messages should create reminders"
    
    @pytest.mark.integration
    def test_acknowledge_message_success(self, mock_pika_connection, rabbitmq_adapter):
        """
        Test successful message acknowledgment.
        
        This test verifies that the acknowledge_message method correctly calls
        basic_ack on the channel with the proper delivery tag.
        """
        # Unpack mocks
        mock_connection, mock_channel = mock_pika_connection
        
        # Connect the adapter to set up the channel
        rabbitmq_adapter.connect()
        
        # Call acknowledge_message
        message_id = "42"  # This should be converted to int(42)
        result = rabbitmq_adapter.acknowledge_message(message_id)
        
        # Verify the result and method call
        assert result is True, "acknowledge_message should return True on success"
        mock_channel.basic_ack.assert_called_once_with(delivery_tag=42)
    
    @pytest.mark.integration
    def test_acknowledge_message_not_connected(self):
        """
        Test acknowledge_message when not connected to RabbitMQ.
        
        This test verifies that the acknowledge_message method returns False
        when called without first connecting to RabbitMQ.
        """
        # Create adapter without connecting
        adapter = RabbitMQMessageConsumer()
        
        # Call acknowledge_message
        result = adapter.acknowledge_message("42")
        
        # Verify the result
        assert result is False, "acknowledge_message should return False when not connected"
    
    @pytest.mark.integration
    def test_acknowledge_message_exception(self, mock_pika_connection, rabbitmq_adapter):
        """
        Test acknowledge_message when an exception occurs.
        
        This test verifies that acknowledge_message handles exceptions correctly
        and returns False when an error occurs.
        """
        # Unpack mocks
        mock_connection, mock_channel = mock_pika_connection
        
        # Configure mock to raise an exception
        mock_channel.basic_ack.side_effect = Exception("Test exception")
        
        # Connect the adapter
        rabbitmq_adapter.connect()
        
        # Call acknowledge_message
        result = rabbitmq_adapter.acknowledge_message("42")
        
        # Verify the result
        assert result is False, "acknowledge_message should return False on exception"
    
    @pytest.mark.integration
    def test_reject_message_success(self, mock_pika_connection, rabbitmq_adapter):
        """
        Test successful message rejection.
        
        This test verifies that the reject_message method correctly calls
        basic_reject on the channel with the proper delivery tag and requeue flag.
        """
        # Unpack mocks
        mock_connection, mock_channel = mock_pika_connection
        
        # Connect the adapter to set up the channel
        rabbitmq_adapter.connect()
        
        # Test with requeue=False (default)
        result1 = rabbitmq_adapter.reject_message("42")
        
        # Test with requeue=True
        result2 = rabbitmq_adapter.reject_message("43", requeue=True)
        
        # Verify the results and method calls
        assert result1 is True, "reject_message should return True on success"
        assert result2 is True, "reject_message should return True on success"
        
        mock_channel.basic_reject.assert_any_call(delivery_tag=42, requeue=False)
        mock_channel.basic_reject.assert_any_call(delivery_tag=43, requeue=True)
    
    @pytest.mark.integration
    def test_reject_message_not_connected(self):
        """
        Test reject_message when not connected to RabbitMQ.
        
        This test verifies that the reject_message method returns False
        when called without first connecting to RabbitMQ.
        """
        # Create adapter without connecting
        adapter = RabbitMQMessageConsumer()
        
        # Call reject_message
        result = adapter.reject_message("42")
        
        # Verify the result
        assert result is False, "reject_message should return False when not connected"
    
    @pytest.mark.integration
    def test_reject_message_exception(self, mock_pika_connection, rabbitmq_adapter):
        """
        Test reject_message when an exception occurs.
        
        This test verifies that reject_message handles exceptions correctly
        and returns False when an error occurs.
        """
        # Unpack mocks
        mock_connection, mock_channel = mock_pika_connection
        
        # Configure mock to raise an exception
        mock_channel.basic_reject.side_effect = Exception("Test exception")
        
        # Connect the adapter
        rabbitmq_adapter.connect()
        
        # Call reject_message
        result = rabbitmq_adapter.reject_message("42")
        
        # Verify the result
        assert result is False, "reject_message should return False on exception"
    
    @pytest.mark.integration
    def test_connection_exception_handling(self):
        """
        Test exception handling during connection.
        
        This test verifies that the connect method handles exceptions correctly
        and returns False when a connection error occurs.
        """
        # Patch BlockingConnection to raise an exception
        with patch('pika.BlockingConnection', side_effect=Exception("Connection error")):
            # Create adapter and try to connect
            adapter = RabbitMQMessageConsumer()
            result = adapter.connect()
            
            # Verify the result
            assert result is False, "connect should return False on exception"
    
    @pytest.mark.integration
    def test_disconnect_exception_handling(self, mock_pika_connection):
        """
        Test exception handling during disconnection.
        
        This test verifies that the disconnect method handles exceptions correctly
        and returns False when an error occurs during disconnection.
        """
        # Unpack mocks
        mock_connection, mock_channel = mock_pika_connection
        
        # Create adapter and connect
        adapter = RabbitMQMessageConsumer()
        adapter.connect()
        
        # Configure mocks to raise exceptions
        mock_channel.basic_cancel.side_effect = Exception("Cancel error")
        mock_channel.close.side_effect = Exception("Close error")
        mock_connection.return_value.close.side_effect = Exception("Connection close error")
        
        # Call disconnect
        result = adapter.disconnect()
        
        # Verify the result
        assert result is False, "disconnect should return False on exception"
    
    @pytest.mark.integration
    def test_consume_messages_not_connected(self):
        """
        Test consume_messages when not connected to RabbitMQ.
        
        This test verifies that consume_messages handles the case correctly
        when called without first connecting to RabbitMQ.
        """
        # Create adapter without connecting
        adapter = RabbitMQMessageConsumer()
        
        # Define a simple callback
        def dummy_callback(message):
            pass
        
        # Call consume_messages
        # This should log an error but not raise an exception
        adapter.consume_messages("test_queue", dummy_callback)
        
        # We can't easily assert on logged messages, but the test passing
        # indicates that the method handled the error gracefully
    
    @pytest.mark.integration
    def test_consume_messages_exception(self, mock_pika_connection):
        """
        Test consume_messages when an exception occurs.
        
        This test verifies that consume_messages handles exceptions correctly
        and calls disconnect when an error occurs.
        """
        # Unpack mocks
        mock_connection, mock_channel = mock_pika_connection
        
        # Configure mock to raise an exception
        mock_channel.queue_declare.side_effect = Exception("Queue declare error")
        
        # Create adapter and connect
        adapter = RabbitMQMessageConsumer()
        adapter.connect()
        
        # Spy on disconnect to verify it gets called
        with patch.object(adapter, 'disconnect', wraps=adapter.disconnect) as mock_disconnect:
            # Define a simple callback
            def dummy_callback(message):
                pass
            
            # Call consume_messages
            adapter.consume_messages("test_queue", dummy_callback)
            
            # Verify disconnect was called
            mock_disconnect.assert_called_once()
    
    @pytest.mark.integration
    def test_on_message_json_decode_error(self, mock_pika_connection, rabbitmq_adapter):
        """
        Test _on_message handling of JSON decode errors.
        
        This test verifies that the _on_message method correctly handles
        malformed JSON messages and rejects them.
        """
        # Unpack mocks
        mock_connection, mock_channel = mock_pika_connection
        
        # Connect the adapter
        rabbitmq_adapter.connect()
        
        # Setup a callback
        callback_mock = MagicMock()
        rabbitmq_adapter._callback = callback_mock
        
        # Create method with delivery tag
        method = MagicMock()
        method.delivery_tag = 42
        
        # Create properties
        properties = MagicMock()
        
        # Create invalid JSON body
        body = b'{ this is not valid JSON }'
        
        # Call _on_message
        rabbitmq_adapter._on_message(mock_channel, method, properties, body)
        
        # Verify behavior
        callback_mock.assert_not_called()  # Callback should not be called for invalid JSON
        mock_channel.basic_reject.assert_called_once_with(delivery_tag=42, requeue=False)
    
    @pytest.mark.integration
    def test_on_message_exception(self, mock_pika_connection, rabbitmq_adapter):
        """
        Test _on_message handling of general exceptions.
        
        This test verifies that the _on_message method correctly handles
        exceptions during message processing and requeues the message.
        """
        # Unpack mocks
        mock_connection, mock_channel = mock_pika_connection
        
        # Connect the adapter
        rabbitmq_adapter.connect()
        
        # Setup a callback that raises an exception
        callback_mock = MagicMock(side_effect=Exception("Processing error"))
        rabbitmq_adapter._callback = callback_mock
        
        # Create method with delivery tag
        method = MagicMock()
        method.delivery_tag = 42
        
        # Create properties
        properties = MagicMock()
        
        # Create valid JSON body
        body = json.dumps({"test": "data"}).encode('utf-8')
        
        # Call _on_message
        rabbitmq_adapter._on_message(mock_channel, method, properties, body)
        
        # Verify behavior
        callback_mock.assert_called_once()  # Callback should be called
        mock_channel.basic_reject.assert_called_once_with(delivery_tag=42, requeue=True)