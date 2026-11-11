"""
User / Citizen Security Portal API Routes
Handles Citizen/Store user camera detection, live weapon AI analysis,
automated hybrid post-quantum encryption, and dispatch to Police Department HQ.
"""

import base64
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.config import settings, ENCRYPTED_EVIDENCE_DIR
from backend.app.database import get_db, get_police_public_key
from backend.app.models import User, Incident, Evidence, Camera
from backend.app.schemas import UserCreate, UserResponse, IncidentResponse
from backend.app.security.auth_handler import (
    get_current_user,
    get_password_hash,
    log_audit_event
)
from backend.crypto.hybrid_envelope import QuantumSafeEvidencePackage
from backend.app.websocket.manager import ws_manager
from edge_ai.detector import ObjectDetector
from edge_ai.buffer_manager import CircularVideoBuffer
from edge_ai.violence_detector import ViolenceAnomalyDetector

router = APIRouter(prefix="/user", tags=["User Portal"])

# Shared server-side detector instances for browser video & camera frame processing
global_detector = ObjectDetector(conf_thresh=settings.DEFAULT_CONFIDENCE_THRESHOLD)
global_violence_detector = ViolenceAnomalyDetector()


@router.post("/register", response_model=UserResponse)
async def register_citizen_user(
    user_data: UserCreate,
    organization: Optional[str] = "Store / Private Facility",
    location_address: Optional[str] = "Main Commercial Road",
    db: Session = Depends(get_db)
):
    """Public registration for Store Managers, Bank Security, and Citizens"""
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered. Please choose another username.")

    user = User(
        username=user_data.username,
        badge_number=f"USR-{int(time.time()) % 10000:04d}",
        full_name=user_data.full_name,
        role="citizen",
        user_type="citizen",
        organization=organization or "Private Property",
        location_address=location_address or "City Commercial Center",
        hashed_password=get_password_hash(user_data.password),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        username=user.username,
        action="USER_SELF_REGISTERED",
        details=f"New user {user.full_name} registered facility '{user.organization}' at {user.location_address}"
    )

    return user


