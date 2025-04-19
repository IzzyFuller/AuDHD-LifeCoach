import pytest
from datetime import datetime, timedelta
from audhd_lifecoach.core.domain.entities.commitment import Commitment


class TestCommitment:
    def test_commitment_creation(self):
        """Test that a commitment can be created with basic attributes."""
        # Arrange
        when = datetime(2025, 4, 20, 15, 30)  # April 20, 2025 at 15:30
        who = "Friend"
        what = "Give a ride to an event"
        where = "Friend's house"
        
        # Act
        commitment = Commitment(
            when=when,
            who=who,
            what=what,
            where=where
        )
        
        # Assert
        assert commitment.when == when
        assert commitment.who == who
        assert commitment.what == what
        assert commitment.where == where
        
    def test_commitment_with_travel_and_prep_time(self):
        """Test that a commitment can be created with travel and prep time."""
        # Arrange
        when = datetime(2025, 4, 20, 15, 30)
        where = "Friend's house"
        estimated_travel_time = timedelta(minutes=25)
        estimated_prep_time = timedelta(minutes=10)
        
        # Act
        commitment = Commitment(
            when=when,
            who="Friend",
            what="Give a ride",
            where=where,
            estimated_travel_time=estimated_travel_time,
            estimated_prep_time=estimated_prep_time
        )
        
        # Assert
        assert commitment.estimated_travel_time == estimated_travel_time
        assert commitment.estimated_prep_time == estimated_prep_time
        
    def test_commitment_lead_time_calculation(self):
        """Test that a commitment can calculate lead time needed."""
        # Arrange
        when = datetime(2025, 4, 20, 15, 30)
        estimated_travel_time = timedelta(minutes=25)
        estimated_prep_time = timedelta(minutes=10)
        
        # Act
        commitment = Commitment(
            when=when,
            who="Friend",
            what="Give a ride",
            where="Friend's house",
            estimated_travel_time=estimated_travel_time,
            estimated_prep_time=estimated_prep_time
        )
        
        # Assert
        # Should return when we need to start getting ready
        departure_time = commitment.calculate_departure_time()
        expected_departure = datetime(2025, 4, 20, 14, 55)  # 15:30 - 25min travel - 10min prep
        assert departure_time == expected_departure
        
    def test_commitment_without_travel_and_prep_time(self):
        """Test that departure time uses default values when travel and prep times are not provided."""
        # Arrange
        when = datetime(2025, 4, 20, 15, 30)
        
        # Act
        commitment = Commitment(
            when=when,
            who="Friend",
            what="Give a ride",
            where="Friend's house"
        )
        
        # Assert
        departure_time = commitment.calculate_departure_time()
        # Should use default values (e.g., 15 mins travel, 5 mins prep)
        expected_departure = when - commitment.DEFAULT_TRAVEL_TIME - commitment.DEFAULT_PREP_TIME
        assert departure_time == expected_departure
        
    def test_missing_required_arguments(self):
        """Test that creating a commitment without required arguments raises an error."""
        # Missing 'when'
        with pytest.raises(TypeError):
            Commitment(who="Friend", what="Call", where="Phone")
            
        # Missing 'who'
        with pytest.raises(TypeError):
            Commitment(when=datetime.now(), what="Call", where="Phone")
            
        # Missing 'what'
        with pytest.raises(TypeError):
            Commitment(when=datetime.now(), who="Friend", where="Phone")
            
        # Missing 'where'
        with pytest.raises(TypeError):
            Commitment(when=datetime.now(), who="Friend", what="Call")
            
    def test_str_representation(self):
        """Test the string representation of a commitment."""
        # Arrange
        when = datetime(2025, 4, 20, 15, 30)
        commitment = Commitment(
            when=when,
            who="Friend",
            what="Give a ride",
            where="Friend's house"
        )
        
        # Act
        str_repr = str(commitment)
        
        # Assert
        assert "Friend" in str_repr
        assert "Give a ride" in str_repr
        assert "Friend's house" in str_repr
        assert "15:30" in str_repr