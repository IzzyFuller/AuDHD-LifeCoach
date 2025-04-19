import pytest
from datetime import datetime
from audhd_lifecoach.core.domain.entities.communication import Communication


class TestCommunication:
    def test_communication_creation(self):
        """Test that a communication can be created with basic attributes."""
        # Arrange
        timestamp = datetime(2025, 4, 19, 14, 30)
        content = "I'll come over to your house at 15:30 and give you and your kid a ride to the event"
        sender = "Me"
        recipient = "Friend"
        
        # Act
        communication = Communication(
            timestamp=timestamp,
            content=content,
            sender=sender,
            recipient=recipient
        )
        
        # Assert
        assert communication.timestamp == timestamp
        assert communication.content == content
        assert communication.sender == sender
        assert communication.recipient == recipient
    
    def test_communication_with_default_timestamp(self):
        """Test that a communication can be created with a default timestamp."""
        # Arrange
        content = "Let me know when you're ready"
        sender = "Me"
        recipient = "Friend"
        before = datetime.now()
        
        # Act
        communication = Communication(
            content=content,
            sender=sender,
            recipient=recipient
        )
        after = datetime.now()
        
        # Assert
        assert communication.content == content
        assert communication.sender == sender
        assert communication.recipient == recipient
        assert before <= communication.timestamp <= after
    
    def test_missing_required_arguments(self):
        """Test that creating a communication without required arguments raises an error."""
        # Missing 'content'
        with pytest.raises(TypeError):
            Communication(sender="Me", recipient="Friend")
        
        # Missing 'sender'
        with pytest.raises(TypeError):
            Communication(content="Hello", recipient="Friend")
            
        # Missing 'recipient'
        with pytest.raises(TypeError):
            Communication(content="Hello", sender="Me")
    
    def test_str_representation(self):
        """Test the string representation of a communication."""
        # Arrange
        timestamp = datetime(2025, 4, 19, 14, 30)
        content = "I'll come over at 15:30"
        sender = "Me"
        recipient = "Friend"
        
        communication = Communication(
            timestamp=timestamp,
            content=content,
            sender=sender,
            recipient=recipient
        )
        
        # Act
        str_repr = str(communication)
        
        # Assert
        assert sender in str_repr
        assert recipient in str_repr
        assert "14:30" in str_repr
        assert content in str_repr