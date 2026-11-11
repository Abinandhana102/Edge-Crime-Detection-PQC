"""
Evidence Recorder & Cryptographic Packaging Pipeline
Coordinates video frame compilation, AES-256-GCM + ML-KEM-768 hybrid encryption, and transmission.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np

from backend.crypto.hybrid_envelope import QuantumSafeEvidencePackage
from edge_ai.buffer_manager import CircularVideoBuffer
from edge_ai.edge_transmitter import EdgeTransmitter


class EvidenceRecorder:
    """
    Automated evidence recorder: captures video buffer, applies hybrid PQC encryption, and dispatches to HQ.
    """

    def __init__(self, transmitter: EdgeTransmitter, buffer_mgr: CircularVideoBuffer):
        self.transmitter = transmitter
        self.buffer_mgr = buffer_mgr

    def process_and_dispatch(
        self,
        incident_id: str,
        detection_info: Dict[str, Any],
        camera_code: str,
        location: str,
        police_public_key: bytes,
        frames_to_encode: Optional[List[np.ndarray]] = None
    ) -> bool:
        """
        1. Compiles video buffer into MP4 binary stream.
        2. Encrypts video with AES-256-GCM and encapsulates AES key with ML-KEM-768 against Police Public Key.
        3. Generates SHA-256 integrity hash.
        4. Transmits evidence package to Police Dashboard.
        """
        # Step 1: Compile video
        video_bytes, duration = self.buffer_mgr.compile_mp4_bytes(frames_to_encode)

        # Step 2: Formulate Incident Metadata
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        metadata = {
            "incident_id": incident_id,
            "camera_code": camera_code,
            "camera_id": camera_code,
            "location": location,
            "detection_type": detection_info.get("detection_type", "Weapon"),
            "object_detected": detection_info.get("object_detected", "Gun"),
            "severity": detection_info.get("severity", "CRITICAL"),
            "confidence": detection_info.get("confidence", 94.2),
            "timestamp": now_str,
            "duration_seconds": duration,
            "original_filename": f"{incident_id}_evidence.mp4",
            "encrypted_filename": f"{incident_id}.qsep"
        }

        # Step 3: Hybrid Post-Quantum Encryption
        qsep_package_bytes, header = QuantumSafeEvidencePackage.encrypt_and_package(
            video_bytes=video_bytes,
            police_public_key=police_public_key,
            metadata=metadata
        )

        # Step 4: Transmit
        incident_payload = {
            "incident_id": incident_id,
            "detection_type": metadata["detection_type"],
            "object_detected": metadata["object_detected"],
            "severity": metadata["severity"],
            "confidence": metadata["confidence"],
            "camera_code": camera_code,
            "location": location,
            "notes": f"Post-Quantum Encrypted Evidence ({header['pqc_algorithm']}) captured at {location}"
        }

        success = self.transmitter.send_incident_and_evidence(
            incident_payload=incident_payload,
            qsep_package_bytes=qsep_package_bytes,
            original_filename=metadata["original_filename"]
        )

        return success
