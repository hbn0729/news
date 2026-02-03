from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/news_db"

    # Proxy settings (for accessing Google News from China)
    # Format: http://host:port or http://user:pass@host:port
    HTTP_PROXY: str | None = None
    HTTPS_PROXY: str | None = None

    # App settings
    APP_NAME: str = "Financial News Aggregator"
    DEBUG: bool = False

    # Collection settings
    COLLECTION_INTERVAL_SECONDS: int = 30  # 实时抓取间隔（秒）- 财联社等快讯数据源
    COLLECTION_INTERVAL_MINUTES: int = 1  # 备用：分钟级抓取间隔（未使用）
    COLLECTION_INTERVAL_HOURS: int = 1  # 备用：小时级抓取间隔（未使用）
    COLLECTION_MAX_CONCURRENCY: int = 5

    NEWS_RETENTION_DAYS: int = 7
    CLEANUP_TIMEZONE: str = "Asia/Shanghai"

    # Security
    API_SECRET_KEY: str = (
        ""  # Required for production - API key for protected endpoints
    )
    ALLOWED_ORIGINS: str = ""  # Comma-separated list of allowed CORS origins

    # Scheduler control
    DISABLE_SCHEDULER: bool = False  # Set to True for web-only containers

    # Jin10 API credentials
    JIN10_APP_ID: str = "bVBF4FyRTn5NJF5n"  # Default app ID
    JIN10_VERSION: str = "1.0.0"  # Default version

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
