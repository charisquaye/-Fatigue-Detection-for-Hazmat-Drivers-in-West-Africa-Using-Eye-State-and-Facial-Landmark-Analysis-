"""WA-PERCLOS-HYS fusion: hysteresis close/open plus weighted evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class FatigueState(str, Enum):
    CALIBRATING = "CALIBRATING"
    NO_FACE = "NO_FACE"
    OPTICS_DIRTY = "OPTICS_DIRTY"
    DEGRADED = "DEGRADED"
    SHARED_DEVICE = "SHARED_DEVICE"
    ALERT = "ALERT"
    DROWSY = "DROWSY"
    MICROSLEEP = "MICROSLEEP"


@dataclass
class FusionResult:
    state: FatigueState
    score: float
    evidence: dict
    reasons: list
    closed: bool = False


class HysteresisGate:
    """Schmitt trigger on smoothed EAR. Both-eye agreement optional."""

    def __init__(self, close_thr: float, open_thr: float) -> None:
        self.close_thr = float(close_thr)
        self.open_thr = float(open_thr)
        self.closed = False

    def set_thresholds(self, close_thr: float, open_thr: float) -> None:
        self.close_thr = float(close_thr)
        self.open_thr = float(max(open_thr, close_thr + 1e-4))

    def step(self, ear: float) -> bool:
        if not self.closed and ear < self.close_thr:
            self.closed = True
        elif self.closed and ear > self.open_thr:
            self.closed = False
        return self.closed


class EvidenceFusion:
    def __init__(self, cfg: dict[str, Any]) -> None:
        fcfg = cfg["fusion"]
        mcfg = cfg["metrics"]
        self.weights = fcfg["weights"]
        self.drowsy_thr = float(fcfg["drowsy_score_threshold"])
        self.severe_thr = float(fcfg["severe_score_threshold"])
        self.trunk_drowsy = float(fcfg.get("trunk_road_drowsy_threshold", self.drowsy_thr))
        self.operating_point = str(cfg.get("west_africa", {}).get("operating_point", "depot_road"))
        self.perclos_thr = float(mcfg["perclos_alert_threshold"])
        self.consec_closed = int(mcfg["consecutive_closed_frames"])
        self.yawn_thr = float(mcfg["mar_yawn_threshold"])
        self.yawn_frames = int(mcfg["yawn_consecutive_frames"])
        self.nod_deg = float(mcfg["nod_pitch_degrees"])
        gap = float(mcfg.get("ear_hysteresis_gap", 0.03))
        close0 = float(mcfg["ear_close_threshold"])
        self.gate = HysteresisGate(close0, close0 + gap)
        self.both_eyes = bool(mcfg.get("both_eyes_required", True))
        self.monocular_fallback = bool(mcfg.get("monocular_fallback", True))
        self._closed_run = 0
        self._yawn_run = 0
        self.monocular = False

    def set_calibrated_thresholds(self, close_thr: float, open_thr: float) -> None:
        self.gate.set_thresholds(close_thr, open_thr)

    def _eye_closed(self, left_ear: Optional[float], right_ear: Optional[float], mean_ear: float) -> bool:
        if left_ear is None or right_ear is None:
            return self.gate.step(mean_ear)
        left_dead = left_ear < 0.08 or abs(left_ear - right_ear) > 0.18 and left_ear < 0.12
        right_dead = right_ear < 0.08 or abs(left_ear - right_ear) > 0.18 and right_ear < 0.12
        if self.monocular_fallback and (left_dead ^ right_dead):
            self.monocular = True
            live = right_ear if left_dead else left_ear
            return self.gate.step(live)
        self.monocular = False
        if not self.gate.closed:
            if left_ear < self.gate.close_thr and right_ear < self.gate.close_thr:
                self.gate.closed = True
        else:
            if mean_ear > self.gate.open_thr:
                self.gate.closed = False
        return self.gate.closed

    def update_runs(self, closed: bool, mar: float, talking: bool) -> None:
        self._closed_run = self._closed_run + 1 if closed else 0
        if talking:
            self._yawn_run = 0
        else:
            self._yawn_run = self._yawn_run + 1 if mar >= self.yawn_thr else 0

    def infer(
        self,
        *,
        calibrating: bool,
        face_present: bool,
        perclos_value: float,
        closed: bool,
        long_blink_rate: float,
        mar: float,
        pitch: float,
        optics_dirty: bool = False,
        glasses_after_dusk: bool = False,
        shared_device: bool = False,
        talking: bool = False,
        rough_road: bool = False,
    ) -> FusionResult:
        if calibrating:
            return FusionResult(FatigueState.CALIBRATING, 0.0, {}, ["Collecting open-eye baseline"])
        if shared_device:
            return FusionResult(FatigueState.SHARED_DEVICE, 0.0, {}, ["Face hash != gate face"])
        if not face_present:
            return FusionResult(FatigueState.NO_FACE, 0.0, {}, ["Face not visible"])
        if optics_dirty:
            return FusionResult(FatigueState.OPTICS_DIRTY, 0.0, {}, ["Eye-crop sharpness below floor"])
        if glasses_after_dusk:
            return FusionResult(FatigueState.DEGRADED, 0.0, {}, ["Glasses on after sunset"])
        self.update_runs(closed, mar, talking)
        e_perclos = _clamp01(perclos_value / max(self.perclos_thr, 1e-6))
        e_close = 1.0 if self._closed_run >= self.consec_closed else self._closed_run / max(self.consec_closed, 1)
        e_blink = _clamp01(long_blink_rate / 0.35)
        e_yawn = 0.0 if talking else (
            1.0 if self._yawn_run >= self.yawn_frames else self._yawn_run / max(self.yawn_frames, 1)
        )
        e_nod = 0.0 if rough_road else _clamp01(max(0.0, pitch) / self.nod_deg)
        evidence = {
            "perclos": e_perclos,
            "ear_closure": e_close,
            "long_blink": e_blink,
            "yawn": e_yawn,
            "head_nod": e_nod,
        }
        score = sum(self.weights[k] * evidence[k] for k in self.weights)
        reasons = [k for k, v in evidence.items() if v >= 0.6]
        drowsy_cut = self.trunk_drowsy if self.operating_point == "trunk_road" else self.drowsy_thr
        if self._closed_run >= self.consec_closed:
            state = FatigueState.MICROSLEEP
            reasons.append("sustained_eye_closure")
        elif score >= self.severe_thr:
            state = FatigueState.MICROSLEEP
        elif score >= drowsy_cut:
            state = FatigueState.DROWSY
        else:
            state = FatigueState.ALERT
        if self.monocular:
            reasons.append("monocular_fallback")
        return FusionResult(state=state, score=float(score), evidence=evidence, reasons=reasons, closed=closed)


def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else float(x)
