#!/usr/bin/env python3
"""Plot nameless alert-observer time deltas from paired CSVs."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fatigue_wa.pairing import pair_logs


def _f(row: dict, key: str) -> float:
    try:
        return float(row.get(key) or 0)
    except (TypeError, ValueError):
        return 0.0


def load_paired(log_dir: Path):
    pair_logs(log_dir)
    def read(name):
        p = log_dir / name
        if not p.exists():
            return []
        with p.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    return read("paired_alerts.csv"), read("alerts.csv"), read("paired_rest_stops.csv")


def plot(log_dir: Path, out: Path) -> Path:
    import matplotlib.pyplot as plt

    paired, alerts, stops = load_paired(log_dir)
    paired = [r for r in paired if r.get("paired") == "yes" and r.get("delta_s")]
    if not paired:
        raise SystemExit(f"No paired labels in {log_dir}. Run a haul or pass --demo.")
    checking = [r for r in paired if r.get("label") == "checking"]
    gone = [r for r in paired if r.get("label") == "gone"]
    d_c = np.array([_f(r, "delta_s") for r in checking]) if checking else np.array([0.0])
    d_g = np.array([_f(r, "delta_s") for r in gone]) if gone else np.array([])
    t0 = min((_f(a, "unix_time") for a in alerts), default=0.0)
    hours = lambda t: (t - t0) / 3600.0

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.facecolor": "#111418",
        "figure.facecolor": "#0b0d10",
        "axes.edgecolor": "#3a4149",
        "axes.labelcolor": "#d7dde3",
        "xtick.color": "#b7bec6",
        "ytick.color": "#b7bec6",
        "text.color": "#e8edf2",
        "grid.color": "#2a3138",
    })
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.6))
    fig.suptitle("Alert-observer time deltas  ·  Unix-time pairing, no names", fontsize=13)

    ax = axes[0, 0]
    bins = np.linspace(0, 120, 17)
    ax.hist(d_c, bins=bins, color="#3dbe7a", alpha=0.88, label=f"checking n={len(checking)}")
    if len(d_g):
        ax.hist(d_g, bins=bins, color="#d4a017", alpha=0.75, label=f"gone n={len(gone)}")
    ax.axvline(float(np.median(d_c)), color="#9be7b8", ls="--", lw=1.2,
               label=f"median checking {np.median(d_c):.1f}s")
    ax.set_xlabel("delta_s seconds")
    ax.set_ylabel("labels")
    ax.set_title("How late the observer tagged the banner")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(True, axis="y")

    ax = axes[0, 1]
    def cdf(x):
        x = np.sort(np.asarray(x))
        return x, np.arange(1, len(x) + 1) / max(len(x), 1)
    xc, yc = cdf(d_c)
    ax.plot(xc, yc, color="#3dbe7a", lw=2.2, label="checking")
    if len(d_g):
        xg, yg = cdf(d_g)
        ax.plot(xg, yg, color="#d4a017", lw=2.0, label="gone")
    ax.axhline(0.8, color="#5b6570", ls=":", lw=1)
    ax.set_xlabel("delta_s seconds")
    ax.set_ylabel("fraction")
    ax.set_title("CDF")
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 1.02)
    ax.legend(frameon=False, fontsize=8)
    ax.grid(True)

    ax = axes[1, 0]
    for a in alerts:
        t = hours(_f(a, "unix_time"))
        col = "#e15b5b" if a.get("state") == "MICROSLEEP" else "#4aa3ff"
        ax.vlines(t, 0.0, 1.0 if a.get("state") == "MICROSLEEP" else 0.62, color=col, lw=1.6)
    for r in paired:
        ax.scatter(hours(_f(r, "unix_time")), 1.18 if r.get("label") == "checking" else 1.38,
                   s=28, c="#3dbe7a" if r.get("label") == "checking" else "#d4a017", zorder=3)
    for s in stops:
        ax.axvline(hours(_f(s, "unix_time")), color="#8b7ec8", ls="--", lw=1, alpha=0.8)
    ax.set_ylim(-0.05, 1.6)
    ax.set_xlabel("hours into haul")
    ax.set_yticks([0.31, 0.81, 1.18, 1.38])
    ax.set_yticklabels(["DROWSY", "MICROSLEEP", "checking", "gone"])
    ax.set_title("Haul timeline")
    ax.grid(True, axis="x")

    ax = axes[1, 1]
    ax.scatter(
        [hours(_f(r, "alert_unix_time")) for r in paired],
        [_f(r, "delta_s") for r in paired],
        s=[max(20, 40 + 80 * _f(r, "score")) for r in paired],
        c=["#3dbe7a" if r.get("label") == "checking" else "#d4a017" for r in paired],
        alpha=0.85,
    )
    ax.set_xlabel("hours into haul")
    ax.set_ylabel("delta_s seconds")
    ax.set_title("Lag vs haul hour")
    ax.grid(True)

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.text(
        0.5, 0.008,
        f"alerts {len(alerts)}  labels {len(paired)}  median checking {np.median(d_c):.1f}s  "
        f"p80 {np.percentile(d_c, 80):.1f}s  gone {len(gone)}  ·  no names",
        ha="center", fontsize=8, color="#9aa3ab",
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=160)
    return out


def write_demo(log_dir: Path) -> None:
    from numpy.random import default_rng
    rng = default_rng(7)
    t0 = 1_700_000_000.0
    alerts, t = [], t0 + 1200
    for _ in range(28):
        t += float(rng.integers(400, 1400))
        if t - t0 > 6.5 * 3600:
            break
        late = (t - t0) / (6.5 * 3600)
        state = "MICROSLEEP" if (late > 0.65 and rng.random() < 0.35) else "DROWSY"
        score = 0.72 + 0.15 * late if state == "MICROSLEEP" else 0.48 + 0.12 * late
        alerts.append({"unix_time": f"{t:.3f}", "state": state, "score": f"{score:.3f}",
                       "reasons": "perclos", "escalated": str(state == "MICROSLEEP").lower()})
    labels = []
    for a in alerts:
        if rng.random() < 0.12:
            continue
        late = (float(a["unix_time"]) - t0) / (6.5 * 3600)
        dt = float(np.clip(rng.lognormal(1.6 + 0.6 * late, 0.45), 0.4, 118))
        label = "gone" if rng.random() < 0.18 else "checking"
        if label == "gone":
            dt = float(np.clip(dt + 10, 1, 119))
        labels.append({"unix_time": f"{float(a['unix_time'])+dt:.3f}", "alert_unix_time": a["unix_time"],
                       "label": label, "last_state": a["state"], "score": a["score"], "ear": "0.18", "perclos": "0.30"})
    log_dir.mkdir(parents=True, exist_ok=True)
    def dump(name, rows, header):
        with (log_dir / name).open("w", newline="", encoding="utf-8") as handle:
            w = csv.DictWriter(handle, fieldnames=header)
            w.writeheader(); w.writerows(rows)
    dump("alerts.csv", alerts, ["unix_time", "state", "score", "reasons", "escalated"])
    dump("alert_labels.csv", labels, ["unix_time", "alert_unix_time", "label", "last_state", "score", "ear", "perclos"])
    dump("rest_stops.csv", [
        {"unix_time": f"{t0+7200:.3f}", "alert_unix_time": alerts[3]["unix_time"], "stimulant": "ataya",
         "kss": "5", "hours_since_sleep": "7.0", "note": ""},
    ], ["unix_time", "alert_unix_time", "stimulant", "kss", "hours_since_sleep", "note"])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--logs", default="logs")
    p.add_argument("--out", default="logs/alert_time_deltas.png")
    p.add_argument("--demo", action="store_true")
    args = p.parse_args()
    log_dir = Path(args.logs)
    if args.demo:
        write_demo(log_dir)
    print("wrote", plot(log_dir, Path(args.out)))


if __name__ == "__main__":
    main()
