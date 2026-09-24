# Fatigue Detection for Hazmat Drivers in West Africa

WA-PERCLOS-HYS: MediaPipe Face Mesh, EMA-smoothed EAR, two-threshold hysteresis, personal P60-median calibration, PERCLOS, PLCDB, and multi-cue fusion for petroleum tanker cabins.

States: `CALIBRATING`, `ALERT`, `DROWSY`, `MICROSLEEP`, `NO_FACE`, `OPTICS_DIRTY`, `DEGRADED` (glasses after dusk), `SHARED_DEVICE`.

Thesis: Quaye, C. (2026). *Fatigue detection for HAZMAT drivers in West Africa using eye-state and facial landmark analysis.*

## Chapter 4 rule (now in the live code)

- EMA alpha 0.4 on EAR
- Close when smoothed EAR < theta_close; stay closed until EAR > theta_open
- theta_close = clip(0.68 * s * EAR_open, 0.16, 0.26) from an 8 s P60-median gate
- theta_open = min(theta_close + 0.03, EAR_open - 0.02)
- Night scale s = 0.92 when face luma < 70
- Both-eye agreement with monocular fallback
- 0.8 s sustained closure -> MICROSLEEP
- Mid-haul open-eye re-estimate clamped +/-0.03 of the gate value
- Dirty-optic and after-dusk glasses flags
- Face-hash shared-phone detect
- Optional IMU-gated nod and mic-gated yawn

## Install

```bash
git pull
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
pytest tests -q
python scripts/run_detector.py --camera 0
python scripts/monday_sheet.py
```

## HUD line: closed= and drift=

Status, not a crash. `closed=1` is the Schmitt hold. `drift=` is gate open-eye EAR minus the slow open-eye EMA.

## Field protocol keys

Focus the OpenCV window. Do not use `--no-window` on a field run.

| Key | Writes | Meaning |
| --- | --- | --- |
| `c` | `logs/alert_labels.csv` | Observer was checking |
| `g` | `logs/alert_labels.csv` | Observer was gone |
| `s` | `logs/rest_stops.csv` | Cycle stimulant |
| `1`-`9` | `logs/rest_stops.csv` | Karolinska score |
| `q` | — | Quit |

No names in any CSV. Each protocol row now also stores `alert_unix_time` from the last DROWSY/MICROSLEEP banner.

## Pair by Unix time

```bash
export PYTHONPATH=src
python scripts/monday_sheet.py logs
```

That writes two nameless joins:

- `logs/paired_alerts.csv` — label row + matching `alerts.csv` row. Match key is `alert_unix_time` when present, else the latest alert within 120 s before the keypress.
- `logs/paired_rest_stops.csv` — rest-stop row + nearest prior alert within 2 h.

`paired=yes` is a gold candidate only when `label=checking`. `label=gone` stays in the file so you can audit discarded banners. There is no driver-name column on purpose.

## Licence

MIT.
