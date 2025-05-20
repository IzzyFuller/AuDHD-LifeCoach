"""
Integration test for the communication to reminder flow.

This test verifies the core domain flow:
1. A communication is created with commitments
2. The communication processor extracts these commitments
3. Reminders are created for these commitments

This test uses the actual transformer pipeline rather than mocks.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.core.services.communication_processor import CommunicationProcessor
from audhd_lifecoach.adapters.ai.hugging_face_onyx_transformer_commitment_identifier import HuggingFaceONYXTransformerCommitmentIdentifier
from audhd_lifecoach.application.use_cases.process_communication import ProcessCommunication
from audhd_lifecoach.application.dtos.communication_dto import CommunicationRequestDTO


class TestCommunicationToReminderFlow:
    """Integration test for the communication to reminder flow."""
    
    @pytest.fixture
    def commitment_identifier(self):
        """Create a real commitment identifier using the transformer pipeline."""
        return HuggingFaceONYXTransformerCommitmentIdentifier()
    
    @pytest.fixture
    def communication_processor(self, commitment_identifier):
        """Create a real communication processor with the transformer pipeline."""
        return CommunicationProcessor(commitment_identifier)

    @pytest.fixture
    def mock_message_publisher(self):
        """Create a mock message publisher for the tests."""
        publisher = MagicMock()
        publisher.connect.return_value = True
        publisher.publish_message.return_value = True
        return publisher
    
    @pytest.fixture
    def process_communication_use_case(self, communication_processor, mock_message_publisher):
        """Create the process communication use case with the mock publisher."""
        return ProcessCommunication(
            communication_processor=communication_processor,
            message_publisher=mock_message_publisher,
            exchange_name='test-exchange'
        )
    
    @pytest.mark.integration
    def test_process_communication_with_commitment(self, process_communication_use_case, mock_message_publisher):
        """Test processing a communication with a commitment."""
        # Arrange
        # Create a communication DTO with a commitment
        communication_dto = CommunicationRequestDTO(
            content="I'll call you tomorrow at 3:30 PM. Bob and Doug are coming too.",
            sender="Alice",
            recipient="Bob",
            timestamp=datetime.now()
        )
        
        # Act
        # Process the communication
        response = process_communication_use_case.execute(communication_dto)
        
        # Assert
        # Verify the processing was successful
        assert response.processed is True
        
        # Verify reminders were created
        assert len(response.reminders) > 0, "No reminders were created"
        
        # Verify the reminder contains the correct information
        reminder = response.reminders[0]
        assert "commitment" in reminder.message.lower(), "Expected the word 'commitment' in the reminder message"
        assert reminder.when > datetime.now()
        
        # Verify the commitment information is present
        assert reminder.commitment_what is not None
        assert reminder.commitment_what.lower() == "call"  # Verify the what field directly
        
        # Verify the message was published
        mock_message_publisher.publish_message.assert_called_once()
        args, kwargs = mock_message_publisher.publish_message.call_args
        
        # Check exchange and routing key
        assert kwargs["exchange"] == "test-exchange"
        assert kwargs["routing_key"] == "communication.processed"
        
        # Check message contents
        message = kwargs["message"]
        assert "original_communication" in message
        assert message["original_communication"]["content"] == communication_dto.content
        assert len(message["reminders"]) > 0
    
    @pytest.mark.integration
    def test_process_communication_no_commitment(self, process_communication_use_case, mock_message_publisher):
        """Test processing a communication without any commitments."""
        # Arrange
        # Create a communication DTO without any commitments
        communication_dto = CommunicationRequestDTO(
            content="The weather is nice today",
            sender="Alice",
            recipient="Bob",
            timestamp=datetime.now()
        )
        
        # Act
        # Process the communication
        response = process_communication_use_case.execute(communication_dto)
        
        # Assert
        # Verify the processing was successful
        assert response.processed is True
        
        # Verify no reminders were created
        assert len(response.reminders) == 0, "Reminders were created when none were expected"
        
        # Verify the message was published even with no commitments
        mock_message_publisher.publish_message.assert_called_once()
        args, kwargs = mock_message_publisher.publish_message.call_args
        
        # Check message contents
        message = kwargs["message"]
        assert "original_communication" in message
        assert message["processed"] is True
        assert len(message["reminders"]) == 0

    @pytest.mark.integration
    def test_process_communication_with_multiple_commitments(self, process_communication_use_case, mock_message_publisher):
        """Test processing a communication with multiple commitments."""
        # Arrange
        # Create a communication DTO with multiple commitments
        communication_dto = CommunicationRequestDTO(
            content="I'll call you tomorrow at 3:30 PM and we can meet on Friday at 10:00 AM.",
            sender="Alice",
            recipient="Bob",
            timestamp=datetime.now()
        )

        # Act
        # Process the communication
        response = process_communication_use_case.execute(communication_dto)

        # Assert
        # Verify the processing was successful
        assert response.processed is True

        # Verify multiple reminders were created
        assert len(response.reminders) == 2, "Expected two reminders to be created"

        # Verify the details of the first reminder
        first_reminder = response.reminders[0]
        assert "call" in first_reminder.commitment_what.lower(), "Expected 'call' in the first reminder's what field"
        assert first_reminder.when > datetime.now(), "The first reminder's time should be in the future"

        # Verify the details of the second reminder
        second_reminder = response.reminders[1]
        assert "meet" in second_reminder.commitment_what.lower(), "Expected 'meet' in the second reminder's what field"
        assert second_reminder.when > datetime.now(), "The second reminder's time should be in the future"

        # Verify the message was published
        mock_message_publisher.publish_message.assert_called_once()
        args, kwargs = mock_message_publisher.publish_message.call_args

        # Check message contents
        message = kwargs["message"]
        assert "original_communication" in message
        assert message["original_communication"]["content"] == communication_dto.content
        assert len(message["reminders"]) == 2, "Expected two reminders in the published message"