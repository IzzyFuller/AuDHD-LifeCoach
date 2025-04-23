import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.core.interfaces.commitment_identifiable import CommitmentIdentifiable
from audhd_lifecoach.adapters.ai.hugging_face_onyx_transformer_commitment_identifier import HuggingFaceONYXTransformerCommitmentIdentifier


class TestHuggingFaceONYXTransformerCommitmentIdentifier:
    """Tests for the HuggingFaceONYXTransformerCommitmentIdentifier adapter."""
    
    def test_interface_compliance(self):
        """Test that the adapter implements the CommitmentIdentifiable interface."""
        with patch('transformers.pipeline'):  # Prevent actual model loading
            identifier = HuggingFaceONYXTransformerCommitmentIdentifier()
            assert isinstance(identifier, CommitmentIdentifiable)
    
    def test_identify_basic_commitment(self):
        """Test identifying a simple commitment with mocked transformers."""
        # Arrange
        mock_ner_pipeline = MagicMock()
        mock_ner_pipeline.return_value = [
            {'entity': 'TIME', 'score': 0.99, 'word': '15:30', 'start': 20, 'end': 25},
            {'entity': 'LOCATION', 'score': 0.95, 'word': 'coffee shop', 'start': 33, 'end': 44}
        ]
        
        # Create identifier with mocked pipeline directly injected
        identifier = HuggingFaceONYXTransformerCommitmentIdentifier(
            ner_pipeline=mock_ner_pipeline
        )
        
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
        # Check start_time instead of when
        assert commitments[0].start_time.hour == 15
        assert commitments[0].start_time.minute == 30
        # Also check that end_time is after start_time
        assert commitments[0].end_time > commitments[0].start_time
        assert commitments[0].who == "Friend"
        assert "coffee shop" in commitments[0].where.lower()
    
    def test_no_commitment_identified(self):
        """Test that no commitments are identified in casual conversation."""
        # Arrange
        mock_ner_pipeline = MagicMock()
        # No time entities returned from the pipeline
        mock_ner_pipeline.return_value = []
        
        # Create identifier with mocked pipeline directly injected
        identifier = HuggingFaceONYXTransformerCommitmentIdentifier(
            ner_pipeline=mock_ner_pipeline
        )
        
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
    
    def test_empty_text_handling(self):
        """Test that empty text is handled gracefully."""
        mock_ner_pipeline = MagicMock()
        
        identifier = HuggingFaceONYXTransformerCommitmentIdentifier(
            ner_pipeline=mock_ner_pipeline
        )
        
        communication = Communication(
            timestamp=datetime(2025, 4, 19, 10, 0),
            content="",
            sender="Me",
            recipient="Friend"
        )
        
        # Act
        commitments = identifier.identify_commitments(communication)
        
        # Assert
        assert len(commitments) == 0
        # Ensure we didn't try to process empty text
        mock_ner_pipeline.assert_not_called()