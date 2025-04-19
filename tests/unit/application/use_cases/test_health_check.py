import pytest
from audhd_lifecoach.application.use_cases.health_check import health_check_use_case


def test_health_check_returns_status_and_version():
    """Test that health check use case returns expected data structure."""
    # Act
    result = health_check_use_case()
    
    # Assert
    assert isinstance(result, dict)
    assert "status" in result
    assert "version" in result
    assert result["status"] == "healthy"
    assert result["version"] == "0.1.0"