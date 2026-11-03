# SCOTUS Explorer

A browsable index of 9,341 U.S. Supreme Court decisions from the 1946 through 2024 terms. Search by case name, majority author, term or issue area, or filter by issue area, Court era (Vinson through Roberts) and justice. Each case card opens to show the vote, the majority author, the SCDB's ideological direction code, concurring and dissenting justices, the citation and links to the full opinion on Justia and Cornell's Legal Information Institute (LII). Picking a justice shows how many opinions that justice wrote, joined in concurrence or dissented from.

Case data comes from the [Supreme Court Database](https://scdb.la.psu.edu/) (SCDB), 2025 Release 01. A hand-written layer of 55 one-sentence holdings, drawn from Oyez and Cornell LII, marks featured cases, and short doctrine summaries appear for seven issue areas. Not legal advice.

## Files

### `index.html`
The explorer. All styles and JavaScript are inline, with no build step. It loads `scdb.json` from the same folder. The featured holdings (`FEATURED`), doctrine summaries (`DOCTRINE`) and Court eras (`ERAS`) are written into the script.

### `scdb.json`
The case data the page loads: one record per case with name, term, decision date, U.S. Reports citation, issue area, vote, ideological direction, chief justice, majority author and the justices in the majority, concurring and dissenting. Identical to `data/scdb.json`.

### `data/`
The two SCDB citation files (case-centered and justice-centered, 2025 Release 01) and `process_scdb.py`, which turns them into the compact JSON. Run it from inside `data/`; it writes the JSON to standard output and progress to standard error:

```bash
cd data
python3 process_scdb.py > scdb.json 2> process.log
cp scdb.json ../scdb.json
```

`scdb_case.csv` and `scdb_justice.csv` are zip archives of the same two SCDB files, despite the .csv extension.

### `scotus-explorer.html`
An earlier version of the explorer: 85 hand-picked landmark rulings from Marbury v. Madison (1803) through the 2024 term, with a grid and timeline view. The current page replaced it.

### `scanner/discover.py`
Left over from an earlier project in this repository, a Vital City experiments gallery. It scans GitHub, Hacker News and Reddit for new urban data tools (`python scanner/discover.py --output report`, with optional `--days` and a `GITHUB_TOKEN` environment variable for higher rate limits). The explorer does not use it.
