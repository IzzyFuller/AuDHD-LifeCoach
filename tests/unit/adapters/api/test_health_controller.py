"""
Tests for the health controller API endpoint.

This test verifies that the health endpoint:
1. Returns the correct HTTP status code
2. Returns the expected response structure and values
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from audhd_lifecoach.adapters.api.fastapi_adapter import FastAPIAdapter
from audhd_lifecoach.adapters.api.health_controller import HealthController
from audhd_lifecoach.application.dtos.health_dto import HealthCheckResponseDTO


class TestHealthController:
    """Test case for the health controller API endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the API using the FastAPI adapter."""
        app = FastAPIAdapter(
            title="Test API",
            description="API for testing"
        )
        
        # Create controller
        controller = HealthController()
        
        # Register the route
        app.register_route(
            path="/health",
            http_method="GET",
            handler_func=controller.get_health_info,
            response_model=HealthCheckResponseDTO,
            tags=["System"]
        )
        
        # Get the fully configured app with router included
        fastapi_app = app.get_app()
        
        return TestClient(fastapi_app)
    
    def test_health_check_endpoint(self, client):
        """Test that the health check endpoint returns the expected response."""
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"