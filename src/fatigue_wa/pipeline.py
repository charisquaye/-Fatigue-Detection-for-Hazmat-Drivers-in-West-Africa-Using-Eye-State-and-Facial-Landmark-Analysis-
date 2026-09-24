"""End-to-end per-frame pipeline."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from fatigue_wa.adaptive import AdaptiveCalibrator
from fatigue_wa.alerts import AlertManager
from fatigue_wa.fusion import EvidenceFusion, FusionResult
from fatigue_wa.landmarks import extract_geometry
from fatigue_wa.metrics import TemporalState, estimate_pitch_degrees, mean_ear, mouth_aspect_ratio


@dataclass
class FrameOutput:
    ear: float
    mar: float
    perclos: float
    pitch: float
    result: FusionResult
    alert: Optional[str]


class FatiguePipeline:
    def __init__(self, cfg: dict[str, Any], fps: float = 25.0) -> None:
        self.cfg = cfg
        self.fps = fps
        self.temporal = TemporalState(fps=fps, window_seconds=float(cfg["metrics"]["perclos_window_seconds"]))
        acfg = cfg["adaptive"]
        self.calibrator = AdaptiveCalibrator(
            calibration_seconds=float(acfg["calibration_seconds"]),
            low_light_ear_scale=float(acfg["low_light_ear_scale"]),
            night_mode_luma_threshold=float(acfg["night_mode_luma_threshold"]),
            base_ear_threshold=float(cfg["metrics"]["ear_close_threshold"]),
        )
        if not acfg.get("enable", True):
            self.calibrator.ready = True
            self.calibrator.ear_threshold = float(cfg["metrics"]["ear_close_threshold"])
        self.fusion = EvidenceFusion(cfg)
        alerts = cfg["alerts"]
        self.alerts = AlertManager(
            cooldown_seconds=float(alerts["cooldown_seconds"]),
            escalate_after=int(alerts["escalate_after"]),
            log_path=str(alerts["log_path"]),
        )
        self._t0 = time.time()

    def process_geometry(self, geometry, frame_bgr: Optional[np.ndarray] = None, timestamp: Optional[float] = None) -> FrameOutput:
        t = time.time() - self._t0 if timestamp is None else timestamp
        if geometry is None:
            result = self.fusion.infer(
                calibrating=not self.calibrator.ready,
                face_present=False,
                perclos_value=self.temporal.current_perclos(),
                closed=False,
                long_blink_rate=self.temporal.long_blink_rate(),
                mar=0.0,
                pitch=0.0,
            )
            return FrameOutput(0.0, 0.0, self.temporal.current_perclos(), 0.0, result, None)
        ear = mean_ear(geometry.left_eye, geometry.right_eye)
        mar = mouth_aspect_ratio(geometry.mouth)
        pitch = estimate_pitch_degrees(geometry.pose_points, geometry.image_size)
        luma = 128.0 if frame_bgr is None else self.calibrator.frame_luma(frame_bgr)
        self.calibrator.observe(ear, luma, 1.0 / max(self.fps, 1.0))
        closed = ear < self.calibrator.ear_threshold
        self.temporal.update(ear, mar, closed, t)
        result = self.fusion.infer(
            calibrating=not self.calibrator.ready,
            face_present=True,
            perclos_value=self.temporal.current_perclos(),
            closed=closed,
            long_blink_rate=self.temporal.long_blink_rate(self.cfg["metrics"]["long_blink_seconds"]),
            mar=mar,
            pitch=pitch,
        )
        return FrameOutput(ear, mar, self.temporal.current_perclos(), pitch, result, self.alerts.maybe_alert(result))

    def process_mediapipe(self, face_landmarks, width: int, height: int, frame_bgr=None, timestamp=None) -> FrameOutput:
        return self.process_geometry(extract_geometry(face_landmarks, width, height), frame_bgr=frame_bgr, timestamp=timestamp)
