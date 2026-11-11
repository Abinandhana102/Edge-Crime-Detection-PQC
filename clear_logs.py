"""
Clear Incident Logs and Evidence Utility Script
Clears incident records from the database and deletes associated encrypted evidence files.

Usage:
    python clear_logs.py               # Clears all incidents & evidence
    python clear_logs.py --user        # Clears only User/Store facility incidents
    python clear_logs.py --keep 10     # Clears older incidents, keeping the latest 10
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.app.config import settings, ENCRYPTED_EVIDENCE_DIR, DECRYPTED_CACHE_DIR
from backend.app.database import SessionLocal
from backend.app.models import Incident, Evidence, AuditLog


def clear_incident_logs(mode="all", keep_count=0):
    db = SessionLocal()
    try:
        query = db.query(Incident).order_by(Incident.created_at.desc())

        if mode == "user":
            query = query.filter(Incident.camera_code.like("CAM-USR%"))

        all_incidents = query.all()
        total_found = len(all_incidents)

        if keep_count > 0:
            incidents_to_delete = all_incidents[keep_count:]
        else:
            incidents_to_delete = all_incidents

        count = len(incidents_to_delete)
        if count == 0:
            print("No incidents found to clear.")
            return 0

        print(f"[*] Found {total_found} incidents in database.")
        print(f"[*] Deleting {count} incidents and associated evidence files...")

        deleted_files = 0
        for inc in incidents_to_delete:
            # 1. Delete DB Evidence records
            evidences = db.query(Evidence).filter(Evidence.incident_id == inc.incident_id).all()
            for ev in evidences:
                db.delete(ev)

            # 2. Delete encrypted evidence file
            qsep_path = ENCRYPTED_EVIDENCE_DIR / f"{inc.incident_id}.qsep"
            if qsep_path.exists():
                try:
                    qsep_path.unlink()
                    deleted_files += 1
                except Exception as e:
                    print(f"  [!] Could not delete {qsep_path.name}: {e}")

            # 3. Delete decrypted cached video
            cached_path = DECRYPTED_CACHE_DIR / f"{inc.incident_id}_decrypted.mp4"
            if cached_path.exists():
                try:
                    cached_path.unlink()
                    deleted_files += 1
                except Exception as e:
                    print(f"  [!] Could not delete {cached_path.name}: {e}")

            # 4. Delete Incident record
            db.delete(inc)

        db.commit()

        print(f"[+] Successfully cleared {count} incidents!")
        print(f"[+] Removed {deleted_files} physical evidence/video files from storage.")
        return count

    except Exception as e:
        db.rollback()
        print(f"[-] Error while clearing incidents: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clear Security Incident Logs and Evidence")
    parser.add_argument("--user", action="store_true", help="Clear only User / Store camera incidents")
    parser.add_argument("--keep", type=int, default=0, help="Number of latest incidents to keep (default: 0 = clear all)")
    args = parser.parse_args()

    mode = "user" if args.user else "all"
    clear_incident_logs(mode=mode, keep_count=args.keep)

