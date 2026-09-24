"""MediaPipe Face Mesh landmark extraction for eye and mouth geometry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
MOUTH = [61, 291, 13, 14, 78, 308]
POSE_IDX = {
    "nose": 1,
    "chin": 152,
    "left_eye_outer": 33,
    "right_eye_outer": 263,
    "left_mouth": 61,
    "right_mouth": 291,
}


@dataclass
class FaceGeometry:
    left_eye: np.ndarray
    right_eye: np.ndarray
    mouth: np.ndarray
    pose_points: dict
    image_size: tuple


def _xy(landmark, width: int, height: int) -> np.ndarray:
    return np.array([landmark.x * width, landmark.y * height], dtype=np.float64)


def extract_geometry(face_landmarks, width: int, height: int) -> Optional[FaceGeometry]:
    if face_landmarks is None:
        return None
    pts = face_landmarks.landmark

    def subset(indices):
        return np.stack([_xy(pts[i], width, height) for i in indices], axis=0)

    pose = {name: _xy(pts[idx], width, height) for name, idx in POSE_IDX.items()}
    return FaceGeometry(
        left_eye=subset(LEFT_EYE),
        right_eye=subset(RIGHT_EYE),
        mouth=subset(MOUTH),
        pose_points=pose,
        image_size=(width, height),
    )
