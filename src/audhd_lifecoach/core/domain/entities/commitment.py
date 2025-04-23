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
    
    A commitment has essential attributes like time range (start_time, end_time), 
    who, what, and where. It can also include optional information like 
    estimated travel and preparation time.
    """
    # Required attributes
    start_time: datetime
    end_time: datetime
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
        return self.start_time - self.estimated_travel_time - self.estimated_prep_time
    
    @classmethod
    def from_single_datetime(cls, when: datetime, who: str, what: str, where: str, 
                             duration: timedelta = timedelta(minutes=60),
                             **kwargs) -> 'Commitment':
        """
        Create a commitment from a single datetime (start time) with a default duration.
        
        This is a convenience method for backward compatibility and cases where only
        a start time is known.
        
        Args:
            when: The start time of the commitment
            who: The person or people involved
            what: The activity or purpose
            where: The location
            duration: The expected duration (defaults to 1 hour)
            **kwargs: Additional keyword arguments for the Commitment constructor
            
        Returns:
            A new Commitment instance with the specified start time and calculated end time
        """
        return cls(
            start_time=when,
            end_time=when + duration,
            who=who,
            what=what,
            where=where,
            **kwargs
        )
    
    def __str__(self) -> str:
        """
        Return a string representation of the commitment.
        
        Returns:
            str: A human-readable description of the commitment
        """
        start_str = self.start_time.strftime("%Y-%m-%d %H:%M")
        end_str = self.end_time.strftime("%H:%M") if self.start_time.date() == self.end_time.date() else self.end_time.strftime("%Y-%m-%d %H:%M")
        duration = int((self.end_time - self.start_time).total_seconds() / 60)
        
        return f"Commitment to {self.what} with {self.who} at {self.where} on {start_str} to {end_str} ({duration} min)"
    
    @property
    def duration(self) -> timedelta:
        """
        Get the duration of this commitment.
        
        Returns:
            timedelta: The time between start_time and end_time
        """
        return self.end_time - self.start_time