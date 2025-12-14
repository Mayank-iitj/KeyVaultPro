"""
Authentication Routes
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.connection import get_db
from app.database.models import User, RefreshToken, UserRole
from app.auth.jwt_handler import jwt_handler
from app.auth.schemas import (
    UserRegister, UserLogin, TokenResponse, RefreshTokenRequest,
    UserResponse, UserUpdate, PasswordChange, RoleUpdate
)
from app.auth.dependencies import get_current_user, require_role
from app.security.hashing import hashing_service
from app.security.key_generator import key_generator
from app.utils.config import settings
from app.logs.audit import audit_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    existing = await db.execute(
        select(User).where(
            (User.email == user_data.email) | (User.username == user_data.username)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    hashed_password = hashing_service.hash_password(user_data.password)
    
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        role=UserRole.DEVELOPER
    )
    
    db.add(new_user)
    await db.flush()
    
    await audit_logger.log(
        db=db,
        action="user_registered",
        user_id=new_user.id,
        ip_address=request.client.host if request.client else None,
        metadata={"email": user_data.email, "username": user_data.username}
    )
    
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked. Try again after {user.locked_until}"
        )
    
    if not hashing_service.verify_password(credentials.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.max_login_attempts:
            user.locked_until = datetime.utcnow() + timedelta(
                minutes=settings.lockout_duration_minutes
            )
        await db.flush()
        
        await audit_logger.log(
            db=db,
            action="login_failed",
            user_id=user.id,
            ip_address=request.client.host if request.client else None
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    
    access_token = jwt_handler.create_access_token(
        user_id=user.id,
        role=user.role.value,
        permissions=["read", "write"] if user.role != UserRole.READONLY else ["read"]
    )
    
    refresh_token = key_generator.generate_refresh_token()
    refresh_token_hash = hashing_service.hash_token(refresh_token)
    
    db_refresh_token = RefreshToken(
        token_hash=refresh_token_hash,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    )
    db.add(db_refresh_token)
    
    await audit_logger.log(
        db=db,
        action="login_success",
        user_id=user.id,
        ip_address=request.client.host if request.client else None
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_request: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    token_hash = hashing_service.hash_token(token_request.refresh_token)
    
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        )
    )
    db_token = result.scalar_one_or_none()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    result = await db.execute(
        select(User).where(User.id == db_token.user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    db_token.revoked = True
    db_token.revoked_at = datetime.utcnow()
    
    access_token = jwt_handler.create_access_token(
        user_id=user.id,
        role=user.role.value,
        permissions=["read", "write"] if user.role != UserRole.READONLY else ["read"]
    )
    
    new_refresh_token = key_generator.generate_refresh_token()
    new_refresh_token_hash = hashing_service.hash_token(new_refresh_token)
    
    new_db_token = RefreshToken(
        token_hash=new_refresh_token_hash,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    )
    db.add(new_db_token)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == current_user.id,
            RefreshToken.revoked == False
        )
    )
    
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == current_user.id,
            RefreshToken.revoked == False
        )
    )
    tokens = result.scalars().all()
    
    for token in tokens:
        token.revoked = True
        token.revoked_at = datetime.utcnow()
    
    await audit_logger.log(
        db=db,
        action="logout",
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None
    )
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user_update.email:
        existing = await db.execute(
            select(User).where(
                User.email == user_update.email,
                User.id != current_user.id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        current_user.email = user_update.email
    
    if user_update.username:
        existing = await db.execute(
            select(User).where(
                User.username == user_update.username,
                User.id != current_user.id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already in use"
            )
        current_user.username = user_update.username
    
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not hashing_service.verify_password(
        password_data.current_password,
        current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.hashed_password = hashing_service.hash_password(
        password_data.new_password
    )
    
    await audit_logger.log(
        db=db,
        action="password_changed",
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None
    )
    
    return {"message": "Password changed successfully"}


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    role_update: RoleUpdate,
    request: Request,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = UserRole(role_update.role)
    
    await audit_logger.log(
        db=db,
        action="role_updated",
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        metadata={"target_user": user_id, "new_role": role_update.role}
    )
    
    return user
