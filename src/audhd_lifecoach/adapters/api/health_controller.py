"""
Controller for handling health-related API requests.

This controller is responsible for processing health check requests
and returning appropriate responses according to API contracts.
"""
from audhd_lifecoach.application.dtos.health_dto import HealthCheckResponseDTO


class HealthController:
    """
    Controller for handling health-related API endpoints.
    
    This controller is responsible for handling health check requests
    and formatting the responses as API responses.
    """
    
    def get_health_info(self) -> HealthCheckResponseDTO:
        """
        Handle health check API requests.
        
        Returns:
            Health check information formatted as a response DTO
        """
        return HealthCheckResponseDTO(
            status="healthy",
            version="0.1.0"
        )