"""
Unit Tests for Violence & Anomaly Detection, Zone Intrusion, and Abandoned Object Tracking
"""

import time
import numpy as np
import pytest
from edge_ai.violence_detector import ViolenceAnomalyDetector
from edge_ai.intrusion_detector import IntrusionDetector
from edge_ai.abandoned_tracker import AbandonedObjectTracker


# --- Violence Detection Tests ---
def test_violence_detector_flow():
    detector = ViolenceAnomalyDetector()
    f1 = np.zeros((240, 320, 3), dtype=np.uint8)
    f2 = np.ones((240, 320, 3), dtype=np.uint8) * 100

    r1 = detector.analyze_frame(f1)
    assert "classification" in r1
    assert "confidence" in r1

    r2 = detector.analyze_frame(f2)
    assert r2["classification"] in ["Normal", "Suspicious Activity", "Violence"]


# --- Zone Intrusion Tests ---
def test_point_in_polygon():
    # Square from (10, 10) to (50, 50)
    polygon = [[10.0, 10.0], [50.0, 10.0], [50.0, 50.0], [10.0, 50.0]]

    # Inside point
    assert IntrusionDetector.point_in_polygon((30.0, 30.0), polygon) is True

    # Outside point
    assert IntrusionDetector.point_in_polygon((5.0, 5.0), polygon) is False
    assert IntrusionDetector.point_in_polygon((70.0, 70.0), polygon) is False


def test_intrusion_detection():
    detector = IntrusionDetector()
    detector.set_zones([{
        "zone_code": "ZONE-01",
        "name": "Armory Vault",
        "polygon_points_json": "[[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]]",
        "severity": "CRITICAL"
    }])

    # Inside detection: bottom_center (250, 300) is inside [128, 96] to [512, 384]
    mock_persons_inside = [{
        "class_name": "person",
        "confidence": 95.0,
        "bbox": [200, 150, 300, 300],
        "bottom_center": [250, 300]  # inside (frame is 640x480)
    }]

    intrusions = detector.check_intrusions(mock_persons_inside, frame_width=640, frame_height=480)
    assert len(intrusions) == 1
    assert intrusions[0]["detection_type"] == "Intrusion"


# --- Abandoned Object Tests ---
def test_abandoned_object_tracker():
    tracker = AbandonedObjectTracker(stationary_threshold_sec=2.0, distance_threshold_px=100.0)
    
    t0 = 1000.0
    mock_bag = [{
        "class_name": "backpack",
        "confidence": 90.0,
        "center": [200, 200],
        "bbox": [180, 180, 220, 220]
    }]

    # First seen at t0
    alerts0 = tracker.update(mock_bag, current_time=t0)
    assert len(alerts0) == 0

    # 1 second later (stationary, but duration < 2.0s)
    alerts1 = tracker.update(mock_bag, current_time=t0 + 1.0)
    assert len(alerts1) == 0

    # 3 seconds later (stationary, duration 3.0s > 2.0s threshold, no persons nearby)
    alerts2 = tracker.update(mock_bag, current_time=t0 + 3.0)
    assert len(alerts2) == 1
    assert alerts2[0]["detection_type"] == "Abandoned Object"
