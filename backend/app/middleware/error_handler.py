"""Global error handler middleware to prevent information leakage."""

import logging
import uuid
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler that sanitizes error responses.

    - Logs full error details server-side for debugging
    - Returns generic error messages to clients
    - Generates unique error ID for correlation

    Args:
        request: The incoming request
        exc: The exception that was raised

    Returns:
        JSONResponse with sanitized error message
    """
    # Generate unique error ID for tracking
    error_id = str(uuid.uuid4())[:8]

    # Log full exception details server-side (with error ID)
    logger.exception(f"Error {error_id}: {type(exc).__name__}: {str(exc)}")

    # Return generic error to client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_id": error_id,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler for intentional HTTP exceptions (from raise HTTPException).

    These are already safe to return to clients as they're explicitly raised
    by application code with intended messages.

    Args:
        request: The incoming request
        exc: The HTTP exception

    Returns:
        JSONResponse with the exception's detail
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handler for request validation errors (invalid request data).

    Sanitizes validation errors to prevent leaking internal structure.

    Args:
        request: The incoming request
        exc: The validation exception

    Returns:
        JSONResponse with sanitized validation error
    """
    # Log validation errors for debugging
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")

    # Return sanitized validation error
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Invalid request data",
            "errors": [
                {
                    "field": ".".join(str(loc) for loc in err["loc"]),
                    "message": err["msg"],
                }
                for err in exc.errors()
            ],
        },
    )


def register_error_handlers(app):
    """
    Register all error handlers with the FastAPI application.

    Args:
        app: The FastAPI application instance
    """
    # Handle intentional HTTP exceptions (keep their messages)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Handle validation errors with sanitized output
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Catch-all for unexpected exceptions
    app.add_exception_handler(Exception, global_exception_handler)
