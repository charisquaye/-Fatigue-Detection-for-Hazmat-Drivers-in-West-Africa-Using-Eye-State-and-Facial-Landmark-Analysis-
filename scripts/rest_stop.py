#!/usr/bin/env python3
"""Confidential rest-stop item. Run at the boom or a lay-by, camera off."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fatigue_wa.field_protocol import STIMULANTS, FieldProtocol


def main() -> None:
    parser = argparse.ArgumentParser(description="Log a rest-stop stimulant / KSS item")
    parser.add_argument("--stimulant", choices=STIMULANTS, default="none")
    parser.add_argument("--kss", type=int, default=0, help="Karolinska 1-9, 0=skipped")
    parser.add_argument("--hours-since-sleep", type=float, default=-1.0)
    parser.add_argument("--note", default="")
    parser.add_argument("--log-dir", default="logs")
    args = parser.parse_args()
    proto = FieldProtocol(args.log_dir)
    print(proto.rest_stop(args.stimulant, args.kss, args.hours_since_sleep, args.note))
    print("wrote", proto.rest_stops)


if __name__ == "__main__":
    main()
