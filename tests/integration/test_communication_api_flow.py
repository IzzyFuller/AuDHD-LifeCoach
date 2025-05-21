"""
Integration test for the communication API flow.

This test verifies the full flow via the API:
1. A communication is sent via the API endpoint
2. The communication is processed to extract commitments
3. Reminders are created for these commitments
4. The processed results are returned to the API caller

This test uses the actual transformer pipeline rather than mocks.
"""
import pytest
from datetime import datetime
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from audhd_lifecoach.adapters.ai.spacy_commitment_identifier import SpaCyCommitmentIdentifier
from audhd_lifecoach.adapters.api.fastapi_adapter import FastAPIAdapter
from audhd_lifecoach.adapters.api.communication_controller import CommunicationController
from audhd_lifecoach.application.use_cases.process_communication import ProcessCommunication
from audhd_lifecoach.core.services.communication_processor import CommunicationProcessor
from audhd_lifecoach.application.dtos.communication_dto import CommunicationResponseDTO


class TestCommunicationAPIFlow:
    """Integration test for the communication API flow."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the API using the FastAPI adapter."""
        app = FastAPIAdapter(
            title="Test API",
            description="API for testing"
        )
        
        # Create a mock message publisher
        mock_publisher = MagicMock()
        mock_publisher.connect.return_value = True
        mock_publisher.publish_message.return_value = True
        
        # Use the actual transformer pipeline
        identifier = SpaCyCommitmentIdentifier()
        processor = CommunicationProcessor(identifier)
        
        # Create the use case with the mock publisher
        process_communication = ProcessCommunication(
            communication_processor=processor,
            message_publisher=mock_publisher,
            exchange_name="test-exchange"
        )
        
        # Create controller with the use case
        controller = CommunicationController(process_communication)
        
        # Register the route
        app.register_route(
            path="/communications",
            http_method="POST",
            handler_func=controller.process_communication,
            response_model=CommunicationResponseDTO
        )
        
        # Get the fully configured app with router included
        fastapi_app = app.get_app()
        
        return TestClient(fastapi_app)
    
    @pytest.mark.integration
    def test_process_communication_with_commitment(self, client):
        """Test processing a communication with a commitment via the API."""
        # Arrange
        communication_data = {
            "content": "I'll call you at 3:30 PM tomorrow.",
            "sender": "Alice",
            "recipient": "Bob",
            "timestamp": datetime.now().isoformat()
        }
        
        # Act
        response = client.post(
            "/communications",
            json=communication_data
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK, f"Unexpected response: {response.json()}"
        
        data = response.json()
        assert data["processed"] is True
        assert len(data["reminders"]) > 0, "No reminders were created"
        
        # Check that at least one reminder contains the commitment details
        reminder = data["reminders"][0]
        assert reminder["message"] is not None
        assert reminder["when"] is not None
    
    @pytest.mark.integration
    def test_process_communication_no_commitment(self, client):
        """Test processing a communication without any commitments via the API."""
        # Arrange
        communication_data = {
            "content": "The weather is nice today.",
            "sender": "Alice",
            "recipient": "Bob",
            "timestamp": datetime.now().isoformat()
        }
        
        # Act
        response = client.post(
            "/communications",
            json=communication_data
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["processed"] is True
        assert len(data["reminders"]) == 0, "Reminders were created when none were expected"