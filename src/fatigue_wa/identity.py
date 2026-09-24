"""Cheap face hash so a shared phone cannot keep another driver's thresholds."""

from __future__ import annotations

from typing import Optional

import hashlib
import numpy as np


def anchor_vector(pose_points: dict) -> np.ndarray:
    order = ("left_eye_outer", "right_eye_outer", "nose", "chin", "left_mouth", "right_mouth")
    raw = np.concatenate([pose_points[k] for k in order])
    origin = raw[:2].copy()
    centered = raw.reshape(-1, 2) - origin
    span = np.linalg.norm(centered[1]) + 1e-6
    return (centered / span).ravel()


def face_hash(pose_points: dict) -> str:
    vec = np.round(anchor_vector(pose_points), 3).tobytes()
    return hashlib.sha256(vec).hexdigest()[:16]


def mismatch(gate_vec: Optional[np.ndarray], now: dict, l2: float = 28.0) -> bool:
    if gate_vec is None:
        return False
    cur = anchor_vector(now)
    return float(np.linalg.norm(cur - gate_vec)) > (l2 / 100.0)
