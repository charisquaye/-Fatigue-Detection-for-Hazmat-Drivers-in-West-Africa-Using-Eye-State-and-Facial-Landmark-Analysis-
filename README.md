# Fatigue Detection for Hazmat Drivers in West Africa

Real-time, camera-based fatigue monitoring for hazardous-materials (HAZMAT) tanker and heavy-goods drivers operating on West African freight corridors.

The system estimates facial landmarks with MediaPipe Face Mesh, computes Eye Aspect Ratio (EAR), Mouth Aspect Ratio (MAR), rolling PERCLOS, blink duration, and a coarse head-pitch cue, then fuses those signals into an interpretable alert state:

`CALIBRATING → ALERT → DROWSY → MICROSLEEP`

It is designed for a dashboard smartphone or USB camera inside a petroleum tanker cabin, with an 8-second open-eye calibration that adapts the EAR closure threshold to the driver and to night-cabin lighting.

This repository accompanies the thesis:

> Quaye, C. (2026). *Fatigue detection for HAZMAT drivers in West Africa using eye-state and facial landmark analysis.*

## Why this setting is different

Generic drowsiness demos assume well-lit passenger cars and a single global EAR threshold. West African HAZMAT operations add:

- long night hauls on corridors such as Tema–Kumasi, Lagos–Ibadan, and Abidjan–Yamoussoukro
- low cabin luminance after dusk and high dynamic range from oncoming headlights
- heat-driven sunglasses and peaked caps
- trip-based pay that suppresses rest
- consequence severity unique to fuel and chemical tankers

The detector therefore uses **personalised thresholds**, **multi-cue fusion** rather than a single blink tripwire, and an **offline event log** suitable for fleet review where mobile connectivity is intermittent.

## Repository layout

```
configs/default.yaml          # thresholds, fusion weights, WA profile
src/fatigue_wa/               # library
  landmarks.py                # MediaPipe index mapping
  metrics.py                  # EAR, MAR, PERCLOS, blinks, pitch
  adaptive.py                 # driver + lighting calibration
  fusion.py                   # weighted evidence + state machine
  alerts.py                   # cooldown, escalation, CSV log
  pipeline.py                 # per-frame orchestration
scripts/run_detector.py       # webcam / video entry point
scripts/evaluate.py           # synthetic physiological evaluation
tests/test_metrics.py
```

## Installation

Python 3.10+ recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
```

MediaPipe and OpenCV are required only for the live camera app. The metric, fusion, and evaluation modules run without a camera.

## Live detection

```bash
export PYTHONPATH=src
python scripts/run_detector.py --camera 0
python scripts/run_detector.py --video path/to/dashcam.mp4
```

Look at the camera with eyes open for about eight seconds while the HUD reads `CALIBRATING`. Press `q` to quit. Alerts are appended to `logs/alerts.csv`.

## Reproducing the thesis evaluation

```bash
export PYTHONPATH=src
python scripts/evaluate.py
pytest tests/test_metrics.py -q
```

The evaluation protocol generates 120 controlled 45-second sessions (40 alert, 40 drowsy, 40 microsleep) whose EAR, MAR, and pitch trajectories sit in published physiological ranges. It is a reproducibility check of the fusion logic, **not** a substitute for on-road tanker trials.

## Safety and ethics

This is a research prototype. It must not be the sole safeguard for a loaded tanker. False negatives remain possible with sunglasses, extreme pose, or total face occlusion. Any field deployment requires informed consent, a data-minimisation policy (landmarks and scores, not raw video, wherever possible), and integration with hours-of-service rules rather than punitive surveillance.

## Citation

```
Quaye, C. (2026). Fatigue detection for HAZMAT drivers in West Africa
using eye-state and facial landmark analysis [Thesis software].
https://github.com/charisquaye/-Fatigue-Detection-for-Hazmat-Drivers-in-West-Africa-Using-Eye-State-and-Facial-Landmark-Analysis-
```

## Licence

MIT. See `LICENSE`.
