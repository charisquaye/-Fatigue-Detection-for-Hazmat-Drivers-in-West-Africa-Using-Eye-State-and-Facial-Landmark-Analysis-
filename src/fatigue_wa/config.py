"""Configuration loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML configuration, falling back to packaged defaults."""
    if path is None:
        candidates = [
            Path("configs/default.yaml"),
            Path(__file__).resolve().parents[2] / "configs" / "default.yaml",
        ]
        for candidate in candidates:
            if candidate.exists():
                path = candidate
                break
        else:
            raise FileNotFoundError("Could not locate configs/default.yaml")
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)
