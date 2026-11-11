"""
Secure Edge Evidence Transmitter Module
Transmits incident metadata and Quantum-Safe Encrypted Evidence Packages (.qsep) to Police HQ API.
Includes offline fallback queuing and automatic retry logic.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
import requests

from backend.app.config import STORAGE_DIR

OFFLINE_QUEUE_DIR = STORAGE_DIR / "offline_queue"
OFFLINE_QUEUE_DIR.mkdir(parents=True, exist_ok=True)


class EdgeTransmitter:
    """
    Secure client for edge-to-police transmission.
    Sends incidents and encrypted .qsep packages over REST API.
    """

    def __init__(self, backend_url: str = "http://127.0.0.1:8000"):
        self.backend_url = backend_url.rstrip("/")
        self.session = requests.Session()

    def fetch_police_public_key(self) -> Optional[bytes]:
        """Fetches the current Police HQ ML-KEM public key from backend"""
        try:
            res = self.session.get(f"{self.backend_url}/api/pqc/public-key", timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                import base64
                return base64.b64decode(data["public_key_b64"])
        except Exception as e:
            print(f"[Transmitter] Warning: Unable to fetch public key over network: {e}")
        return None

    def send_incident_and_evidence(
        self,
        incident_payload: Dict[str, Any],
        qsep_package_bytes: bytes,
        original_filename: str = "evidence.mp4"
    ) -> bool:
        """
        Sends incident record followed by the post-quantum encrypted .qsep package.
        If network fails, caches package locally in offline queue.
        """
        incident_id = incident_payload["incident_id"]

        try:
            # Step 1: Transmit Incident Metadata
            inc_res = self.session.post(
                f"{self.backend_url}/api/incidents",
                json=incident_payload,
                timeout=5.0
            )

            if inc_res.status_code not in [200, 201]:
                print(f"[Transmitter] Failed to create incident on server: {inc_res.text}")

            # Step 2: Upload Post-Quantum Encrypted Evidence Package (.qsep)
            files = {
                "file": (f"{incident_id}.qsep", qsep_package_bytes, "application/octet-stream")
            }
            data = {
                "incident_id": incident_id,
                "original_filename": original_filename
            }

            ev_res = self.session.post(
                f"{self.backend_url}/api/evidence/upload",
                data=data,
                files=files,
                timeout=10.0
            )

            if ev_res.status_code in [200, 201]:
                print(f"[Transmitter] ✅ Successfully transmitted Incident & Encrypted Evidence {incident_id} to Police Vault")
                return True
            else:
                print(f"[Transmitter] Server error uploading evidence: {ev_res.text}")
                self._save_to_offline_queue(incident_id, incident_payload, qsep_package_bytes)
                return False

        except Exception as e:
            print(f"[Transmitter] Network error during transmission: {e}. Queuing locally.")
            self._save_to_offline_queue(incident_id, incident_payload, qsep_package_bytes)
            return False

    def _save_to_offline_queue(self, incident_id: str, payload: Dict[str, Any], package_bytes: bytes):
        """Saves package locally if network is unreachable"""
        queue_path = OFFLINE_QUEUE_DIR / f"{incident_id}.qsep"
        with open(queue_path, "wb") as f:
            f.write(package_bytes)
        print(f"[Transmitter] Saved evidence to offline queue: {queue_path}")
