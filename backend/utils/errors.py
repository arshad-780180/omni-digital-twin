import os
import logging
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("omni.errors")


class OmniException(Exception):
    """Base exception for OMNI Digital Twin domain errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AIProviderError(OmniException):
    """Raised when an AI provider (e.g. Gemini) encounters an unrecoverable failure."""
    def __init__(self, message: str = "AI service unavailable"):
        super().__init__(message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class DatabaseOperationError(OmniException):
    """Raised when a database operation fails."""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResourceNotFoundError(OmniException):
    """Raised when a requested resource is not found."""
    def __init__(self, message: str = "Requested resource not found"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedError(OmniException):
    """Raised when authentication or authorization fails."""
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


def get_cors_headers(request: Request) -> dict:
    """Helper to ensure CORS headers are present on exception responses."""
    origin = request.headers.get("origin")
    if not origin:
        return {}
    
    allowed = [
        "http://localhost:5173", "http://localhost:5174",
        "http://127.0.0.1:5173", "http://127.0.0.1:5174",
        "http://localhost:3000"
    ]
    env_origins = os.getenv("CORS_ORIGINS")
    if env_origins:
        allowed.extend([o.strip() for o in env_origins.split(",") if o.strip()])
    
    if origin in allowed:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    return {}


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers global centralized exception handlers on the FastAPI application.
    Ensures structured JSON error responses across all routes.
    """
    @app.exception_handler(OmniException)
    async def omni_exception_handler(request: Request, exc: OmniException):
        logger.warning(f"OmniException [{exc.status_code}]: {exc.message} on {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": exc.message, "path": request.url.path},
            headers=get_cors_headers(request)
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.info(f"HTTPException [{exc.status_code}]: {exc.detail} on {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": str(exc.detail), "path": request.url.path},
            headers=get_cors_headers(request)
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled server error on {request.url.path}: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal Server Error",
                "detail": str(exc),
                "path": request.url.path
            },
            headers=get_cors_headers(request)
        )
