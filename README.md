# Fatigue Detection for Hazmat Drivers in West Africa

WA-PERCLOS-HYS: MediaPipe Face Mesh, EMA-smoothed EAR, two-threshold hysteresis, personal P60-median calibration, PERCLOS, PLCDB, and multi-cue fusion for petroleum tanker cabins.

**Thesis author (University of Ghana, MSc Data Science, Cohort C):** ADDO Austin Gamey, student ID **22424506**, Department of Computer Science, College of Basic and Applied Sciences, September 2026.

Copyright (c) 2026 Addo Austin Gamey. MIT licence.

Chapter order in the manuscript:

1. Introduction
2. Literature review
3. West African HAZMAT context
4. Research methodology
5. WA-PERCLOS-HYS algorithm
6. System implementation
7. Results
8. Discussion
9. Conclusion and recommendations

The Word file is `Addo_Austin_Gamey_22424506_HAZMAT_Fatigue_Thesis.docx` in the project folder. This repository holds the detector, pairing, rostering scripts, and `data/Tema_Kumasi_Rostering_PERCLOS.csv`.

States: `CALIBRATING`, `ALERT`, `DROWSY`, `MICROSLEEP`, `NO_FACE`, `OPTICS_DIRTY`, `DEGRADED` (glasses after dusk), `SHARED_DEVICE`.

## Algorithm rule (live code, Chapter 5)

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
- Depot cut 0.45 / trunk cut 0.55 on the same night

## Field protocol keys

Focus the OpenCV window.

| Key | Writes | Meaning |
| --- | --- | --- |
| `c` | `logs/alert_labels.csv` | Observer was checking |
| `g` | `logs/alert_labels.csv` | Observer was gone |
| `s` | `logs/rest_stops.csv` | Cycle stimulant |
| `1`-`9` | `logs/rest_stops.csv` | Karolinska score |
| `n` | `logs/near_misses.csv` | Near miss; starts 30 s startle clip |
| `q` | — | Quit |

Automatic 1 Hz rows go to `logs/perclos_1hz.csv`. No names in any CSV. HUD prints `closed=` and `drift=`.

## Gold set

Sensitivity uses only `paired=yes` AND `label=checking`. Quote the gone rate on the same sheet.

```bash
git pull
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
pytest tests -q
python scripts/run_detector.py --camera 0 --logs logs
python scripts/monday_sheet.py logs
python scripts/overwrite_rostering.py --logs logs --out Tema_Kumasi_Rostering_PERCLOS.xlsx
```

## Synthetic coded night

No on-road tanker video was labelled. Seed 42, 6.5 h Tema–Kumasi template. Status `CODED — SYNTHETIC`. 128 banners, 94 checking, 18 gone (14.1%).

## Ethics

Keep landmarks and scores. Delete raw video after coding. No names. A banner is not a disciplinary event.

## Licence

MIT. Copyright (c) 2026 Addo Austin Gamey.
