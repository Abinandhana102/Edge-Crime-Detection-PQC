"""
Quantum-Safe Digital Evidence Management API Routes
Handles post-quantum encrypted evidence upload, SHA-256 integrity verification,
authorized ML-KEM decapsulation, AES-256 decryption, and secure streaming.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from backend.app.config import settings, ENCRYPTED_EVIDENCE_DIR, DECRYPTED_CACHE_DIR
from backend.app.database import get_db, get_police_secret_key
from backend.app.models import Evidence, Incident
from backend.app.schemas import (
    EvidenceResponse,
    EvidenceVerifyResponse,
    EvidenceRetrieveResponse
)
from backend.app.security.auth_handler import get_current_user, require_officer, log_audit_event
from backend.crypto.hybrid_envelope import QuantumSafeEvidencePackage
from backend.crypto.integrity import EvidenceIntegrity

router = APIRouter(prefix="/evidence", tags=["Quantum-Safe Evidence"])


@router.post("/upload", response_model=EvidenceResponse)
async def upload_evidence(
    incident_id: str = Form(...),
    original_filename: str = Form(...),
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Endpoint for Edge AI surveillance system to upload post-quantum encrypted (.qsep) evidence.
    """
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    content = await file.read()
    if len(content) < 16:
        raise HTTPException(status_code=400, detail="Invalid empty or truncated evidence file")

    # Parse and inspect QSEP package header
    try:
        header, ciphertext = QuantumSafeEvidencePackage.parse_package_header(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Quantum-Safe package format: {str(e)}")

    encrypted_filename = f"{incident_id}.qsep"
    storage_path = ENCRYPTED_EVIDENCE_DIR / encrypted_filename

    with open(storage_path, "wb") as f:
        f.write(content)

    # Check if evidence record exists or create new
    evidence = db.query(Evidence).filter(Evidence.incident_id == incident_id).first()
    if not evidence:
        evidence = Evidence(
            incident_id=incident_id,
            original_filename=original_filename,
            encrypted_filename=encrypted_filename,
            storage_path=str(storage_path),
            crypto_scheme=header.get("crypto_scheme", "HYBRID:AES-256-GCM+ML-KEM-768"),
            pqc_algorithm=header.get("pqc_algorithm", "NIST FIPS 203 ML-KEM-768"),
            symmetric_cipher=header.get("symmetric_cipher", "AES-256-GCM"),
            plaintext_sha256=header.get("plaintext_sha256", ""),
            encrypted_sha256=header.get("encrypted_sha256", ""),
            encryption_status="ENCRYPTED",
            integrity_status="UNVERIFIED",
            file_size_bytes=len(content),
            duration_seconds=float(header.get("duration_seconds", 0.0)),
            created_at=datetime.utcnow()
        )
        db.add(evidence)
    else:
        evidence.storage_path = str(storage_path)
        evidence.plaintext_sha256 = header.get("plaintext_sha256", evidence.plaintext_sha256)
        evidence.encrypted_sha256 = header.get("encrypted_sha256", evidence.encrypted_sha256)
        evidence.file_size_bytes = len(content)

    db.commit()
    db.refresh(evidence)

    log_audit_event(
        db=db,
        username="EDGE_AI_CRYPTO",
        action="EVIDENCE_ENCRYPTED_AND_UPLOADED",
        incident_id=incident_id,
        details=f"Uploaded quantum-safe evidence package ({len(content)} bytes, PQC: ML-KEM-768, Cipher: AES-256-GCM)",
        ip_address=request.client.host if (request and request.client) else "127.0.0.1"
    )

    return evidence


@router.get("/{incident_id}", response_model=EvidenceResponse)
async def get_evidence_info(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """Retrieves metadata of quantum-safe encrypted evidence for an incident"""
    evidence = db.query(Evidence).filter(Evidence.incident_id == incident_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence package not found for this incident")
    return evidence


@router.post("/{incident_id}/verify", response_model=EvidenceVerifyResponse)
async def verify_evidence_integrity(
    incident_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """
    Evidence Integrity Verification:
    Performs authorized decapsulation and SHA-256 hash comparison to verify evidence integrity.
    Demonstrates tamper detection without exposing plaintext video.
    """
    evidence = db.query(Evidence).filter(Evidence.incident_id == incident_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence package not found")

    storage_path = Path(evidence.storage_path)
    if not storage_path.exists():
        raise HTTPException(status_code=404, detail="Encrypted evidence file missing on disk")

    with open(storage_path, "rb") as f:
        package_bytes = f.read()

    police_sk = get_police_secret_key()

    try:
        decrypted_video, is_valid, msg, header = QuantumSafeEvidencePackage.decrypt_and_verify(
            package_bytes=package_bytes,
            police_secret_key=police_sk
        )
        calculated_sha256 = EvidenceIntegrity.calculate_sha256(decrypted_video)
    except Exception as e:
        is_valid = False
        calculated_sha256 = "ERROR_INTEGRITY_COMPROMISED"
        msg = f"❌ Integrity Verification Error: {str(e)}"

    # Update evidence integrity record
    evidence.integrity_status = "VERIFIED" if is_valid else "FAILED"
    evidence.last_verified_at = datetime.utcnow()
    db.commit()

    # Log audit event
    log_audit_event(
        db=db,
        username=current_user.username,
        action="EVIDENCE_INTEGRITY_VERIFIED" if is_valid else "INTEGRITY_CHECK_FAILED",
        incident_id=incident_id,
        details=f"Integrity check performed by {current_user.username}. Result: {'PASSED' if is_valid else 'FAILED'}. SHA-256: {evidence.plaintext_sha256[:16]}...",
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_id=current_user.id
    )

    return EvidenceVerifyResponse(
        incident_id=incident_id,
        is_valid=is_valid,
        status="VERIFIED" if is_valid else "FAILED",
        message="✅ Evidence Integrity Verified: Cryptographic SHA-256 hash matches original edge capture." if is_valid else "❌ Integrity Check Failed: Evidence has been tampered with or corrupted.",
        expected_sha256=evidence.plaintext_sha256,
        calculated_sha256=calculated_sha256,
        pqc_algorithm=evidence.pqc_algorithm,
        timestamp=datetime.utcnow()
    )


@router.post("/{incident_id}/decrypt", response_model=EvidenceRetrieveResponse)
async def decrypt_and_retrieve_evidence(
    incident_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_officer)
):
    """
    Authorized Decryption & Video Playback:
    1. Authenticates Police Officer.
    2. Performs Post-Quantum ML-KEM-768 decapsulation with Police Private Key.
    3. Performs AES-256-GCM authenticated decryption.
    4. Caches plaintext temporarily in secure ephemeral cache for browser playback.
    5. Records full audit event.
    """
    evidence = db.query(Evidence).filter(Evidence.incident_id == incident_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence package not found")

    storage_path = Path(evidence.storage_path)
    if not storage_path.exists():
        raise HTTPException(status_code=404, detail="Encrypted evidence file missing on disk")

    with open(storage_path, "rb") as f:
        package_bytes = f.read()

    police_sk = get_police_secret_key()

    try:
        decrypted_video, is_valid, msg, header = QuantumSafeEvidencePackage.decrypt_and_verify(
            package_bytes=package_bytes,
            police_secret_key=police_sk
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Post-Quantum Decryption Failed: {str(e)}")

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Evidence decryption halted: SHA-256 integrity check failed. Possible evidence tampering."
        )

    # Save to ephemeral playback cache
    ephemeral_filename = f"{incident_id}_decrypted.mp4"
    cache_path = DECRYPTED_CACHE_DIR / ephemeral_filename
    with open(cache_path, "wb") as f:
        f.write(decrypted_video)

    evidence.last_retrieved_at = datetime.utcnow()
    evidence.integrity_status = "VERIFIED"
    db.commit()

    # Record in immutable audit log
    log_audit_event(
        db=db,
        username=current_user.username,
        action="EVIDENCE_RETRIEVED_AND_DECRYPTED",
        incident_id=incident_id,
        details=f"Officer {current_user.username} (Badge: {current_user.badge_number}) successfully decapsulated ML-KEM-768 and decrypted AES-256-GCM video evidence",
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_id=current_user.id
    )

    stream_url = f"{settings.API_PREFIX}/evidence/stream/{incident_id}?token={request.headers.get('authorization', '').replace('Bearer ', '')}"

    return EvidenceRetrieveResponse(
        incident_id=incident_id,
        video_stream_url=stream_url,
        pqc_decapsulation_status="SUCCESS (NIST FIPS 203 ML-KEM-768)",
        symmetric_decryption_status="SUCCESS (AES-256-GCM Authenticated)",
        integrity_status="VERIFIED (SHA-256 Digest Match)",
        message="✅ Evidence successfully decapsulated and decrypted for authorized playback."
    )


@router.get("/stream/{incident_id}")
async def stream_decrypted_video(
    incident_id: str,
    request: Request,
    current_user = Depends(require_officer)
):
    """
    Secure video stream endpoint for authorized officers.
    Serves the ephemeral decrypted MP4 video.
    """
    ephemeral_filename = f"{incident_id}_decrypted.mp4"
    cache_path = DECRYPTED_CACHE_DIR / ephemeral_filename

    if not cache_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Decrypted video stream expired or not yet decapsulated. Click 'Retrieve Evidence' first."
        )

    # Auto-detect media type (WebM vs MP4)
    with open(cache_path, "rb") as f:
        magic = f.read(8)
    media_type = "video/webm" if magic.startswith(b"\x1a\x45\xdf\xa3") else "video/mp4"

    return FileResponse(
        path=str(cache_path),
        media_type=media_type,
        filename=f"{incident_id}_evidence.mp4"
    )
