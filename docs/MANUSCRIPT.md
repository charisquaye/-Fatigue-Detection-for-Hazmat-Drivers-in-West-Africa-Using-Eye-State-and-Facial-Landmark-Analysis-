# Full manuscript files

The complete thesis is available in both formats:

- [Word thesis](Austine_Gamey_Addo_22424506_HAZMAT_Fatigue_Thesis.docx)
- [PDF thesis](Austine_Gamey_Addo_22424506_HAZMAT_Fatigue_Thesis.pdf)

The repository's detector matches the thesis specification (`HysteresisGate`, field keys `c/g/s/1-9/n`, pairing, and `overwrite_rostering`). The synthetic workbook values are also recorded in `data/synthetic_rostering.md`. Rebuild the workbook with:

```bash
python scripts/overwrite_rostering.py --logs logs --out Tema_Kumasi_Rostering_PERCLOS.xlsx
```
