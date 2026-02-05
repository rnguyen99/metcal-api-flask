"""Application configuration utilities."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Container for environment-driven settings."""

    database_path: str = os.getenv("DATABASE_PATH", "asset.db")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expires_hours: int = int(os.getenv("JWT_EXPIRES_HOURS", "24"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", str(Path("logs") / "api.log"))
    issuer: str = os.getenv("JWT_ISSUER", "metcal-api")
    audience: str = os.getenv("JWT_AUDIENCE", "metcal-clients")


settings = Settings()
