"""Health service for orchestrating health-related use cases."""
from typing import Dict, Any

from audhd_lifecoach.application.dtos.health_dto import HealthCheckResponseDTO
from audhd_lifecoach.application.use_cases.health_check import health_check_use_case


def get_health_info() -> HealthCheckResponseDTO:
    """
    Application service that handles health check requests.
    This service coordinates with the application use case.
    """
    # Get data from application use case
    result = health_check_use_case()
    
    # Transform to application DTO
    return HealthCheckResponseDTO(**result)