"""
Integration test for the full flow from Communication to Commitment to Reminder.

This test verifies the end-to-end processing of communications in the system:
1. A communication is received
2. Commitments are extracted from it
3. Reminders are created for these commitments

This test uses the actual transformer pipeline rather than mocks.
"""
import pytest
from datetime import datetime, timedelta

from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.core.domain.entities.commitment import Commitment
from audhd_lifecoach.core.domain.entities.reminder import Reminder
from audhd_lifecoach.adapters.ai.hugging_face_onyx_transformer_commitment_identifier import HuggingFaceONYXTransformerCommitmentIdentifier
from audhd_lifecoach.core.services.communication_processor import CommunicationProcessor


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
        
        # 2. Create the commitment identifier and processor
        identifier = HuggingFaceONYXTransformerCommitmentIdentifier()
        processor = CommunicationProcessor(identifier)
        
        # Act
        # 3. Process the communication to create reminders
        reminders = processor.process_communication(communication)
        
        # Assert
        # 4. Verify that reminders were created
        assert len(reminders) > 0, "No reminders were created from the communication"
        
        # 5. Get the first reminder and its associated commitment
        reminder = reminders[0]
        commitment = reminder.commitment
        
        # 6. Verify commitment details
        assert commitment is not None, "Reminder has no associated commitment"
        assert commitment.who == "Friend"
        assert commitment.what == "Meeting or appointment" or "call" in commitment.what.lower()
        
        # Using 15:30 as the expected time from our message
        expected_hour = 15
        expected_minute = 30
        assert commitment.when.hour == expected_hour
        assert commitment.when.minute == expected_minute
        
        # 7. Verify reminder details
        assert not reminder.acknowledged
        # Reminder time should be before the commitment time
        assert reminder.when < commitment.when
        # Reminder should include relevant info
        assert "Friend" in reminder.message
    
    @pytest.mark.integration
    @pytest.mark.parametrize("content, core_name, expected_activity, time_range", [
        (
            "I'll meet with Dr. Smith tomorrow morning for my checkup.", 
            "Smith", 
            ["checkup", "appointment", "meet"], 
            (7, 12)  # Morning hours range
        ),
        (
            "I promised Sarah I would attend her recital this evening.", 
            "Sarah", 
            ["recital", "attend", "event"], 
            (17, 22)  # Evening hours range
        ),
        (
            "I need to submit my report to Manager Johnson by Friday.", 
            "Johnson", 
            ["report", "submit"], 
            None  # No specific time range, just checking it sets a time
        )
    ])
    def test_time_references(self, content, core_name, expected_activity, time_range):
        """
        Parameterized test for different time reference formats.
        
        Tests various time formats like morning, evening, specific days, etc.
        and verifies that appropriate times are assigned to commitments.
        
        Args:
            content: The message content containing the commitment
            core_name: The core person name expected to be identified (without titles)
            expected_activity: List of possible activities that might be identified
            time_range: Expected time range (min_hour, max_hour) or None if just checking for a valid time
        """
        # Arrange
        today = datetime.now().date()
        
        communication = Communication(
            timestamp=datetime.now(),
            content=content,
            sender="Me",
            recipient="Calendar"
        )
        
        # Create the commitment identifier and processor
        identifier = HuggingFaceONYXTransformerCommitmentIdentifier()
        processor = CommunicationProcessor(identifier)
        
        # Act
        reminders = processor.process_communication(communication)
        
        # Assert
        assert len(reminders) > 0, "No reminders were created from the communication"
        
        # Get the first reminder and its associated commitment
        reminder = reminders[0]
        commitment = reminder.commitment
        
        # Verify commitment details
        assert commitment is not None, "Reminder has no associated commitment"
        
        # Check who field - now only requiring the core name without title
        assert core_name in commitment.who, f"Expected '{core_name}' in who field, got: {commitment.who}"
        
        # Check what field - should match at least one of the expected activities
        assert any(activity in commitment.what.lower() for activity in expected_activity), \
            f"Expected one of {expected_activity} in what field, got: {commitment.what}"
        
        # Check time references
        if time_range:
            min_hour, max_hour = time_range
            assert min_hour <= commitment.when.hour <= max_hour, \
                f"Expected hour between {min_hour}-{max_hour}, got {commitment.when.hour}"
        else:
            # If no specific time range, just ensure it's a valid datetime
            assert commitment.when > datetime.now(), "Expected future datetime for commitment"
            
            # For day references like "Friday", check it's within the next week
            days_difference = (commitment.when.date() - today).days
            assert 0 <= days_difference <= 7, f"Expected commitment within the next week, got {days_difference} days from now"
        
        # Verify reminder details
        assert not reminder.acknowledged
        assert reminder.when < commitment.when
        # Also update the reminder message check to look for core name only
        assert core_name in reminder.message

    @pytest.mark.integration
    def test_complex_person_extraction(self):
        """
        Test extraction of different person references.
        
        This test verifies that the system can extract various formats of person references,
        focusing on core names rather than titles.
        """
        # Arrange
        communication = Communication(
            timestamp=datetime.now(),
            content="I need to discuss the project with Director Maria Rodriguez and the team lead, Mr. James Smith, next Monday at 10 AM.",
            sender="Me",
            recipient="Calendar"
        )
        
        # Create the commitment identifier and processor
        identifier = HuggingFaceONYXTransformerCommitmentIdentifier()
        processor = CommunicationProcessor(identifier)
        
        # Act
        reminders = processor.process_communication(communication)
        
        # Assert
        assert len(reminders) > 0, "No reminders were created from the communication"
        
        # Get the first reminder and its associated commitment
        reminder = reminders[0]
        commitment = reminder.commitment
        
        # Verify commitment details
        assert commitment is not None, "Reminder has no associated commitment"
        
        # Check for core person entities in the who field
        who_field = commitment.who
        # Now we're checking for core names without requiring titles
        assert any(name in who_field for name in ["Maria", "Rodriguez", "James", "Smith"]), \
            f"Expected core person name in who field, got: {who_field}"
        
        assert "project" in commitment.what.lower() or "meeting" in commitment.what.lower() or "discuss" in commitment.what.lower()
        
        # Should be next Monday at 10 AM
        assert commitment.when.hour == 10, f"Expected hour 10, got {commitment.when.hour}"
        assert commitment.when.minute == 0, f"Expected minute 0, got {commitment.when.minute}"
        
        # Verify reminder details
        assert not reminder.acknowledged
        assert reminder.when < commitment.when