"""Multi-cue evidence fusion for fatigue state classification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FatigueState(str, Enum):
    CALIBRATING = "CALIBRATING"
    NO_FACE = "NO_FACE"
    ALERT = "ALERT"
    DROWSY = "DROWSY"
    MICROSLEEP = "MICROSLEEP"


@dataclass
class FusionResult:
    state: FatigueState
    score: float
    evidence: dict
    reasons: list


class EvidenceFusion:
    def __init__(self, cfg: dict[str, Any]) -> None:
        fcfg = cfg["fusion"]
        mcfg = cfg["metrics"]
        self.weights = fcfg["weights"]
        self.drowsy_thr = float(fcfg["drowsy_score_threshold"])
        self.severe_thr = float(fcfg["severe_score_threshold"])
        self.perclos_thr = float(mcfg["perclos_alert_threshold"])
        self.consec_closed = int(mcfg["consecutive_closed_frames"])
        self.yawn_thr = float(mcfg["mar_yawn_threshold"])
        self.yawn_frames = int(mcfg["yawn_consecutive_frames"])
        self.nod_deg = float(mcfg["nod_pitch_degrees"])
        self._closed_run = 0
        self._yawn_run = 0

    def update_runs(self, closed: bool, mar: float) -> None:
        self._closed_run = self._closed_run + 1 if closed else 0
        self._yawn_run = self._yawn_run + 1 if mar >= self.yawn_thr else 0

    def infer(self, *, calibrating: bool, face_present: bool, perclos_value: float,
              closed: bool, long_blink_rate: float, mar: float, pitch: float) -> FusionResult:
        if calibrating:
            return FusionResult(FatigueState.CALIBRATING, 0.0, {}, ["Collecting open-eye baseline"])
        if not face_present:
            return FusionResult(FatigueState.NO_FACE, 0.0, {}, ["Face not visible"])
        self.update_runs(closed, mar)
        e_perclos = _clamp01(perclos_value / max(self.perclos_thr, 1e-6))
        e_close = 1.0 if self._closed_run >= self.consec_closed else self._closed_run / max(self.consec_closed, 1)
        e_blink = _clamp01(long_blink_rate / 0.35)
        e_yawn = 1.0 if self._yawn_run >= self.yawn_frames else self._yawn_run / max(self.yawn_frames, 1)
        e_nod = _clamp01(max(0.0, pitch) / self.nod_deg)
        evidence = {
            "perclos": e_perclos,
            "ear_closure": e_close,
            "long_blink": e_blink,
            "yawn": e_yawn,
            "head_nod": e_nod,
        }
        score = sum(self.weights[k] * evidence[k] for k in self.weights)
        reasons = [k for k, v in evidence.items() if v >= 0.6]
        if self._closed_run >= self.consec_closed:
            state = FatigueState.MICROSLEEP
            reasons.append("sustained_eye_closure")
        elif score >= self.severe_thr:
            state = FatigueState.MICROSLEEP
        elif score >= self.drowsy_thr:
            state = FatigueState.DROWSY
        else:
            state = FatigueState.ALERT
        return FusionResult(state=state, score=float(score), evidence=evidence, reasons=reasons)


def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else float(x)
