"""West Africa HAZMAT driver fatigue detection package."""

__version__ = "1.0.0"
__author__ = "Charis Quaye"

from fatigue_wa.pipeline import FatiguePipeline
from fatigue_wa.metrics import eye_aspect_ratio, mouth_aspect_ratio, perclos

__all__ = [
    "FatiguePipeline",
    "eye_aspect_ratio",
    "mouth_aspect_ratio",
    "perclos",
    "__version__",
]
