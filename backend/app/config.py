import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings with environment-based configuration"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Environment
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_ssl: bool = Field(default=False, alias="REDIS_SSL")
    redis_connection_timeout: int = Field(default=5, alias="REDIS_CONNECTION_TIMEOUT")
    redis_max_retries: int = Field(default=3, alias="REDIS_MAX_RETRIES")
    
    # Bloom Filter Configuration
    bloom_expected_items: int = Field(default=1_000_000, alias="BLOOM_EXPECTED_ITEMS")
    bloom_false_positive_rate: float = Field(default=0.001, alias="BLOOM_FALSE_POSITIVE_RATE")
    bloom_redis_key: str = Field(default="bloom:passwords", alias="BLOOM_REDIS_KEY")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_workers: int = Field(default=1, alias="API_WORKERS")
    
    # Security
    cors_origins: List[str] = Field(default=["*"], alias="CORS_ORIGINS")
    api_key: Optional[str] = Field(default=None, alias="API_KEY")
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ["production", "prod"]
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() in ["development", "dev", "local"]
    
    @property
    def redis_url(self) -> str:
        """Build Redis connection URL"""
        scheme = "rediss" if self.redis_ssl else "redis"
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"{scheme}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

# Global settings instance
settings = Settings()
