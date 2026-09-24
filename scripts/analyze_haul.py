#!/usr/bin/env python3
"""Haul-hour rostering analysis. Gold set = paired=yes AND label=checking."""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fatigue_wa.pairing import pair_logs


def _f(row, key):
    try:
        return float(row.get(key) or 0)
    except (TypeError, ValueError):
        return 0.0


def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def gone_report(labels):
    n = len(labels)
    checking = sum(1 for r in labels if r.get("label") == "checking" and r.get("paired") == "yes")
    gone = sum(1 for r in labels if r.get("label") == "gone")
    return {"n": n, "checking": checking, "gone": gone, "gone_rate": gone / n if n else 0.0}


def gold_rows(labels):
    return [r for r in labels if r.get("paired") == "yes" and r.get("label") == "checking"]


def roc_point(pos, neg, thr):
    pos = np.asarray(pos); neg = np.asarray(neg)
    if len(pos) == 0 or len(neg) == 0:
        return float("nan"), float("nan")
    return float((pos >= thr).mean()), float((neg >= thr).mean())


def p95_by_hour(samples):
    buckets = defaultdict(list)
    if not samples:
        return []
    t0 = min(s[0] for s in samples)
    for t, p, stim in samples:
        buckets[(int((t - t0) // 3600), stim)].append(p)
    rows = []
    for (h, stim), vals in sorted(buckets.items()):
        arr = np.asarray(vals)
        rows.append({"hour": h, "stimulant": stim, "p95": float(np.percentile(arr, 95)),
                     "median": float(np.median(arr)), "n": int(arr.size)})
    return rows


def startle_blind(conf_series, t0, window=30.0, floor=0.45):
    """conf_series: list of (unix_time, mesh_confidence)."""
    w = [(t, c) for t, c in conf_series if t0 <= t <= t0 + window]
    if not w:
        return float("nan")
    return float(np.mean([c < floor for _, c in w]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--logs", default="logs")
    args = p.parse_args()
    root = Path(args.logs)
    pair_logs(root)
    labels = read_csv(root / "paired_alerts.csv")
    stops = read_csv(root / "paired_rest_stops.csv")
    g = gone_report(labels)
    gold = gold_rows(labels)
    print("GOLD RULE: paired=yes AND label=checking")
    print(f"labels {g['n']}  checking {g['checking']}  gone {g['gone']}  gone_rate {g['gone_rate']:.1%}")
    pos = [_f(r, "score") for r in gold if r.get("state") in ("DROWSY", "MICROSLEEP")]
    neg = [_f(r, "score") for r in gold if r.get("state") == "ALERT"]
    for name, thr in (("depot", 0.45), ("trunk", 0.55)):
        tpr, fpr = roc_point(pos, neg, thr)
        print(f"{name} cut {thr:.2f}  TPR {tpr:.3f}  FPR {fpr:.3f}  (gold windows only)")
    stim = stops[0]["stimulant"] if stops else "none"
    print("rest-stop stimulant", stim)
    print("Run plot_deltas.py for observer lag. PERCLOS p95 needs a per-frame log; see thesis protocol pack.")


if __name__ == "__main__":
    main()
