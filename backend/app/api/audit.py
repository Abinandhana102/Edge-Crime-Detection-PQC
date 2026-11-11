"""
Audit Trail API Routes
Provides immutable forensic history for all system actions.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models import AuditLog
from backend.app.schemas import AuditLogResponse
from backend.app.security.auth_handler import require_officer

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action name"),
    username: Optional[str] = Query(None, description="Filter by officer"),
    incident_id: Optional[str] = Query(None, description="Filter by incident ID"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """Returns chronologically ordered immutable audit trail"""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if username:
        query = query.filter(AuditLog.username == username)
    if incident_id:
        query = query.filter(AuditLog.incident_id == incident_id)

    return query.order_by(desc(AuditLog.timestamp)).limit(limit).all()
