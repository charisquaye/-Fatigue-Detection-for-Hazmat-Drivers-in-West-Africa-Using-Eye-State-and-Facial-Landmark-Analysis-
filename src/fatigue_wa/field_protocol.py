"""Field protocol logs. No names. After-alert labels, rest stops, near misses, 1 Hz PERCLOS."""

from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Optional

STIMULANTS = ("none", "ataya", "energy_drink", "tramadol_coffee", "cola_nut", "other")


def _ensure(path: Path, header: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(header)


class FieldProtocol:
    def __init__(self, log_dir: str = "logs") -> None:
        root = Path(log_dir)
        self.alert_labels = root / "alert_labels.csv"
        self.rest_stops = root / "rest_stops.csv"
        self.near_misses = root / "near_misses.csv"
        self.perclos_1hz = root / "perclos_1hz.csv"
        _ensure(self.alert_labels, ["unix_time", "alert_unix_time", "label", "last_state", "score", "ear", "perclos"])
        _ensure(self.rest_stops, ["unix_time", "alert_unix_time", "stimulant", "kss", "hours_since_sleep", "note"])
        _ensure(self.near_misses, ["unix_time", "note"])
        _ensure(self.perclos_1hz, ["unix_time", "perclos", "ear", "state", "face", "mesh_conf"])
        self.last_state = "ALERT"
        self.last_score = 0.0
        self.last_ear = 0.0
        self.last_perclos = 0.0
        self.last_alert_unix = 0.0
        self.pending_alert = False
        self._last_hz = 0.0
        self.status = "c=checking  g=gone  s=stimulant  1-9=KSS  n=near-miss"

    def note_frame(self, state: str, score: float, ear: float, perclos: float, alert: Optional[str],
                   face: bool = True, mesh_conf: float = 1.0) -> None:
        now = time.time()
        self.last_state = state
        self.last_score = score
        self.last_ear = ear
        self.last_perclos = perclos
        if now - self._last_hz >= 1.0:
            self._last_hz = now
            with self.perclos_1hz.open("a", newline="", encoding="utf-8") as handle:
                csv.writer(handle).writerow(
                    [f"{now:.3f}", f"{perclos:.4f}", f"{ear:.4f}", state,
                     "1" if face else "0", f"{mesh_conf:.3f}"]
                )
        if alert and state in ("DROWSY", "MICROSLEEP"):
            self.last_alert_unix = now
            self.pending_alert = True
            self.status = "Label last alert: c=checking  g=gone"

    def label_alert(self, label: str) -> str:
        if label not in ("checking", "gone"):
            return "unknown label"
        now = time.time()
        with self.alert_labels.open("a", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(
                [f"{now:.3f}", f"{self.last_alert_unix:.3f}", label, self.last_state,
                 f"{self.last_score:.3f}", f"{self.last_ear:.3f}", f"{self.last_perclos:.3f}"]
            )
        self.pending_alert = False
        self.status = f"logged {label}"
        return self.status

    def rest_stop(self, stimulant: str = "none", kss: int = 0, hours_since_sleep: float = -1.0, note: str = "") -> str:
        if stimulant not in STIMULANTS:
            stimulant = "other"
        kss = int(max(0, min(9, kss)))
        now = time.time()
        with self.rest_stops.open("a", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(
                [f"{now:.3f}", f"{self.last_alert_unix:.3f}", stimulant, str(kss),
                 f"{hours_since_sleep:.1f}", note]
            )
        self.status = f"rest-stop {stimulant} KSS={kss}"
        return self.status

    def near_miss(self, note: str = "") -> str:
        now = time.time()
        with self.near_misses.open("a", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow([f"{now:.3f}", note])
        self.status = "near-miss marked"
        return self.status
