"""
Reminder entity represents a notification about a commitment.
"""
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

from audhd_lifecoach.core.domain.entities.commitment import Commitment


@dataclass
class Reminder:
    """
    Represents a reminder notification for a commitment.
    
    Reminders are created from commitments and have a scheduled notification time,
    a reference to the commitment, and a message.
    """
    # The specific time when this reminder should be sent
    when: datetime
    
    # The commitment this reminder is for
    commitment: Commitment
    
    # The message to display/send in the reminder
    message: str
    
    # Whether the user has seen and acknowledged this reminder
    acknowledged: bool = False
    
    @classmethod
    def from_commitment(cls, commitment: Commitment, 
                        lead_time: timedelta = timedelta(minutes=30),
                        message: Optional[str] = None) -> 'Reminder':
        """
        Create a reminder from a commitment.
        
        By default, sets the reminder time to 30 minutes before the commitment's start time.
        
        Args:
            commitment: The commitment to create a reminder for
            lead_time: How long before the commitment the reminder should be sent
            message: Optional custom message (will be auto-generated if None)
            
        Returns:
            A new Reminder instance for the commitment
        """
        # Calculate when the reminder should be sent
        reminder_time = commitment.start_time - lead_time
        
        # Generate a default message if none provided
        if message is None:
            # Format the time based on whether it's today or a future date
            today = datetime.now().date()
            if commitment.start_time.date() == today:
                time_str = commitment.start_time.strftime("%H:%M")
                message = f"Reminder: You have a commitment with {commitment.who} at {time_str} today."
            else:
                date_time_str = commitment.start_time.strftime("%Y-%m-%d at %H:%M")
                message = f"Reminder: You have a commitment with {commitment.who} on {date_time_str}."
        
        return cls(
            when=reminder_time,
            commitment=commitment,
            message=message
        )
    
    def acknowledge(self) -> None:
        """
        Mark the reminder as acknowledged by the user.
        
        This indicates the user has seen and acknowledged the reminder.
        """
        self.acknowledged = True
    
    def snooze(self, duration: timedelta) -> None:
        """
        Postpone the reminder by the specified duration.
        
        Args:
            duration: How long to postpone the reminder
        """
        self.when = self.when + duration
    
    def is_due(self) -> bool:
        """
        Check if the reminder is due (time to show it).
        
        A reminder is considered due when its scheduled time has passed
        and it hasn't been acknowledged yet.
        
        Returns:
            bool: True if the reminder is due, False otherwise
        """
        return datetime.now() >= self.when and not self.acknowledged
    
    def __str__(self) -> str:
        """
        Return a string representation of the reminder.
        
        Returns:
            str: A human-readable description of the reminder
        """
        status = "Acknowledged" if self.acknowledged else "Not acknowledged"
        return f"Reminder at {self.when.strftime('%Y-%m-%d %H:%M')}: {self.message} [{status}]"