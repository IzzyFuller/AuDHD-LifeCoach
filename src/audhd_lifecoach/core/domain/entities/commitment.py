"""
Commitment entity represents a promise or obligation made by the user.
"""
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional


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
    
    # Optional attributes
    estimated_travel_time: Optional[timedelta] = None
    estimated_prep_time: Optional[timedelta] = None
    
    # Default values for travel and prep time if not specified
    DEFAULT_TRAVEL_TIME = timedelta(minutes=15)
    DEFAULT_PREP_TIME = timedelta(minutes=5)
    
    def calculate_departure_time(self) -> datetime:
        """
        Calculate when the user needs to leave to make this commitment.
        
        Takes into account the estimated travel time and preparation time.
        If these are not specified, uses default values.
        
        Returns:
            datetime: The time the user should begin preparing for the commitment
        """
        travel_time = self.estimated_travel_time or self.DEFAULT_TRAVEL_TIME
        prep_time = self.estimated_prep_time or self.DEFAULT_PREP_TIME
        
        return self.when - travel_time - prep_time
    
    def __str__(self) -> str:
        """
        Return a string representation of the commitment.
        
        Returns:
            str: A human-readable description of the commitment
        """
        time_str = self.when.strftime("%Y-%m-%d %H:%M")
        return f"Commitment to {self.what} with {self.who} at {self.where} on {time_str}"