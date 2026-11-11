"""
Incident Management API Routes
Handles security incidents, weapon alerts, violence detections, and real-time broadcasts.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.config import ENCRYPTED_EVIDENCE_DIR, DECRYPTED_CACHE_DIR
from backend.app.database import get_db
from backend.app.models import Incident, Camera, Evidence
from backend.app.schemas import IncidentCreate, IncidentResponse, IncidentUpdate
from backend.app.security.auth_handler import get_current_user, require_officer, log_audit_event
from backend.app.websocket.manager import ws_manager

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    severity: Optional[str] = Query(None, description="Filter by severity e.g. CRITICAL, HIGH"),
    detection_type: Optional[str] = Query(None, description="Filter by type e.g. Weapon, Violence"),
    status: Optional[str] = Query(None, description="Filter by status e.g. NEW, INVESTIGATING, RESOLVED"),
    camera_code: Optional[str] = Query(None, description="Filter by camera code e.g. CAM-01"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """Retrieves list of incidents with optional filters"""
    query = db.query(Incident)

    if severity:
        query = query.filter(Incident.severity == severity.upper())
    if detection_type:
        query = query.filter(Incident.detection_type.ilike(f"%{detection_type}%"))
    if status:
        query = query.filter(Incident.status == status.upper())
    if camera_code:
        query = query.filter(Incident.camera_code == camera_code.upper())

    incidents = query.order_by(desc(Incident.created_at)).limit(limit).all()

    # Annotate with evidence presence
    results = []
    for inc in incidents:
        has_ev = db.query(Evidence).filter(Evidence.incident_id == inc.incident_id).first() is not None
        inc_dict = {
            "id": inc.id,
            "incident_id": inc.incident_id,
            "detection_type": inc.detection_type,
            "object_detected": inc.object_detected,
            "severity": inc.severity,
            "confidence": inc.confidence,
            "camera_code": inc.camera_code,
            "location": inc.location,
            "status": inc.status,
            "transmission_status": inc.transmission_status,
            "notes": inc.notes,
            "created_at": inc.created_at,
            "evidence_encrypted": True,
            "has_evidence": has_ev
        }
        results.append(IncidentResponse(**inc_dict))

    return results


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """Retrieves detailed information for a single incident"""
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    has_ev = db.query(Evidence).filter(Evidence.incident_id == inc.incident_id).first() is not None
    return IncidentResponse(
        id=inc.id,
        incident_id=inc.incident_id,
        detection_type=inc.detection_type,
        object_detected=inc.object_detected,
        severity=inc.severity,
        confidence=inc.confidence,
        camera_code=inc.camera_code,
        location=inc.location,
        status=inc.status,
        transmission_status=inc.transmission_status,
        notes=inc.notes,
        created_at=inc.created_at,
        evidence_encrypted=True,
        has_evidence=has_ev
    )


@router.post("", response_model=IncidentResponse)
async def create_incident(
    incident_data: IncidentCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint for Edge AI surveillance system to report newly detected crime incidents.
    Automatically broadcasts real-time critical alert to connected police dashboards.
    """
    # Verify or link Camera
    camera = db.query(Camera).filter(Camera.camera_code == incident_data.camera_code).first()
    camera_id = camera.id if camera else 1

    # Check for existing duplicate incident_id
    existing = db.query(Incident).filter(Incident.incident_id == incident_data.incident_id).first()
    if existing:
        return IncidentResponse(
            id=existing.id,
            incident_id=existing.incident_id,
            detection_type=existing.detection_type,
            object_detected=existing.object_detected,
            severity=existing.severity,
            confidence=existing.confidence,
            camera_code=existing.camera_code,
            location=existing.location,
            status=existing.status,
            transmission_status=existing.transmission_status,
            notes=existing.notes,
            created_at=existing.created_at,
            evidence_encrypted=True,
            has_evidence=False
        )

    incident = Incident(
        incident_id=incident_data.incident_id,
        detection_type=incident_data.detection_type,
        object_detected=incident_data.object_detected,
        severity=incident_data.severity.upper(),
        confidence=incident_data.confidence,
        camera_id=camera_id,
        camera_code=incident_data.camera_code,
        location=incident_data.location,
        status="NEW",
        transmission_status="SENT",
        notes=incident_data.notes,
        created_at=datetime.utcnow()
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    # Log in immutable audit trail
    log_audit_event(
        db=db,
        username="EDGE_AI_SYSTEM",
        action="INCIDENT_RECORDED",
        incident_id=incident.incident_id,
        details=f"Alert: {incident.detection_type} ({incident.object_detected}) detected at {incident.location} with {incident.confidence:.1f}% confidence",
        ip_address=request.client.host if request.client else "127.0.0.1"
    )

    # Broadcast real-time Red Alert over WebSocket
    alert_payload = {
        "incident_id": incident.incident_id,
        "detection_type": incident.detection_type,
        "object_detected": incident.object_detected,
        "severity": incident.severity,
        "confidence": incident.confidence,
        "camera_code": incident.camera_code,
        "location": incident.location,
        "timestamp": incident.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }
    await ws_manager.broadcast_alert(alert_payload)

    return IncidentResponse(
        id=incident.id,
        incident_id=incident.incident_id,
        detection_type=incident.detection_type,
        object_detected=incident.object_detected,
        severity=incident.severity,
        confidence=incident.confidence,
        camera_code=incident.camera_code,
        location=incident.location,
        status=incident.status,
        transmission_status=incident.transmission_status,
        notes=incident.notes,
        created_at=incident.created_at,
        evidence_encrypted=True,
        has_evidence=False
    )


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident_status(
    incident_id: str,
    update_data: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """Allows police officer to acknowledge or resolve an incident status"""
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    old_status = inc.status
    if update_data.status:
        inc.status = update_data.status.upper()
    if update_data.notes:
        inc.notes = update_data.notes

    db.commit()
    db.refresh(inc)

    log_audit_event(
        db=db,
        username=current_user.username,
        action="INCIDENT_STATUS_UPDATED",
        incident_id=inc.incident_id,
        details=f"Status changed from {old_status} to {inc.status} by Officer {current_user.username}",
        user_id=current_user.id
    )

    has_ev = db.query(Evidence).filter(Evidence.incident_id == inc.incident_id).first() is not None
    return IncidentResponse(
        id=inc.id,
        incident_id=inc.incident_id,
        detection_type=inc.detection_type,
        object_detected=inc.object_detected,
        severity=inc.severity,
        confidence=inc.confidence,
        camera_code=inc.camera_code,
        location=inc.location,
        status=inc.status,
        transmission_status=inc.transmission_status,
        notes=inc.notes,
        created_at=inc.created_at,
        evidence_encrypted=True,
        has_evidence=has_ev
    )


@router.delete("/{incident_id}")
async def delete_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """Allows authorized police officers or admins to delete an incident and its evidence"""
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Delete evidence records
    evidences = db.query(Evidence).filter(Evidence.incident_id == inc.incident_id).all()
    for ev in evidences:
        db.delete(ev)

    # Remove files
    qsep_file = ENCRYPTED_EVIDENCE_DIR / f"{inc.incident_id}.qsep"
    if qsep_file.exists():
        try:
            qsep_file.unlink()
        except Exception:
            pass

    cached_file = DECRYPTED_CACHE_DIR / f"{inc.incident_id}_decrypted.mp4"
    if cached_file.exists():
        try:
            cached_file.unlink()
        except Exception:
            pass

    db.delete(inc)
    db.commit()

    log_audit_event(
        db=db,
        username=current_user.username,
        action="INCIDENT_DELETED",
        incident_id=incident_id,
        details=f"Incident {incident_id} permanently deleted by {current_user.username}",
        user_id=current_user.id
    )

    return {"success": True, "message": f"Incident {incident_id} deleted successfully."}


@router.delete("")
async def clear_all_incidents(
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """Allows authorized police officers or admins to clear all incidents and evidence"""
    incidents = db.query(Incident).all()
    count = len(incidents)

    for inc in incidents:
        evidences = db.query(Evidence).filter(Evidence.incident_id == inc.incident_id).all()
        for ev in evidences:
            db.delete(ev)

        qsep_file = ENCRYPTED_EVIDENCE_DIR / f"{inc.incident_id}.qsep"
        if qsep_file.exists():
            try:
                qsep_file.unlink()
            except Exception:
                pass

        cached_file = DECRYPTED_CACHE_DIR / f"{inc.incident_id}_decrypted.mp4"
        if cached_file.exists():
            try:
                cached_file.unlink()
            except Exception:
                pass

        db.delete(inc)

    db.commit()

    log_audit_event(
        db=db,
        username=current_user.username,
        action="ALL_INCIDENTS_CLEARED",
        details=f"All {count} incidents cleared by {current_user.username}",
        user_id=current_user.id
    )

    return {"success": True, "cleared_count": count, "message": f"Successfully cleared {count} incidents."}
