"""Application health check use case."""
from typing import Dict, Any


def health_check_use_case() -> Dict[str, Any]:
    """
    Simple health check use case.
    
    This use case returns data that indicates the system is operational.
    It belongs in the application layer as it's not core domain logic
    but rather an operational concern of the application itself.
    """
    return {"status": "healthy", "version": "0.1.0"}