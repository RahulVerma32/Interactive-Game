from typing import List, Optional, Literal
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from pydantic import field_validator
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env", PROJECT_DIR / ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    DATABASE_URL: Optional[str] = None
    DATABASE_URL_UNPOOLED: Optional[str] = None
    NEON_AUTH_BASE_URL: Optional[str] = None
    NEON_AUTH_JWKS_URL: Optional[str] = None

    ALLOWED_ORIGINS: str = ""

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    OPENROUTER_API_KEY: Optional[str] = None
    STORY_LLM_MODEL: str = "openrouter/free"
    SESSION_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    SESSION_COOKIE_SECURE: bool = False

    def __init__(self, **values):
        super().__init__(**values)
        if self.SESSION_COOKIE_SAMESITE == "none" and not self.SESSION_COOKIE_SECURE:
            raise ValueError("SESSION_COOKIE_SECURE must be true when SameSite is none")
        
        # Only build DATABASE_URL from components if not already set
        if not self.DATABASE_URL and not self.DEBUG:
            db_user = os.getenv("DB_USER")
            db_password = os.getenv("DB_PASSWORD")
            db_host = os.getenv("DB_HOST")
            db_port = os.getenv("DB_PORT")
            db_name = os.getenv("DB_NAME")
            
            # Only build URL if all components are present
            if all([db_user, db_password, db_host, db_port, db_name]):
                self.DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # SQLite is for local development only; a deployment needs persistent storage.
        if not self.DATABASE_URL:
            if self.DEBUG:
                self.DATABASE_URL = "sqlite:///./database.db"
            else:
                raise ValueError("DATABASE_URL is required when DEBUG is false")

    @field_validator("ALLOWED_ORIGINS")
    def parse_allowed_origins(cls, v: str) -> List[str]:
        return v.split(",") if v else []

settings = Settings()
