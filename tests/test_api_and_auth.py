import time
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, seed_database
from backend.crypto.ml_kem import generate_police_keypair
from backend.crypto.hybrid_envelope import QuantumSafeEvidencePackage
from edge_ai.buffer_manager import CircularVideoBuffer
import numpy as np

seed_database()
client = TestClient(app)


def test_auth_login_and_me():
    """Validates login with admin credentials and retrieves JWT token"""
    res = client.post("/api/auth/login", json={"username": "admin", "password": "PoliceSecure2026!"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "admin"

    token = data["access_token"]
    # Test protected /me endpoint
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["username"] == "admin"


def test_invalid_login():
    """Validates rejection of bad passwords"""
    res = client.post("/api/auth/login", json={"username": "admin", "password": "WrongPassword123"})
    assert res.status_code == 401


def test_incident_creation_and_listing():
    """Validates incident creation and query filtering"""
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "PoliceSecure2026!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    inc_payload = {
        "incident_id": "INC-TEST-9999",
        "detection_type": "Weapon",
        "object_detected": "Gun",
        "severity": "CRITICAL",
        "confidence": 98.4,
        "camera_code": "CAM-01",
        "location": "Main Gate North"
    }

    create_res = client.post("/api/incidents", json=inc_payload)
    assert create_res.status_code == 200
    assert create_res.json()["incident_id"] == "INC-TEST-9999"

    # List incidents
    list_res = client.get("/api/incidents?detection_type=Weapon", headers=headers)
    assert list_res.status_code == 200
    incidents = list_res.json()
    assert any(i["incident_id"] == "INC-TEST-9999" for i in incidents)


def test_complete_evidence_upload_verify_and_decrypt():
    """Validates full evidence upload, SHA-256 verification, and authorized decryption"""
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "PoliceSecure2026!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch Police ML-KEM Public Key
    pk_res = client.get("/api/pqc/public-key")
    assert pk_res.status_code == 200
    import base64
    police_pk = base64.b64decode(pk_res.json()["public_key_b64"])

    # 2. Prepare Sample Evidence Clip
    buffer_mgr = CircularVideoBuffer(fps=10, pre_event_sec=1, post_event_sec=1)
    frames = [np.ones((240, 320, 3), dtype=np.uint8) * i for i in range(20)]
    raw_video, duration = buffer_mgr.compile_mp4_bytes(frames)

    # 3. Create Incident
    inc_id = "INC-TEST-CRYPTO-1"
    client.post("/api/incidents", json={
        "incident_id": inc_id,
        "detection_type": "Weapon",
        "object_detected": "Rifle",
        "severity": "CRITICAL",
        "confidence": 95.0,
        "camera_code": "CAM-01",
        "location": "Main Gate"
    })

    # 4. Encrypt with ML-KEM-768 + AES-256-GCM
    metadata = {
        "incident_id": inc_id,
        "camera_code": "CAM-01",
        "location": "Main Gate",
        "detection_type": "Weapon",
        "confidence": 95.0,
        "original_filename": f"{inc_id}.mp4"
    }
    qsep_bytes, header = QuantumSafeEvidencePackage.encrypt_and_package(raw_video, police_pk, metadata)

    # 5. Upload Evidence Package
    files = {"file": (f"{inc_id}.qsep", qsep_bytes, "application/octet-stream")}
    data = {"incident_id": inc_id, "original_filename": f"{inc_id}.mp4"}
    upload_res = client.post("/api/evidence/upload", data=data, files=files)
    assert upload_res.status_code == 200

    # 6. Verify Integrity
    verify_res = client.post(f"/api/evidence/{inc_id}/verify", headers=headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["is_valid"] is True
    assert verify_res.json()["status"] == "VERIFIED"

    # 7. Authorized Decryption
    decrypt_res = client.post(f"/api/evidence/{inc_id}/decrypt", headers=headers)
    assert decrypt_res.status_code == 200
    assert "video_stream_url" in decrypt_res.json()


def test_user_portal_registration_and_emergency_dispatch():
    """Validates Citizen/Store user registration, login, and emergency dispatch to Police HQ"""
    # 1. Register Citizen / Store Manager
    unique_username = f"store_mgr_{int(time.time()) % 10000}"
    reg_payload = {
        "username": unique_username,
        "badge_number": f"USR-{unique_username}",
        "full_name": "Marcus Kane (Vault Manager)",
        "role": "citizen",
        "password": "StorePass2026!"
    }
    reg_res = client.post(
        f"/api/user/register?organization=Crown%20Jewelers&location_address=77%20Fifth%20Avenue",
        json=reg_payload
    )
    assert reg_res.status_code == 200
    assert reg_res.json()["username"] == unique_username

    # 2. Login as Citizen User
    login_res = client.post("/api/auth/login", json={"username": unique_username, "password": "StorePass2026!"})
    assert login_res.status_code == 200
    user_token = login_res.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 3. User Camera Detects Weapon & Dispatches Emergency to Police HQ
    emergency_data = {
        "incident_id": f"INC-USR-{unique_username}",
        "detection_type": "Weapon",
        "object_detected": "Gun (Handgun)",
        "confidence": "96.5"
    }
    dispatch_res = client.post("/api/user/dispatch-emergency", data=emergency_data, headers=user_headers)
    assert dispatch_res.status_code == 200
    res_json = dispatch_res.json()
    assert res_json["status"] == "DISPATCHED_TO_POLICE"
    assert "NIST FIPS 203 ML-KEM-768" in res_json["pqc_encryption"]

    # 4. Check User Incident History
    history_res = client.get("/api/user/my-incidents", headers=user_headers)
    assert history_res.status_code == 200
    assert len(history_res.json()) >= 1
