"""
Integration test for the Communication API endpoint.

This test verifies the full flow via the API endpoint:
1. A communication is sent to the API endpoint
2. Commitments are extracted from it
3. Reminders are created for these commitments

This test uses the actual transformer pipeline rather than mocks.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from audhd_lifecoach.main import create_app
from audhd_lifecoach.application.dtos.communication_dto import CommunicationRequestDTO


class TestCommunicationAPIFlow:
    """Integration test for the Communication API endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI application."""
        app = create_app()
        return TestClient(app.get_app())
    
    @pytest.mark.integration
    def test_basic_flow_with_one_commitment(self, client):
        """
        Test the basic flow through the API from Communication to Reminder.
        
        This test sends a simple communication with one time-based commitment
        to the API and verifies that proper Commitments and Reminders are created.
        """
        # Arrange
        # 1. Create a communication request with a commitment
        communication_request = {
            "content": "I'll call you at 15:30 tomorrow.",
            "sender": "Me",
            "recipient": "Friend"
        }
        
        # Act
        # 2. Send the communication to the API
        response = client.post("/communications", json=communication_request)
        
        # Assert
        # 3. Check that the request was successful
        assert response.status_code == 200, f"API request failed with status {response.status_code}: {response.text}"
        
        # 4. Parse the response
        response_data = response.json()
        
        # 5. Verify that processing was successful
        assert response_data["processed"] is True, "Communication was not processed successfully"
        
        # 6. Verify that reminders were created
        reminders = response_data["reminders"]
        assert len(reminders) > 0, "No reminders were created from the communication"
        
        # 7. Get the first reminder and verify its details
        reminder = reminders[0]
        
        # 8. Verify reminder commitment details
        assert "Friend" == reminder["commitment_who"], f"Expected recipient 'Friend', got '{reminder['commitment_who']}'"
        assert "Meeting or appointment" in reminder["commitment_what"] or "call" in reminder["commitment_what"].lower(), f"Unexpected commitment type: {reminder['commitment_what']}"
        
        # Using 15:30 as the expected time from our message
        # Check for start_time and end_time instead of when
        commitment_start = datetime.fromisoformat(reminder["commitment_start_time"])
        commitment_end = datetime.fromisoformat(reminder["commitment_end_time"])
        
        assert commitment_start.hour == 15, f"Expected start hour 15, got {commitment_start.hour}"
        assert commitment_start.minute == 30, f"Expected start minute 30, got {commitment_start.minute}"
        
        # Make sure end_time is after start_time
        assert commitment_end > commitment_start, "Commitment end time should be after start time"
        
        # 9. Verify reminder time and acknowledgment
        reminder_when = datetime.fromisoformat(reminder["when"])
        assert reminder_when < commitment_start, "Reminder time should be before commitment start time"
        assert reminder["acknowledged"] is False, "New reminder should not be acknowledged"