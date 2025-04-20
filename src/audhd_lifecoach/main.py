"""
Main entry point for AuDHD LifeCoach application.
This file orchestrates the setup of the application using clean architecture principles.
"""
from typing import Dict, Any

from audhd_lifecoach.adapters.api.fastapi_adapter import FastAPIAdapter
from audhd_lifecoach.application.interfaces.web_app_interface import WebAppInterface
from audhd_lifecoach.application.services.health_service import get_health_info
from audhd_lifecoach.application.dtos.communication_dto import CommunicationRequestDTO, CommunicationResponseDTO
from audhd_lifecoach.application.services.communication_processor import CommunicationProcessor
from audhd_lifecoach.application.use_cases.process_communication import ProcessCommunication
from audhd_lifecoach.adapters.ai.hugging_face_onyx_transformer_commitment_identifier import HuggingFaceONYXTransformerCommitmentIdentifier


# Create API route handlers here, outside of functions to avoid recreation on each request
def process_communication_handler(communication_request: CommunicationRequestDTO) -> CommunicationResponseDTO:
    """
    Handle incoming communication API requests.
    
    Args:
        communication_request: The communication data sent to the API
        
    Returns:
        Response with processing results and created reminders
    """
    # Create the needed components
    identifier = HuggingFaceONYXTransformerCommitmentIdentifier()
    processor = CommunicationProcessor(identifier)
    use_case = ProcessCommunication(processor)
    
    # Process the request
    return use_case.execute(communication_request)


def create_app() -> WebAppInterface:
    """Create and configure the web application."""
    # Create the web interface implementation
    web_app = FastAPIAdapter(
        title="AuDHD LifeCoach API", 
        description="A life coach application for people with AuDHD"
    )
    
    # Register routes with application services
    # Notice how the adapters only interact with the application layer,
    # and the application layer coordinates with the core domain
    web_app.register_route(
        path="/health",
        http_method="GET",
        handler_func=get_health_info,
        response_model=get_health_info.__annotations__["return"],
        tags=["System"]
    )
    
    # Register the new communication endpoint
    web_app.register_route(
        path="/communications",
        http_method="POST",
        handler_func=process_communication_handler,
        response_model=CommunicationResponseDTO,
        tags=["Communications"]
    )
    
    return web_app


def start_application():
    """Start the web application."""
    app = create_app()
    app.run()


if __name__ == "__main__":
    start_application()