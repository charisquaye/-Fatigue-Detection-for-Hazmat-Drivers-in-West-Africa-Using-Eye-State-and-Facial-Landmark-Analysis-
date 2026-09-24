#!/usr/bin/env python3
"""Nameless weekly PERCLOS sheet from logs/alerts.csv."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path


def main(path: str = "logs/alerts.csv") -> None:
    p = Path(path)
    if not p.exists():
        print("No alert log yet:", p)
        return
    states = Counter()
    rows = 0
    with p.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows += 1
            states[row.get("state") or row.get("State") or "?"] += 1
    print("WA-PERCLOS-HYS Monday sheet (no names)")
    print("events", rows)
    for k, v in states.most_common():
        print(f"  {k:16} {v}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "logs/alerts.csv")
