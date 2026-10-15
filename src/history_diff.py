"""Offline, conservative comparisons of externally sourced CT.gov revision snapshots.

Input JSONL rows: {"nctId": "NCT########", "versionDate": "YYYY-MM-DD",
                   "study": {"protocolSection": {...}}}.
Source revisions must be independently obtained and verified: separate current
records must never be treated as historical versions.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

NCT = re.compile(r"NCT\d{8}\Z")
MISSING = object()

FIELD_PATHS = {
    "primary_outcomes": ("outcomesModule", "primaryOutcomes"),
    "secondary_outcomes": ("outcomesModule", "secondaryOutcomes"),
    "eligibility_criteria": ("eligibilityModule", "eligibilityCriteria"),
    "enrollment": ("designModule", "enrollmentInfo"),
    "allocation": ("designModule", "designInfo", "allocation"),
    "masking": ("designModule", "designInfo", "maskingInfo", "masking"),
    "arm_groups": ("armsInterventionsModule", "armGroups"),
}


def field(study, path):
    data = study.get("protocolSection", MISSING)
    for part in path:
        if not isinstance(data, dict) or part not in data:
            return MISSING
        data = data[part]
    return data


def canonical(value):
    """Normalise presentation whitespace/list order without dropping distinctions."""
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        items = [canonical(x) for x in value]
        return sorted(items, key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))
    if isinstance(value, str):
        return " ".join(value.split())
    return value


def diff_history(records):
    revisions = defaultdict(list)
    seen = set()
    for record in records:
        nct_id = record.get("nctId")
        if not isinstance(nct_id, str) or not NCT.fullmatch(nct_id):
            raise ValueError("Revision has an invalid NCT ID")
        version = record.get("versionDate")
        try:
            date.fromisoformat(version)
        except (TypeError, ValueError):
            raise ValueError("Each revision requires an ISO YYYY-MM-DD versionDate") from None
        study = record.get("study")
        if not isinstance(study, dict) or not isinstance(study.get("protocolSection"), dict):
            raise ValueError("Each revision requires a v2 study protocolSection")
        embedded = study["protocolSection"].get("identificationModule", {}).get("nctId")
        if embedded and embedded != nct_id:
            raise ValueError("Embedded NCT identifier disagrees with revision")
        identity = (nct_id, version)
        if identity in seen:
            raise ValueError("Duplicate NCT/versionDate; revision ordering is ambiguous")
        seen.add(identity)
        revisions[nct_id].append((version, study))

    events = []
    assessed_pairs = 0
    missing_fields = 0
    for nct_id, versioned in sorted(revisions.items()):
        versioned.sort(key=lambda x: x[0])
        for (before_date, before), (after_date, after) in zip(versioned, versioned[1:]):
            assessed_pairs += 1
            for field_name, path in FIELD_PATHS.items():
                old, new = field(before, path), field(after, path)
                if old is MISSING or new is MISSING:
                    missing_fields += 1
                    # Missing coverage is neither 'no change' nor an amendment.
                    continue
                old, new = canonical(old), canonical(new)
                if old == new:
                    continue
                change_kind = "FIELD_CHANGED"
                if field_name == "enrollment":
                    if isinstance(old, dict) and isinstance(new, dict) and old.get("type") != new.get("type"):
                        change_kind = "ENROLLMENT_ESTIMATE_ACTUAL_TRANSITION"
                events.append({
                    "nctId": nct_id, "fromVersion": before_date, "toVersion": after_date,
                    "field": field_name, "changeKind": change_kind,
                    "before": old, "after": new,
                })
    return {
        "metadata": {
            "study_ids": len(revisions), "records": len(seen),
            "adjacent_version_pairs": assessed_pairs,
            "field_comparisons_unassessable_missing_version_data": missing_fields,
            "source_verified": False,
            "scope_warning": "Requires authentic archived revisions; this does not establish when an amendment was submitted, clinical materiality, or misconduct",
        },
        "changes": events,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Versioned v2-study JSONL input; NOT a current-record registry export")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle if line.strip()]
    result = diff_history(records)
    if not result["metadata"]["adjacent_version_pairs"]:
        raise ValueError("No within-trial historical revision pairs; current records cannot measure protocol changes")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote", len(result["changes"]), "observed field differences to", args.output)


if __name__ == "__main__":
    main()
