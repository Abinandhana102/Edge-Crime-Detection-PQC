"""
SQLAlchemy Database Models
Defines relational schemas for Users (Police & Citizens), Cameras, Incidents, Evidence, Audit Logs, and Restricted Zones.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


class User(Base):
    """Police Department Staff and Citizen / Store Users"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    badge_number = Column(String(64), unique=True, nullable=False)  # Badge for officer, Account ID for citizen
    full_name = Column(String(128), nullable=False)
    role = Column(String(32), default="citizen")  # "admin", "officer", "citizen", "store_owner", "bank"
    user_type = Column(String(32), default="citizen")  # "police" or "citizen"
    organization = Column(String(128), default="Private Residence")  # e.g., "Metro Jewelers", "First City Bank"
    location_address = Column(String(256), default="Downtown Plaza, Sector 4")
    hashed_password = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user")


class Camera(Base):
    """Surveillance Camera Streams & Locations"""
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    camera_code = Column(String(32), unique=True, index=True, nullable=False)  # e.g., CAM-01, CAM-USER-01
    name = Column(String(128), nullable=False)
    location = Column(String(128), nullable=False)  # e.g., "Main Gate Entrance"
    stream_source = Column(String(256), default="webcam")  # "webcam", "rtsp://...", "user_camera"
    status = Column(String(32), default="ONLINE")  # "ONLINE", "OFFLINE", "ALERT"
    ai_detection = Column(String(32), default="ACTIVE")  # "ACTIVE", "PAUSED", "DISABLED"
    ip_address = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    incidents = relationship("Incident", back_populates="camera")
    zones = relationship("RestrictedZone", back_populates="camera")


class Incident(Base):
    """Detected Security Incidents and Alarms"""
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(64), unique=True, index=True, nullable=False)  # e.g., INC-20260827-0001
    detection_type = Column(String(64), nullable=False)  # "Weapon", "Violence", "Intrusion", "Abandoned Object"
    object_detected = Column(String(64), nullable=False)  # "Gun", "Knife", "Person", "Luggage"
    severity = Column(String(32), default="CRITICAL")     # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    confidence = Column(Float, nullable=False)           # Percentage / score e.g. 94.2
    
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=True)
    camera_code = Column(String(32), nullable=False)
    location = Column(String(128), nullable=False)
    reported_by = Column(String(128), default="Edge AI System")  # User name / Store Name
    
    status = Column(String(32), default="NEW")           # "NEW", "INVESTIGATING", "RESOLVED"
    transmission_status = Column(String(32), default="SENT")  # "SENT", "PENDING", "FAILED"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    camera = relationship("Camera", back_populates="incidents")
    evidence = relationship("Evidence", uselist=False, back_populates="incident")


class Evidence(Base):
    """Quantum-Safe Encrypted Digital Evidence Package Record"""
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(64), ForeignKey("incidents.incident_id"), unique=True, nullable=False)
    
    original_filename = Column(String(256), nullable=False)
    encrypted_filename = Column(String(256), nullable=False)
    storage_path = Column(String(512), nullable=False)
    
    # Cryptographic Metadata
    crypto_scheme = Column(String(128), default="HYBRID:AES-256-GCM+ML-KEM-768")
    pqc_algorithm = Column(String(64), default="NIST FIPS 203 ML-KEM-768")
    symmetric_cipher = Column(String(64), default="AES-256-GCM")
    
    plaintext_sha256 = Column(String(64), nullable=False)  # Expected SHA-256
    encrypted_sha256 = Column(String(64), nullable=False)
    
    encryption_status = Column(String(32), default="ENCRYPTED")  # "ENCRYPTED", "DECRYPTED_EPHEMERAL"
    integrity_status = Column(String(64), default="UNVERIFIED")  # "VERIFIED", "FAILED", "UNVERIFIED"
    file_size_bytes = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_verified_at = Column(DateTime, nullable=True)
    last_retrieved_at = Column(DateTime, nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="evidence")


class AuditLog(Base):
    """Immutable Forensic Audit Trail"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    username = Column(String(64), nullable=False)
    action = Column(String(128), nullable=False)  # "LOGIN", "INCIDENT_CREATED", "EVIDENCE_RETRIEVED", etc.
    incident_id = Column(String(64), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(64), default="127.0.0.1")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")


class RestrictedZone(Base):
    """Configurable Geo-fenced Polygon Restricted Areas"""
    __tablename__ = "restricted_zones"

    id = Column(Integer, primary_key=True, index=True)
    zone_code = Column(String(32), unique=True, nullable=False)
    name = Column(String(128), nullable=False)  # e.g., "Laboratory Entrance"
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    polygon_points_json = Column(Text, nullable=False)  # JSON string of [[x1, y1], [x2, y2], ...]
    severity = Column(String(32), default="HIGH")  # "CRITICAL", "HIGH", "MEDIUM"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    camera = relationship("Camera", back_populates="zones")
