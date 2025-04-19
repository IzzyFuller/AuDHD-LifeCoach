"""
Commitment entity represents a promise or obligation made by the user.
"""
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

from audhd_lifecoach.core.domain.config import DEFAULT_TRAVEL_TIME, DEFAULT_PREP_TIME


@dataclass
class Commitment:
    """
    Represents a commitment or obligation that the user has made.
    
    A commitment has essential attributes like when, who, what, and where.
    It can also include optional information like estimated travel and preparation time.
    """
    # Required attributes
    when: datetime
    who: str
    what: str
    where: str
    
    # Optional attributes with default values from config
    estimated_travel_time: timedelta = DEFAULT_TRAVEL_TIME
    estimated_prep_time: timedelta = DEFAULT_PREP_TIME
    
    def calculate_departure_time(self) -> datetime:
        """
        Calculate when the user needs to leave to make this commitment.
        
        Takes into account the estimated travel time and preparation time.
        
        Returns:
            datetime: The time the user should begin preparing for the commitment
        """
        return self.when - self.estimated_travel_time - self.estimated_prep_time
    
    def __str__(self) -> str:
        """
        Return a string representation of the commitment.
        
        Returns:
            str: A human-readable description of the commitment
        """
        time_str = self.when.strftime("%Y-%m-%d %H:%M")
        return f"Commitment to {self.what} with {self.who} at {self.where} on {time_str}"