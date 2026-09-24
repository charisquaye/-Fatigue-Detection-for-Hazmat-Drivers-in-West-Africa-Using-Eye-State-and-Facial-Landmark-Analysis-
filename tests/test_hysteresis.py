"""Hysteresis, calibration, and gate tests for Chapter 4."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fatigue_wa.adaptive import AdaptiveCalibrator
from fatigue_wa.config import load_config
from fatigue_wa.fusion import EvidenceFusion, FatigueState, HysteresisGate
from fatigue_wa.metrics import EarSmoother


def test_hysteresis_holds_through_rising_edge():
    g = HysteresisGate(0.20, 0.23)
    assert g.step(0.30) is False
    assert g.step(0.19) is True
    assert g.step(0.21) is True
    assert g.step(0.24) is False


def test_ema_lags_spike():
    s = EarSmoother(0.4)
    s.update(0.30)
    jumped = s.update(0.10)
    assert 0.10 < jumped < 0.30


def test_calibrator_p60_ratio():
    cal = AdaptiveCalibrator(calibration_seconds=0.5, min_valid_frames=10)
    for i in range(40):
        ear = 0.30 if i % 20 else 0.10
        cal.observe(ear, 120.0, 0.04)
    assert cal.ready
    assert 0.19 < cal.ear_threshold < 0.22
    assert cal.ear_open_thr > cal.ear_threshold


def test_calibrator_rejects_sunglasses_like_low_open():
    cal = AdaptiveCalibrator(calibration_seconds=0.4, min_valid_frames=8)
    for _ in range(30):
        cal.observe(0.12, 80.0, 0.04)
    assert cal.ready
    assert cal.rejected


def test_fusion_uses_hysteresis_run():
    cfg = load_config(ROOT / "configs" / "default.yaml")
    fusion = EvidenceFusion(cfg)
    fusion.set_calibrated_thresholds(0.20, 0.23)
    result = None
    for _ in range(cfg["metrics"]["consecutive_closed_frames"] + 2):
        result = fusion.infer(
            calibrating=False, face_present=True, perclos_value=0.4,
            closed=True, long_blink_rate=0.5, mar=0.2, pitch=1.0,
        )
    assert result.state == FatigueState.MICROSLEEP


def test_optics_and_shared_states():
    cfg = load_config(ROOT / "configs" / "default.yaml")
    fusion = EvidenceFusion(cfg)
    dirty = fusion.infer(
        calibrating=False, face_present=True, perclos_value=0.05,
        closed=False, long_blink_rate=0.0, mar=0.2, pitch=0.0, optics_dirty=True,
    )
    assert dirty.state == FatigueState.OPTICS_DIRTY
    dusk = fusion.infer(
        calibrating=False, face_present=True, perclos_value=0.05,
        closed=False, long_blink_rate=0.0, mar=0.2, pitch=0.0, glasses_after_dusk=True,
    )
    assert dusk.state == FatigueState.DEGRADED
