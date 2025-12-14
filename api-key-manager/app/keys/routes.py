"""
API Key Routes
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.connection import get_db
from app.database.models import APIKey, KeyStatus, User, UserRole
from app.auth.dependencies import get_current_user, require_role
from app.security.hashing import hashing_service
from app.security.key_generator import key_generator
from app.security.encryption import encryption_service
from app.logs.audit import audit_logger
from app.utils.config import settings
from app.keys.schemas import (
    APIKeyCreate, APIKeyResponse, APIKeyCreatedResponse, APIKeyUpdate,
    APIKeyRotateRequest, APIKeyRotateResponse, APIKeyListResponse
)

router = APIRouter(prefix="/keys", tags=["API Keys"])


@router.post("", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    raw_key, key_prefix = key_generator.generate_api_key()
    key_hash = hashing_service.hash_api_key(raw_key)
    
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
    elif settings.default_key_expiry_days:
        expires_at = datetime.utcnow() + timedelta(days=settings.default_key_expiry_days)
    
    metadata = {
        "created_by": current_user.username,
        "created_from_ip": request.client.host if request.client else None
    }
    encrypted_metadata = encryption_service.encrypt_dict(metadata)
    
    new_key = APIKey(
        name=key_data.name,
        description=key_data.description,
        key_prefix=key_prefix,
        key_hash=key_hash,
        encrypted_metadata=encrypted_metadata,
        owner_id=current_user.id,
        permissions=key_data.permissions,
        allowed_services=key_data.allowed_services,
        allowed_ips=key_data.allowed_ips,
        allowed_user_agents=key_data.allowed_user_agents,
        environment=key_data.environment,
        rate_limit_per_minute=key_data.rate_limit_per_minute,
        rate_limit_per_hour=key_data.rate_limit_per_hour,
        rate_limit_per_day=key_data.rate_limit_per_day,
        expires_at=expires_at
    )
    
    db.add(new_key)
    await db.flush()
    
    await audit_logger.log(
        db=db,
        action="api_key_created",
        user_id=current_user.id,
        api_key_id=new_key.id,
        ip_address=request.client.host if request.client else None,
        metadata={"key_name": key_data.name, "environment": key_data.environment}
    )
    
    return APIKeyCreatedResponse(
        id=new_key.id,
        name=new_key.name,
        description=new_key.description,
        key_prefix=new_key.key_prefix,
        status=new_key.status.value,
        permissions=new_key.permissions,
        allowed_services=new_key.allowed_services,
        allowed_ips=new_key.allowed_ips,
        environment=new_key.environment,
        rate_limit_per_minute=new_key.rate_limit_per_minute,
        rate_limit_per_hour=new_key.rate_limit_per_hour,
        rate_limit_per_day=new_key.rate_limit_per_day,
        expires_at=new_key.expires_at,
        last_used_at=new_key.last_used_at,
        usage_count=new_key.usage_count,
        created_at=new_key.created_at,
        updated_at=new_key.updated_at,
        api_key=raw_key
    )


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = None,
    environment: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(APIKey).where(APIKey.owner_id == current_user.id)
    
    if status_filter:
        try:
            key_status = KeyStatus(status_filter)
            query = query.where(APIKey.status == key_status)
        except ValueError:
            pass
    
    if environment:
        query = query.where(APIKey.environment == environment)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(APIKey.created_at.desc())
    
    result = await db.execute(query)
    keys = result.scalars().all()
    
    return APIKeyListResponse(
        items=[APIKeyResponse(
            id=k.id,
            name=k.name,
            description=k.description,
            key_prefix=k.key_prefix,
            status=k.status.value,
            permissions=k.permissions,
            allowed_services=k.allowed_services,
            allowed_ips=k.allowed_ips,
            environment=k.environment,
            rate_limit_per_minute=k.rate_limit_per_minute,
            rate_limit_per_hour=k.rate_limit_per_hour,
            rate_limit_per_day=k.rate_limit_per_day,
            expires_at=k.expires_at,
            last_used_at=k.last_used_at,
            usage_count=k.usage_count,
            created_at=k.created_at,
            updated_at=k.updated_at
        ) for k in keys],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.owner_id == current_user.id
        )
    )
    key = result.scalar_one_or_none()
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return key


@router.put("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: str,
    key_update: APIKeyUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.owner_id == current_user.id
        )
    )
    key = result.scalar_one_or_none()
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    update_data = key_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(key, field, value)
    
    await audit_logger.log(
        db=db,
        action="api_key_updated",
        user_id=current_user.id,
        api_key_id=key_id,
        ip_address=request.client.host if request.client else None,
        metadata={"updated_fields": list(update_data.keys())}
    )
    
    return key


@router.post("/{key_id}/rotate", response_model=APIKeyRotateResponse)
async def rotate_api_key(
    key_id: str,
    rotate_request: APIKeyRotateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.owner_id == current_user.id
        )
    )
    old_key = result.scalar_one_or_none()
    
    if not old_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    if old_key.status != KeyStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only rotate active keys"
        )
    
    raw_key, key_prefix = key_generator.generate_api_key()
    key_hash = hashing_service.hash_api_key(raw_key)
    
    grace_period_ends = None
    if rotate_request.grace_period_hours > 0:
        grace_period_ends = datetime.utcnow() + timedelta(hours=rotate_request.grace_period_hours)
        old_key.status = KeyStatus.ROTATING
        old_key.grace_period_ends_at = grace_period_ends
    else:
        old_key.status = KeyStatus.REVOKED
    
    new_key = APIKey(
        name=old_key.name,
        description=old_key.description,
        key_prefix=key_prefix,
        key_hash=key_hash,
        encrypted_metadata=old_key.encrypted_metadata,
        owner_id=current_user.id,
        permissions=old_key.permissions,
        allowed_services=old_key.allowed_services,
        allowed_ips=old_key.allowed_ips,
        allowed_user_agents=old_key.allowed_user_agents,
        environment=old_key.environment,
        rate_limit_per_minute=old_key.rate_limit_per_minute,
        rate_limit_per_hour=old_key.rate_limit_per_hour,
        rate_limit_per_day=old_key.rate_limit_per_day,
        expires_at=old_key.expires_at,
        rotated_from_id=old_key.id
    )
    
    db.add(new_key)
    await db.flush()
    
    await audit_logger.log(
        db=db,
        action="api_key_rotated",
        user_id=current_user.id,
        api_key_id=old_key.id,
        ip_address=request.client.host if request.client else None,
        metadata={"new_key_id": new_key.id, "grace_period_hours": rotate_request.grace_period_hours}
    )
    
    return APIKeyRotateResponse(
        old_key_id=old_key.id,
        new_key=APIKeyCreatedResponse(
            id=new_key.id,
            name=new_key.name,
            description=new_key.description,
            key_prefix=new_key.key_prefix,
            status=new_key.status.value,
            permissions=new_key.permissions,
            allowed_services=new_key.allowed_services,
            allowed_ips=new_key.allowed_ips,
            environment=new_key.environment,
            rate_limit_per_minute=new_key.rate_limit_per_minute,
            rate_limit_per_hour=new_key.rate_limit_per_hour,
            rate_limit_per_day=new_key.rate_limit_per_day,
            expires_at=new_key.expires_at,
            last_used_at=new_key.last_used_at,
            usage_count=new_key.usage_count,
            created_at=new_key.created_at,
            updated_at=new_key.updated_at,
            api_key=raw_key
        ),
        grace_period_ends_at=grace_period_ends
    )


@router.post("/{key_id}/disable", response_model=APIKeyResponse)
async def disable_api_key(
    key_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.owner_id == current_user.id
        )
    )
    key = result.scalar_one_or_none()
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    key.status = KeyStatus.DISABLED
    
    await audit_logger.log(
        db=db,
        action="api_key_disabled",
        user_id=current_user.id,
        api_key_id=key_id,
        ip_address=request.client.host if request.client else None
    )
    
    return key


@router.post("/{key_id}/enable", response_model=APIKeyResponse)
async def enable_api_key(
    key_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.owner_id == current_user.id
        )
    )
    key = result.scalar_one_or_none()
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    if key.status == KeyStatus.REVOKED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot enable revoked keys"
        )
    
    key.status = KeyStatus.ACTIVE
    
    await audit_logger.log(
        db=db,
        action="api_key_enabled",
        user_id=current_user.id,
        api_key_id=key_id,
        ip_address=request.client.host if request.client else None
    )
    
    return key


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.owner_id == current_user.id
        )
    )
    key = result.scalar_one_or_none()
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    key.status = KeyStatus.REVOKED
    
    await audit_logger.log(
        db=db,
        action="api_key_revoked",
        user_id=current_user.id,
        api_key_id=key_id,
        ip_address=request.client.host if request.client else None
    )
