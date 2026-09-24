"""End-to-end per-frame pipeline matching Chapter 4 WA-PERCLOS-HYS."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import numpy as np

from fatigue_wa.adaptive import AdaptiveCalibrator
from fatigue_wa.alerts import AlertManager
from fatigue_wa.fusion import EvidenceFusion, FusionResult
from fatigue_wa.identity import anchor_vector, mismatch
from fatigue_wa.landmarks import extract_geometry
from fatigue_wa.metrics import EarSmoother, TemporalState, estimate_pitch_degrees, eye_aspect_ratio, mouth_aspect_ratio
from fatigue_wa.optics import after_dusk, eye_crop_sharpness, glasses_dark_fraction
from fatigue_wa.sensors import ImuGate, VoiceGate


@dataclass
class FrameOutput:
    ear: float
    mar: float
    perclos: float
    pitch: float
    result: FusionResult
    alert: Optional[str]
    closed: bool = False
    ear_open_drift: float = 0.0


class FatiguePipeline:
    def __init__(self, cfg: dict[str, Any], fps: float = 25.0) -> None:
        self.cfg = cfg
        self.fps = fps
        mcfg = cfg["metrics"]
        self.temporal = TemporalState(fps=fps, window_seconds=float(mcfg["perclos_window_seconds"]))
        self.smoother = EarSmoother(alpha=float(mcfg.get("ema_alpha", 0.4)))
        acfg = cfg["adaptive"]
        self.calibrator = AdaptiveCalibrator(
            calibration_seconds=float(acfg["calibration_seconds"]),
            min_valid_frames=int(acfg.get("min_valid_frames", 80)),
            close_ratio=float(acfg.get("close_ratio", 0.68)),
            low_light_ear_scale=float(acfg["low_light_ear_scale"]),
            night_mode_luma_threshold=float(acfg["night_mode_luma_threshold"]),
            base_ear_threshold=float(mcfg["ear_close_threshold"]),
            hysteresis_gap=float(mcfg.get("ear_hysteresis_gap", 0.03)),
            ear_open_min=float(acfg.get("ear_open_min", 0.18)),
            ear_open_max=float(acfg.get("ear_open_max", 0.45)),
            midhaul_seconds=float(acfg.get("midhaul_seconds", 2700)),
            midhaul_clamp=float(acfg.get("midhaul_clamp", 0.03)),
            open_drift_alpha=float(acfg.get("open_drift_alpha", 0.02)),
        )
        if not acfg.get("enable", True):
            self.calibrator.ready = True
        self.fusion = EvidenceFusion(cfg)
        alerts = cfg["alerts"]
        self.alerts = AlertManager(
            cooldown_seconds=float(alerts["cooldown_seconds"]),
            escalate_after=int(alerts["escalate_after"]),
            log_path=str(alerts["log_path"]),
        )
        ocfg = cfg.get("optics", {})
        self.sharpness_min = float(ocfg.get("sharpness_min", 18.0))
        self.glasses_dark = float(ocfg.get("glasses_dark_fraction", 0.62))
        self.sunset_hour = int(ocfg.get("sunset_hour_local", 18))
        icfg = cfg.get("identity", {})
        self.identity_on = bool(icfg.get("enable", True))
        self.mismatch_l2 = float(icfg.get("mismatch_l2", 28.0))
        self._gate_vec = None
        self.imu = ImuGate(rough_rms=float(cfg.get("imu", {}).get("rough_rms", 2.4)))
        self.voice = VoiceGate(energy_threshold=float(cfg.get("voice", {}).get("energy_threshold", 0.035)))
        self._t0 = time.time()

    def process_geometry(
        self,
        geometry,
        frame_bgr: Optional[np.ndarray] = None,
        timestamp: Optional[float] = None,
        hour_local: Optional[int] = None,
        accel_xyz: Optional[tuple] = None,
        mic_rms: Optional[float] = None,
    ) -> FrameOutput:
        t = time.time() - self._t0 if timestamp is None else timestamp
        dt = 1.0 / max(self.fps, 1.0)
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

        raw_left = eye_aspect_ratio(geometry.left_eye)
        raw_right = eye_aspect_ratio(geometry.right_eye)
        raw_mean = 0.5 * (raw_left + raw_right)
        ear = self.smoother.update(raw_mean)
        mar = mouth_aspect_ratio(geometry.mouth)
        pitch = estimate_pitch_degrees(geometry.pose_points, geometry.image_size)
        luma = 128.0 if frame_bgr is None else self.calibrator.frame_luma(frame_bgr)
        self.calibrator.observe(ear, luma, dt)
        if self.calibrator.ready:
            self.fusion.set_calibrated_thresholds(self.calibrator.ear_threshold, self.calibrator.ear_open_thr)
            if self._gate_vec is None:
                self._gate_vec = anchor_vector(geometry.pose_points)

        closed = self.fusion._eye_closed(raw_left, raw_right, ear)
        self.calibrator.note_open_frame(ear, closed, dt)
        if self.calibrator.ready:
            self.fusion.set_calibrated_thresholds(self.calibrator.ear_threshold, self.calibrator.ear_open_thr)

        self.temporal.update(ear, mar, closed, t)
        self.imu.observe(accel_xyz)

        hour = datetime.now().hour if hour_local is None else hour_local
        sharp = eye_crop_sharpness(frame_bgr, geometry.left_eye, geometry.right_eye)
        glasses = glasses_dark_fraction(frame_bgr, geometry.left_eye, geometry.right_eye) >= self.glasses_dark
        optics_dirty = frame_bgr is not None and sharp < self.sharpness_min
        glasses_dusk = glasses and after_dusk(hour, self.sunset_hour)
        shared = self.identity_on and mismatch(self._gate_vec, geometry.pose_points, self.mismatch_l2)

        result = self.fusion.infer(
            calibrating=not self.calibrator.ready,
            face_present=True,
            perclos_value=self.temporal.current_perclos(),
            closed=closed,
            long_blink_rate=self.temporal.long_blink_rate(self.cfg["metrics"]["long_blink_seconds"]),
            mar=mar,
            pitch=pitch,
            optics_dirty=optics_dirty,
            glasses_after_dusk=glasses_dusk,
            shared_device=shared,
            talking=self.voice.talking(mic_rms),
            rough_road=self.imu.rough_road(),
        )
        return FrameOutput(
            ear, mar, self.temporal.current_perclos(), pitch, result,
            self.alerts.maybe_alert(result), closed=closed,
            ear_open_drift=self.calibrator.open_eye_drift(),
        )

    def process_mediapipe(self, face_landmarks, width: int, height: int, frame_bgr=None, timestamp=None, **kw) -> FrameOutput:
        return self.process_geometry(extract_geometry(face_landmarks, width, height), frame_bgr=frame_bgr, timestamp=timestamp, **kw)
