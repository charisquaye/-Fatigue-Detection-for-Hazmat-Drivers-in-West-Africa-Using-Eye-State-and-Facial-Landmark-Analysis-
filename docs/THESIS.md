# Thesis addendum

**Author:** ADDO, Austine Gamey (22424506), MSc Data Science, Cohort C, Department of Computer Science, University of Ghana.

Word file: `Addo_Austine_Gamey_22424506_HAZMAT_Fatigue_Thesis.docx`

Chapters now in the Word manuscript:

1. Introduction
2. Literature review
3. West African HAZMAT context
4. WA-PERCLOS-HYS algorithm
5. System implementation
6. Evaluation
7. Conclusion and recommendations
8. Research methodology (design, sample, procedure, YAML parameters, gold set, ethics as method)
9. Results (Object A 120 sessions; Object B seed 42 night; p95; two cuts; startle; worked scores)
10. Discussion of method and results (repo map vs `configs/default.yaml`)

Cuts in Chapter 8 Table 8.1 are copied from `configs/default.yaml` on this branch: ema_alpha 0.4, gap 0.03, close_ratio 0.68, gate 8 s, night scale 0.92, luma 70, PERCLOS window 60 s, closed frames 20, depot 0.45, trunk 0.55, severe 0.70, cooldown 4 s.

Object B (SYNTHETIC): 128 banners, 94 checking, 18 gone (14.1%), p95 hours 0–6 as in `data/Tema_Kumasi_Rostering_PERCLOS.csv`, depot TPR 0.86 / FPR 0.12, trunk TPR 0.68 / FPR 0.02, startle 94–97%.

Nothing above is an on-road tanker result.
