"""
Unit tests for the ProcessCommunication use case with publishing capability.

This test module validates that the ProcessCommunication use case correctly
processes communications and publishes the results.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from audhd_lifecoach.application.dtos.communication_dto import CommunicationRequestDTO, CommunicationResponseDTO
from audhd_lifecoach.application.interfaces.message_publisher_interface import MessagePublisherInterface
from audhd_lifecoach.application.use_cases.process_communication import ProcessCommunication
from audhd_lifecoach.core.domain.entities.commitment import Commitment
from audhd_lifecoach.core.domain.entities.reminder import Reminder


class TestProcessCommunicationPublishing:
    """Test case for the ProcessCommunication use case with publishing capability."""
    
    @pytest.fixture
    def mock_communication_processor(self):
        """Create a mock communication processor."""
        processor = MagicMock()
        
        # Mock the processing method to return some test reminders
        test_reminder = Reminder(
            message="Call Bob tomorrow",
            when=datetime(2025, 4, 25, 15, 30),
            acknowledged=False,
            commitment=Commitment(
                what="Call Bob",
                who="Bob",
                start_time=datetime(2025, 4, 25, 15, 30),
                end_time=datetime(2025, 4, 25, 16, 0),
                where="Phone"
            )
        )
        processor.process_communication.return_value = [test_reminder]
        
        return processor
    
    @pytest.fixture
    def mock_message_publisher(self):
        """Create a mock message publisher."""
        publisher = MagicMock()
        publisher.publish_message.return_value = True
        return publisher
    
    @pytest.fixture
    def communication_dto(self):
        """Create a test communication DTO."""
        return CommunicationRequestDTO(
            content="I'll call Bob tomorrow at 3:30 PM",
            sender="Alice",
            recipient="Bob",
            timestamp=datetime(2025, 4, 24, 10, 0)
        )
    
    def test_execute_with_publishing(self, mock_communication_processor, mock_message_publisher, communication_dto):
        """Test that the use case processes and publishes results."""
        # Arrange
        use_case = ProcessCommunication(
            communication_processor=mock_communication_processor,
            message_publisher=mock_message_publisher,
            exchange_name="test-exchange"
        )
        
        # Act
        response = use_case.execute(communication_dto)
        
        # Assert
        # 1. Verify the communication was processed
        mock_communication_processor.process_communication.assert_called_once()
        assert response.processed is True
        assert len(response.reminders) == 1
        
        # 2. Verify the results were published
        mock_message_publisher.publish_message.assert_called_once()
        args, kwargs = mock_message_publisher.publish_message.call_args
        
        # Check exchange and routing key
        assert kwargs["exchange"] == "test-exchange"
        assert kwargs["routing_key"] == "communication.processed"
        
        # Check message contents
        message = kwargs["message"]
        assert "original_communication" in message
        assert message["original_communication"]["content"] == communication_dto.content
        assert message["original_communication"]["sender"] == communication_dto.sender
        assert message["original_communication"]["recipient"] == communication_dto.recipient
        assert message["processed"] is True
        assert len(message["reminders"]) == 1
    
    def test_execute_with_publisher_failure(self, mock_communication_processor, mock_message_publisher, communication_dto):
        """Test that the use case handles publishing failures gracefully."""
        # Arrange
        mock_message_publisher.publish_message.return_value = False  # Simulate publishing failure
        
        use_case = ProcessCommunication(
            communication_processor=mock_communication_processor,
            message_publisher=mock_message_publisher,
            exchange_name="test-exchange"
        )
        
        # Act
        response = use_case.execute(communication_dto)
        
        # Assert
        # Verify the use case completes successfully despite publishing failure
        assert response.processed is True
        assert len(response.reminders) == 1
    
    def test_execute_with_publisher_exception(self, mock_communication_processor, mock_message_publisher, communication_dto):
        """Test that the use case handles publishing exceptions gracefully."""
        # Arrange
        mock_message_publisher.publish_message.side_effect = Exception("Publishing error")
        
        use_case = ProcessCommunication(
            communication_processor=mock_communication_processor,
            message_publisher=mock_message_publisher,
            exchange_name="test-exchange"
        )
        
        # Act
        response = use_case.execute(communication_dto)
        
        # Assert
        # Verify the use case completes successfully despite publishing exception
        assert response.processed is True
        assert len(response.reminders) == 1