"""Alert policy and CSV event log for fleet review."""

from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Optional

from fatigue_wa.fusion import FatigueState, FusionResult

_QUIET = {
    FatigueState.ALERT,
    FatigueState.CALIBRATING,
    FatigueState.NO_FACE,
    FatigueState.OPTICS_DIRTY,
    FatigueState.DEGRADED,
    FatigueState.SHARED_DEVICE,
}


class AlertManager:
    def __init__(self, cooldown_seconds: float = 4.0, escalate_after: int = 3, log_path: str = "logs/alerts.csv") -> None:
        self.cooldown = cooldown_seconds
        self.escalate_after = escalate_after
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            with self.log_path.open("w", newline="", encoding="utf-8") as handle:
                csv.writer(handle).writerow(["unix_time", "state", "score", "reasons", "escalated"])
        self._last_alert = 0.0
        self._drowsy_streak = 0

    def maybe_alert(self, result: FusionResult) -> Optional[str]:
        now = time.time()
        if result.state in _QUIET:
            if result.state in (FatigueState.OPTICS_DIRTY, FatigueState.DEGRADED, FatigueState.SHARED_DEVICE):
                if now - self._last_alert >= self.cooldown:
                    self._last_alert = now
                    with self.log_path.open("a", newline="", encoding="utf-8") as handle:
                        csv.writer(handle).writerow(
                            [f"{now:.3f}", result.state.value, f"{result.score:.3f}", "|".join(result.reasons), "false"]
                        )
                    return result.reasons[0] if result.reasons else result.state.value
            self._drowsy_streak = 0
            return None
        self._drowsy_streak += 1
        if now - self._last_alert < self.cooldown:
            return None
        self._last_alert = now
        escalated = self._drowsy_streak >= self.escalate_after or result.state == FatigueState.MICROSLEEP
        if result.state == FatigueState.MICROSLEEP:
            message = "CRITICAL: possible microsleep. Pull over when safe."
        elif escalated:
            message = "ESCALATED DROWSINESS warning. Take a rest break."
        else:
            message = "Drowsiness warning."
        with self.log_path.open("a", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(
                [f"{now:.3f}", result.state.value, f"{result.score:.3f}", "|".join(result.reasons), str(escalated).lower()]
            )
        return message
