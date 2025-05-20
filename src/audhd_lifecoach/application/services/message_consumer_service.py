"""
Message Consumer Service.

This service is responsible for consuming messages from a message queue
and processing them to extract commitments and create reminders.
"""
import datetime
import logging
from typing import Any, Dict, Optional

from audhd_lifecoach.application.interfaces.message_consumer_interface import MessageConsumerInterface
from audhd_lifecoach.application.use_cases.process_communication import ProcessCommunication
from audhd_lifecoach.application.dtos.communication_dto import CommunicationRequestDTO


logger = logging.getLogger(__name__)


class MessageConsumerService:
    """
    Service that consumes messages from a message broker and processes
    them to extract commitments and create reminders.
    """
    
    def __init__(self, 
                 message_consumer: MessageConsumerInterface, 
                 process_communication_use_case: ProcessCommunication,
                 queue_name: str = "communications"):
        """
        Initialize the message consumer service.
        
        Args:
            message_consumer: The message consumer adapter to use
            process_communication_use_case: The use case for processing communications
            queue_name: The name of the queue to consume from
        """
        self.message_consumer = message_consumer
        self.process_communication_use_case = process_communication_use_case
        self.queue_name = queue_name
        self.is_consuming = False
        
    def _validate_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Validate that a message has the required fields.
        
        Args:
            message_data: The message data to validate
            
        Returns:
            bool: True if the message is valid, False otherwise
        """
        # Check for required fields
        required_fields = ["content", "sender", "recipient"]
        return all(field in message_data for field in required_fields)
    
    def _process_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a message to extract commitments and create reminders.
        
        This method validates the message, processes it through the communication
        processor, and returns the result including any reminders created.
        
        Args:
            message_data: The message data to process
            
        Returns:
            Optional[Dict[str, Any]]: The processing result, or None if validation fails
        """
        # First, validate the message
        if not self._validate_message(message_data):
            logger.warning(f"Received invalid message: {message_data}")
            return None
            
        # Create a CommunicationRequestDTO from the message data
        communication_dto = CommunicationRequestDTO(
            content=message_data["content"],
            sender=message_data["sender"],
            recipient=message_data["recipient"]
        )
        if "timestamp" in message_data:
            communication_dto.timestamp = datetime.datetime.fromisoformat(message_data["timestamp"])
        
        # Process the communication using the use case
        response_dto = self.process_communication_use_case.execute(communication_dto)
        
        # Format the results for return
        result = {
            "message_id": message_data.get("message_id", "unknown"),
            "commitments_found": len(response_dto.reminders),
            "reminders": [self._format_reminder(r) for r in response_dto.reminders]
        }
        
        return result
    
    @staticmethod
    def _format_reminder(reminder_dto) -> Dict[str, Any]:
        """
        Format a reminder DTO as a dictionary for the response.
        
        Args:
            reminder_dto: The reminder DTO to format
            
        Returns:
            Dict[str, Any]: A dictionary representation of the reminder
        """
        return {
            "when": reminder_dto.when.isoformat(),
            "message": reminder_dto.message,
            "acknowledged": reminder_dto.acknowledged,
            "commitment_who": reminder_dto.commitment_who,
            "commitment_what": reminder_dto.commitment_what,
            "commitment_where": reminder_dto.commitment_where,
            "commitment_start_time": reminder_dto.commitment_start_time.isoformat(),
            "commitment_end_time": reminder_dto.commitment_end_time.isoformat(),
        }
    
    def _message_callback(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Callback function for the message consumer.
        
        This function is called by the message consumer when a message is received.
        It processes the message and handles acknowledgment/rejection.
        
        Args:
            message_data: The message data received from the queue
            
        Returns:
            Optional[Dict[str, Any]]: The processing result, or None if validation fails
        """
        message_id = message_data.get("message_id", "unknown")
        
        try:
            # Process the message
            result = self._process_message(message_data)
            
            # If processing succeeded, acknowledge the message
            if result is not None and "error" not in result:
                self.message_consumer.acknowledge_message(message_id)
                logger.info(f"Successfully processed message {message_id} "
                           f"with {result.get('commitments_found', 0)} commitments found.")
                return result
            
            # If processing failed or returned None (invalid message), reject the message
            self.message_consumer.reject_message(message_id, requeue=False)
            logger.warning(f"Failed to process message {message_id}")
            return result
            
        except Exception as e:
            # If an exception occurred, reject the message and log the error
            logger.exception(f"Error in message callback for message {message_id}: {e}")
            self.message_consumer.reject_message(message_id, requeue=True)
            return None
    
    def start(self, block: bool = True) -> None:
        """
        Start consuming messages.
        
        Args:
            block: Whether to block the current thread. If True, the method
                  will not return until stop() is called. If False, the consumer
                  will run in a separate thread.
        """
            
        # Connect to the message broker first - this is needed in both blocking and non-blocking modes
        connected = self.message_consumer.connect()
        if not connected:
            logger.error("Failed to connect to the message broker")
            return
        
        self.is_consuming = True
        
        try:
            # Start consuming messages
            logger.info(f"Starting to consume messages from queue '{self.queue_name}'")
            self.message_consumer.consume_messages(self.queue_name, self._message_callback)
        except Exception as e:
            logger.exception(f"Error in consumer loop: {e}")
        finally:
            # Make sure to disconnect when the loop ends
            self.message_consumer.disconnect()
            self.is_consuming = False
    
    def stop(self) -> None:
        """Stop consuming messages."""
        
        logger.info("Stopping message consumer")
        self.is_consuming = False
        
        # Disconnect from the message broker
        # This should cause the consumer loop to exit
        self.message_consumer.disconnect()
            
        logger.info("Message consumer stopped")