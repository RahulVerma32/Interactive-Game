from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os

class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    DATABASE_URL: Optional[str] = None

    ALLOWED_ORIGINS: str = ""

    OPENAI_API_KEY: Optional[str] = None
    GITHUB_TOKEN: Optional[str] = None

    def __init__(self, **values):
        super().__init__(**values)
        
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
        
        # Fallback to SQLite if DATABASE_URL is still not set
        if not self.DATABASE_URL:
            self.DATABASE_URL = "sqlite:///./database.db"

    @field_validator("ALLOWED_ORIGINS")
    def parse_allowed_origins(cls, v: str) -> List[str]:
        return v.split(",") if v else []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()