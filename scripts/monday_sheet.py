#!/usr/bin/env python3
"""Nameless Monday sheet: count alerts and pair protocol CSVs by Unix time."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fatigue_wa.pairing import pair_logs, _read


def main(log_dir: str = "logs") -> None:
    root = Path(log_dir)
    summary = pair_logs(root)
    alerts = _read(root / "alerts.csv")
    states = Counter(r.get("state") or "?" for r in alerts)
    labels = _read(root / "paired_alerts.csv")
    label_counts = Counter(r.get("label") or "?" for r in labels)
    usable = sum(1 for r in labels if r.get("label") == "checking" and r.get("paired") == "yes")
    gone = sum(1 for r in labels if r.get("label") == "gone")
    print("WA-PERCLOS-HYS Monday sheet (no names)")
    print("alerts", summary["alerts"])
    for k, v in states.most_common():
        print(f"  {k:16} {v}")
    print("labels", summary["labels"], "paired", summary["labels_paired"])
    for k, v in label_counts.most_common():
        print(f"  {k:16} {v}")
    print("gold checking+paired", usable, "discard gone", gone)
    print("rest stops", summary["rest_stops"], "paired", summary["rest_stops_paired"])
    print("wrote", summary["paired_alerts"])
    print("wrote", summary["paired_rest_stops"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "logs")
