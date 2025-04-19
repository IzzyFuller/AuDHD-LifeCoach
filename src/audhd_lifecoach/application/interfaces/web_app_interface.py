"""
Web Application Interface that defines how external web frameworks 
should interact with our application layer.
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Type


class WebAppInterface(ABC):
    """Interface for web framework adapters."""
    
    @abstractmethod
    def register_route(
        self, 
        path: str, 
        http_method: str, 
        handler_func: Callable,
        response_model: Optional[Type] = None,
        status_code: int = 200,
        **kwargs
    ) -> None:
        """Register a route with the web framework."""
        pass
    
    @abstractmethod
    def get_app(self) -> Any:
        """Return the underlying web application instance."""
        pass
    
    @abstractmethod
    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs) -> None:
        """Run the web application server."""
        pass