"""
Use case for processing communications received through the API.

This use case handles the flow of receiving a communication via the API,
processing it to extract commitments, and creating reminders.
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any

from audhd_lifecoach.application.dtos.communication_dto import CommunicationRequestDTO, CommunicationResponseDTO, ReminderResponseDTO
from audhd_lifecoach.core.services.communication_processor import CommunicationProcessor
from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.application.interfaces.message_publisher_interface import MessagePublisherInterface


logger = logging.getLogger(__name__)


class ProcessCommunication:
    """Use case for processing communications through the API."""
    
    def __init__(
        self,
        communication_processor: CommunicationProcessor,
        message_publisher: MessagePublisherInterface,
        exchange_name: str = "audhd_lifecoach"
    ):
        """
        Initialize the use case with a communication processor.
        
        Args:
            communication_processor: Service that processes communications
            message_publisher: Message publisher for broadcasting results
            exchange_name: Name of the exchange to publish messages to
        """
        self.communication_processor = communication_processor
        self.message_publisher = message_publisher
        self.exchange_name = exchange_name
    
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
                commitment_start_time=reminder.commitment.start_time,
                commitment_end_time=reminder.commitment.end_time,
                commitment_where=reminder.commitment.where
            )
            reminder_dtos.append(reminder_dto)
        
        # Create response DTO
        response = CommunicationResponseDTO(
            processed=True,
            reminders=reminder_dtos
        )
        
        # Publish the results
        try:
            self._publish_results(communication_dto, response)
        except Exception as e:
            logger.error(f"Failed to publish communication results: {e}")
            # We intentionally don't re-raise the exception to avoid affecting the main flow
            # The communication was processed successfully even if publishing fails
        
        return response
    
    def _format_reminder_for_publishing(self, reminder_dto: ReminderResponseDTO) -> Dict[str, Any]:
        """
        Format a reminder DTO for publishing.
        
        Args:
            reminder_dto: The reminder DTO to format
            
        Returns:
            Dict[str, Any]: A dictionary representation of the reminder
        """
        return {
            "when": reminder_dto.when.isoformat(),
            "message": reminder_dto.message,
            "acknowledged": reminder_dto.acknowledged,
            "commitment": {
                "who": reminder_dto.commitment_who,
                "what": reminder_dto.commitment_what,
                "where": reminder_dto.commitment_where,
                "start_time": reminder_dto.commitment_start_time.isoformat() if reminder_dto.commitment_start_time else None,
                "end_time": reminder_dto.commitment_end_time.isoformat() if reminder_dto.commitment_end_time else None,
            }
        }
    
    def _publish_results(
        self, 
        communication_dto: CommunicationRequestDTO, 
        response_dto: CommunicationResponseDTO
    ) -> bool:
        """
        Publish the results of processing a communication.
        
        Args:
            communication_dto: The original communication DTO
            response_dto: The response DTO containing processing results
            
        Returns:
            bool: True if publishing was successful, False otherwise
        """
        # Prepare the message
        message = {
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "original_communication": {
                "content": communication_dto.content,
                "sender": communication_dto.sender,
                "recipient": communication_dto.recipient,
                "timestamp": communication_dto.timestamp.isoformat() if communication_dto.timestamp else None,
            },
            "processed": response_dto.processed,
            "reminders": [self._format_reminder_for_publishing(r) for r in response_dto.reminders]
        }
        
        # Define the routing key for this type of message
        routing_key = "communication.processed"
        
        # Publish the message
        success = self.message_publisher.publish_message(
            exchange=self.exchange_name,
            routing_key=routing_key,
            message=message
        )
        
        if success:
            logger.info(f"Published communication results with {len(message['reminders'])} reminders")
        else:
            logger.warning("Failed to publish communication results")
            
        return success