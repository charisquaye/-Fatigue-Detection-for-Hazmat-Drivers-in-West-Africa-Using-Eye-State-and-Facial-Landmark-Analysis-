"""Geometric fatigue metrics: EAR, MAR, PERCLOS, blinks, and head pose."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque

import numpy as np


def _dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def eye_aspect_ratio(eye: np.ndarray) -> float:
    if eye.shape != (6, 2):
        raise ValueError(f"Expected eye array of shape (6, 2), got {eye.shape}")
    vertical = _dist(eye[1], eye[5]) + _dist(eye[2], eye[4])
    horizontal = _dist(eye[0], eye[3])
    if horizontal < 1e-6:
        return 0.0
    return vertical / (2.0 * horizontal)


def mouth_aspect_ratio(mouth: np.ndarray) -> float:
    if mouth.shape != (6, 2):
        raise ValueError(f"Expected mouth array of shape (6, 2), got {mouth.shape}")
    vertical = _dist(mouth[2], mouth[3])
    horizontal = _dist(mouth[0], mouth[1])
    if horizontal < 1e-6:
        return 0.0
    return vertical / horizontal


def mean_ear(left_eye: np.ndarray, right_eye: np.ndarray) -> float:
    return 0.5 * (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye))


def estimate_pitch_degrees(pose_points: dict, image_size: tuple) -> float:
    left = pose_points["left_eye_outer"]
    right = pose_points["right_eye_outer"]
    nose = pose_points["nose"]
    chin = pose_points["chin"]
    eye_mid = 0.5 * (left + right)
    eye_to_chin = chin[1] - eye_mid[1]
    eye_to_nose = nose[1] - eye_mid[1]
    if abs(eye_to_chin) < 1e-6:
        return 0.0
    ratio = eye_to_nose / eye_to_chin
    pitch = (ratio - 0.45) * 80.0
    return float(np.clip(pitch, -45.0, 45.0))


def perclos(closed_flags: Deque[bool] | list[bool]) -> float:
    if not closed_flags:
        return 0.0
    return float(sum(closed_flags)) / float(len(closed_flags))


@dataclass
class TemporalState:
    fps: float = 25.0
    window_seconds: float = 60.0
    ear_history: Deque[float] = field(default_factory=deque)
    closed_history: Deque[bool] = field(default_factory=deque)
    mar_history: Deque[float] = field(default_factory=deque)
    timestamps: Deque[float] = field(default_factory=deque)
    blink_durations: Deque[float] = field(default_factory=deque)
    _in_closure: bool = False
    _closure_start: float = 0.0
    frames_seen: int = 0

    @property
    def maxlen(self) -> int:
        return max(1, int(self.window_seconds * self.fps))

    def update(self, ear: float, mar: float, closed: bool, t: float) -> None:
        self.frames_seen += 1
        self.ear_history.append(ear)
        self.mar_history.append(mar)
        self.closed_history.append(closed)
        self.timestamps.append(t)
        while len(self.ear_history) > self.maxlen:
            self.ear_history.popleft()
            self.mar_history.popleft()
            self.closed_history.popleft()
            self.timestamps.popleft()
        if closed and not self._in_closure:
            self._in_closure = True
            self._closure_start = t
        elif not closed and self._in_closure:
            duration = max(0.0, t - self._closure_start)
            self.blink_durations.append(duration)
            if len(self.blink_durations) > 40:
                self.blink_durations.popleft()
            self._in_closure = False

    def current_perclos(self) -> float:
        return perclos(self.closed_history)

    def mean_blink_duration(self) -> float:
        if not self.blink_durations:
            return 0.0
        return float(np.mean(self.blink_durations))

    def long_blink_rate(self, long_s: float = 0.40) -> float:
        if not self.blink_durations:
            return 0.0
        long_n = sum(1 for d in self.blink_durations if d >= long_s)
        return long_n / len(self.blink_durations)
