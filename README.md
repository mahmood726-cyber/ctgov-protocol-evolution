# ctgov-protocol-evolution

A project to track how clinical trial protocols dynamically adapt over their lifecycle based on ClinicalTrials.gov historical API data.

## Features
- Fetches real historical data from ClinicalTrials.gov API (v2)
- Quantifies frequency and impact of protocol changes (TruthCert compliance)
- Generates an interactive static HTML dashboard
- Outputs an E156 micro-paper

## Structure
- `data/`: Raw and processed data, TruthCert hashes.
- `src/`: Ingestion and analysis scripts.
- `site/`: HTML dashboard (GitHub Pages ready).
- `tests/`: Offline test suites.