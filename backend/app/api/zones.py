"""
Restricted Area Intrusion Zones API Routes
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import RestrictedZone, Camera
from backend.app.schemas import ZoneResponse, ZoneCreate
from backend.app.security.auth_handler import require_officer, log_audit_event

router = APIRouter(prefix="/zones", tags=["Restricted Zones"])


@router.get("", response_model=List[ZoneResponse])
async def list_zones(
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """List all configured restricted perimeter zones"""
    return db.query(RestrictedZone).filter(RestrictedZone.is_active == True).all()


@router.post("", response_model=ZoneResponse)
async def create_zone(
    zone_data: ZoneCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """Creates a new geo-fenced polygon restricted zone"""
    cam = db.query(Camera).filter(Camera.id == zone_data.camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera ID not found")

    existing = db.query(RestrictedZone).filter(RestrictedZone.zone_code == zone_data.zone_code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Zone code already exists")

    zone = RestrictedZone(
        zone_code=zone_data.zone_code.upper(),
        name=zone_data.name,
        camera_id=zone_data.camera_id,
        polygon_points_json=zone_data.polygon_points_json,
        severity=zone_data.severity.upper(),
        is_active=True
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)

    log_audit_event(
        db=db,
        username=current_user.username,
        action="ZONE_CREATED",
        details=f"Created restricted zone '{zone.name}' (Code: {zone.zone_code}) on Camera {cam.camera_code}",
        user_id=current_user.id
    )

    return zone


@router.delete("/{zone_id}")
async def delete_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """Deletes a restricted zone"""
    zone = db.query(RestrictedZone).filter(RestrictedZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    zone.is_active = False
    db.commit()

    log_audit_event(
        db=db,
        username=current_user.username,
        action="ZONE_DELETED",
        details=f"Deleted restricted zone '{zone.name}' (Code: {zone.zone_code})",
        user_id=current_user.id
    )

    return {"message": "Zone removed successfully"}
