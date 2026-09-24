"""Unit tests for geometric metrics and fusion logic."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fatigue_wa.config import load_config
from fatigue_wa.fusion import EvidenceFusion, FatigueState
from fatigue_wa.metrics import eye_aspect_ratio, mouth_aspect_ratio, perclos


def open_eye():
    return np.array([[0, 0], [6, -6], [14, -6], [20, 0], [14, 6], [6, 6]], dtype=float)


def closed_eye():
    return np.array([[0, 0], [6, -1], [14, -1], [20, 0], [14, 1], [6, 1]], dtype=float)


def test_ear_open_greater_than_closed():
    assert eye_aspect_ratio(open_eye()) > eye_aspect_ratio(closed_eye())
    assert eye_aspect_ratio(open_eye()) > 0.25
    assert eye_aspect_ratio(closed_eye()) < 0.15


def test_mar_increases_with_opening():
    closed = np.array([[0, 0], [40, 0], [20, -2], [20, 2], [8, 0], [32, 0]], dtype=float)
    yawn = np.array([[0, 0], [40, 0], [20, -20], [20, 20], [8, 0], [32, 0]], dtype=float)
    assert mouth_aspect_ratio(yawn) > mouth_aspect_ratio(closed)


def test_perclos():
    flags = [False] * 70 + [True] * 30
    assert perclos(flags) == pytest.approx(0.3)


def test_fusion_microsleep_on_sustained_closure():
    cfg = load_config(ROOT / "configs" / "default.yaml")
    fusion = EvidenceFusion(cfg)
    result = None
    for _ in range(cfg["metrics"]["consecutive_closed_frames"] + 2):
        result = fusion.infer(
            calibrating=False, face_present=True, perclos_value=0.5, closed=True,
            long_blink_rate=0.6, mar=0.2, pitch=5.0,
        )
    assert result.state == FatigueState.MICROSLEEP


def test_fusion_alert_when_open():
    cfg = load_config(ROOT / "configs" / "default.yaml")
    fusion = EvidenceFusion(cfg)
    result = fusion.infer(
        calibrating=False, face_present=True, perclos_value=0.05, closed=False,
        long_blink_rate=0.05, mar=0.2, pitch=2.0,
    )
    assert result.state == FatigueState.ALERT
