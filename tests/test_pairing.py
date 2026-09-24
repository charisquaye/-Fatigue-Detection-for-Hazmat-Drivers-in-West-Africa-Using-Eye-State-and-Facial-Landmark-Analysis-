"""Unix-time pairing has no name columns and prefers alert_unix_time."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fatigue_wa.pairing import PAIRED_ALERT_HEADER, pair_labels, pair_logs


def test_pairs_by_prior_unix_time():
    alerts = [
        {"unix_time": "100.000", "state": "DROWSY", "score": "0.50", "reasons": "perclos", "escalated": "false"},
        {"unix_time": "250.000", "state": "MICROSLEEP", "score": "0.80", "reasons": "ear_closure", "escalated": "true"},
    ]
    labels = [
        {"unix_time": "104.200", "label": "checking", "last_state": "DROWSY", "score": "0.50", "ear": "0.18", "perclos": "0.32"},
        {"unix_time": "255.000", "label": "gone", "last_state": "MICROSLEEP", "score": "0.80", "ear": "0.11", "perclos": "0.41"},
    ]
    rows = pair_labels(alerts, labels, window=120.0)
    assert rows[0]["paired"] == "yes"
    assert rows[0]["alert_unix_time"] == "100.000"
    assert rows[0]["label"] == "checking"
    assert rows[1]["label"] == "gone"
    assert rows[1]["state"] == "MICROSLEEP"
    assert "name" not in rows[0] and "driver" not in rows[0]


def test_uses_explicit_alert_unix_time():
    alerts = [
        {"unix_time": "10.000", "state": "DROWSY", "score": "0.4", "reasons": "", "escalated": "false"},
        {"unix_time": "40.000", "state": "MICROSLEEP", "score": "0.9", "reasons": "", "escalated": "true"},
    ]
    labels = [{"unix_time": "41.000", "alert_unix_time": "10.000", "label": "checking", "ear": "0.2", "perclos": "0.2"}]
    rows = pair_labels(alerts, labels, window=120.0)
    assert rows[0]["alert_unix_time"] == "10.000"
    assert rows[0]["state"] == "DROWSY"


def test_pair_logs_writes_nameless_files(tmp_path):
    (tmp_path / "alerts.csv").write_text(
        "unix_time,state,score,reasons,escalated\n100.000,DROWSY,0.50,perclos,false\n",
        encoding="utf-8",
    )
    (tmp_path / "alert_labels.csv").write_text(
        "unix_time,alert_unix_time,label,last_state,score,ear,perclos\n103.000,100.000,checking,DROWSY,0.50,0.19,0.30\n",
        encoding="utf-8",
    )
    (tmp_path / "rest_stops.csv").write_text(
        "unix_time,alert_unix_time,stimulant,kss,hours_since_sleep,note\n400.000,100.000,ataya,6,8.0,\n",
        encoding="utf-8",
    )
    summary = pair_logs(tmp_path)
    text = (tmp_path / "paired_alerts.csv").read_text(encoding="utf-8")
    assert "name" not in text.lower()
    assert "checking" in text
    assert summary["labels_paired"] == 1
    assert set(text.splitlines()[0].split(",")) == set(PAIRED_ALERT_HEADER)
