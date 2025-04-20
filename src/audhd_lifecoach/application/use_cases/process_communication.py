"""
Use case for processing communications received through the API.

This use case handles the flow of receiving a communication via the API,
processing it to extract commitments, and creating reminders.
"""
from typing import List

from audhd_lifecoach.application.dtos.communication_dto import CommunicationRequestDTO, CommunicationResponseDTO, ReminderResponseDTO
from audhd_lifecoach.application.services.communication_processor import CommunicationProcessor
from audhd_lifecoach.core.domain.entities.communication import Communication


class ProcessCommunication:
    """Use case for processing communications through the API."""
    
    def __init__(self, communication_processor: CommunicationProcessor):
        """
        Initialize the use case with a communication processor.
        
        Args:
            communication_processor: Service that processes communications
        """
        self.communication_processor = communication_processor
    
    def execute(self, communication_dto: CommunicationRequestDTO) -> CommunicationResponseDTO:
        """
        Execute the use case to process a communication.
        
        Args:
            communication_dto: DTO containing the communication data
            
        Returns:
            Response DTO with processing results and created reminders
        """
        # Convert DTO to domain entity
        communication = Communication(
            content=communication_dto.content,
            sender=communication_dto.sender,
            recipient=communication_dto.recipient,
            timestamp=communication_dto.timestamp
        )
        
        # Process the communication
        reminders = self.communication_processor.process_communication(communication)
        
        # Convert reminders to DTOs
        reminder_dtos = []
        for reminder in reminders:
            reminder_dto = ReminderResponseDTO(
                message=reminder.message,
                when=reminder.when,
                acknowledged=reminder.acknowledged,
                commitment_what=reminder.commitment.what,
                commitment_who=reminder.commitment.who,
                commitment_when=reminder.commitment.when
            )
            reminder_dtos.append(reminder_dto)
        
        # Create and return response DTO
        response = CommunicationResponseDTO(
            processed=True,
            reminders=reminder_dtos
        )
        
        return response