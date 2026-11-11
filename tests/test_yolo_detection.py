"""
Unit Tests for Edge AI YOLO Detection Module
"""

import numpy as np
import pytest
from edge_ai.detector import ObjectDetector


def test_detector_initialization():
    """Validates detector loads YOLO weights and class mappings"""
    detector = ObjectDetector(conf_thresh=0.25)
    assert detector.model is not None
    assert "gun" in detector.weapon_classes
    assert "knife" in detector.weapon_classes


def test_detector_inference_on_synthetic_frame():
    """Validates inference pipeline executes cleanly without exceptions"""
    detector = ObjectDetector(conf_thresh=0.25)
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Draw simple shape
    test_frame[100:300, 200:400] = 128

    detections = detector.detect(test_frame)
    assert isinstance(detections, list)


def test_detector_hud_overlay():
    """Validates HUD overlay drawing on frames"""
    detector = ObjectDetector()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_detections = [{
        "class_name": "Gun",
        "confidence": 94.2,
        "bbox": [100, 100, 200, 200],
        "is_weapon": True,
        "color": (0, 0, 255)
    }]

    annotated = detector.draw_hud_overlay(
        frame=frame,
        detections=mock_detections,
        camera_code="CAM-01",
        location="Main Gate",
        critical_alert_active=True,
        alert_text="CRITICAL ALERT: GUN DETECTED"
    )

    assert annotated.shape == frame.shape
    assert not np.array_equal(annotated, frame)  # Has HUD overlays drawn
