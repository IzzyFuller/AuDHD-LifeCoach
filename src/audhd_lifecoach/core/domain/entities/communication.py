"""
Communication entity represents a message or interaction between individuals.
"""
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Communication:
    """
    Represents a communication or interaction between individuals.
    
    A communication has essential attributes like content, sender, and recipient.
    It also includes a timestamp which defaults to the current time if not provided.
    """
    # Required attributes
    content: str
    sender: str
    recipient: str
    
    # Optional attributes with defaults
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        """
        Return a string representation of the communication.
        
        Returns:
            str: A human-readable description of the communication
        """
        time_str = self.timestamp.strftime("%Y-%m-%d %H:%M")
        return f"From {self.sender} to {self.recipient} at {time_str}: {self.content}"