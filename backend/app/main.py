import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import settings
from app.database import init_db
from app.services.scheduler import start_scheduler, stop_scheduler
from app.middleware.error_handler import register_error_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME}")
    await init_db()

    # Only start scheduler if not disabled
    if not settings.DISABLE_SCHEDULER:
        logger.info("Starting news collection scheduler...")
        start_scheduler()
    else:
        logger.info("Scheduler disabled (DISABLE_SCHEDULER=true)")

    yield

    # Shutdown
    if not settings.DISABLE_SCHEDULER:
        stop_scheduler()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="Financial news aggregation platform with AI filtering",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - configure allowed origins from environment
allowed_origins = []
if settings.ALLOWED_ORIGINS:
    # Parse comma-separated origins
    allowed_origins = [
        origin.strip()
        for origin in settings.ALLOWED_ORIGINS.split(",")
        if origin.strip()
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else [],
    allow_origin_regex=r"^https?://(\d{1,3}(\.\d{1,3}){3})(:\d+)?$"
    if not allowed_origins
    else None,
    allow_credentials=False,  # Set to True only if needed with credentials
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Accept", "X-API-Key"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Register error handlers for security
register_error_handlers(app)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
