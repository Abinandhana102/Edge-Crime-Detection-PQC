"""
Camera Surveillance Management API Routes
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Camera
from backend.app.schemas import CameraResponse, CameraCreate
from backend.app.security.auth_handler import require_officer, require_admin

router = APIRouter(prefix="/cameras", tags=["Cameras"])


@router.get("", response_model=List[CameraResponse])
async def list_cameras(
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """Returns list of all active surveillance camera feeds"""
    return db.query(Camera).all()


@router.post("", response_model=CameraResponse)
async def create_camera(
    camera_data: CameraCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Admin endpoint to add a new CCTV camera"""
    existing = db.query(Camera).filter(Camera.camera_code == camera_data.camera_code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Camera code already registered")

    cam = Camera(
        camera_code=camera_data.camera_code.upper(),
        name=camera_data.name,
        location=camera_data.location,
        stream_source=camera_data.stream_source,
        ip_address=camera_data.ip_address,
        status="ONLINE",
        ai_detection="ACTIVE"
    )
    db.add(cam)
    db.commit()
    db.refresh(cam)
    return cam


@router.get("/{camera_code}", response_model=CameraResponse)
async def get_camera(
    camera_code: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """Get single camera information"""
    cam = db.query(Camera).filter(Camera.camera_code == camera_code.upper()).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cam
