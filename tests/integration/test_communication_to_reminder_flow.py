"""
Integration test for the full flow from Communication to Commitment to Reminder.

This test verifies the end-to-end processing of communications in the system:
1. A communication is received
2. Commitments are extracted from it
3. Reminders are created for these commitments

This test uses the actual transformer pipeline rather than mocks.
"""
import pytest
from datetime import datetime

from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.core.domain.entities.commitment import Commitment
from audhd_lifecoach.core.domain.entities.reminder import Reminder
from audhd_lifecoach.adapters.ai.hugging_face_onyx_transformer_commitment_identifier import HuggingFaceONYXTransformerCommitmentIdentifier


class TestCommunicationToReminderFlow:
    """Integration test for the full flow from Communication to Reminder."""
    
    @pytest.mark.integration
    def test_basic_flow_with_one_commitment(self):
        """
        Test the basic flow from Communication to Commitment to Reminder.
        
        This test uses a simple communication with one time-based commitment
        mentioned, and verifies that a proper Commitment and Reminder are created.
        """
        # Arrange
        # 1. Create a communication with a commitment
        communication = Communication(
            timestamp=datetime.now(),
            content="I'll call you at 15:30 tomorrow.",
            sender="Me",
            recipient="Friend"
        )
        
        # 2. Create the commitment identifier
        identifier = HuggingFaceONYXTransformerCommitmentIdentifier()
        
        # Act
        # 3. Process the communication to extract commitments
        commitments = identifier.identify_commitments(communication)
        
        # 4. Create reminders from the commitments
        reminders = []
        for commitment in commitments:
            reminder = Reminder.from_commitment(commitment)
            reminders.append(reminder)
        
        # Assert
        # 5. Verify that commitments were identified
        assert len(commitments) > 0, "No commitments were identified from the communication"
        
        # 6. Get the first commitment
        commitment = commitments[0]
        
        # 7. Verify commitment details
        assert commitment.who == "Friend"
        assert commitment.what == "Meeting or appointment" or "call" in commitment.what.lower()
        # Using 15:30 as the expected time from our message
        expected_hour = 15
        expected_minute = 30
        assert commitment.when.hour == expected_hour
        assert commitment.when.minute == expected_minute
        
        # 8. Verify that reminders were created
        assert len(reminders) > 0, "No reminders were created from the commitments"
        
        # 9. Get the first reminder
        reminder = reminders[0]
        
        # 10. Verify reminder details
        assert not reminder.acknowledged
        assert reminder.commitment == commitment
        # Reminder time should be before the commitment time
        assert reminder.when < commitment.when
        # Reminder should include relevant info
        assert "Friend" in reminder.message