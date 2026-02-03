"""API Key authentication middleware for protecting endpoints."""

from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.config import settings

# Define API key header security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """
    Dependency that validates API key from X-API-Key header.

    Raises:
        HTTPException: 401 if API key is missing or invalid

    Returns:
        The validated API key
    """
    # If no API key configured, allow all requests (development mode)
    if not settings.API_SECRET_KEY:
        return ""

    # Check if API key was provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Provide X-API-Key header.",
        )

    # Validate API key
    if api_key != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return api_key
