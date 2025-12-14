"""
Configuration Management
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import os
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = Field(default="API Key Manager")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    secret_key: str = Field(default="change-me-in-production")
    api_version: str = Field(default="v1")
    
    database_url: str = Field(default="sqlite+aiosqlite:///./api_key_manager.db")
    
    jwt_secret_key: str = Field(default="change-me-jwt-secret")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    
    master_encryption_key: str = Field(default="")
    
    rate_limit_per_minute: int = Field(default=60)
    rate_limit_per_hour: int = Field(default=1000)
    rate_limit_per_day: int = Field(default=10000)
    
    allowed_hosts: str = Field(default="localhost,127.0.0.1")
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8000")
    max_login_attempts: int = Field(default=5)
    lockout_duration_minutes: int = Field(default=15)
    
    auto_rotation_enabled: bool = Field(default=True)
    default_key_expiry_days: int = Field(default=90)
    rotation_warning_days: int = Field(default=7)
    grace_period_hours: int = Field(default=24)
    
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    webhook_enabled: bool = Field(default=False)
    webhook_url: Optional[str] = Field(default=None)
    webhook_secret: Optional[str] = Field(default=None)
    
    anomaly_detection_enabled: bool = Field(default=True)
    anomaly_threshold: float = Field(default=3.0)
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        return [h.strip() for h in self.allowed_hosts.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
