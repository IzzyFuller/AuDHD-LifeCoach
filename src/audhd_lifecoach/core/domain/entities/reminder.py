"""
Reminder entity represents a notification to alert about an upcoming obligation or task.
"""
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional

from audhd_lifecoach.core.domain.entities.commitment import Commitment


@dataclass
class Reminder:
    """
    Represents a reminder notification for an upcoming obligation or task.
    
    A reminder has essential attributes like when it should trigger and what message to display.
    It can also include optional information like priority and a reference to an associated commitment.
    """
    # Required attributes
    when: datetime
    message: str
    
    # Optional attributes with defaults
    priority: str = "Normal"
    acknowledged: bool = False
    commitment: Optional[Commitment] = None
    
    @classmethod
    def from_commitment(cls, commitment: Commitment) -> "Reminder":
        """
        Create a reminder from a commitment.
        
        This creates a reminder scheduled at the commitment's departure time
        with a message that includes details about the commitment.
        
        Args:
            commitment: The commitment to create a reminder from
            
        Returns:
            A new Reminder instance
        """
        departure_time = commitment.calculate_departure_time()
        
        message = (f"Time to prepare for: {commitment.what} "
                  f"with {commitment.who} at {commitment.where}")
        
        return cls(
            when=departure_time,
            message=message,
            commitment=commitment
        )
    
    def acknowledge(self) -> None:
        """Mark this reminder as acknowledged."""
        self.acknowledged = True
    
    def snooze(self, duration: timedelta) -> None:
        """
        Delay this reminder by the specified duration.
        
        Args:
            duration: How long to delay the reminder
        """
        self.when += duration
    
    def is_due(self) -> bool:
        """
        Check if this reminder is currently due (i.e., its time has passed).
        
        Returns:
            True if the reminder is due, False otherwise
        """
        return datetime.now() >= self.when
    
    def __str__(self) -> str:
        """
        Return a string representation of the reminder.
        
        Returns:
            str: A human-readable description of the reminder
        """
        time_str = self.when.strftime("%Y-%m-%d %H:%M")
        ack_status = "Acknowledged" if self.acknowledged else "Not acknowledged"
        return f"[{self.priority}] {self.message} - Due at {time_str} - {ack_status}"