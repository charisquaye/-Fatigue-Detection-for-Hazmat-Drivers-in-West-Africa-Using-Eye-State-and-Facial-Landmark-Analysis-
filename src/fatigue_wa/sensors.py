"""Optional phone IMU and mic gates. Safe no-ops when hardware is absent."""

from __future__ import annotations

from collections import deque
from typing import Optional


class ImuGate:
    def __init__(self, rough_rms: float = 2.4) -> None:
        self.rough_rms = rough_rms
        self._buf: deque = deque(maxlen=25)

    def observe(self, accel_xyz: Optional[tuple[float, float, float]]) -> None:
        if accel_xyz is None:
            return
        ax, ay, az = accel_xyz
        self._buf.append((ax * ax + ay * ay + az * az) ** 0.5)

    def rough_road(self) -> bool:
        if len(self._buf) < 8:
            return False
        mean = sum(self._buf) / len(self._buf)
        var = sum((x - mean) ** 2 for x in self._buf) / len(self._buf)
        return var ** 0.5 >= self.rough_rms


class VoiceGate:
    def __init__(self, energy_threshold: float = 0.035) -> None:
        self.energy_threshold = energy_threshold

    def talking(self, rms: Optional[float]) -> bool:
        if rms is None:
            return False
        return float(rms) >= self.energy_threshold
