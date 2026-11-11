"""
Pydantic Validation Schemas for REST API
"""

from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# Auth Schemas
class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    full_name: str
    badge_number: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    badge_number: str
    full_name: str
    role: str = "officer"
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    badge_number: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Camera Schemas
class CameraCreate(BaseModel):
    camera_code: str
    name: str
    location: str
    stream_source: str = "webcam"
    ip_address: Optional[str] = None


class CameraResponse(BaseModel):
    id: int
    camera_code: str
    name: str
    location: str
    stream_source: str
    status: str
    ai_detection: str
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Restricted Zone Schemas
class ZoneCreate(BaseModel):
    zone_code: str
    name: str
    camera_id: int
    polygon_points_json: str  # JSON string of [[x, y], ...]
    severity: str = "HIGH"


class ZoneResponse(BaseModel):
    id: int
    zone_code: str
    name: str
    camera_id: int
    polygon_points_json: str
    severity: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Incident Schemas
class IncidentCreate(BaseModel):
    incident_id: str
    detection_type: str
    object_detected: str
    severity: str = "CRITICAL"
    confidence: float
    camera_code: str
    location: str
    notes: Optional[str] = None


class IncidentUpdate(BaseModel):
    status: Optional[str] = None  # "NEW", "INVESTIGATING", "RESOLVED"
    notes: Optional[str] = None


class IncidentResponse(BaseModel):
    id: int
    incident_id: str
    detection_type: str
    object_detected: str
    severity: str
    confidence: float
    camera_code: str
    location: str
    status: str
    transmission_status: str
    notes: Optional[str] = None
    created_at: datetime
    evidence_encrypted: bool = True
    has_evidence: bool = False

    model_config = ConfigDict(from_attributes=True)


# Evidence Schemas
class EvidenceResponse(BaseModel):
    id: int
    incident_id: str
    original_filename: str
    encrypted_filename: str
    crypto_scheme: str
    pqc_algorithm: str
    symmetric_cipher: str
    plaintext_sha256: str
    encrypted_sha256: str
    encryption_status: str
    integrity_status: str
    file_size_bytes: int
    duration_seconds: float
    created_at: datetime
    last_verified_at: Optional[datetime] = None
    last_retrieved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceVerifyResponse(BaseModel):
    incident_id: str
    is_valid: bool
    status: str
    message: str
    expected_sha256: str
    calculated_sha256: str
    pqc_algorithm: str
    timestamp: datetime


class EvidenceRetrieveResponse(BaseModel):
    incident_id: str
    video_stream_url: str
    pqc_decapsulation_status: str
    symmetric_decryption_status: str
    integrity_status: str
    message: str


# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    username: str
    action: str
    incident_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: str

    model_config = ConfigDict(from_attributes=True)


# Stats Schema
class DashboardStats(BaseModel):
    total_incidents: int
    critical_alerts: int
    weapons_detected: int
    violence_alerts: int
    intrusion_alerts: int
    abandoned_objects: int
    evidence_files: int
    verified_evidence: int
    active_cameras: int
