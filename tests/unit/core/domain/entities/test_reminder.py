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
        priority = "High"
        
        # Act
        reminder = Reminder(
            when=when,
            message=message,
            priority=priority
        )
        
        # Assert
        assert reminder.when == when
        assert reminder.message == message
        assert reminder.priority == priority
        assert not reminder.acknowledged
        
    def test_reminder_with_defaults(self):
        """Test that a reminder can be created with default values."""
        # Arrange
        when = datetime(2025, 4, 20, 15, 0)  # April 20, 2025 at 15:00
        message = "Reminder for appointment"
        
        # Act
        reminder = Reminder(
            when=when,
            message=message
        )
        
        # Assert
        assert reminder.when == when
        assert reminder.message == message
        assert reminder.priority == "Normal"  # Default priority
        assert not reminder.acknowledged
        
    def test_reminder_from_commitment(self):
        """Test that a reminder can be created from a commitment."""
        # Arrange
        commitment = Commitment(
            when=datetime(2025, 4, 20, 15, 30),  # 3:30 PM
            who="Friend",
            what="Give a ride",
            where="Friend's house",
            estimated_travel_time=timedelta(minutes=25),
            estimated_prep_time=timedelta(minutes=10)
        )
        
        # Act
        reminder = Reminder.from_commitment(commitment)
        
        # Assert
        # Should remind at the departure time (3:30 - 35 minutes = 2:55 PM)
        assert reminder.when == datetime(2025, 4, 20, 14, 55)
        assert commitment.who in reminder.message
        assert commitment.what in reminder.message
        assert commitment.where in reminder.message
        assert reminder.commitment == commitment
        
    def test_acknowledge_reminder(self):
        """Test that a reminder can be acknowledged."""
        # Arrange
        reminder = Reminder(
            when=datetime(2025, 4, 20, 15, 0),
            message="Time to leave"
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
        reminder = Reminder(
            when=original_time,
            message="Time to leave"
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
            Reminder(message="Reminder")
        
        # Missing 'message'
        with pytest.raises(TypeError):
            Reminder(when=datetime.now())
            
    def test_is_due(self):
        """Test that a reminder can determine if it's due."""
        # Arrange
        now = datetime.now()
        past_time = now - timedelta(hours=2)  # Due 2 hours ago
        future_time = now + timedelta(hours=2)  # Due 2 hours from now
        
        past_reminder = Reminder(when=past_time, message="Past reminder")
        future_reminder = Reminder(when=future_time, message="Future reminder")
        
        # Act & Assert
        assert past_reminder.is_due()
        assert not future_reminder.is_due()
        
    def test_str_representation(self):
        """Test the string representation of a reminder."""
        # Arrange
        when = datetime(2025, 4, 20, 15, 0)
        message = "Time to leave for Friend's house"
        priority = "High"
        
        reminder = Reminder(
            when=when,
            message=message,
            priority=priority
        )
        
        # Act
        str_repr = str(reminder)
        
        # Assert
        assert message in str_repr
        assert "15:00" in str_repr
        assert priority in str_repr