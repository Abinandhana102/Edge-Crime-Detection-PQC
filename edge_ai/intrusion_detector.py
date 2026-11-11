"""
Restricted Area Intrusion Detection Module
Performs Point-in-Polygon ray casting to detect unauthorized persons entering restricted zones.
"""

import json
from typing import List, Dict, Any, Tuple, Optional
import cv2
import numpy as np


class IntrusionDetector:
    """
    Evaluates whether detected person coordinates intersect with geo-fenced restricted polygon zones.
    """

    def __init__(self, zones: Optional[List[Dict[str, Any]]] = None):
        self.zones = zones or []

    def set_zones(self, zones: List[Dict[str, Any]]):
        """Updates active restricted zones"""
        self.zones = zones

    @staticmethod
    def point_in_polygon(point: Tuple[float, float], polygon: List[List[float]]) -> bool:
        """
        Ray-casting algorithm to test if (x, y) is inside polygon vertices.
        """
        x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def check_intrusions(
        self,
        person_detections: List[Dict[str, Any]],
        frame_width: int,
        frame_height: int
    ) -> List[Dict[str, Any]]:
        """
        Tests all detected persons against all active restricted zones.
        Returns list of intrusion events.
        """
        intrusions = []

        for zone in self.zones:
            try:
                poly_data = zone.get("polygon_points_json")
                if isinstance(poly_data, str):
                    poly_points = json.loads(poly_data)
                elif isinstance(poly_data, list):
                    poly_points = poly_data
                else:
                    continue
            except Exception:
                continue

            # Convert normalized points to absolute pixels if in [0, 1]
            abs_polygon = []
            for pt in poly_points:
                px = pt[0] * frame_width if pt[0] <= 1.0 else pt[0]
                py = pt[1] * frame_height if pt[1] <= 1.0 else pt[1]
                abs_polygon.append([px, py])

            for person in person_detections:
                if person.get("class_name", "").lower() != "person":
                    continue

                # Test bottom-center of person bounding box (feet position)
                cx, y2 = person["bottom_center"]
                if self.point_in_polygon((cx, y2), abs_polygon):
                    intrusions.append({
                        "zone_code": zone.get("zone_code", "ZONE-01"),
                        "zone_name": zone.get("name", "Restricted Area"),
                        "severity": zone.get("severity", "HIGH"),
                        "person_bbox": person["bbox"],
                        "confidence": person["confidence"],
                        "detection_type": "Intrusion",
                        "object_detected": "Person in Restricted Zone"
                    })

        return intrusions

    def draw_zones(self, frame: np.ndarray) -> np.ndarray:
        """Draws highlighted translucent overlay over all active restricted zones"""
        annotated = frame.copy()
        h, w = frame.shape[:2]
        overlay = annotated.copy()

        for zone in self.zones:
            try:
                poly_data = zone.get("polygon_points_json")
                poly_points = json.loads(poly_data) if isinstance(poly_data, str) else poly_data
                abs_points = np.array([
                    [int(pt[0] * w if pt[0] <= 1.0 else pt[0]), int(pt[1] * h if pt[1] <= 1.0 else pt[1])]
                    for pt in poly_points
                ], np.int32)
                abs_points = abs_points.reshape((-1, 1, 2))

                # Red/Orange filled translucent zone
                cv2.fillPoly(overlay, [abs_points], (0, 0, 180))
                cv2.polylines(annotated, [abs_points], True, (0, 140, 255), 2)

                # Zone label
                centroid_x = int(np.mean(abs_points[:, 0, 0]))
                centroid_y = int(np.mean(abs_points[:, 0, 1]))
                label = f"RESTRICTED: {zone.get('name', 'Zone')}"
                cv2.putText(annotated, label, (centroid_x - 80, centroid_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            except Exception:
                continue

        cv2.addWeighted(overlay, 0.25, annotated, 0.75, 0, annotated)
        return annotated
