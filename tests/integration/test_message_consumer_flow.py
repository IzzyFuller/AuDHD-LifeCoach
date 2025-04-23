"""
Integration test for the message consumer flow.

This test verifies the full flow via the message consumer:
1. A communication message is received from a message queue
2. The message is processed to extract commitments
3. Reminders are created for these commitments

This test uses the actual transformer pipeline rather than mocks.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from audhd_lifecoach.application.dtos.communication_dto import CommunicationRequestDTO
from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.adapters.ai.hugging_face_onyx_transformer_commitment_identifier import HuggingFaceONYXTransformerCommitmentIdentifier
from audhd_lifecoach.core.services.communication_processor import CommunicationProcessor
from audhd_lifecoach.application.interfaces.message_consumer_interface import MessageConsumerInterface


class TestMessageConsumerFlow:
    """Integration test for the message consumer flow."""
    
    @pytest.fixture
    def mock_message_consumer(self):
        """Create a mock message consumer that implements the interface."""
        class MockConsumer:
            def __init__(self):
                self.connected = False
                self.callback = None
                self.queue_name = None
                self.messages_processed = []
                self.acknowledged_messages = []
                self.rejected_messages = []
            
            def connect(self) -> bool:
                self.connected = True
                return True
                
            def disconnect(self) -> bool:
                self.connected = False
                return True
            
            def consume_messages(self, queue_name, callback):
                self.queue_name = queue_name
                self.callback = callback
            
            def acknowledge_message(self, message_id: str) -> bool:
                self.acknowledged_messages.append(message_id)
                return True
            
            def reject_message(self, message_id: str, requeue: bool = False) -> bool:
                self.rejected_messages.append((message_id, requeue))
                return True
                
            # Helper method for tests to simulate receiving a message
            def simulate_message_received(self, message_data, message_id=None):
                # Ensure we're marked as connected when simulating message processing
                self.connected = True
                
                # Use message_id from data if not provided explicitly
                if message_id is None and "message_id" in message_data:
                    message_id = message_data["message_id"]
                
                if self.callback:
                    if message_id:
                        self.messages_processed.append(message_id)
                    return self.callback(message_data)
                return None
        
        return MockConsumer()
    
    @pytest.fixture
    def message_consumer_service(self):
        """
        This fixture should return the actual MessageConsumerService implementation.
        
        For now, it will just raise NotImplementedError to make the test fail,
        indicating we need to implement it.
        """
        raise NotImplementedError("MessageConsumerService not implemented yet")
    
    @pytest.mark.integration
    def test_basic_message_flow_with_one_commitment(self, mock_message_consumer):
        """
        Test the basic flow through the message consumer from message to reminder.
        
        This test simulates receiving a message with one time-based commitment
        and verifies that proper Commitments and Reminders are created.
        """
        # Arrange
        # 1. Create a communication message
        message_data = {
            "content": "I'll call you at 15:30 tomorrow.",
            "sender": "Me",
            "recipient": "Friend",
            "message_id": "test-message-1"
        }
        
        # 2. Create the necessary services for our message consumer service
        commitment_identifier = HuggingFaceONYXTransformerCommitmentIdentifier()
        communication_processor = CommunicationProcessor(commitment_identifier)
        
        # 3. Create our message consumer service (this will be implemented later)
        with patch("audhd_lifecoach.adapters.messaging.rabbitmq_message_consumer.RabbitMQMessageConsumer", 
                  return_value=mock_message_consumer):
            
            # This should be replaced with the actual import once implemented
            from audhd_lifecoach.application.services.message_consumer_service import MessageConsumerService
            
            # Initialize the message consumer service
            message_consumer_service = MessageConsumerService(
                message_consumer=mock_message_consumer,
                communication_processor=communication_processor
            )
            
            # Act
            # 4. Start the message consumer service (non-blocking for testing)
            message_consumer_service.start(block=False)
            
            # 5. Simulate receiving a message
            result = mock_message_consumer.simulate_message_received(message_data)
            
            # Assert
            # 6. Verify that the message was processed
            assert mock_message_consumer.connected, "Message consumer should be connected"
            assert len(mock_message_consumer.messages_processed) == 1, "One message should be processed"
            assert len(mock_message_consumer.acknowledged_messages) == 1, "One message should be acknowledged"
            
            # 7. Verify that reminders were created
            assert result is not None, "Message processing should return a result"
            reminders = result["reminders"]
            assert len(reminders) > 0, "No reminders were created from the communication"
            
            # 8. Get the first reminder and verify its details
            reminder = reminders[0]
            
            # 9. Verify reminder commitment details
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
            
            # 10. Verify reminder time and acknowledgment
            reminder_when = datetime.fromisoformat(reminder["when"])
            assert reminder_when < commitment_start, "Reminder time should be before commitment start time"
            assert reminder["acknowledged"] is False, "New reminder should not be acknowledged"
            
            # Clean up
            message_consumer_service.stop()
    
    @pytest.mark.integration
    def test_error_handling_for_invalid_message(self, mock_message_consumer):
        """
        Test that the message consumer properly handles invalid messages.
        
        This test ensures that when an invalid message is received,
        it's rejected properly and doesn't cause the service to crash.
        """
        # Arrange
        # 1. Create an invalid communication message (missing required fields)
        invalid_message_data = {
            "content": "This message is missing sender and recipient",
            "message_id": "test-invalid-message"
        }
        
        # 2. Create the necessary services for our message consumer service
        commitment_identifier = HuggingFaceONYXTransformerCommitmentIdentifier()
        communication_processor = CommunicationProcessor(commitment_identifier)
        
        # 3. Create our message consumer service (this will be implemented later)
        with patch("audhd_lifecoach.adapters.messaging.rabbitmq_message_consumer.RabbitMQMessageConsumer", 
                  return_value=mock_message_consumer):
            
            # This should be replaced with the actual import once implemented
            from audhd_lifecoach.application.services.message_consumer_service import MessageConsumerService
            
            # Initialize the message consumer service
            message_consumer_service = MessageConsumerService(
                message_consumer=mock_message_consumer,
                communication_processor=communication_processor
            )
            
            # Act
            # 4. Start the message consumer service (non-blocking for testing)
            message_consumer_service.start(block=False)
            
            # 5. Simulate receiving an invalid message
            result = mock_message_consumer.simulate_message_received(invalid_message_data)
            
            # Assert
            # 6. Verify that the message was rejected
            assert mock_message_consumer.connected, "Message consumer should be connected"
            assert len(mock_message_consumer.messages_processed) == 1, "One message should be processed"
            assert len(mock_message_consumer.acknowledged_messages) == 0, "Invalid message should not be acknowledged"
            assert len(mock_message_consumer.rejected_messages) == 1, "Invalid message should be rejected"
            
            # 7. Verify that no reminders were created for the invalid message
            assert result is None or "error" in result, "Should return None or error for invalid message"
            
            # Clean up
            message_consumer_service.stop()
    
    @pytest.mark.integration
    def test_multiple_messages_processing(self, mock_message_consumer):
        """
        Test that the message consumer can process multiple messages.
        """
        # Arrange
        # 1. Create multiple communication messages
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
        
        # 2. Create the necessary services for our message consumer service
        commitment_identifier = HuggingFaceONYXTransformerCommitmentIdentifier()
        communication_processor = CommunicationProcessor(commitment_identifier)
        
        # 3. Create our message consumer service (this will be implemented later)
        with patch("audhd_lifecoach.adapters.messaging.rabbitmq_message_consumer.RabbitMQMessageConsumer", 
                  return_value=mock_message_consumer):
            
            # This should be replaced with the actual import once implemented
            from audhd_lifecoach.application.services.message_consumer_service import MessageConsumerService
            
            # Initialize the message consumer service
            message_consumer_service = MessageConsumerService(
                message_consumer=mock_message_consumer,
                communication_processor=communication_processor
            )
            
            # Act
            # 4. Start the message consumer service (non-blocking for testing)
            message_consumer_service.start(block=False)
            
            # 5. Simulate receiving multiple messages
            results = []
            for message in messages:
                result = mock_message_consumer.simulate_message_received(message)
                results.append(result)
            
            # Assert
            # 6. Verify that all messages were processed
            assert mock_message_consumer.connected, "Message consumer should be connected"
            assert len(mock_message_consumer.messages_processed) == len(messages), "All messages should be processed"
            assert len(mock_message_consumer.acknowledged_messages) == len(messages), "All messages should be acknowledged"
            
            # 7. Verify that reminders were created for all messages
            assert all(result is not None for result in results), "All messages should return results"
            assert all(len(result["reminders"]) > 0 for result in results), "All messages should create reminders"
            
            # Clean up
            message_consumer_service.stop()