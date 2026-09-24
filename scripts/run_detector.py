#!/usr/bin/env python3
"""Real-time webcam detector for HAZMAT-cabin fatigue monitoring."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fatigue_wa.config import load_config
from fatigue_wa.field_protocol import STIMULANTS, FieldProtocol
from fatigue_wa.pipeline import FatiguePipeline


def parse_args():
    parser = argparse.ArgumentParser(description="WA-HAZMAT fatigue detector")
    parser.add_argument("--config", default=None)
    parser.add_argument("--camera", type=int, default=None)
    parser.add_argument("--video", default=None)
    parser.add_argument("--no-window", action="store_true")
    return parser.parse_args()


def draw_hud(frame, output, proto: FieldProtocol) -> None:
    state = output.result.state.value
    colour = {
        "ALERT": (40, 180, 40),
        "DROWSY": (0, 165, 255),
        "MICROSLEEP": (0, 0, 255),
        "CALIBRATING": (200, 200, 200),
        "NO_FACE": (128, 128, 128),
        "OPTICS_DIRTY": (0, 140, 255),
        "DEGRADED": (180, 180, 0),
        "SHARED_DEVICE": (200, 100, 200),
    }.get(state, (255, 255, 255))
    cv2.rectangle(frame, (8, 8), (620, 150), (0, 0, 0), -1)
    cv2.putText(frame, f"STATE: {state}", (18, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.7, colour, 2)
    cv2.putText(
        frame,
        f"EAR {output.ear:.3f}  MAR {output.mar:.3f}  PERCLOS {output.perclos:.2f}",
        (18, 64), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (230, 230, 230), 1,
    )
    cv2.putText(
        frame,
        f"closed={int(output.closed)}  drift={output.ear_open_drift:+.3f}",
        (18, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1,
    )
    hint = proto.status
    if output.alert:
        hint = output.alert[:54] + "  [c/g]"
    cv2.putText(frame, hint[:70], (18, 114), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 200, 255) if proto.pending_alert else (200, 200, 200), 1)
    cv2.putText(frame, "c checking  g gone  s stimulant  1-9 KSS  q quit", (18, 138), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (160, 160, 160), 1)


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    source = args.video if args.video else (args.camera if args.camera is not None else int(cfg["camera"]["index"]))
    cap = cv2.VideoCapture(source)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(cfg["camera"]["width"]))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(cfg["camera"]["height"]))
    if not cap.isOpened():
        raise SystemExit(f"Could not open video source: {source}")
    import mediapipe as mp
    fps = cap.get(cv2.CAP_PROP_FPS) or cfg["camera"]["fps_hint"]
    pipeline = FatiguePipeline(cfg, fps=float(fps) if fps and fps > 1 else 25.0)
    proto = FieldProtocol("logs")
    stim_i = 0
    mesh = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=int(cfg["landmarks"]["max_num_faces"]),
        refine_landmarks=True,
        min_detection_confidence=float(cfg["landmarks"]["min_detection_confidence"]),
        min_tracking_confidence=float(cfg["landmarks"]["min_tracking_confidence"]),
    )
    print("WA-PERCLOS-HYS")
    print("  c = I was checking   g = I was gone")
    print("  s = cycle stimulant and write rest-stop row")
    print("  1-9 = Karolinska on the last rest-stop write")
    print("  q = quit")
    pending_kss = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = mesh.process(rgb)
            h, w = frame.shape[:2]
            face = res.multi_face_landmarks[0] if res.multi_face_landmarks else None
            output = pipeline.process_mediapipe(face, w, h, frame_bgr=frame)
            proto.note_frame(output.result.state.value, output.result.score, output.ear, output.perclos, output.alert)
            if args.no_window:
                if output.alert:
                    print(output.alert)
                continue
            draw_hud(frame, output, proto)
            cv2.imshow("WA-HAZMAT Fatigue Detector", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("c"):
                print(proto.label_alert("checking"))
            elif key == ord("g"):
                print(proto.label_alert("gone"))
            elif key == ord("s"):
                stim_i = (stim_i + 1) % len(STIMULANTS)
                print(proto.rest_stop(STIMULANTS[stim_i], pending_kss))
            elif ord("1") <= key <= ord("9"):
                pending_kss = key - ord("0")
                print(proto.rest_stop(STIMULANTS[stim_i], pending_kss))
    finally:
        mesh.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
