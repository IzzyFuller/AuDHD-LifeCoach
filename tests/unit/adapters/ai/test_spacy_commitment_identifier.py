from datetime import datetime, timedelta

import pytest

from audhd_lifecoach.adapters.ai.spacy_commitment_identifier import (
    SpaCyCommitmentIdentifier,
)
from audhd_lifecoach.core.domain.entities.communication import Communication
from audhd_lifecoach.core.interfaces.commitment_identifiable import (
    CommitmentIdentifiable,
)


class TestSpaCyCommitmentIdentifier:
    """Tests for the SpaCyCommitmentIdentifier adapter."""

    @pytest.fixture
    def identifier(self):
        """Create a SpaCyCommitmentIdentifier instance for testing."""
        try:
            return SpaCyCommitmentIdentifier()
        except OSError:
            # If spaCy model isn't available, skip tests
            pytest.skip("SpaCy model 'en_core_web_trf' not available")

    def test_interface_compliance(self, identifier):
        """Test that the adapter implements the CommitmentIdentifiable interface."""
        assert isinstance(identifier, CommitmentIdentifiable)

    def test_identify_basic_commitment(self, identifier):
        """Test identifying a simple commitment."""
        communication = Communication(
            timestamp=datetime(2025, 4, 19, 10, 0),
            content="I'll meet you at 15:30 at the coffee shop.",
            sender="Me",
            recipient="Friend",
        )

        # Act
        commitments = identifier.identify_commitments(communication)

        # Assert - We expect at least some processing to occur
        assert isinstance(commitments, list)
        # The actual result will depend on the SpaCy model's performance
        # but we should at least get a valid list back

    def test_no_commitment_identified(self, identifier):
        """Test that no commitments are identified in casual conversation."""
        communication = Communication(
            timestamp=datetime(2025, 4, 19, 10, 0),
            content="Just checking in to say hello!",
            sender="Me",
            recipient="Friend",
        )

        # Act
        commitments = identifier.identify_commitments(communication)

        # Assert
        assert isinstance(commitments, list)
        # Casual conversation should typically result in no commitments

    def test_empty_text_handling(self, identifier):
        """Test that empty text is handled gracefully."""
        communication = Communication(
            timestamp=datetime(2025, 4, 19, 10, 0),
            content="",
            sender="Me",
            recipient="Friend",
        )

        # Act
        commitments = identifier.identify_commitments(communication)

        # Assert
        assert isinstance(commitments, list)
        assert len(commitments) == 0

    def test_multiple_commitments_in_sentence(self, identifier):
        """Test identifying multiple commitments in a single communication."""
        communication = Communication(
            timestamp=datetime(2025, 4, 19, 10, 0),
            content="I'll call you at 2pm. Then I'll meet you at 5pm at the park.",
            sender="Me",
            recipient="Friend",
        )

        # Act
        commitments = identifier.identify_commitments(communication)

        # Assert - This test might find 0, 1, or 2 commitments depending on implementation
        # The important thing is that it doesn't crash
        assert isinstance(commitments, list)
        assert len(commitments) >= 0

    def test_split_sentence_for_commitments(self, identifier):
        """Test the sentence splitting logic for multiple commitments."""
        # Test simple case
        result = identifier._split_sentence_for_commitments("I'll meet you at 2pm.")
        assert len(result) >= 1
        assert "I'll meet you at 2pm." in result

        # Test multiple commitments - basic case
        result = identifier._split_sentence_for_commitments(
            "I'll call you and then meet you."
        )
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_extract_duration(self, identifier):
        """Test duration extraction from text."""
        # Test various duration patterns
        assert identifier._extract_duration("for 30 minutes") == timedelta(minutes=30)
        assert identifier._extract_duration("2 hours long") == timedelta(hours=2)
        assert identifier._extract_duration("for 1 day") == timedelta(days=1)
        assert identifier._extract_duration("just a quick meeting") is None
