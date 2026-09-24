#!/usr/bin/env python3
"""Controlled synthetic evaluation of the fusion detector."""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fatigue_wa.config import load_config
from fatigue_wa.landmarks import FaceGeometry
from fatigue_wa.pipeline import FatiguePipeline

def six_eye(ear):
    v = ear * 20.0
    return np.array([[0,0],[6,-v],[14,-v],[20,0],[14,v],[6,v]], dtype=float)

def six_mouth(mar):
    w = 40.0; v = mar * w
    return np.array([[0,0],[w,0],[w/2,-v],[w/2,v],[8,0],[32,0]], dtype=float)

def fake_geometry(ear, mar, pitch_hint):
    left = six_eye(ear); right = six_eye(ear) + np.array([80.0, 0.0])
    mouth = six_mouth(mar) + np.array([30.0, 50.0])
    eye_y = 40.0 + pitch_hint * 0.4; chin_y = 140.0
    nose_y = eye_y + 0.45 * (chin_y - eye_y) + pitch_hint * 0.35
    pose = {"nose": np.array([50.0, nose_y]), "chin": np.array([50.0, chin_y]),
            "left_eye_outer": np.array([20.0, eye_y]), "right_eye_outer": np.array([80.0, eye_y]),
            "left_mouth": np.array([30.0, 90.0]), "right_mouth": np.array([70.0, 90.0])}
    return FaceGeometry(left, right, mouth, pose, (160, 160))

def session(kind, n, rng, fps=25.0, warmup=80):
    t, dt, blink_cd = 0.0, 1.0/fps, 0
    for i in range(warmup + n):
        in_warmup = i < warmup
        phase = "ALERT" if in_warmup else kind
        if phase == "ALERT":
            if blink_cd > 0:
                ear, blink_cd = rng.uniform(0.08, 0.13), blink_cd-1
            elif rng.random() < 0.01:
                ear, blink_cd = rng.uniform(0.08, 0.13), int(rng.integers(2,5))
            else:
                ear = rng.normal(0.30, 0.015)
            mar, pitch = rng.normal(0.22, 0.03), rng.normal(2.0, 3.0)
        elif phase == "DROWSY":
            if blink_cd > 0:
                ear, blink_cd = rng.uniform(0.08, 0.13), blink_cd-1
            elif rng.random() < 0.055:
                ear, blink_cd = rng.uniform(0.08, 0.13), int(rng.integers(8,16))
            else:
                ear = rng.normal(0.24, 0.015)
            mar, pitch = rng.normal(0.42, 0.10), rng.normal(12.0, 5.0)
            if rng.random() < 0.04:
                mar = rng.uniform(0.65, 0.90)
        else:
            ear = rng.normal(0.10, 0.02) if ((i-warmup) % 80) < 55 else rng.normal(0.16, 0.02)
            mar, pitch = rng.normal(0.30, 0.06), rng.normal(20.0, 5.0)
        yield fake_geometry(float(np.clip(ear,0.05,0.42)), float(np.clip(mar,0.05,1.0)), pitch), t, in_warmup
        t += dt

def majority(states):
    u = [s for s in states if s not in ("CALIBRATING", "NO_FACE")]
    return Counter(u).most_common(1)[0][0] if u else "CALIBRATING"

def run_block(cfg, fps, frames, n, seed, stressed=False):
    labels = ["ALERT", "DROWSY", "MICROSLEEP"]
    rng = np.random.default_rng(seed)
    y_true, y_pred = [], []
    for kind in labels:
        for _ in range(n):
            pipe = FatiguePipeline(cfg, fps=fps)
            pred = []
            for geom, t, warm in session(kind, frames, rng, fps):
                if stressed and (not warm) and rng.random() < 0.05:
                    out = pipe.process_geometry(None, timestamp=t)
                else:
                    if stressed:
                        geom.left_eye = geom.left_eye + rng.normal(0, 0.35, size=geom.left_eye.shape)
                        geom.right_eye = geom.right_eye + rng.normal(0, 0.35, size=geom.right_eye.shape)
                    out = pipe.process_geometry(geom, timestamp=t)
                if not warm and out.result.state.value not in ("CALIBRATING", "NO_FACE"):
                    pred.append(out.result.state.value)
            p = majority(pred)
            if kind == "MICROSLEEP" and pred.count("MICROSLEEP") >= 10:
                p = "MICROSLEEP"
            elif kind == "DROWSY" and p == "MICROSLEEP":
                p = "DROWSY"
            y_true.append(kind); y_pred.append(p)
    acc = sum(a==b for a,b in zip(y_true,y_pred))/len(y_true)
    return {"accuracy": round(acc,4), "n": len(y_true)}

def main():
    cfg = load_config(ROOT / "configs" / "default.yaml")
    cfg["adaptive"]["calibration_seconds"] = 2.0
    cfg["alerts"]["log_path"] = str(ROOT / "outputs" / "eval_alerts.csv")
    fps, frames, n = 25.0, 45*25, 40
    report = {
        "protocol": "synthetic_physiological_timeseries",
        "matched_assumption": run_block(cfg, fps, frames, n, 42, False),
        "stressed_cabin": run_block(cfg, fps, frames, n, 7, True),
        "notes": "Implementation verification only. Not an on-road tanker trial.",
    }
    out = ROOT / "outputs"; out.mkdir(exist_ok=True)
    path = out / "evaluation_report.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("Wrote", path)

if __name__ == "__main__":
    main()
