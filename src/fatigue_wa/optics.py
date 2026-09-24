"""Dirty-lens and after-dusk glasses flags."""

from __future__ import annotations

from typing import Optional

import numpy as np


def eye_crop_sharpness(bgr_frame: Optional[np.ndarray], left_eye: Optional[np.ndarray], right_eye: Optional[np.ndarray]) -> float:
    if bgr_frame is None or left_eye is None:
        return 999.0
    gray = (0.114 * bgr_frame[:, :, 0] + 0.587 * bgr_frame[:, :, 1] + 0.299 * bgr_frame[:, :, 2]).astype(np.float64)
    pts = np.vstack([left_eye, right_eye]) if right_eye is not None else left_eye
    x0, y0 = int(max(0, pts[:, 0].min() - 4)), int(max(0, pts[:, 1].min() - 4))
    x1, y1 = int(min(gray.shape[1], pts[:, 0].max() + 4)), int(min(gray.shape[0], pts[:, 1].max() + 4))
    crop = gray[y0:y1, x0:x1]
    if crop.size < 16:
        return 0.0
    gy, gx = np.gradient(crop)
    return float(np.var(gx) + np.var(gy))


def glasses_dark_fraction(bgr_frame: Optional[np.ndarray], left_eye: Optional[np.ndarray], right_eye: Optional[np.ndarray]) -> float:
    if bgr_frame is None or left_eye is None:
        return 0.0
    gray = (0.114 * bgr_frame[:, :, 0] + 0.587 * bgr_frame[:, :, 1] + 0.299 * bgr_frame[:, :, 2])
    pts = np.vstack([left_eye, right_eye]) if right_eye is not None else left_eye
    x0, y0 = int(max(0, pts[:, 0].min() - 2)), int(max(0, pts[:, 1].min() - 2))
    x1, y1 = int(min(gray.shape[1], pts[:, 0].max() + 2)), int(min(gray.shape[0], pts[:, 1].max() + 2))
    crop = gray[y0:y1, x0:x1]
    if crop.size < 8:
        return 0.0
    return float(np.mean(crop < 40.0))


def after_dusk(hour_local: int, sunset_hour: int = 18) -> bool:
    return int(hour_local) >= int(sunset_hour) or int(hour_local) < 6
