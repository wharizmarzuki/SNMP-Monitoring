from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional

class Settings(BaseSettings):
    # SNMP Configuration
    snmp_community: str = Field(
        default="public",
        validation_alias="SNMP_COMMUNITY",  # Changed from env
        description="SNMP community string for device access"
    )
    snmp_timeout: int = Field(
        default=10,
        validation_alias="SNMP_TIMEOUT",  # Changed from env
        ge=1, le=60,
        description="SNMP timeout in seconds"
    )
    snmp_retries: int = Field(
        default=3,
        validation_alias="SNMP_RETRIES",  # Changed from env
        ge=0, le=10,
        description="Number of SNMP retry attempts"
    )
    
    # Database Configuration  
    database_url: str = Field(
        default="sqlite:///./monitoring.db",
        validation_alias="DATABASE_URL",  # Changed from env
        description="Database connection URL"
    )
    
    # Application Settings
    polling_interval: int = Field(
        default=60,
        validation_alias="POLLING_INTERVAL",  # Changed from env
        ge=10, le=3600,
        description="Device polling interval in seconds"
    )
    discovery_concurrency: int = Field(
        default=20,
        validation_alias="DISCOVERY_CONCURRENCY",  # Changed from env
        ge=1, le=100,
        description="Max concurrent device discovery operations"
    )
    polling_concurrency: int = Field(
        default=20,
        validation_alias="POLLING_CONCURRENCY",  # Changed from env
        ge=1, le=100,
        description="Max concurrent polling operations"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",  # Changed from env
        description="Logging level"
    )
    log_file: Optional[str] = Field(
        default=None,
        validation_alias="LOG_FILE",  # Changed from env
        description="Log file path (optional)"
    )
    # Email Configuration
    smtp_server: str = Field(default="smtp.gmail.com", validation_alias="SMTP_SERVER")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    sender_email: str = Field(default="", validation_alias="SENDER_EMAIL")
    sender_password: str = Field(default="", validation_alias="SENDER_PASSWORD")

    # Redis Cache Configuration
    redis_host: str = Field(
        default="localhost",
        validation_alias="REDIS_HOST",
        description="Redis server hostname"
    )
    redis_port: int = Field(
        default=6379,
        validation_alias="REDIS_PORT",
        ge=1, le=65535,
        description="Redis server port"
    )
    redis_db: int = Field(
        default=0,
        validation_alias="REDIS_DB",
        ge=0, le=15,
        description="Redis database number (0-15)"
    )
    cache_enabled: bool = Field(
        default=True,
        validation_alias="CACHE_ENABLED",
        description="Enable/disable Redis caching"
    )

    # Environment
    environment: str = Field(
        default="development",
        validation_alias="ENVIRONMENT",  # Changed from env
        description="Application environment"
    )
    debug: bool = Field(
        default=False,
        validation_alias="DEBUG",  # Changed from env
        description="Enable debug mode"
    )

    # Validators remain the same
    @field_validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()

    @field_validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v.lower() not in valid_envs:
            raise ValueError(f'Environment must be one of: {valid_envs}')
        return v.lower()

    # Replaced inner Config class
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True  # Allows using field names directly
    )

settings = Settings()