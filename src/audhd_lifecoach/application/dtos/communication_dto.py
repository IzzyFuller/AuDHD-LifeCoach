"""
Data Transfer Objects for Communication related API requests and responses.
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List


class CommunicationRequestDTO(BaseModel):
    """DTO for incoming communication API requests."""
    content: str
    sender: str
    recipient: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ReminderResponseDTO(BaseModel):
    """DTO for reminder information in API responses."""
    message: str
    when: datetime  # The single timestamp when the reminder should be triggered
    acknowledged: bool
    commitment_what: str
    commitment_who: str
    commitment_start_time: datetime  # Start time of the commitment (replacing when)
    commitment_end_time: datetime    # End time of the commitment (new field)
    commitment_where: str|None = None


class CommunicationResponseDTO(BaseModel):
    """DTO for the response from processing a communication."""
    processed: bool
    reminders: List[ReminderResponseDTO] = []