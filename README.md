# CT.gov Protocol Evolution — corrected research scope

## Existing dataset: cross-sectional baseline

The checked-in `data/protocol_changes.csv` is **misleadingly named**: `src/fetch_ctgov.py` downloaded one current ClinicalTrials.gov API v2 record per study. It **does not** retrieve prior registry versions. The checked-in clustering/Benford/Gini dashboard describes current-record features; it **cannot** establish protocol amendment frequency, outcome switching, adaptive trial strategy or study misconduct. Benford fit is descriptive and its assumptions may not hold for selected trial enrollment sizes. The dashboard's previous “verified” wording displayed a hash manifest without checking the CSV checksum.

## New: genuine version-to-version comparisons (offline)

`src/history_diff.py` compares explicit archived revisions for the **same NCT ID**; it never fabricates history from contemporaneous different trials. The input is JSONL, each line containing:

```json
{"nctId":"NCT01234567","versionDate":"2023-01-01","study":{"protocolSection":{"identificationModule":{"nctId":"NCT01234567"},"outcomesModule":{"primaryOutcomes":[{"measure":"Example outcome","timeFrame":"6 months"}]}}}}
```

Supply **at least two independently authenticated historical versions** of an NCT study. Do not invent version dates. For actual data, acquire the registry's dated archived versions separately and record their provenance: this repo **does not yet provide a verified public history API client**.

```bash
python src/history_diff.py --input my_verified_revisions.jsonl --output data/history_diffs.json
python -m unittest discover -s tests -p 'test_history_diff.py'
```

The output contains from/to version dates, all observed field differences (including outcomes, enrollment, eligibility and design), and explicitly unassessable fields when a version omits data. Estimated-to-actual enrollment transitions are identified separately, not presumed protocol amendments. Changes in record fields are not necessarily prespecified endpoint switching or misconduct; interpreting materiality requires verified amendment histories and independent adjudication.

## Repository structure

- `src/fetch_ctgov.py`: legacy **current-record** download, not protocol-history ingestion.
- `src/advanced_stats.py`: descriptive single-record statistics; clustering initialisation is now deterministic.
- `src/history_diff.py`: separate longitudinal comparison of user-supplied authentic revision snapshots.
- `site/index.html`: labelled cross-sectional dashboard.
- `tests/`: descriptive-pipeline tests and history-diff regression tests.

This correction does not change the original underlying study data or retrospectively validate the original E156 analysis.
