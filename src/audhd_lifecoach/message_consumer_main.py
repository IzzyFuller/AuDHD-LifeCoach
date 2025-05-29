"""
Main entry point for AuDHD LifeCoach message consumer.
This file orchestrates the setup of the message consumer service.
"""
import logging
from typing import Dict, Any

from audhd_lifecoach.adapters.ai.spacy_commitment_identifier import SpaCyCommitmentIdentifier
from audhd_lifecoach.adapters.messaging.rabbitmq_message_consumer import RabbitMQMessageConsumer
from audhd_lifecoach.adapters.messaging.rabbitmq_message_publisher import RabbitMQMessagePublisher
from audhd_lifecoach.adapters.messaging.rabbitmq_settings import RabbitMQSettings
from audhd_lifecoach.application.services.message_consumer_service import MessageConsumerService
from audhd_lifecoach.core.services.communication_processor import CommunicationProcessor
from audhd_lifecoach.application.use_cases.process_communication import ProcessCommunication

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_message_consumer() -> MessageConsumerService:
    """Create and configure the message consumer service."""
    # Load settings from environment variables
    rabbitmq_settings = RabbitMQSettings()
    
    logger.info(f"Configured to consume from queue: {rabbitmq_settings.consume_queue_name}")
    logger.info(f"Configured to publish to exchange: {rabbitmq_settings.publish_exchange_name}")
    
    # Create message consumer adapter (RabbitMQ implementation)
    message_consumer = RabbitMQMessageConsumer(rabbitmq_settings)
    
    # Create message publisher adapter (RabbitMQ implementation)
    message_publisher = RabbitMQMessagePublisher(rabbitmq_settings)
    
    # Connect to RabbitMQ for publishing
    if not message_publisher.connect():
        raise RuntimeError("Failed to connect message publisher to RabbitMQ")
    
    # Initialize dependencies for commitment processing
    identifier = SpaCyCommitmentIdentifier()
    processor = CommunicationProcessor(identifier)
    
    # Create the process communication use case with message publisher
    process_communication = ProcessCommunication(
        communication_processor=processor,
        message_publisher=message_publisher
    )
    
    # Create and return the message consumer service
    return MessageConsumerService(
        message_consumer=message_consumer,
        process_communication_use_case=process_communication
    )


def start_message_consumer():
    """Start the message consumer service."""
    logger.info("Initializing message consumer service")

    consumer = None
    
    try:
        consumer = create_message_consumer()
        logger.info("Starting message consumer service")
        consumer.start(block=True)  # Block the thread to keep the consumer running
    except KeyboardInterrupt:
        logger.info("Stopping message consumer service due to keyboard interrupt")
        if consumer:
            consumer.stop()
    except Exception as e:
        logger.exception(f"Error in message consumer service: {e}")
        if consumer:
            consumer.stop()


if __name__ == "__main__":
    start_message_consumer()