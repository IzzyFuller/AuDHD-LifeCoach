"""
Main entry point for AuDHD LifeCoach message consumer.
This file orchestrates the setup of the message consumer service.
"""
import logging
import os
from typing import Dict, Any

from audhd_lifecoach.adapters.ai.spacy_commitment_identifier import SpaCyCommitmentIdentifier
from audhd_lifecoach.adapters.messaging.rabbitmq_message_consumer import RabbitMQMessageConsumer
from audhd_lifecoach.adapters.messaging.rabbitmq_message_publisher import RabbitMQMessagePublisher
from audhd_lifecoach.application.services.message_consumer_service import MessageConsumerService
from audhd_lifecoach.core.services.communication_processor import CommunicationProcessor
from audhd_lifecoach.application.use_cases.process_communication import ProcessCommunication

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_message_consumer(queue_name: str = "communications") -> MessageConsumerService:
    """Create and configure the message consumer service."""
    # Get configuration from environment variables or use defaults
    rabbitmq_host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    rabbitmq_port = int(os.environ.get("RABBITMQ_PORT", "5672"))
    rabbitmq_user = os.environ.get("RABBITMQ_USER", "guest")
    rabbitmq_pass = os.environ.get("RABBITMQ_PASS", "guest")
    exchange_name = os.environ.get("RABBITMQ_EXCHANGE", "audhd_lifecoach")
    
    # Create message consumer adapter (RabbitMQ implementation)
    message_consumer = RabbitMQMessageConsumer(
        host=rabbitmq_host,
        port=rabbitmq_port,
        username=rabbitmq_user,
        password=rabbitmq_pass
    )
    
    # Create message publisher adapter (RabbitMQ implementation)
    message_publisher = RabbitMQMessagePublisher(
        host=rabbitmq_host,
        port=rabbitmq_port,
        username=rabbitmq_user,
        password=rabbitmq_pass
    )
    
    # Connect to RabbitMQ for publishing
    message_publisher.connect()
    
    # Initialize dependencies for commitment processing
    identifier = SpaCyCommitmentIdentifier()
    processor = CommunicationProcessor(identifier)
    
    # Create the process communication use case with message publisher
    process_communication = ProcessCommunication(
        communication_processor=processor,
        message_publisher=message_publisher,
        exchange_name=exchange_name
    )
    
    # Create and return the message consumer service
    return MessageConsumerService(
        message_consumer=message_consumer,
        process_communication_use_case=process_communication,
        queue_name=queue_name
    )


def start_message_consumer():
    """Start the message consumer service."""
    logger.info("Initializing message consumer service")
    consumer = create_message_consumer()
    
    try:
        logger.info("Starting message consumer service")
        consumer.start(block=True)  # Block the thread to keep the consumer running
    except KeyboardInterrupt:
        logger.info("Stopping message consumer service due to keyboard interrupt")
        consumer.stop()
    except Exception as e:
        logger.exception(f"Error in message consumer service: {e}")
        consumer.stop()


if __name__ == "__main__":
    start_message_consumer()