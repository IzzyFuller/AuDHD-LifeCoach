"""
Message Consumer Service.

This service is responsible for consuming messages from a message queue
and processing them to extract commitments and create reminders.
"""
import json
import logging
import threading
from typing import Any, Dict, List, Optional

from audhd_lifecoach.application.interfaces.message_consumer_interface import MessageConsumerInterface
from audhd_lifecoach.core.services.communication_processor import CommunicationProcessor
from audhd_lifecoach.core.domain.entities.communication import Communication


logger = logging.getLogger(__name__)


class MessageConsumerService:
    """
    Service that consumes messages from a message broker and processes
    them to extract commitments and create reminders.
    """
    
    def __init__(self, 
                 message_consumer: MessageConsumerInterface, 
                 communication_processor: CommunicationProcessor,
                 queue_name: str = "communications"):
        """
        Initialize the message consumer service.
        
        Args:
            message_consumer: The message consumer adapter to use
            communication_processor: The processor for handling communications
            queue_name: The name of the queue to consume from
        """
        self.message_consumer = message_consumer
        self.communication_processor = communication_processor
        self.queue_name = queue_name
        self.is_consuming = False
        self._consumer_thread = None
        
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
        
        try:
            # Extract the communication data from the message
            
            # Create a Communication entity from the message data
            communication = Communication(
                content=message_data["content"],
                sender=message_data["sender"],
                recipient=message_data["recipient"],
                timestamp=message_data.get("timestamp")
            )
            
            # Process the communication using the correct method name
            reminders = self.communication_processor.process_communication(communication)
            
            # Format the results for return
            result = {
                "message_id": message_data.get("message_id", "unknown"),
                "commitments_found": len(reminders),
                "reminders": [self._format_reminder(r) for r in reminders]
            }
            
            return result
            
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _format_reminder(reminder) -> Dict[str, Any]:
        """
        Format a reminder entity as a dictionary for the response.
        
        Args:
            reminder: The reminder entity to format
            
        Returns:
            Dict[str, Any]: A dictionary representation of the reminder
        """
        commitment = reminder.commitment
        return {
            "when": reminder.when.isoformat(),
            "message": reminder.message,
            "acknowledged": reminder.acknowledged,
            "commitment_who": commitment.who,
            "commitment_what": commitment.what,
            "commitment_where": commitment.where,
            "commitment_start_time": commitment.start_time.isoformat(),
            "commitment_end_time": commitment.end_time.isoformat(),
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
    
    def _consumer_loop(self) -> None:
        """
        Main consumer loop that runs in a separate thread.
        
        This method connects to the message broker and starts consuming messages.
        """
        try:
            # Connect to the message broker
            if not self.message_consumer.connect():
                logger.error("Failed to connect to the message broker")
                return
            
            # Start consuming messages
            logger.info(f"Starting to consume messages from queue '{self.queue_name}'")
            self.message_consumer.consume_messages(self.queue_name, self._message_callback)
            
        except Exception as e:
            logger.exception(f"Error in consumer loop: {e}")
        finally:
            # Make sure to disconnect when the loop ends
            self.message_consumer.disconnect()
            self.is_consuming = False
    
    def start(self, block: bool = True) -> None:
        """
        Start consuming messages.
        
        Args:
            block: Whether to block the current thread. If True, the method
                  will not return until stop() is called. If False, the consumer
                  will run in a separate thread.
        """
        if self.is_consuming:
            logger.warning("Message consumer already started")
            return
            
        # Connect to the message broker first - this is needed in both blocking and non-blocking modes
        connected = self.message_consumer.connect()
        if not connected:
            logger.error("Failed to connect to the message broker")
            return
        
        self.is_consuming = True
        
        if block:
            # Run the consumer loop in the current thread
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
        else:
            # Run the consumer loop in a separate thread
            self._consumer_thread = threading.Thread(
                target=self._consumer_loop, 
                daemon=True  # Make this a daemon thread so it exits when the main thread exits
            )
            self._consumer_thread.start()
            logger.info("Message consumer started in background thread")
    
    def stop(self) -> None:
        """Stop consuming messages."""
        if not self.is_consuming:
            logger.warning("Message consumer not started")
            return
        
        logger.info("Stopping message consumer")
        self.is_consuming = False
        
        # Disconnect from the message broker
        # This should cause the consumer loop to exit
        self.message_consumer.disconnect()
        
        # If we're running in a thread, wait for it to finish
        if self._consumer_thread and self._consumer_thread.is_alive():
            self._consumer_thread.join(timeout=5.0)  # Wait up to 5 seconds
            if self._consumer_thread.is_alive():
                logger.warning("Consumer thread did not exit within timeout")
            
        logger.info("Message consumer stopped")