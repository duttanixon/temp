from pydantic_settings import BaseSettings
from typing import Optional, List
import secrets

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Email
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
settings = Settings()

    

