import pytest
from datetime import datetime, timedelta
from audhd_lifecoach.core.domain.entities.commitment import Commitment
from audhd_lifecoach.core.domain.config import DEFAULT_TRAVEL_TIME, DEFAULT_PREP_TIME


class TestCommitment:
    def test_commitment_creation(self):
        """Test that a commitment can be created with basic attributes."""
        # Arrange
        start_time = datetime(2025, 4, 20, 15, 30)  # April 20, 2025 at 15:30
        end_time = start_time + timedelta(hours=1)  # Default 1 hour duration
        who = "Friend"
        what = "Give a ride to an event"
        where = "Friend's house"
        
        # Act
        commitment = Commitment(
            start_time=start_time,
            end_time=end_time,
            who=who,
            what=what,
            where=where
        )
        
        # Assert
        assert commitment.start_time == start_time
        assert commitment.end_time == end_time
        assert commitment.who == who
        assert commitment.what == what
        assert commitment.where == where
        
    def test_commitment_with_travel_and_prep_time(self):
        """Test that a commitment can be created with travel and prep time."""
        # Arrange
        start_time = datetime(2025, 4, 20, 15, 30)
        end_time = start_time + timedelta(hours=1)
        where = "Friend's house"
        estimated_travel_time = timedelta(minutes=25)
        estimated_prep_time = timedelta(minutes=10)
        
        # Act
        commitment = Commitment(
            start_time=start_time,
            end_time=end_time,
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
        start_time = datetime(2025, 4, 20, 15, 30)
        end_time = start_time + timedelta(hours=1)
        estimated_travel_time = timedelta(minutes=25)
        estimated_prep_time = timedelta(minutes=10)
        
        # Act
        commitment = Commitment(
            start_time=start_time,
            end_time=end_time,
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
        start_time = datetime(2025, 4, 20, 15, 30)
        end_time = start_time + timedelta(hours=1)
        
        # Act
        commitment = Commitment(
            start_time=start_time,
            end_time=end_time,
            who="Friend",
            what="Give a ride",
            where="Friend's house"
        )
        
        # Assert
        departure_time = commitment.calculate_departure_time()
        # Should use default values from config
        expected_departure = start_time - DEFAULT_TRAVEL_TIME - DEFAULT_PREP_TIME
        assert departure_time == expected_departure
        
    def test_missing_required_arguments(self):
        """Test that creating a commitment without required arguments raises an error."""
        # Missing 'start_time'
        with pytest.raises(TypeError):
            Commitment(end_time=datetime.now(), who="Friend", what="Call", where="Phone")
            
        # Missing 'end_time'
        with pytest.raises(TypeError):
            Commitment(start_time=datetime.now(), who="Friend", what="Call", where="Phone")
            
        # Missing 'who'
        with pytest.raises(TypeError):
            Commitment(start_time=datetime.now(), end_time=datetime.now() + timedelta(hours=1), what="Call", where="Phone")
            
        # Missing 'what'
        with pytest.raises(TypeError):
            Commitment(start_time=datetime.now(), end_time=datetime.now() + timedelta(hours=1), who="Friend", where="Phone")
            
        # Missing 'where'
        with pytest.raises(TypeError):
            Commitment(start_time=datetime.now(), end_time=datetime.now() + timedelta(hours=1), who="Friend", what="Call")
            
    def test_str_representation(self):
        """Test the string representation of a commitment."""
        # Arrange
        start_time = datetime(2025, 4, 20, 15, 30)
        end_time = start_time + timedelta(hours=1)
        commitment = Commitment(
            start_time=start_time,
            end_time=end_time,
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
        
    def test_duration_property(self):
        """Test that the duration property correctly calculates the time between start and end."""
        # Arrange
        start_time = datetime(2025, 4, 20, 15, 30)
        end_time = start_time + timedelta(hours=1, minutes=30)  # 1.5 hour duration
        
        commitment = Commitment(
            start_time=start_time,
            end_time=end_time,
            who="Friend",
            what="Give a ride",
            where="Friend's house"
        )
        
        # Act & Assert
        assert commitment.duration == timedelta(hours=1, minutes=30)
        assert commitment.duration.total_seconds() == 5400  # 1.5 hours = 5400 seconds