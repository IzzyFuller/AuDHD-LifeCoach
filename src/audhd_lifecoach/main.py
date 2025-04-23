"""
Main entry point for AuDHD LifeCoach application.
This file orchestrates the setup of the application using clean architecture principles.
"""
from typing import Dict, Any

from audhd_lifecoach.adapters.api.fastapi_adapter import FastAPIAdapter
from audhd_lifecoach.adapters.api.communication_controller import CommunicationController
from audhd_lifecoach.adapters.api.health_controller import HealthController
from audhd_lifecoach.application.interfaces.web_app_interface import WebAppInterface
from audhd_lifecoach.application.dtos.communication_dto import CommunicationResponseDTO
from audhd_lifecoach.application.dtos.health_dto import HealthCheckResponseDTO
from audhd_lifecoach.core.services.communication_processor import CommunicationProcessor
from audhd_lifecoach.application.use_cases.process_communication import ProcessCommunication
from audhd_lifecoach.adapters.ai.hugging_face_onyx_transformer_commitment_identifier import HuggingFaceONYXTransformerCommitmentIdentifier


def create_app() -> WebAppInterface:
    """Create and configure the web application."""
    # Create the web interface implementation
    web_app = FastAPIAdapter(
        title="AuDHD LifeCoach API", 
        description="A life coach application for people with AuDHD"
    )
    
    # Initialize controllers
    health_controller = HealthController()
    
    # Initialize dependencies for communication processing
    identifier = HuggingFaceONYXTransformerCommitmentIdentifier()
    processor = CommunicationProcessor(identifier)
    process_communication_use_case = ProcessCommunication(processor)
    communication_controller = CommunicationController(process_communication_use_case)
    
    # Register routes with application services
    # Notice how the adapters only interact with the application layer,
    # and the application layer coordinates with the core domain
    web_app.register_route(
        path="/health",
        http_method="GET",
        handler_func=health_controller.get_health_info,
        response_model=HealthCheckResponseDTO,
        tags=["System"]
    )
    
    # Register the communication endpoint using the controller
    web_app.register_route(
        path="/communications",
        http_method="POST",
        handler_func=communication_controller.process_communication,
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