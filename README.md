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
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export PYTHONPATH=src      # Windows: set PYTHONPATH=src
pytest tests -q
python scripts/run_detector.py --camera 0
```

If you already cloned before the field-protocol commit, `git pull` first. Missing module errors (`field_protocol`) mean the working copy is stale.

## HUD line: closed= and drift=

This is status, not a crash.

- `closed=1` means the Schmitt gate is in the closed band (EAR dropped through theta_close and has not yet risen through theta_open).
- `closed=0` means open.
- `drift=` is gate EAR_open minus the slow open-eye EMA. A rising positive number over a long haul is the mid-shift sag the thesis tracks. It is not an error code.

## Field protocol keys (observer, not the driver)

The window must be focused. Keys do nothing if you used `--no-window`.

| Key | Writes | Meaning |
| --- | --- | --- |
| `c` | `logs/alert_labels.csv` | Observer was checking the road / phone / papers after an alert |
| `g` | `logs/alert_labels.csv` | Observer was gone; do not treat the last alert as a gold label |
| `s` | `logs/rest_stops.csv` | Cycle stimulant at this rest stop: none, ataya, energy_drink, tramadol_coffee, cola_nut, other |
| `1`–`9` | `logs/rest_stops.csv` | Karolinska Sleepiness Scale on that rest-stop row |
| `q` | — | Quit |

After a DROWSY or MICROSLEEP banner, press `c` or `g` before the next event. The HUD line turns cyan while a label is pending.

Rows have no names. Monday review is `python scripts/monday_sheet.py`.

## Licence

MIT.
