from typing import Any, Callable, Dict, List, Optional, Type, Union

from fastapi import FastAPI, APIRouter, HTTPException
import uvicorn

from audhd_lifecoach.application.interfaces.web_app_interface import WebAppInterface


class FastAPIAdapter(WebAppInterface):
    """Adapter for FastAPI that implements the WebAppInterface."""
    
    def __init__(self, title: str = "AuDHD LifeCoach", description: str = "A life coach application for people with AuDHD"):
        """Initialize the FastAPI adapter."""
        self.app = FastAPI(title=title, description=description)
        self.router = APIRouter()
        
    def register_route(
        self,
        path: str,
        http_method: str,
        handler_func: Callable,
        response_model: Optional[Type] = None,
        status_code: int = 200,
        **kwargs
    ) -> None:
        """Register a route with FastAPI."""
        method = http_method.lower()
        
        # Get the appropriate method from the router
        if method == "get":
            route_method = self.router.get
        elif method == "post":
            route_method = self.router.post
        elif method == "put":
            route_method = self.router.put
        elif method == "delete":
            route_method = self.router.delete
        elif method == "patch":
            route_method = self.router.patch
        else:
            raise ValueError(f"HTTP method {http_method} not supported")
        
        # Register the route
        route_method(
            path=path,
            response_model=response_model,
            status_code=status_code,
            **kwargs
        )(handler_func)
    
    def get_app(self) -> FastAPI:
        """Return the FastAPI application instance."""
        # Make sure the router is included in the app
        self.app.include_router(self.router)
        return self.app
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs) -> None:
        """Run the FastAPI application with Uvicorn."""
        app = self.get_app()
        uvicorn.run(app, host=host, port=port, **kwargs)