@router.post("/detect-frame")
async def detect_user_camera_frame(
    payload: Dict[str, str],
    db: Session = Depends(get_db)
):
    """
    Processes a live frame sent from the user's browser camera.
    Runs YOLO detection for weapons (Knife, Scissors, Gun, Fire) and returns detections.
    """
    image_b64 = payload.get("image_b64", "")
    if not image_b64:
        raise HTTPException(status_code=400, detail="Missing base64 image frame")

    try:
        # Strip header if present
        if "base64," in image_b64:
            image_b64 = image_b64.split("base64,")[1]

        image_bytes = base64.b64decode(image_b64)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Failed to decode image")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")

    # Ignore empty, black, or low-light transition frames
    if float(np.mean(frame)) < 15.0:
        return {
            "detections": [],
            "has_weapon": False,
            "threat_info": None
        }

    # 1. Run robust YOLO deep learning weapon & security object detection
    detections = global_detector.detect(frame)

    # 2. Run Temporal Motion Dynamics for violent hitting, fighting & physical assault
    violence_info = global_violence_detector.analyze_frame(frame)
    is_violence = violence_info.get("is_alert", False)

    # Check if a weapon or threat is confirmed by YOLO
    has_weapon = any(d["is_weapon"] for d in detections)
    primary_weapon = next((d for d in detections if d["is_weapon"]), None)

    # If violent hitting / assault is detected in the video/camera
    if is_violence:
        persons = [d for d in detections if d.get("raw_class") == "person"]
        v_class = violence_info.get("classification", "Violence / Physical Assault")
        v_conf = float(violence_info.get("confidence", 88.0))
        threat_title = "Weapon Assault / Physical Strike" if has_weapon else v_class

        if not has_weapon:
            has_weapon = True
            primary_weapon = {
                "class_name": threat_title,
                "raw_class": "violence",
                "confidence": round(v_conf, 1),
                "severity": "CRITICAL",
                "type": "Violence",
                "is_weapon": True,
                "is_violence": True
            }

            if persons:
                # Highlight the person involved in the fight
                p = persons[0]
                detections.append({
                    "class_name": threat_title,
                    "raw_class": "violence",
                    "confidence": round(v_conf, 1),
                    "bbox": p["bbox"],
                    "normalized_bbox": p["normalized_bbox"],
                    "center": p["center"],
                    "bottom_center": p["bottom_center"],
                    "is_weapon": True,
                    "is_violence": True,
                    "severity": "CRITICAL",
                    "detection_type": "Violence"
                })
            else:
                h, w = frame.shape[:2]
                detections.append({
                    "class_name": threat_title,
                    "raw_class": "violence",
                    "confidence": round(v_conf, 1),
                    "bbox": [int(w * 0.1), int(h * 0.1), int(w * 0.9), int(h * 0.9)],
                    "normalized_bbox": [0.1, 0.1, 0.9, 0.9],
                    "center": [w // 2, h // 2],
                    "bottom_center": [w // 2, int(h * 0.9)],
                    "is_weapon": True,
                    "is_violence": True,
                    "severity": "CRITICAL",
                    "detection_type": "Violence"
                })

    return {
        "detections": detections,
        "has_weapon": has_weapon,
        "threat_info": primary_weapon
    }


@router.post("/dispatch-emergency")
async def dispatch_user_emergency(
    incident_id: str = Form(...),
    detection_type: str = Form(...),
    object_detected: str = Form(...),
    confidence: float = Form(...),
    file: Optional[UploadFile] = File(None),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    User Camera Distress / Weapon Alert Dispatch:
    1. Creates Critical Incident originating from Citizen/Store user camera.
    2. Post-Quantum Hybrid Encrypts (AES-256-GCM + ML-KEM-768 against Police Public Key).
    3. Saves Encrypted Evidence in Police Vault.
    4. Broadcasts LIVE CRITICAL ALARM to all connected Police Command Dashboards via WebSocket.
    """
    camera_code = f"CAM-USR-{current_user.id:02d}"
    location = f"{current_user.organization} ({current_user.location_address})"

    # Check for existing camera record for this user or create one
    cam = db.query(Camera).filter(Camera.camera_code == camera_code).first()
    if not cam:
        cam = Camera(
            camera_code=camera_code,
            name=f"{current_user.organization} Camera",
            location=location,
            stream_source="user_camera",
            status="ALERT",
            ai_detection="ACTIVE"
        )
        db.add(cam)
        db.commit()
        db.refresh(cam)
    else:
        cam.status = "ALERT"
        db.commit()

    # Step 1: Create Incident in Relational Database
    incident = Incident(
        incident_id=incident_id,
        detection_type=detection_type,
        object_detected=object_detected,
        severity="CRITICAL",
        confidence=confidence,
        camera_id=cam.id,
        camera_code=camera_code,
        location=location,
        reported_by=f"{current_user.full_name} ({current_user.organization})",
        status="NEW",
        transmission_status="SENT",
        notes=f"CRITICAL: Weapon detected on User Camera at {current_user.organization}. Emergency response dispatched.",
        created_at=datetime.utcnow()
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    # Step 2: Handle Video Evidence Package
    police_pk = get_police_public_key()
    
    if file:
        raw_video_bytes = await file.read()
    else:
        # Generate synthetic evidence clip if raw stream wasn't attached
        buf_mgr = CircularVideoBuffer(fps=10, pre_event_sec=2, post_event_sec=2)
        raw_video_bytes, _ = buf_mgr.compile_mp4_bytes()

    metadata = {
        "incident_id": incident_id,
        "camera_code": camera_code,
        "location": location,
        "detection_type": detection_type,
        "object_detected": object_detected,
        "severity": "CRITICAL",
        "confidence": confidence,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "original_filename": f"{incident_id}_user_camera.mp4",
        "encrypted_filename": f"{incident_id}.qsep"
    }

    # Execute Hybrid Post-Quantum Encryption
    qsep_package_bytes, header = QuantumSafeEvidencePackage.encrypt_and_package(
        video_bytes=raw_video_bytes,
        police_public_key=police_pk,
        metadata=metadata
    )

    encrypted_storage_path = ENCRYPTED_EVIDENCE_DIR / f"{incident_id}.qsep"
    with open(encrypted_storage_path, "wb") as f:
        f.write(qsep_package_bytes)

    evidence = Evidence(
        incident_id=incident_id,
        original_filename=metadata["original_filename"],
        encrypted_filename=metadata["encrypted_filename"],
        storage_path=str(encrypted_storage_path),
        crypto_scheme=header["crypto_scheme"],
        pqc_algorithm=header["pqc_algorithm"],
        symmetric_cipher=header["symmetric_cipher"],
        plaintext_sha256=header["plaintext_sha256"],
        encrypted_sha256=header["encrypted_sha256"],
        encryption_status="ENCRYPTED",
        integrity_status="UNVERIFIED",
        file_size_bytes=len(qsep_package_bytes),
        duration_seconds=float(header.get("duration_seconds", 3.0)),
        created_at=datetime.utcnow()
    )
    db.add(evidence)
    db.commit()

    # Step 3: Record Immutable Forensic Audit Trail
    log_audit_event(
        db=db,
        username=current_user.username,
        action="USER_EMERGENCY_DISPATCHED",
        incident_id=incident_id,
        details=f"Distress alert dispatched by User '{current_user.full_name}' from '{current_user.organization}'. Threat: {detection_type} ({object_detected}, {confidence}%). Evidence PQC Encrypted.",
        ip_address=request.client.host if request and request.client else "127.0.0.1",
        user_id=current_user.id
    )

    # Step 4: Real-Time WebSocket Critical Alert Broadcast to Police HQ
    alert_payload = {
        "incident_id": incident_id,
        "detection_type": detection_type,
        "object_detected": object_detected,
        "severity": "CRITICAL",
        "confidence": confidence,
        "camera_code": camera_code,
        "location": location,
        "reported_by": current_user.full_name,
        "organization": current_user.organization,
        "timestamp": incident.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }
    await ws_manager.broadcast_alert(alert_payload)

    return {
        "success": True,
        "incident_id": incident_id,
        "status": "DISPATCHED_TO_POLICE",
        "pqc_encryption": header["pqc_algorithm"],
        "cipher": header["symmetric_cipher"],
        "message": f"🚨 Red Alert & Quantum-Safe Evidence successfully transmitted to Police HQ Command."
    }


@router.get("/my-incidents")
async def get_user_incidents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves all incidents reported from this user / facility"""
    camera_code = f"CAM-USR-{current_user.id:02d}"
    incidents = db.query(Incident).filter(
        (Incident.camera_code == camera_code) | 
        (Incident.reported_by.ilike(f"%{current_user.username}%")) |
        (Incident.reported_by.ilike(f"%{current_user.full_name}%"))
    ).order_by(desc(Incident.created_at)).all()

    return incidents


@router.delete("/my-incidents")
@router.post("/clear-incidents")
async def clear_user_incidents(
    incident_id: Optional[str] = Query(None, description="Optional incident ID to delete single incident; omit to clear all"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clears / deletes incidents reported from this user / facility.
    - If incident_id is specified: deletes that individual incident and associated files.
    - If incident_id is omitted or 'ALL': clears all incidents belonging to this user / facility.
    Also removes corresponding encrypted packages and cached videos from disk.
    """
    from backend.app.config import DECRYPTED_CACHE_DIR, ENCRYPTED_EVIDENCE_DIR

    camera_code = f"CAM-USR-{current_user.id:02d}"
    if current_user.role in ["admin", "officer"]:
        query = db.query(Incident)
    else:
        query = db.query(Incident).filter(
            (Incident.camera_code == camera_code) | 
            (Incident.reported_by.ilike(f"%{current_user.username}%")) |
            (Incident.reported_by.ilike(f"%{current_user.full_name}%"))
        )

    if incident_id and incident_id.strip() and incident_id.strip().upper() != "ALL":
        query = query.filter(Incident.incident_id == incident_id.strip())

    incidents_to_delete = query.all()
    count = len(incidents_to_delete)

    for inc in incidents_to_delete:
        # Delete DB evidence records
        evidences = db.query(Evidence).filter(Evidence.incident_id == inc.incident_id).all()
        for ev in evidences:
            db.delete(ev)

        # Delete encrypted evidence file
        qsep_file = ENCRYPTED_EVIDENCE_DIR / f"{inc.incident_id}.qsep"
        if qsep_file.exists():
            try:
                qsep_file.unlink()
            except Exception:
                pass

        # Delete decrypted cached file
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
        action="USER_INCIDENTS_CLEARED",
        details=f"Cleared {count} incidents for facility {current_user.organization} (ID: {incident_id or 'ALL'})",
        user_id=current_user.id
    )

    return {
        "success": True,
        "cleared_count": count,
        "message": f"Successfully cleared {count} incident(s)."
    }


@router.delete("/my-incidents/{incident_id}")
async def delete_single_user_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await clear_user_incidents(incident_id=incident_id, current_user=current_user, db=db)


@router.get("/video/{incident_id}")
async def stream_user_incident_video(
    incident_id: str,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Streams the recorded weapon detection video clip for playback in the User Portal.
    """
    from fastapi.responses import FileResponse, Response
    from backend.app.config import DECRYPTED_CACHE_DIR, ENCRYPTED_EVIDENCE_DIR
    from backend.crypto.hybrid_envelope import QuantumSafeEvidencePackage
    from backend.app.database import get_police_secret_key

    # Check if decrypted mp4 already cached in temp
    cached_mp4 = DECRYPTED_CACHE_DIR / f"{incident_id}_decrypted.mp4"
    if cached_mp4.exists():
        with open(cached_mp4, "rb") as f:
            magic = f.read(8)
        mtype = "video/webm" if magic.startswith(b"\x1a\x45\xdf\xa3") else "video/mp4"
        return FileResponse(str(cached_mp4), media_type=mtype)

    # If not cached, decrypt from .qsep using Police Secret Key
    qsep_file = ENCRYPTED_EVIDENCE_DIR / f"{incident_id}.qsep"
    if not qsep_file.exists():
        raise HTTPException(status_code=404, detail="Incident evidence video not found")

    try:
        with open(qsep_file, "rb") as f:
            qsep_bytes = f.read()

        police_sk = get_police_secret_key()
        decrypted_video_bytes, verify_ok, msg, header = QuantumSafeEvidencePackage.decrypt_and_verify(
            package_bytes=qsep_bytes,
            police_secret_key=police_sk
        )

        # Save to cache for streaming
        DECRYPTED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(cached_mp4, "wb") as f:
            f.write(decrypted_video_bytes)

        mtype = "video/webm" if decrypted_video_bytes.startswith(b"\x1a\x45\xdf\xa3") else "video/mp4"
        return FileResponse(str(cached_mp4), media_type=mtype)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load user video: {str(e)}")
