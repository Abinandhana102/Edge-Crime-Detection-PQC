import sys
import time
import argparse
import cv2
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from backend.app.config import settings
from backend.app.database import get_police_public_key
from edge_ai.camera_stream import CameraStream
from edge_ai.detector import ObjectDetector
from edge_ai.violence_detector import ViolenceAnomalyDetector
from edge_ai.intrusion_detector import IntrusionDetector
from edge_ai.abandoned_tracker import AbandonedObjectTracker
from edge_ai.buffer_manager import CircularVideoBuffer
from edge_ai.event_manager import EventManager
from edge_ai.evidence_recorder import EvidenceRecorder
from edge_ai.edge_transmitter import EdgeTransmitter


def run_edge_ai(
    source: str = "demo",
    camera_code: str = "CAM-01",
    location: str = "Main Gate North",
    backend_url: str = "http://127.0.0.1:8000",
    show_display: bool = True
):
    print("=" * 70)
    print("🛡️  EDGE AI CRIME DETECTION & QUANTUM-SAFE EVIDENCE SYSTEM")
    print(f"📡 Camera: {camera_code} | Location: {location} | Stream Source: {source}")
    print("🔐 Post-Quantum Scheme: NIST FIPS 203 ML-KEM-768 + AES-256-GCM")
    print("=" * 70)

    # 1. Initialize Subsystems
    stream = CameraStream(source=source, camera_code=camera_code, location=location)
    detector = ObjectDetector(conf_thresh=settings.DEFAULT_CONFIDENCE_THRESHOLD)
    violence_detector = ViolenceAnomalyDetector()
    intrusion_detector = IntrusionDetector()
    abandoned_tracker = AbandonedObjectTracker(stationary_threshold_sec=settings.ABANDONED_OBJECT_TIME_SEC)
    buffer_mgr = CircularVideoBuffer(fps=15, pre_event_sec=settings.PRE_EVENT_BUFFER_SEC, post_event_sec=settings.POST_EVENT_BUFFER_SEC)
    event_mgr = EventManager(cooldown_seconds=settings.DEBOUNCE_COOLDOWN_SEC)
    transmitter = EdgeTransmitter(backend_url=backend_url)
    recorder = EvidenceRecorder(transmitter=transmitter, buffer_mgr=buffer_mgr)

    # 2. Get Police HQ ML-KEM Public Key
    police_pk = transmitter.fetch_police_public_key()
    if not police_pk:
        print("[EdgeAI] Fetching Police Public Key from local secure store...")
        police_pk = get_police_public_key()

    # Pre-configure Demo Restricted Zone on CAM-04 or CAM-01
    intrusion_detector.set_zones([{
        "zone_code": "ZONE-01",
        "name": "Secured Perimeter Entrance",
        "polygon_points_json": "[[0.20, 0.40], [0.80, 0.40], [0.85, 0.90], [0.15, 0.90]]",
        "severity": "HIGH"
    }])

    fps_timer = time.time()
    frame_count = 0
    fps_display = 0.0

    critical_alert_active = False
    alert_banner_text = ""
    alert_banner_expire = 0.0

    print("\n[EdgeAI] System Online. Monitoring live surveillance feed... Press 'q' to stop.")

    try:
        while True:
            ret, frame = stream.read()
            if not ret:
                time.sleep(0.05)
                continue

            current_time = time.time()
            frame_count += 1
            if current_time - fps_timer >= 1.0:
                fps_display = frame_count / (current_time - fps_timer)
                frame_count = 0
                fps_timer = current_time

            # Add raw frame to circular rolling buffer
            buffer_mgr.add_frame(frame)

            # Step 1: Run YOLO Object Detection
            detections = detector.detect(frame)

            # Step 2: Run Violence & Anomaly Detection
            violence_result = violence_detector.analyze_frame(frame)

            # Step 3: Run Restricted Zone Intrusion Check
            intrusions = intrusion_detector.check_intrusions(detections, frame.shape[1], frame.shape[0])

            # Step 4: Run Abandoned Luggage Tracking
            abandoned_alerts = abandoned_tracker.update(detections, current_time)

            # Step 5: Evaluate Threats & Trigger Red Alert
            active_threat = None

            # Priority 1: Weapon Detection (CRITICAL)
            for d in detections:
                if d["is_weapon"]:
                    active_threat = {
                        "detection_type": "Weapon",
                        "object_detected": d["class_name"],
                        "severity": "CRITICAL",
                        "confidence": d["confidence"]
                    }
                    break

            # Priority 2: Violence Detected (CRITICAL/HIGH)
            if not active_threat and violence_result["is_alert"]:
                active_threat = {
                    "detection_type": "Violence",
                    "object_detected": violence_result["classification"],
                    "severity": "CRITICAL" if violence_result["classification"] == "Violence" else "HIGH",
                    "confidence": violence_result["confidence"]
                }

            # Priority 3: Restricted Area Intrusion (HIGH)
            if not active_threat and intrusions:
                inv = intrusions[0]
                active_threat = {
                    "detection_type": "Intrusion",
                    "object_detected": f"Intruder in {inv['zone_name']}",
                    "severity": inv["severity"],
                    "confidence": inv["confidence"]
                }

            # Priority 4: Abandoned Luggage (MEDIUM/HIGH)
            if not active_threat and abandoned_alerts:
                ab = abandoned_alerts[0]
                active_threat = {
                    "detection_type": "Abandoned Object",
                    "object_detected": ab["object_detected"],
                    "severity": ab["severity"],
                    "confidence": ab["confidence"]
                }

            # Step 6: Trigger Incident & Hybrid Encryption
            if active_threat:
                # Check debounce controller
                should_alert, inc_id_or_reason = event_mgr.should_trigger(
                    camera_code=camera_code,
                    detection_type=active_threat["detection_type"],
                    current_time=current_time
                )

                if should_alert:
                    incident_id = inc_id_or_reason
                    critical_alert_active = True
                    alert_banner_text = f"CRITICAL ALERT: {active_threat['detection_type'].upper()} ({active_threat['object_detected'].upper()}) - {active_threat['confidence']}%"
                    alert_banner_expire = current_time + 6.0

                    print("\n" + "=" * 55)
                    print("🔴 CRITICAL ALERT GENERATED")
                    print(f"   Incident ID: {incident_id}")
                    print(f"   Detection:   {active_threat['detection_type']} ({active_threat['object_detected']})")
                    print(f"   Camera:      {camera_code} ({location})")
                    print(f"   Confidence:  {active_threat['confidence']:.1f}%")
                    print(f"   Time:        {time.strftime('%H:%M:%S')}")
                    print("=" * 55)

                    # Trigger evidence clip recording
                    buffer_mgr.trigger_recording(incident_id)

                    # Dispatch hybrid encrypted evidence package (.qsep)
                    recorder.process_and_dispatch(
                        incident_id=incident_id,
                        detection_info=active_threat,
                        camera_code=camera_code,
                        location=location,
                        police_public_key=police_pk
                    )
                else:
                    # Incident is ongoing under debounce cooldown
                    buffer_mgr.extend_recording()

            # Manage alert banner timer
            if critical_alert_active and current_time > alert_banner_expire:
                critical_alert_active = False

            # Step 7: Render HUD Overlays & Visual Output
            if show_display:
                annotated_frame = detector.draw_hud_overlay(
                    frame=frame,
                    detections=detections,
                    camera_code=camera_code,
                    location=location,
                    critical_alert_active=critical_alert_active,
                    alert_text=alert_banner_text
                )
                annotated_frame = intrusion_detector.draw_zones(annotated_frame)

                # Overlay FPS & Status
                cv2.putText(
                    annotated_frame,
                    f"FPS: {fps_display:.1f} | Stream: {source}",
                    (annotated_frame.shape[1] - 220, 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1
                )

                cv2.imshow("Edge AI Surveillance - High Security Monitor", annotated_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[EdgeAI] Stopping Edge Surveillance Worker...")
    finally:
        stream.release()
        cv2.destroyAllWindows()
        print("[EdgeAI] Worker cleanly terminated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Edge AI Crime Detection & Quantum-Safe Surveillance Worker")
    parser.add_argument("--source", type=str, default="demo", help="Stream source: 'webcam', '0', 'demo', or RTSP/video URL")
    parser.add_argument("--camera", type=str, default="CAM-01", help="Camera code e.g. CAM-01")
    parser.add_argument("--location", type=str, default="Main Gate North", help="Camera physical location")
    parser.add_argument("--backend", type=str, default="http://127.0.0.1:8000", help="Police HQ Backend URL")
    parser.add_argument("--headless", action="store_true", help="Run without opening OpenCV GUI window")

    args = parser.parse_args()
    run_edge_ai(
        source=args.source,
        camera_code=args.camera,
        location=args.location,
        backend_url=args.backend,
        show_display=not args.headless
    )
