"""Health check DTO for application responses."""
from pydantic import BaseModel


class HealthCheckResponseDTO(BaseModel):
    """Response DTO for health check endpoints."""
    status: str
    version: str