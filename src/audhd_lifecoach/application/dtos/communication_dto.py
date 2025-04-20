"""
Data Transfer Objects for Communication related API requests and responses.
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


class CommunicationRequestDTO(BaseModel):
    """DTO for incoming communication API requests."""
    content: str
    sender: str
    recipient: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class ReminderResponseDTO(BaseModel):
    """DTO for reminder information in API responses."""
    message: str
    when: datetime
    acknowledged: bool
    commitment_what: str
    commitment_who: str
    commitment_when: datetime


class CommunicationResponseDTO(BaseModel):
    """DTO for the response from processing a communication."""
    processed: bool
    reminders: List[ReminderResponseDTO] = []