import os
import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    APP_NAME: str = "moobaan_smart_backend"
    ENV: str = "local"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # PostgreSQL ONLY - NO DEFAULTS to prevent misconfiguration
    DATABASE_URL: str = ""  # MUST be provided via environment
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production-use-openssl-rand-hex-32"
    
    class Config:
        env_file = ".env"

    def __post_init__(self):
        """Validate configuration on startup - FAIL FAST on misconfiguration"""
        self._validate_database_url()
        self._log_database_config()

    def _validate_database_url(self):
        """Enforce PostgreSQL + psycopg v3 ONLY"""
        if not self.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL environment variable is required. "
                "Expected format: postgresql+psycopg://user:password@host:port/dbname"
            )
        
        if not self.DATABASE_URL.startswith("postgresql+psycopg://"):
            raise RuntimeError(
                f"Invalid DATABASE_URL scheme. Got: {self.DATABASE_URL[:30]}... "
                f"Expected: postgresql+psycopg://user:password@host:port/dbname. "
                f"This enforces PostgreSQL with psycopg v3 driver ONLY."
            )
        
        logger.info("✅ DATABASE_URL validation passed - PostgreSQL + psycopg v3 confirmed")

    def _log_database_config(self):
        """Log resolved SQLAlchemy dialect and driver for debugging"""
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.engine.url import make_url
            
            url = make_url(self.DATABASE_URL)
            logger.info(f"🔍 Database Config:")
            logger.info(f"  - Driver: {url.drivername}")
            logger.info(f"  - Host: {url.host}")
            logger.info(f"  - Database: {url.database}")
            
            # Create temporary engine to verify dialect resolution
            temp_engine = create_engine(self.DATABASE_URL, strategy='mock', executor=lambda *a, **kw: None)
            logger.info(f"  - SQLAlchemy Dialect: {temp_engine.dialect.__class__.__name__}")
            logger.info(f"  - Driver Module: {temp_engine.dialect.driver}")
            
        except Exception as e:
            logger.warning(f"Could not log database config details: {e}")


# Initialize settings with validation
try:
    settings = Settings()
    settings.__post_init__()
except Exception as e:
    logger.error(f"❌ Configuration validation failed: {e}")
    raise