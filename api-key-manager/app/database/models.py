"""
Database Models
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, 
    ForeignKey, JSON, Enum as SQLEnum, Index, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.database.connection import Base


def generate_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    READONLY = "readonly"


class KeyStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ROTATING = "rotating"


class Permission(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.DEVELOPER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    api_keys = relationship("APIKey", back_populates="owner", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="refresh_tokens")


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    key_prefix = Column(String(10), nullable=False, index=True)
    key_hash = Column(String(255), nullable=False, unique=True)
    encrypted_metadata = Column(Text, nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(SQLEnum(KeyStatus), default=KeyStatus.ACTIVE, nullable=False, index=True)
    permissions = Column(JSON, default=list)
    allowed_services = Column(JSON, default=list)
    allowed_ips = Column(JSON, default=list)
    allowed_user_agents = Column(JSON, default=list)
    environment = Column(String(50), default="production")
    rate_limit_per_minute = Column(Integer, nullable=True)
    rate_limit_per_hour = Column(Integer, nullable=True)
    rate_limit_per_day = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    rotated_from_id = Column(String(36), ForeignKey("api_keys.id"), nullable=True)
    grace_period_ends_at = Column(DateTime, nullable=True)
    
    owner = relationship("User", back_populates="api_keys")
    audit_logs = relationship("AuditLog", back_populates="api_key", cascade="all, delete-orphan")
    usage_stats = relationship("UsageStats", back_populates="api_key", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_api_keys_owner_status", "owner_id", "status"),
        Index("ix_api_keys_prefix_hash", "key_prefix", "key_hash"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    api_key_id = Column(String(36), ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    endpoint = Column(String(500), nullable=True)
    method = Column(String(10), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(36), nullable=True)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    api_key = relationship("APIKey", back_populates="audit_logs")
    
    __table_args__ = (
        Index("ix_audit_logs_timestamp_action", "timestamp", "action"),
        Index("ix_audit_logs_api_key_timestamp", "api_key_id", "timestamp"),
    )


class UsageStats(Base):
    __tablename__ = "usage_stats"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    api_key_id = Column(String(36), ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=False)
    request_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    avg_response_time_ms = Column(Float, default=0)
    endpoints_accessed = Column(JSON, default=dict)
    unique_ips = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    api_key = relationship("APIKey", back_populates="usage_stats")
    
    __table_args__ = (
        Index("ix_usage_stats_api_key_period", "api_key_id", "period_start", "period_type"),
    )


class RateLimitBucket(Base):
    __tablename__ = "rate_limit_buckets"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    key_identifier = Column(String(255), nullable=False, index=True)
    bucket_type = Column(String(20), nullable=False)
    tokens = Column(Integer, default=0)
    last_refill = Column(DateTime, default=datetime.utcnow)
    blocked_until = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("ix_rate_limit_key_type", "key_identifier", "bucket_type", unique=True),
    )


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnomalyDetection(Base):
    __tablename__ = "anomaly_detections"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    api_key_id = Column(String(36), ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False)
    anomaly_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    detected_value = Column(Float, nullable=True)
    expected_range = Column(JSON, nullable=True)
    action_taken = Column(String(100), nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
