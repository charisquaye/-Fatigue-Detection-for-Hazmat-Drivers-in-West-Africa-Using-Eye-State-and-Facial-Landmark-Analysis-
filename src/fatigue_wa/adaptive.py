"""Personal close/open thresholds, night scale, mid-haul clamp, open-eye drift."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class AdaptiveCalibrator:
    calibration_seconds: float = 8.0
    min_valid_frames: int = 80
    close_ratio: float = 0.68
    low_light_ear_scale: float = 0.92
    night_mode_luma_threshold: float = 70.0
    base_ear_threshold: float = 0.21
    hysteresis_gap: float = 0.03
    ear_open_min: float = 0.18
    ear_open_max: float = 0.45
    midhaul_seconds: float = 2700.0
    midhaul_clamp: float = 0.03
    open_drift_alpha: float = 0.02
    _ear_samples: list = field(default_factory=list)
    _luma_samples: list = field(default_factory=list)
    _elapsed: float = 0.0
    _since_reestimate: float = 0.0
    ready: bool = False
    rejected: bool = False
    reject_reason: str = ""
    ear_open: float = 0.30
    ear_threshold: float = 0.21
    ear_open_thr: float = 0.24
    night_mode: bool = False
    open_band_ema: Optional[float] = None
    last_clamp: bool = False

    def reset(self) -> None:
        self._ear_samples.clear()
        self._luma_samples.clear()
        self._elapsed = 0.0
        self._since_reestimate = 0.0
        self.ready = False
        self.rejected = False
        self.reject_reason = ""
        self.ear_threshold = self.base_ear_threshold
        self.ear_open_thr = self.base_ear_threshold + self.hysteresis_gap
        self.night_mode = False
        self.open_band_ema = None
        self.last_clamp = False

    def observe(self, ear: float, frame_luma: float, dt: float) -> None:
        if self.ready:
            return
        self._ear_samples.append(ear)
        self._luma_samples.append(frame_luma)
        self._elapsed += dt
        if self._elapsed >= self.calibration_seconds and len(self._ear_samples) >= max(15, self.min_valid_frames // 4):
            self._finalise()

    def _finalise(self) -> None:
        ears = np.array(self._ear_samples, dtype=np.float64)
        lumas = np.array(self._luma_samples, dtype=np.float64)
        if len(ears) < 15:
            self.rejected = True
            self.reject_reason = "too_few_frames"
            self.ready = True
            return
        p60 = float(np.percentile(ears, 60))
        high = ears[ears >= p60]
        upper = float(np.median(high)) if len(high) else float(np.median(ears))
        self.ear_open = upper
        if upper < self.ear_open_min:
            self.rejected = True
            self.reject_reason = "ear_open_low_sunglasses_or_mesh"
        elif upper > self.ear_open_max:
            self.rejected = True
            self.reject_reason = "ear_open_implausible"
        self.night_mode = float(np.median(lumas)) < self.night_mode_luma_threshold
        scale = self.low_light_ear_scale if self.night_mode else 1.0
        raw = float(upper * self.close_ratio * scale)
        self.ear_threshold = float(np.clip(raw, 0.16, 0.26))
        self.ear_open_thr = float(min(self.ear_threshold + self.hysteresis_gap, upper - 0.02))
        if self.ear_open_thr <= self.ear_threshold:
            self.ear_open_thr = self.ear_threshold + self.hysteresis_gap
        self.open_band_ema = upper
        self.ready = True

    def note_open_frame(self, smoothed_ear: float, closed: bool, dt: float) -> None:
        if not self.ready or closed:
            return
        if self.open_band_ema is None:
            self.open_band_ema = smoothed_ear
        else:
            self.open_band_ema = (
                self.open_drift_alpha * smoothed_ear + (1.0 - self.open_drift_alpha) * self.open_band_ema
            )
        self._since_reestimate += dt
        if self._since_reestimate < self.midhaul_seconds:
            return
        self._since_reestimate = 0.0
        candidate = float(self.open_band_ema)
        lo = self.ear_open - self.midhaul_clamp
        hi = self.ear_open + self.midhaul_clamp
        clamped = float(np.clip(candidate, lo, hi))
        self.last_clamp = abs(clamped - candidate) > 1e-6
        scale = self.low_light_ear_scale if self.night_mode else 1.0
        raw = float(clamped * self.close_ratio * scale)
        self.ear_threshold = float(np.clip(raw, 0.16, 0.26))
        self.ear_open_thr = float(min(self.ear_threshold + self.hysteresis_gap, clamped - 0.02))

    def open_eye_drift(self) -> float:
        if self.open_band_ema is None:
            return 0.0
        return float(self.ear_open - self.open_band_ema)

    def frame_luma(self, bgr_frame) -> float:
        h, w = bgr_frame.shape[:2]
        roi = bgr_frame[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
        b, g, r = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
        y = 0.114 * b + 0.587 * g + 0.299 * r
        return float(np.mean(y))
