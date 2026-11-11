"""
System Statistics and Metrics API Routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models import Incident, Evidence, Camera
from backend.app.schemas import DashboardStats
from backend.app.security.auth_handler import require_officer

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """Calculates live dashboard statistics across all cameras and incidents"""
    total_incidents = db.query(Incident).count()
    critical_alerts = db.query(Incident).filter(Incident.severity == "CRITICAL").count()
    weapons_detected = db.query(Incident).filter(Incident.detection_type == "Weapon").count()
    violence_alerts = db.query(Incident).filter(Incident.detection_type == "Violence").count()
    intrusion_alerts = db.query(Incident).filter(Incident.detection_type == "Intrusion").count()
    abandoned_objects = db.query(Incident).filter(Incident.detection_type == "Abandoned Object").count()
    evidence_files = db.query(Evidence).count()
    verified_evidence = db.query(Evidence).filter(Evidence.integrity_status == "VERIFIED").count()
    active_cameras = db.query(Camera).filter(Camera.status == "ONLINE").count()

    return DashboardStats(
        total_incidents=total_incidents,
        critical_alerts=critical_alerts,
        weapons_detected=weapons_detected,
        violence_alerts=violence_alerts,
        intrusion_alerts=intrusion_alerts,
        abandoned_objects=abandoned_objects,
        evidence_files=evidence_files,
        verified_evidence=verified_evidence,
        active_cameras=active_cameras
    )
