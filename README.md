# Fatigue Detection for Hazmat Drivers in West Africa

WA-PERCLOS-HYS: MediaPipe Face Mesh, EMA-smoothed EAR, two-threshold hysteresis, personal P60-median calibration, PERCLOS, PLCDB, and multi-cue fusion for petroleum tanker cabins.

**Thesis author (University of Ghana, MSc Data Science, Cohort C):** ADDO, Austine Gamey, student ID **22424506**, Department of Computer Science, College of Basic and Applied Sciences, September 2026.

Seven chapters: Introduction; Literature review; West African HAZMAT context; WA-PERCLOS-HYS algorithm; System implementation; Evaluation; Conclusion and recommendations.

Chapters 4.10, 5, 6.4, 6.5, 7 and Appendices A–D match the live code. The Word manuscript is the project file `Addo_Austine_Gamey_22424506_HAZMAT_Fatigue_Thesis.docx`. This repository holds the detector, pairing, rostering scripts, and `data/Tema_Kumasi_Rostering_PERCLOS.csv`.

States: `CALIBRATING`, `ALERT`, `DROWSY`, `MICROSLEEP`, `NO_FACE`, `OPTICS_DIRTY`, `DEGRADED` (glasses after dusk), `SHARED_DEVICE`.

## Chapter 4 rule (live code)

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

Automatic 1 Hz rows go to `logs/perclos_1hz.csv`. No names in any CSV. Each protocol row stores `alert_unix_time` from the last DROWSY/MICROSLEEP banner. HUD prints `closed=` (Schmitt hold) and `drift=` (open-eye sag).

## Gold set

Sensitivity uses only `paired=yes` AND `label=checking`. Quote the gone rate on the same sheet. Do not bury it.

```bash
git pull
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
pytest tests -q
python scripts/run_detector.py --camera 0 --logs logs
python scripts/monday_sheet.py logs
python scripts/plot_deltas.py --logs logs --out logs/alert_time_deltas.png
python scripts/analyze_haul.py --logs logs
python scripts/overwrite_rostering.py --logs logs --out Tema_Kumasi_Rostering_PERCLOS.xlsx
```

Pairing: exact `alert_unix_time` when present, else nearest prior alert within 120 s (labels) or 2 h (rest stops).

## Synthetic coded night

No on-road tanker video was labelled for the thesis. A 6.5 h Tema–Kumasi template (seed 42) exercises the Monday scripts. Cover status `CODED — SYNTHETIC` is not field performance. Replace with a real `logs/` folder and rerun `overwrite_rostering.py`.

On that template: 128 banners, 94 checking, 18 gone (14.1%), median checking lag 8.3 s, PERCLOS p95 crosses 0.30 after hour 4 even with ataya, depot 0.45 TPR 0.86 / FPR 0.12, trunk 0.55 TPR 0.68 / FPR 0.02, startle blind 0–30 s ≈ 94–97%.

## Ethics

Keep landmarks and scores. Delete raw video after coding. No names, plates, or phone numbers. Refusal of the camera is allowed and is not stored as a name. A banner is not a disciplinary event.

## Licence

MIT.
