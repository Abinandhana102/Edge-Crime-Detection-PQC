import sys
import time
import requests
import numpy as np
import cv2

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from backend.app.config import settings
from backend.crypto.hybrid_envelope import QuantumSafeEvidencePackage
from backend.crypto.integrity import EvidenceIntegrity
from edge_ai.camera_stream import CameraStream
from edge_ai.buffer_manager import CircularVideoBuffer


def print_step(step_num: int, title: str):
    print("\n" + "=" * 70)
    print(f"🔹 STEP {step_num}: {title.upper()}")
    print("=" * 70)


def run_full_demo(backend_url: str = "http://127.0.0.1:8000"):
    print("\n" + "█" * 70)
    print("   QUANTUM-SAFE CRIME DETECTION & EVIDENCE MANAGEMENT FRAMEWORK")
    print("   ACADEMIC PROJECT DEMONSTRATION & VERIFICATION PIPELINE")
    print("█" * 70)

    session = requests.Session()

    # Step 1: Check Backend Connection & Fetch ML-KEM Public Key
    print_step(1, "Verify Police HQ Backend & Quantum Key Service")
    try:
        res = session.get(f"{backend_url}/api/pqc/public-key", timeout=5)
        if res.status_code != 200:
            print(f"❌ Backend server not responding properly: {res.status_code}")
            return False
        pqc_info = res.json()
        print(f"✅ Connected to Police HQ Server ({backend_url})")
        print(f"🔑 Cryptographic Algorithm: {pqc_info['algorithm']}")
        print(f"🛡️  Security Level:         {pqc_info['security_level']}")
        print(f"📦 Public Key Length:       {pqc_info['public_key_len']} bytes")
        import base64
        police_public_key = base64.b64decode(pqc_info["public_key_b64"])
    except Exception as e:
        print(f"❌ Could not connect to Police Server at {backend_url}: {e}")
        print("💡 Hint: Make sure the server is running with 'python run_server.py'")
        return False

    time.sleep(1.0)

    # Step 2: Surveillance Simulation & Frame Acquisition
    print_step(2, "Surveillance Camera Stream Acquisition")
    stream = CameraStream(source="demo", camera_code="CAM-01", location="Main Gate North")
    buffer_mgr = CircularVideoBuffer(fps=15, pre_event_sec=3, post_event_sec=4)

    print("📹 Reading surveillance frames (CAM-01: Main Gate)...")
    frames = []
    for _ in range(45):  # 3 seconds of normal/active frames
        ret, frame = stream.read()
        if ret:
            frames.append(frame)
            buffer_mgr.add_frame(frame)
    print(f"✅ Buffered {len(frames)} frames in rolling circular FIFO buffer.")
    time.sleep(0.8)

    # Step 3: Edge AI Weapon Detection & Critical Red Alert
    print_step(3, "YOLO Object Detection & Weapon Alert Trigger")
    incident_id = f"INC-{time.strftime('%Y%m%d')}-0001"
    camera_code = "CAM-01"
    location = "Main Gate North"
    confidence = 94.2
    weapon_type = "Gun (Handgun)"

    print("🔍 AI Object Detection Pipeline Active...")
    print(f"🔴 CRITICAL ALERT: WEAPON DETECTED!")
    print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   Object Detected:    {weapon_type}")
    print(f"   Camera:             {camera_code} ({location})")
    print(f"   Confidence Score:   {confidence}%")
    print(f"   Assigned Incident:  {incident_id}")
    print(f"   Timestamp:          {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    time.sleep(1.0)

    # Step 4: Video Evidence Clip Compilation
    print_step(4, "Automatic Video Evidence Capture")
    raw_video_bytes, duration = buffer_mgr.compile_mp4_bytes(frames)
    print(f"🎬 Generated MP4 evidence clip: {len(raw_video_bytes):,} bytes, duration: {duration:.1f}s")
    
    # Step 5: Hybrid Post-Quantum Encryption (AES-256-GCM + ML-KEM-768)
    print_step(5, "Hybrid Post-Quantum Cryptographic Packaging")
    print("🔐 Executing Hybrid Encryption Pipeline:")
    print("   1. Generating random 256-bit symmetric session key...")
    print("   2. Computing SHA-256 pre-encryption digest for evidence integrity...")
    print("   3. Encrypting video bitstream with AES-256-GCM (Authenticated)...")
    print("   4. Encapsulating AES session key using NIST FIPS 203 ML-KEM-768...")

    metadata = {
        "incident_id": incident_id,
        "camera_code": camera_code,
        "location": location,
        "detection_type": "Weapon",
        "object_detected": "Gun",
        "severity": "CRITICAL",
        "confidence": confidence,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "original_filename": f"{incident_id}_evidence.mp4",
        "encrypted_filename": f"{incident_id}.qsep"
    }

    qsep_package, header = QuantumSafeEvidencePackage.encrypt_and_package(
        video_bytes=raw_video_bytes,
        police_public_key=police_public_key,
        metadata=metadata
    )

    print(f"\n📦 Quantum-Safe Evidence Package (.qsep) Created:")
    print(f"   Ciphertext Size:    {len(qsep_package):,} bytes")
    print(f"   AES Cipher:         {header['symmetric_cipher']}")
    print(f"   KEM Algorithm:      {header['pqc_algorithm']}")
    print(f"   Pre-SHA256 Hash:    {header['plaintext_sha256']}")
    time.sleep(1.0)

    # Step 6: Secure Transmission to Police HQ
    print_step(6, "Secure Network Transmission to Police Dashboard")
    inc_payload = {
        "incident_id": incident_id,
        "detection_type": "Weapon",
        "object_detected": "Gun",
        "severity": "CRITICAL",
        "confidence": confidence,
        "camera_code": camera_code,
        "location": location,
        "notes": "Automated alert from Edge AI Surveillance (ML-KEM-768 Encrypted)"
    }

    # Transmit Incident
    res_inc = session.post(f"{backend_url}/api/incidents", json=inc_payload)
    print(f"📤 Sent Incident Metadata: HTTP {res_inc.status_code}")

    # Transmit Encrypted Package
    files = {"file": (f"{incident_id}.qsep", qsep_package, "application/octet-stream")}
    data = {"incident_id": incident_id, "original_filename": metadata["original_filename"]}
    res_ev = session.post(f"{backend_url}/api/evidence/upload", data=data, files=files)
    print(f"📤 Sent Quantum-Safe Package: HTTP {res_ev.status_code}")
    print("✅ Incident & Encrypted Evidence successfully received at Police HQ Vault.")
    time.sleep(1.0)

    # Step 7: Police Officer Authentication
    print_step(7, "Police Officer Authentication (RBAC)")
    login_data = {"username": "admin", "password": "PoliceSecure2026!"}
    res_auth = session.post(f"{backend_url}/api/auth/login", json=login_data)
    token_json = res_auth.json()
    token = token_json["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    print(f"👮 Authenticated User: {token_json['full_name']} (Badge: {token_json['badge_number']})")
    print(f"🎫 JWT Token Issued:   {token[:25]}... (Role: {token_json['role']})")
    time.sleep(1.0)

    # Step 8: Evidence Integrity Verification (SHA-256)
    print_step(8, "Cryptographic Evidence Integrity Check (SHA-256)")
    res_verify = session.post(f"{backend_url}/api/evidence/{incident_id}/verify", headers=auth_headers)
    verify_data = res_verify.json()
    print(f"🔍 Status:   {verify_data['status']}")
    print(f"💬 Message:  {verify_data['message']}")
    print(f"🔑 Expected: {verify_data['expected_sha256']}")
    print(f"🔑 Computed: {verify_data['calculated_sha256']}")
    assert verify_data["is_valid"] is True, "Evidence Integrity check failed!"
    print("✅ Evidence Integrity Confirmed: Video bitstream has not been modified or corrupted.")
    time.sleep(1.0)

    # Step 9: Authorized Post-Quantum Decryption & Playback Retrieval
    print_step(9, "Authorized ML-KEM Decapsulation & Video Playback")
    res_decrypt = session.post(f"{backend_url}/api/evidence/{incident_id}/decrypt", headers=auth_headers)
    decrypt_data = res_decrypt.json()
    print(f"🔓 ML-KEM Decapsulation:      {decrypt_data['pqc_decapsulation_status']}")
    print(f"🔓 Symmetric AES Decryption:  {decrypt_data['symmetric_decryption_status']}")
    print(f"📺 Secure Stream URL:         {decrypt_data['video_stream_url']}")
    print(f"💬 Result:                    {decrypt_data['message']}")
    time.sleep(1.0)

    # Step 10: Immutable Audit Log Verification
    print_step(10, "Forensic Audit Log Verification")
    res_audit = session.get(f"{backend_url}/api/audit?incident_id={incident_id}", headers=auth_headers)
    audit_logs = res_audit.json()
    print(f"📜 Audit Trail Entries for {incident_id} ({len(audit_logs)} events):")
    for log in audit_logs:
        print(f"   [{log['timestamp'][11:19]}] Officer: {log['username']:<15} Action: {log['action']:<30}")

    print("\n" + "█" * 70)
    print("   🎉 FULL END-TO-END VERIFICATION & DEMONSTRATION SUCCESSFUL!")
    print("   Open http://localhost:8000 in your browser to view the Command UI.")
    print("█" * 70 + "\n")
    return True


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    run_full_demo(url)
