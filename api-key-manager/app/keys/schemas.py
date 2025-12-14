"""
API Key Schemas
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    permissions: List[str] = Field(default=["read"])
    allowed_services: List[str] = Field(default=[])
    allowed_ips: List[str] = Field(default=[])
    allowed_user_agents: List[str] = Field(default=[])
    environment: str = Field(default="production")
    rate_limit_per_minute: Optional[int] = Field(default=None, ge=1, le=10000)
    rate_limit_per_hour: Optional[int] = Field(default=None, ge=1, le=100000)
    rate_limit_per_day: Optional[int] = Field(default=None, ge=1, le=1000000)
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)
    
    @validator("permissions")
    def validate_permissions(cls, v):
        valid_permissions = {"read", "write", "delete", "admin"}
        for perm in v:
            if perm not in valid_permissions:
                raise ValueError(f"Invalid permission: {perm}")
        return v
    
    @validator("environment")
    def validate_environment(cls, v):
        valid_envs = {"development", "staging", "production"}
        if v not in valid_envs:
            raise ValueError(f"Invalid environment: {v}")
        return v


class APIKeyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    key_prefix: str
    status: str
    permissions: List[str]
    allowed_services: List[str]
    allowed_ips: List[str]
    environment: str
    rate_limit_per_minute: Optional[int]
    rate_limit_per_hour: Optional[int]
    rate_limit_per_day: Optional[int]
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class APIKeyCreatedResponse(APIKeyResponse):
    api_key: str


class APIKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    allowed_services: Optional[List[str]] = None
    allowed_ips: Optional[List[str]] = None
    allowed_user_agents: Optional[List[str]] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=10000)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000)
    rate_limit_per_day: Optional[int] = Field(None, ge=1, le=1000000)
    
    @validator("permissions")
    def validate_permissions(cls, v):
        if v is None:
            return v
        valid_permissions = {"read", "write", "delete", "admin"}
        for perm in v:
            if perm not in valid_permissions:
                raise ValueError(f"Invalid permission: {perm}")
        return v


class APIKeyRotateRequest(BaseModel):
    grace_period_hours: Optional[int] = Field(default=24, ge=0, le=168)


class APIKeyRotateResponse(BaseModel):
    old_key_id: str
    new_key: APIKeyCreatedResponse
    grace_period_ends_at: Optional[datetime]


class APIKeyListResponse(BaseModel):
    items: List[APIKeyResponse]
    total: int
    page: int
    page_size: int
    pages: int


class APIKeyValidationResult(BaseModel):
    valid: bool
    key_id: Optional[str] = None
    permissions: List[str] = []
    error: Optional[str] = None
