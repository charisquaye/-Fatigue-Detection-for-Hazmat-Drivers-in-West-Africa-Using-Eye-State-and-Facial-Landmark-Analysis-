"""West Africa operational adaptation: lighting, calibration, cabin context."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class AdaptiveCalibrator:
    calibration_seconds: float = 8.0
    low_light_ear_scale: float = 0.92
    night_mode_luma_threshold: float = 70.0
    base_ear_threshold: float = 0.21
    _ear_samples: list = field(default_factory=list)
    _luma_samples: list = field(default_factory=list)
    _elapsed: float = 0.0
    ready: bool = False
    ear_threshold: float = 0.21
    night_mode: bool = False

    def reset(self) -> None:
        self._ear_samples.clear()
        self._luma_samples.clear()
        self._elapsed = 0.0
        self.ready = False
        self.ear_threshold = self.base_ear_threshold
        self.night_mode = False

    def observe(self, ear: float, frame_luma: float, dt: float) -> None:
        if self.ready:
            return
        self._ear_samples.append(ear)
        self._luma_samples.append(frame_luma)
        self._elapsed += dt
        if self._elapsed >= self.calibration_seconds and len(self._ear_samples) >= 15:
            self._finalise()

    def _finalise(self) -> None:
        ears = np.array(self._ear_samples, dtype=np.float64)
        lumas = np.array(self._luma_samples, dtype=np.float64)
        openish = ears[ears >= np.quantile(ears, 0.6)]
        upper = float(np.median(openish)) if len(openish) else float(np.median(ears))
        raw = float(upper * 0.68)
        self.night_mode = float(np.median(lumas)) < self.night_mode_luma_threshold
        if self.night_mode:
            raw *= self.low_light_ear_scale
        self.ear_threshold = float(np.clip(raw, 0.16, 0.26))
        self.ready = True

    def frame_luma(self, bgr_frame) -> float:
        h, w = bgr_frame.shape[:2]
        roi = bgr_frame[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
        b, g, r = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
        y = 0.114 * b + 0.587 * g + 0.299 * r
        return float(np.mean(y))
