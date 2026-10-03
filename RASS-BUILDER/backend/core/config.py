"""
RASS-BUILDER: Stage 10 Production Configuration & Environment Validation
Manages application configuration, environment parsing, and startup validation.
"""

import os
from pathlib import Path
from typing import List, Dict, Any


class AppConfig:
    """
    Centralized configuration management for RASS-BUILDER.
    Validates required settings and provides safe operational defaults.
    """

    def __init__(self):
        self.env = os.environ.get("RASS_ENV", "production").lower()
        self.log_level = os.environ.get("RASS_LOG_LEVEL", "INFO").upper()

        # Database Path
        default_db = Path(__file__).resolve().parent.parent / "data" / "rass_builder.db"
        self.db_path = Path(os.environ.get("RASS_DB_PATH") or os.environ.get("DATABASE_PATH") or default_db)

        # CORS Configuration
        raw_origins = os.environ.get("RASS_CORS_ORIGINS")
        if raw_origins:
            self.cors_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
        else:
            self.cors_origins = [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
            ]

        # Upload & Request Size Limits (default: 25 MB)
        max_upload_mb = int(os.environ.get("RASS_MAX_UPLOAD_SIZE_MB", "25"))
        self.max_upload_size_bytes = max_upload_mb * 1024 * 1024

        # Rate Limiting
        rate_limit_env = os.environ.get("RASS_RATE_LIMIT_ENABLED", "1").lower()
        self.rate_limit_enabled = rate_limit_env in ("1", "true", "yes", "on")

        # Security
        self.require_auth = os.environ.get("RASS_REQUIRE_AUTH", "0") == "1"

    def validate(self) -> Dict[str, Any]:
        """
        Validates configuration sanity on application startup.
        Returns a sanitized configuration summary strictly omitting any secrets.
        """
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level not in valid_log_levels:
            self.log_level = "INFO"

        # Ensure directory for database exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        return {
            "environment": self.env,
            "log_level": self.log_level,
            "database_path": str(self.db_path),
            "cors_origins_count": len(self.cors_origins),
            "max_upload_size_mb": self.max_upload_size_bytes // (1024 * 1024),
            "rate_limiting_enabled": self.rate_limit_enabled,
            "require_auth_strict": self.require_auth,
        }


# Global config instance
settings = AppConfig()
