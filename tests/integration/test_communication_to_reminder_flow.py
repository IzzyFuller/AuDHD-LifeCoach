"""
Integration test for the communication to reminder flow.

This test verifies the core domain flow:
1. A communication is created with commitments
2. The communication processor extracts these commitments
3. Reminders are created for these commitments

This test uses the actual transformer pipeline rather than mocks.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.core.services.communication_processor import CommunicationProcessor
from audhd_lifecoach.adapters.ai.spacy_commitment_identifier import SpaCyCommitmentIdentifier
from audhd_lifecoach.application.use_cases.process_communication import ProcessCommunication
from audhd_lifecoach.application.dtos.communication_dto import CommunicationRequestDTO


class TestCommunicationToReminderFlow:
    """Integration test for the communication to reminder flow."""

    @pytest.fixture
    def commitment_identifier(self):
        """Create a real commitment identifier using the transformer pipeline."""
        return SpaCyCommitmentIdentifier()

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
    @pytest.mark.parametrize(
        "content, expected_reminders, expected_what",
        [
            # Test case: No commitments
            ("The weather is nice today", 0, []),

            # Test case: Single commitment
            ("I'll call you tomorrow at 3:30 PM. Bob and Doug are coming too.", 1, ["call"]),

            # Test case: Multiple commitments
            ("I'll call you tomorrow at 3:30 PM and we will meet on Friday at 10:00 AM.", 2, ["call", "meet"]),
        ],
    )
    def test_process_communication(
        self, process_communication_use_case, mock_message_publisher, content, expected_reminders, expected_what
    ):
        """Test processing a communication with varying commitments."""
        # Arrange
        communication_dto = CommunicationRequestDTO(
            content=content,
            sender="Alice",
            recipient="Bob",
            timestamp=datetime.now()
        )

        # Act
        response = process_communication_use_case.execute(communication_dto)

        # Assert
        # Verify the processing was successful
        assert response.processed is True

        # Verify the number of reminders created
        assert len(response.reminders) == expected_reminders, f"Expected {expected_reminders} reminders"

        # Verify the details of each reminder
        for i, reminder in enumerate(response.reminders):
            assert expected_what[i] in reminder.commitment_what.lower(), f"Expected '{expected_what[i]}' in reminder's what field"
            assert reminder.when > datetime.now(), "The reminder's time should be in the future"

        # Verify the message was published
        mock_message_publisher.publish_message.assert_called_once()
        args, kwargs = mock_message_publisher.publish_message.call_args

        # Check message contents
        message = kwargs["message"]
        assert "original_communication" in message
        assert message["original_communication"]["content"] == communication_dto.content
        assert len(message["reminders"]) == expected_reminders, f"Expected {expected_reminders} reminders in the published message"