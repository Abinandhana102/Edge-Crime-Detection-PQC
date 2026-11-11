"""
YOLO Object & Weapon Detection Engine
Integrates YOLO for real-time inference, weapon identification, and bounding box rendering.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import cv2
import numpy as np
from ultralytics import YOLO

from backend.app.config import BASE_DIR, settings

# Target Surveillance & Threat Classes (Ignore non-security COCO items like TV/Laptop)
DEFAULT_WEAPON_CLASSES = {
    "gun": {"severity": "CRITICAL", "type": "Weapon", "display_name": "Gun / Firearm", "color": (0, 0, 255)},
    "pistol": {"severity": "CRITICAL", "type": "Weapon", "display_name": "Pistol / Handgun", "color": (0, 0, 255)},
    "rifle": {"severity": "CRITICAL", "type": "Weapon", "display_name": "Rifle / Long Gun", "color": (0, 0, 255)},
    "knife": {"severity": "CRITICAL", "type": "Weapon", "display_name": "Knife / Blade", "color": (0, 0, 255)},
    "scissors": {"severity": "HIGH", "type": "Weapon", "display_name": "Scissors / Sharp Edge", "color": (0, 140, 255)},
    "baseball bat": {"severity": "CRITICAL", "type": "Weapon", "display_name": "Stick / Blunt Weapon", "color": (0, 0, 255)},
    "tennis racket": {"severity": "CRITICAL", "type": "Weapon", "display_name": "Stick / Blunt Weapon", "color": (0, 0, 255)},
    "umbrella": {"severity": "HIGH", "type": "Weapon", "display_name": "Rod / Blunt Weapon", "color": (0, 0, 255)},
    "bottle": {"severity": "CRITICAL", "type": "Weapon", "display_name": "Glass Bottle / Weapon", "color": (0, 0, 255)},
    "backpack": {"severity": "MEDIUM", "type": "Object", "display_name": "Backpack", "color": (255, 180, 0)},
    "handbag": {"severity": "MEDIUM", "type": "Object", "display_name": "Handbag", "color": (255, 180, 0)},
    "suitcase": {"severity": "MEDIUM", "type": "Object", "display_name": "Suitcase", "color": (255, 180, 0)},
    "person": {"severity": "LOW", "type": "Person", "display_name": "Person", "color": (0, 255, 0)}
}


class ObjectDetector:
    """
    YOLOv8/v11 Object & Weapon Detection Engine.
    Processes surveillance frames, extracts bounding boxes, classes, and confidence scores
    strictly using YOLO deep neural network inference (100% heuristic-free).
    """

    def __init__(self, model_path: Optional[str] = None, conf_thresh: float = 0.35):
        self.conf_thresh = conf_thresh
        self.weapon_conf_thresh = 0.15  # Optimized threshold for moving weapons & surveillance sticks

        if model_path is None:
            local_model = BASE_DIR / "models" / "yolov8n.pt"
            root_model = BASE_DIR / "yolov8n.pt"
            if local_model.exists():
                model_path = str(local_model)
            elif root_model.exists():
                model_path = str(root_model)
            else:
                model_path = "yolov8n.pt"

        print(f"[EdgeAI] Initializing YOLO Object Detection model from '{model_path}'...")
        self.model = YOLO(model_path)
        self.weapon_classes = DEFAULT_WEAPON_CLASSES

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Runs object & weapon detection on a single frame using pure YOLO deep neural network.
        Detects Knife, Scissors, Gun, Baseball Bat, Wooden Stick/Kattai, Person, and Luggage.
        Filters out stationery (e.g. Marker pens, Pencils) and non-security objects (e.g. TV, Laptop).
        """
        results = self.model(frame, verbose=False, conf=self.weapon_conf_thresh)
        detections = []
        h, w = frame.shape[:2]

        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_id = int(box.cls[0].item())
                cls_name = self.model.names[cls_id].lower()
                conf = float(box.conf[0].item()) * 100.0
                xyxy = box.xyxy[0].cpu().numpy().astype(int).tolist()
                x1, y1, x2, y2 = xyxy

                # Filter strictly to surveillance / threat classes
                if cls_name not in self.weapon_classes:
                    continue

                is_weapon = cls_name in [
                    "knife", "scissors", "gun", "pistol", "rifle",
                    "baseball bat", "tennis racket", "umbrella", "bottle"
                ]

                # Threshold verification
                if cls_name == "person":
                    if conf < (self.conf_thresh * 100.0):
                        continue
                elif is_weapon and conf < (self.weapon_conf_thresh * 100.0):
                    continue

                # Normalized coordinates
                nx1, ny1, nx2, ny2 = x1 / w, y1 / h, x2 / w, y2 / h
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                meta = self.weapon_classes[cls_name]
                display_label = meta.get("display_name", cls_name.capitalize())
                severity = meta["severity"]
                detection_type = meta["type"]
                color = meta.get("color", (0, 255, 0))

                detections.append({
                    "class_name": display_label,
                    "raw_class": cls_name,
                    "confidence": round(conf, 1),
                    "bbox": [x1, y1, x2, y2],
                    "normalized_bbox": [round(nx1, 4), round(ny1, 4), round(nx2, 4), round(ny2, 4)],
                    "center": [cx, cy],
                    "bottom_center": [cx, y2],
                    "is_weapon": is_weapon,
                    "severity": severity,
                    "detection_type": detection_type,
                    "color": color
                })

        return detections

    def draw_hud_overlay(
        self,
        frame: np.ndarray,
        detections: List[Dict[str, Any]],
        camera_code: str = "CAM-01",
        location: str = "Main Gate North",
        critical_alert_active: bool = False,
        alert_text: Optional[str] = None
    ) -> np.ndarray:
        """
        Renders HUD overlays, bounding boxes, labels, telemetry banner, and Red Alert indicators on frame.
        """
        annotated = frame.copy()
        h, w = annotated.shape[:2]

        # Draw Detections
        for d in detections:
            x1, y1, x2, y2 = d["bbox"]
            color = d.get("color", (0, 255, 0))
            label = f"{d['class_name']} {d['confidence']}%"

            # Thicker glow for weapons
            thickness = 3 if d["is_weapon"] else 2
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

            # Label banner
            (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            cv2.rectangle(annotated, (x1, max(0, y1 - th - 10)), (x1 + tw + 10, y1), color, -1)
            cv2.putText(
                annotated,
                label,
                (x1 + 5, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255) if color != (255, 255, 255) else (0, 0, 0),
                2
            )

        # Top Telemetry Header
        cv2.rectangle(annotated, (0, 0), (w, 40), (20, 24, 33), -1)
        header_text = f"CAM: {camera_code} | LOC: {location} | AI: ACTIVE | PQC: ML-KEM-768"
        cv2.putText(annotated, header_text, (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 240, 255), 2)

        # Red Alert Banner if Critical Weapon Detected
        if critical_alert_active:
            # Flashing red border & top alert banner
            cv2.rectangle(annotated, (0, 0), (w, h), (0, 0, 255), 8)
            cv2.rectangle(annotated, (0, 40), (w, 90), (0, 0, 220), -1)
            alert_msg = alert_text or "CRITICAL ALERT: WEAPON DETECTED - EVIDENCE SECURING"
            cv2.putText(annotated, alert_msg, (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        return annotated
