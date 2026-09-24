# Full manuscript location

The long thesis (declaration through Appendix C, including §4.10 and §6.5) is the project Word file:

- `Quaye_Fatigue_Detection_HAZMAT_West_Africa_Thesis.docx`
- source: `Quaye_HAZMAT_Fatigue_Thesis.md`

Those two files already contain the full text. This repository’s detector matches that text (`HysteresisGate`, field keys `c/g/s/1-9/n`, pairing, overwrite_rostering).

Binary `.docx` / `.xlsx` cannot be uploaded through the text-file GitHub tool used here without corrupting the ZIP. The **numbers** from the synthetic workbook are in `data/synthetic_rostering.md`. Rebuild Excel with:

```
python scripts/overwrite_rostering.py --logs logs --out Tema_Kumasi_Rostering_PERCLOS.xlsx
```

After `git pull`, copy the Word manuscript from the project folder into `docs/` locally if you need it next to the code:

```
cp Quaye_Fatigue_Detection_HAZMAT_West_Africa_Thesis.docx docs/
cp Tema_Kumasi_Rostering_PERCLOS.xlsx data/
git add docs/ data/
git commit -m "Add Word thesis and synthetic workbook binaries"
git push
```

Run that last block on your machine (you have git credentials). This remote helper can push text; you can push the two binaries in one commit.
