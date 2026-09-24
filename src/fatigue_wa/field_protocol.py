"""Field protocol logs. No names. After-alert labels and rest-stop items."""

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
        _ensure(self.alert_labels, ["unix_time", "label", "last_state", "score", "ear", "perclos"])
        _ensure(self.rest_stops, ["unix_time", "stimulant", "kss", "hours_since_sleep", "note"])
        self.last_state = "ALERT"
        self.last_score = 0.0
        self.last_ear = 0.0
        self.last_perclos = 0.0
        self.pending_alert = False
        self.status = "c=checking  g=gone  s=stimulant  1-5=KSS"

    def note_frame(self, state: str, score: float, ear: float, perclos: float, alert: Optional[str]) -> None:
        self.last_state = state
        self.last_score = score
        self.last_ear = ear
        self.last_perclos = perclos
        if alert and state in ("DROWSY", "MICROSLEEP"):
            self.pending_alert = True
            self.status = "Label last alert: c=checking  g=gone"

    def label_alert(self, label: str) -> str:
        if label not in ("checking", "gone"):
            return "unknown label"
        with self.alert_labels.open("a", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(
                [
                    f"{time.time():.3f}",
                    label,
                    self.last_state,
                    f"{self.last_score:.3f}",
                    f"{self.last_ear:.3f}",
                    f"{self.last_perclos:.3f}",
                ]
            )
        self.pending_alert = False
        self.status = f"logged {label}"
        return self.status

    def rest_stop(self, stimulant: str = "none", kss: int = 0, hours_since_sleep: float = -1.0, note: str = "") -> str:
        if stimulant not in STIMULANTS:
            stimulant = "other"
        kss = int(max(0, min(9, kss)))
        with self.rest_stops.open("a", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(
                [f"{time.time():.3f}", stimulant, str(kss), f"{hours_since_sleep:.1f}", note]
            )
        self.status = f"rest-stop {stimulant} KSS={kss}"
        return self.status
