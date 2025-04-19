"""
Main entry point for AuDHD LifeCoach application.
This file orchestrates the setup of the application using clean architecture principles.
"""
from typing import Dict, Any

from audhd_lifecoach.adapters.api.fastapi_adapter import FastAPIAdapter
from audhd_lifecoach.application.interfaces.web_app_interface import WebAppInterface
from audhd_lifecoach.application.services.health_service import get_health_info


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
    
    return web_app


def start_application():
    """Start the web application."""
    app = create_app()
    app.run()


if __name__ == "__main__":
    start_application()