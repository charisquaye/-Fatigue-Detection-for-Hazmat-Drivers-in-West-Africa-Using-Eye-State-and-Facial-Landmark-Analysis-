# Tema-Kumasi rostering workbook (SYNTHETIC)

Status: **CODED — SYNTHETIC**. Seed 42. Not an on-road tanker night. No names.
Gold rule: `paired=yes` AND `label=checking`.

Rebuild the Excel file after any haul:

```
python scripts/overwrite_rostering.py --logs data/synthetic_haul --out Tema_Kumasi_Rostering_PERCLOS.xlsx
```

## Haul cover

| Field | Value |
| --- | --- |
| Status | CODED — SYNTHETIC |
| Banners | 128 |
| Labels | 112 |
| checking gold | 94 |
| gone | 18 |
| gone rate | 14.1% |
| Names | none |

## PERCLOS p95 by haul hour

| Hour | p95 none | p95 ataya | n | Flag |
| --- | --- | --- | --- | --- |
| 0 | 0.129 | — | 3600 | within band |
| 1 | 0.172 | — | 3600 | within band |
| 2 | 0.182 | 0.178 | 3600 | within band |
| 3 | — | 0.233 | 3600 | shorten next duty |
| 4 | — | 0.286 | 3600 | shorten next duty |
| 5 | — | 0.344 | 3600 | SPLIT or STOP |
| 6 | — | 0.383 | 1800 | SPLIT or STOP |

## Operating points (latent fatigue + noise)

| Point | Cut | TPR | FPR |
| --- | --- | --- | --- |
| Depot road | 0.45 | 0.864 | 0.121 |
| Trunk road | 0.55 | 0.683 | 0.021 |

## Startle 0-30 s

| Clip | Blind fraction | Samples |
| --- | --- | --- |
| Near-miss 1 | 93.5% | 31 |
| Near-miss 2 | 96.8% | 31 |
| Near-miss 3 | 93.5% | 31 |
