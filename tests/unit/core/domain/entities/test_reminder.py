import pytest
from datetime import datetime, timedelta
from audhd_lifecoach.core.domain.entities.reminder import Reminder
from audhd_lifecoach.core.domain.entities.commitment import Commitment


class TestReminder:
    def test_reminder_creation(self):
        """Test that a reminder can be created with basic attributes."""
        # Arrange
        when = datetime(2025, 4, 20, 15, 0)  # April 20, 2025 at 15:00
        message = "Time to leave for Friend's house"
        
        # Create a test commitment for the reminder
        commitment = Commitment(
            start_time=datetime(2025, 4, 20, 15, 30),
            end_time=datetime(2025, 4, 20, 16, 30),
            who="Friend",
            what="Meeting",
            where="Office"
        )
        
        # Act
        reminder = Reminder(
            when=when,
            message=message,
            commitment=commitment
        )
        
        # Assert
        assert reminder.when == when
        assert reminder.message == message
        assert reminder.commitment == commitment
        assert not reminder.acknowledged
        
    def test_reminder_with_defaults(self):
        """Test that a reminder can be created with default values."""
        # Arrange
        when = datetime(2025, 4, 20, 15, 0)  # April 20, 2025 at 15:00
        message = "Reminder for appointment"
        
        # Create a test commitment for the reminder
        commitment = Commitment(
            start_time=datetime(2025, 4, 20, 15, 30),
            end_time=datetime(2025, 4, 20, 16, 30),
            who="Friend",
            what="Meeting",
            where="Office"
        )
        
        # Act
        reminder = Reminder(
            when=when,
            message=message,
            commitment=commitment
        )
        
        # Assert
        assert reminder.when == when
        assert reminder.message == message
        assert reminder.commitment == commitment
        assert not reminder.acknowledged
        
    def test_reminder_from_commitment(self):
        """Test that a reminder can be created from a commitment."""
        # Arrange
        commitment = Commitment(
            start_time=datetime(2025, 4, 20, 15, 30),  # 3:30 PM
            end_time=datetime(2025, 4, 20, 16, 30),    # 4:30 PM
            who="Friend",
            what="Give a ride",
            where="Friend's house",
            estimated_travel_time=timedelta(minutes=25),
            estimated_prep_time=timedelta(minutes=10)
        )
        
        # Act
        reminder = Reminder.from_commitment(commitment)
        
        # Assert
        # Should remind 30 minutes before the commitment start time (default lead time)
        expected_reminder_time = datetime(2025, 4, 20, 15, 0)  # 3:30 PM - 30min
        assert reminder.when == expected_reminder_time
        assert commitment.who in reminder.message
        assert commitment.what in reminder.message or "commitment" in reminder.message.lower()
        assert reminder.commitment == commitment
        
    def test_acknowledge_reminder(self):
        """Test that a reminder can be acknowledged."""
        # Arrange
        commitment = Commitment(
            start_time=datetime(2025, 4, 20, 15, 30),
            end_time=datetime(2025, 4, 20, 16, 30),
            who="Friend",
            what="Meeting",
            where="Office"
        )
        
        reminder = Reminder(
            when=datetime(2025, 4, 20, 15, 0),
            message="Time to leave",
            commitment=commitment
        )
        assert not reminder.acknowledged  # Initially not acknowledged
        
        # Act
        reminder.acknowledge()
        
        # Assert
        assert reminder.acknowledged
        
    def test_snooze_reminder(self):
        """Test that a reminder can be snoozed."""
        # Arrange
        original_time = datetime(2025, 4, 20, 15, 0)
        
        commitment = Commitment(
            start_time=datetime(2025, 4, 20, 15, 30),
            end_time=datetime(2025, 4, 20, 16, 30),
            who="Friend",
            what="Meeting",
            where="Office"
        )
        
        reminder = Reminder(
            when=original_time,
            message="Time to leave",
            commitment=commitment
        )
        snooze_duration = timedelta(minutes=10)
        
        # Act
        reminder.snooze(snooze_duration)
        
        # Assert
        assert reminder.when == original_time + snooze_duration
        assert not reminder.acknowledged  # Snoozing doesn't acknowledge
        
    def test_missing_required_arguments(self):
        """Test that creating a reminder without required arguments raises an error."""
        # Missing 'when'
        with pytest.raises(TypeError):
            commitment = Commitment(
                start_time=datetime(2025, 4, 20, 15, 30),
                end_time=datetime(2025, 4, 20, 16, 30),
                who="Friend", what="Meeting", where="Office"
            )
            Reminder(message="Reminder", commitment=commitment)
        
        # Missing 'message'
        with pytest.raises(TypeError):
            commitment = Commitment(
                start_time=datetime(2025, 4, 20, 15, 30),
                end_time=datetime(2025, 4, 20, 16, 30),
                who="Friend", what="Meeting", where="Office"
            )
            Reminder(when=datetime.now(), commitment=commitment)
            
        # Missing 'commitment'
        with pytest.raises(TypeError):
            Reminder(when=datetime.now(), message="Reminder")
            
    def test_is_due(self):
        """Test that a reminder can determine if it's due."""
        # Arrange
        now = datetime.now()
        past_time = now - timedelta(hours=2)  # Due 2 hours ago
        future_time = now + timedelta(hours=2)  # Due 2 hours from now
        
        commitment = Commitment(
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=4),
            who="Friend", what="Meeting", where="Office"
        )
        
        past_reminder = Reminder(when=past_time, message="Past reminder", commitment=commitment)
        future_reminder = Reminder(when=future_time, message="Future reminder", commitment=commitment)
        
        # Act & Assert
        assert past_reminder.is_due()
        assert not future_reminder.is_due()
        
    def test_str_representation(self):
        """Test the string representation of a reminder."""
        # Arrange
        when = datetime(2025, 4, 20, 15, 0)
        message = "Time to leave for Friend's house"
        
        commitment = Commitment(
            start_time=datetime(2025, 4, 20, 15, 30),
            end_time=datetime(2025, 4, 20, 16, 30),
            who="Friend",
            what="Meeting",
            where="Office"
        )
        
        reminder = Reminder(
            when=when,
            message=message,
            commitment=commitment
        )
        
        # Act
        str_repr = str(reminder)
        
        # Assert
        assert message in str_repr
        assert "15:00" in str_repr