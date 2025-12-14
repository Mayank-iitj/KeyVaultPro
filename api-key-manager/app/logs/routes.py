"""
Audit Log Routes
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import csv
import json
import io
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database.connection import get_db
from app.database.models import AuditLog, User, UserRole, APIKey
from app.auth.dependencies import get_current_user, require_role


router = APIRouter(prefix="/logs", tags=["Audit Logs"])


class AuditLogResponse(BaseModel):
    id: str
    api_key_id: Optional[str]
    user_id: Optional[str]
    action: str
    endpoint: Optional[str]
    method: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    status_code: Optional[int]
    response_time_ms: Optional[float]
    error_message: Optional[str]
    metadata: dict
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    pages: int


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    api_key_id: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditLog)
    
    if api_key_id:
        query = query.where(AuditLog.api_key_id == api_key_id)
    
    if action:
        query = query.where(AuditLog.action == action)
    
    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)
    
    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(AuditLog.timestamp.desc())
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return AuditLogListResponse(
        items=[AuditLogResponse(
            id=l.id,
            api_key_id=l.api_key_id,
            user_id=l.user_id,
            action=l.action,
            endpoint=l.endpoint,
            method=l.method,
            ip_address=l.ip_address,
            user_agent=l.user_agent,
            status_code=l.status_code,
            response_time_ms=l.response_time_ms,
            error_message=l.error_message,
            metadata=l.metadata or {},
            timestamp=l.timestamp
        ) for l in logs],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/my-keys")
async def list_my_key_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    api_key_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    key_result = await db.execute(
        select(APIKey.id).where(APIKey.owner_id == current_user.id)
    )
    user_key_ids = [k for k in key_result.scalars().all()]
    
    if not user_key_ids:
        return AuditLogListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            pages=0
        )
    
    query = select(AuditLog).where(AuditLog.api_key_id.in_(user_key_ids))
    
    if api_key_id and api_key_id in user_key_ids:
        query = query.where(AuditLog.api_key_id == api_key_id)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(AuditLog.timestamp.desc())
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return AuditLogListResponse(
        items=[AuditLogResponse(
            id=l.id,
            api_key_id=l.api_key_id,
            user_id=l.user_id,
            action=l.action,
            endpoint=l.endpoint,
            method=l.method,
            ip_address=l.ip_address,
            user_agent=l.user_agent,
            status_code=l.status_code,
            response_time_ms=l.response_time_ms,
            error_message=l.error_message,
            metadata=l.metadata or {},
            timestamp=l.timestamp
        ) for l in logs],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/export/csv")
async def export_logs_csv(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    api_key_id: Optional[str] = None,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditLog)
    
    if api_key_id:
        query = query.where(AuditLog.api_key_id == api_key_id)
    
    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)
    
    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)
    
    query = query.order_by(AuditLog.timestamp.desc()).limit(10000)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "ID", "Timestamp", "Action", "API Key ID", "User ID",
        "Endpoint", "Method", "IP Address", "Status Code",
        "Response Time (ms)", "Error Message"
    ])
    
    for log in logs:
        writer.writerow([
            log.id,
            log.timestamp.isoformat(),
            log.action,
            log.api_key_id or "",
            log.user_id or "",
            log.endpoint or "",
            log.method or "",
            log.ip_address or "",
            log.status_code or "",
            log.response_time_ms or "",
            log.error_message or ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.get("/export/json")
async def export_logs_json(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    api_key_id: Optional[str] = None,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditLog)
    
    if api_key_id:
        query = query.where(AuditLog.api_key_id == api_key_id)
    
    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)
    
    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)
    
    query = query.order_by(AuditLog.timestamp.desc()).limit(10000)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    data = [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "action": log.action,
            "api_key_id": log.api_key_id,
            "user_id": log.user_id,
            "endpoint": log.endpoint,
            "method": log.method,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "status_code": log.status_code,
            "response_time_ms": log.response_time_ms,
            "error_message": log.error_message,
            "metadata": log.metadata
        }
        for log in logs
    ]
    
    output = json.dumps(data, indent=2)
    
    return StreamingResponse(
        iter([output]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )


@router.get("/stats")
async def get_log_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    
    total_result = await db.execute(
        select(func.count()).where(AuditLog.timestamp >= start_date)
    )
    total_logs = total_result.scalar()
    
    action_result = await db.execute(
        select(AuditLog.action, func.count().label("count"))
        .where(AuditLog.timestamp >= start_date)
        .group_by(AuditLog.action)
        .order_by(func.count().desc())
        .limit(20)
    )
    action_counts = {row[0]: row[1] for row in action_result}
    
    error_result = await db.execute(
        select(func.count())
        .where(
            AuditLog.timestamp >= start_date,
            AuditLog.status_code >= 400
        )
    )
    error_count = error_result.scalar()
    
    return {
        "period_days": days,
        "total_logs": total_logs,
        "error_count": error_count,
        "error_rate": error_count / total_logs if total_logs > 0 else 0,
        "actions_by_count": action_counts
    }
