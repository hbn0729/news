"""
Scheduler-only entry point for news collection.

This script runs ONLY the scheduler, not the web server.
It should be deployed as a separate container with replica=1.
"""

import asyncio
import logging
import signal
import sys

from app.config import settings
from app.database import init_db
from app.services.scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Global flag for graceful shutdown
shutdown_event = asyncio.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()


async def main():
    """Main scheduler loop."""
    try:
        # Initialize database
        logger.info(f"Initializing database for {settings.APP_NAME} Scheduler")
        await init_db()

        # Start scheduler
        logger.info("Starting news collection scheduler...")
        start_scheduler()
        logger.info("Scheduler started successfully")

        # Wait for shutdown signal
        await shutdown_event.wait()

    except Exception as e:
        logger.exception(f"Fatal error in scheduler: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        logger.info("Stopping scheduler...")
        stop_scheduler()
        logger.info("Scheduler stopped. Exiting.")


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
