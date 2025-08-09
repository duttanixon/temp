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

    # AWS Settings
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] =None
    AWS_ACCOUNT_ID: Optional[str] = None
    IOT_CUSTOMER_POLICY_NAME: Optional[str] = None
    IOT_CUSTOMER_POLICY_ARN: Optional[str] = None
    IOT_DEVICE_POLICY_NAME: Optional[str] = None
    IOT_DEVICE_POLICY_ARN: Optional[str] = None
    IOT_ENABLED: bool = True  # Flag to enable/disable IoT integration
    
    # S3 Settings
    S3_BUCKET_NAME: Optional[str] = None
    S3_CERTIFICATES_PATH: Optional[str] = None
    TIMESTREAM_DATABASE: Optional[str] = None
    TIMESTREAM_RAW_TABLE: Optional[str] = None
    AI_MODEL_BUCKET_NAME: Optional[str] = None

    # API Key for internal services
    INTERNAL_API_KEY: Optional[str] = None
    FRONTEND_URL: Optional[str] = None
    RESTART_APP_TEMPLATE_ARN: Optional[str] = None
    REBOOT_TEMPLATE_ARN: Optional[str] = None


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
settings = Settings()

    

