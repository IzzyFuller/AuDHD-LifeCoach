import pytest
from datetime import datetime
from typing import List

from audhd_lifecoach.core.interfaces.commitment_identifiable import CommitmentIdentifiable
from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.core.domain.entities.commitment import Commitment


class SimpleCommitmentIdentifier:
    """A simple implementation of CommitmentIdentifiable for testing."""
    
    def identify_commitments(self, communication: Communication) -> List[Commitment]:
        """
        Identify commitments using simple keyword matching.
        This is a basic implementation for testing the interface contract.
        """
        commitments = []
        
        # Simple rule: if text contains both "at" and a time indicator like "15:30",
        # and has a promise-like phrase, consider it a commitment
        if ("at" in communication.content and 
            ("15:30" in communication.content or "3:30" in communication.content) and
            any(phrase in communication.content.lower() for phrase in ["i'll", "will", "going to"])):
            
            # Extract time from the message (simplified for testing)
            when = datetime(2025, 4, 19, 15, 30)  # Hardcoded for test simplicity
            
            # Create a commitment
            commitment = Commitment(
                when=when,
                who=communication.recipient,
                what="Meet up",  # Simplified extraction
                where="Location mentioned in message"  # Simplified extraction
            )
            
            commitments.append(commitment)
            
        return commitments


class AnotherIdentifier:
    """Another implementation of CommitmentIdentifiable for testing."""
    
    def identify_commitments(self, communication: Communication) -> List[Commitment]:
        # Different implementation but same interface
        return []


class TestCommitmentIdentifiable:
    def test_interface_compliance(self):
        """Test that a class implementing the interface can be recognized as such."""
        # Arrange
        identifier = SimpleCommitmentIdentifier()
        
        # Act & Assert
        # This will raise a TypeError if SimpleCommitmentIdentifier doesn't implement the interface
        assert isinstance(identifier, CommitmentIdentifiable)
    
    def test_identify_commitments_with_commitment(self):
        """Test identifying a communication that contains a commitment."""
        # Arrange
        identifier = SimpleCommitmentIdentifier()
        communication = Communication(
            timestamp=datetime(2025, 4, 19, 10, 0),
            content="I'll meet you at 15:30 at the coffee shop.",
            sender="Me",
            recipient="Friend"
        )
        
        # Act
        commitments = identifier.identify_commitments(communication)
        
        # Assert
        assert len(commitments) == 1
        assert commitments[0].when.hour == 15
        assert commitments[0].when.minute == 30
        assert commitments[0].who == "Friend"
    
    def test_identify_commitments_without_commitment(self):
        """Test identifying a communication that doesn't contain a commitment."""
        # Arrange
        identifier = SimpleCommitmentIdentifier()
        communication = Communication(
            timestamp=datetime(2025, 4, 19, 10, 0),
            content="Just checking in to say hello!",
            sender="Me",
            recipient="Friend"
        )
        
        # Act
        commitments = identifier.identify_commitments(communication)
        
        # Assert
        assert len(commitments) == 0
    
    @pytest.mark.parametrize("identifier_class", [
        SimpleCommitmentIdentifier,
        AnotherIdentifier
    ])
    def test_multiple_implementations_compatibility(self, identifier_class):
        """
        Test that different implementations of the interface can be used interchangeably.
        This is a key benefit of using interfaces.
        """
        # Arrange
        identifier = identifier_class()
        communication = Communication(
            content="Test", sender="Test", recipient="Test"
        )
        
        # Act & Assert
        assert isinstance(identifier, CommitmentIdentifiable)
        
        # Verify we can call the method without errors
        result = identifier.identify_commitments(communication)
        assert isinstance(result, list)