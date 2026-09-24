"""Nameless Unix-time join of protocol rows onto logs/alerts.csv."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional


def _f(row: dict, key: str, default: float = 0.0) -> float:
    raw = row.get(key) or row.get(key.lower()) or row.get("unix_time") or ""
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write(path: Path, rows: list[dict], header: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in header})


def nearest_prior(events: list[dict], t: float, window: float) -> Optional[dict]:
    """Latest event with unix_time <= t and t - unix_time <= window."""
    best = None
    best_dt = window + 1.0
    for ev in events:
        et = _f(ev, "unix_time")
        if et <= 0:
            continue
        dt = t - et
        if 0 <= dt <= window and dt < best_dt:
            best = ev
            best_dt = dt
    return best


def pair_labels(alerts: list[dict], labels: list[dict], window: float = 120.0) -> list[dict]:
    out = []
    for lab in labels:
        hinted = lab.get("alert_unix_time") or ""
        try:
            hint_t = float(hinted) if hinted not in ("", "0", "0.000") else 0.0
        except ValueError:
            hint_t = 0.0
        if hint_t > 0:
            match = min(alerts, key=lambda a: abs(_f(a, "unix_time") - hint_t), default=None)
            if match is None or abs(_f(match, "unix_time") - hint_t) > window:
                match = None
        else:
            match = nearest_prior(alerts, _f(lab, "unix_time"), window)
        row = {
            "unix_time": lab.get("unix_time", ""),
            "alert_unix_time": (match or {}).get("unix_time", hinted),
            "delta_s": "",
            "label": lab.get("label", ""),
            "state": (match or {}).get("state", lab.get("last_state", "")),
            "score": (match or {}).get("score", lab.get("score", "")),
            "reasons": (match or {}).get("reasons", ""),
            "escalated": (match or {}).get("escalated", ""),
            "ear": lab.get("ear", ""),
            "perclos": lab.get("perclos", ""),
            "paired": "yes" if match else "no",
        }
        if match:
            row["delta_s"] = f"{_f(lab, 'unix_time') - _f(match, 'unix_time'):.3f}"
        out.append(row)
    return out


def pair_rest_stops(alerts: list[dict], stops: list[dict], window: float = 7200.0) -> list[dict]:
    out = []
    for stop in stops:
        match = nearest_prior(alerts, _f(stop, "unix_time"), window)
        row = {
            "unix_time": stop.get("unix_time", ""),
            "alert_unix_time": (match or {}).get("unix_time", ""),
            "delta_s": "",
            "stimulant": stop.get("stimulant", ""),
            "kss": stop.get("kss", ""),
            "hours_since_sleep": stop.get("hours_since_sleep", ""),
            "note": stop.get("note", ""),
            "prior_state": (match or {}).get("state", ""),
            "prior_score": (match or {}).get("score", ""),
            "paired": "yes" if match else "no",
        }
        if match:
            row["delta_s"] = f"{_f(stop, 'unix_time') - _f(match, 'unix_time'):.3f}"
        out.append(row)
    return out


PAIRED_ALERT_HEADER = [
    "unix_time", "alert_unix_time", "delta_s", "label", "state", "score",
    "reasons", "escalated", "ear", "perclos", "paired",
]
PAIRED_STOP_HEADER = [
    "unix_time", "alert_unix_time", "delta_s", "stimulant", "kss",
    "hours_since_sleep", "note", "prior_state", "prior_score", "paired",
]


def pair_logs(log_dir: str | Path = "logs", label_window: float = 120.0, stop_window: float = 7200.0) -> dict:
    root = Path(log_dir)
    alerts = _read(root / "alerts.csv")
    labels = _read(root / "alert_labels.csv")
    stops = _read(root / "rest_stops.csv")
    paired_labels = pair_labels(alerts, labels, label_window)
    paired_stops = pair_rest_stops(alerts, stops, stop_window)
    _write(root / "paired_alerts.csv", paired_labels, PAIRED_ALERT_HEADER)
    _write(root / "paired_rest_stops.csv", paired_stops, PAIRED_STOP_HEADER)
    return {
        "alerts": len(alerts),
        "labels": len(labels),
        "labels_paired": sum(1 for r in paired_labels if r["paired"] == "yes"),
        "rest_stops": len(stops),
        "rest_stops_paired": sum(1 for r in paired_stops if r["paired"] == "yes"),
        "paired_alerts": str(root / "paired_alerts.csv"),
        "paired_rest_stops": str(root / "paired_rest_stops.csv"),
    }
