# Thesis addendum (Quaye 2026)

These sections were written so the manuscript matches the live repository. The full Word thesis is `Quaye_Fatigue_Detection_HAZMAT_West_Africa_Thesis.docx` in the project folder. Nothing below is an on-road tanker result.

## 4.10 Field log, gold set, and consequence cuts

The detector is not the whole method. An observer in the jump seat presses `c` when they were watching the banner and `g` when they were not. `s` cycles the rest-stop stimulant list (none, ataya, energy drink, tramadol-coffee, cola nut, other). Keys `1`–`9` write a Karolinska score (Åkerstedt & Gillberg, 1990). `n` marks a near miss and opens a 30-second startle clip. Every protocol row stores the last alert Unix time. No name, plate, or phone number is written.

Pairing is done later. If `alert_unix_time` is present, the join is exact within a 120-second window. Otherwise the latest prior alert in that window is used. Rest stops search two hours back. Gold analysis uses only rows with `paired=yes` and `label=checking`. The gone rate is reported on the same sheet.

Two score cuts live on the same night. Depot road and the loaded start use 0.45. The night trunk uses 0.55.

PERCLOS 95th percentile by haul hour, split by the stimulant logged at the last rest stop, is the rostering input. The 0.30 line is a discussion band after Wierwille et al. (1994) and Dinges and Grace (1998), not a medical diagnosis.

If mesh confidence stays under 0.45 for most of the 30 seconds after a near miss, the detector is blind in the minute that matters.

## 5. Implementation (live modules)

`field_protocol.py` writes nameless observer keys, rest-stop stimulant and KSS, near-miss marks, and a 1 Hz PERCLOS series. `pairing.py` joins those rows to `alerts.csv` by Unix time. `scripts/monday_sheet.py` and `scripts/overwrite_rostering.py` are the Monday morning objects. `scripts/plot_deltas.py` draws observer lag. `scripts/analyze_haul.py` prints the gold-set counts. `scripts/run_detector.py` is the cab loop (`c` `g` `s` `1-9` `n` `q`).

## 6.4 Field protocol that was not run on a real tanker

1. One corridor. Tema–Kumasi night tanker is the default.
2. Eight-second open-eye gate at the depot. Face hash only.
3. Observer in the jump seat. Banner then `c` or `g`.
4. Rest-stop `s` and Karolinska `1`–`9`. Near-miss `n`.
5. Sensitivity only on `paired=yes` and `label=checking`. Quote the gone rate on the same table.
6. One glasses-after-dusk or monocular night stays in the file.
7. Raw video deleted after coding.

## 6.5 Synthetic coded night (not a field result)

Seed 42. 6.5 h template. 128 banners, 94 checking, 18 gone (14.1%), 16 untagged. Median checking lag 8.3 s.

PERCLOS p95: hour 0–1 within band (0.13–0.17, none); hour 2 rest/ataya 0.18; hour 3–4 shorten next duty (0.23–0.29); hour 5–6 SPLIT or STOP (0.34–0.38). Ataya does not keep the late haul under 0.30.

Latent-fatigue ROC (truth = latent ≥ 0.42, score = latent + N(0,0.10)):

- depot 0.45: TPR 0.86, FPR 0.12
- trunk 0.55: TPR 0.68, FPR 0.02

Startle blind fraction 0–30 s: 94%, 97%, 94%.

Workbook cover: `CODED — SYNTHETIC`. Replace with a real `logs/` folder and `overwrite_rostering.py`.

## 7. Ethics (method, not an appendix footnote)

Keep landmarks and scores. Delete raw video after coding. No names, plates, or phone numbers. Refusal of the camera is allowed and is not stored as a name. A banner is not a disciplinary event.

## Appendix B operating points (added)

Depot / drowsy score 0.45. Trunk score 0.55. Observer pairing window 120 s. Rest-stop pairing window 2 h. Startle clip 30 s. Mesh-lost floor 0.45. Mid-haul open-eye clamp ±0.03.
