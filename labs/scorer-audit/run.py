"""Run the Week 4 deterministic-verifier regression suite.

Pure standard library; no model, API key, Docker, or tau2 install required.

    python3 labs/scorer-audit/run.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CONTROLS = ROOT / "controls.json"

PASS = "PASS"
FAIL = "FAIL"
UNKNOWN = "UNKNOWN"

PASSENGER_ID = "anya_garcia_5901"
ITINERARY_ID = "JMO1MG"


def official_substring_scorer(case: dict[str, Any]) -> str:
    """Approximate the vulnerable COMMUNICATE predicate used in the teardown."""

    return PASS if "4" in case["message"].replace(",", "") else FAIL


def candidate_scorer(case: dict[str, Any]) -> dict[str, Any]:
    """Apply the course score contract to structured, evidence-linked claims."""

    if not case["evidence_complete"]:
        return {
            "overall": UNKNOWN,
            "criteria": {"evidence_complete": UNKNOWN},
            "reason_codes": ["INSUFFICIENT_EVIDENCE"],
        }

    claim = case.get("claim") or {}
    criteria = {
        "identity_evidence": PASS
        if case.get("identity_passenger_id") == PASSENGER_ID
        else FAIL,
        "itinerary_evidence": PASS
        if case.get("itinerary_id") == ITINERARY_ID
        else FAIL,
        "communication": PASS
        if (
            claim.get("type") == "baggage_allowance"
            and claim.get("quantity") == 4
            and claim.get("unit") == "bags"
            and claim.get("affirmed") is True
        )
        else FAIL,
        "authorization": FAIL if case.get("forbidden_side_effect") else PASS,
    }
    failed = [name for name, label in criteria.items() if label == FAIL]
    return {
        "overall": FAIL if failed else PASS,
        "criteria": criteria,
        "reason_codes": [f"FAILED_{name.upper()}" for name in failed],
    }


def confusion(rows: list[dict[str, str]], scorer: str) -> Counter[str]:
    matrix: Counter[str] = Counter()
    for row in rows:
        expected = row["expected"]
        observed = row[scorer]
        if expected == UNKNOWN:
            matrix["EXPECTED_UNKNOWN"] += 1
        elif observed == UNKNOWN:
            matrix["UNEXPECTED_UNKNOWN"] += 1
        elif expected == PASS and observed == PASS:
            matrix["TP"] += 1
        elif expected == FAIL and observed == PASS:
            matrix["FP"] += 1
        elif expected == PASS and observed == FAIL:
            matrix["FN"] += 1
        else:
            matrix["TN"] += 1
    return matrix


def main() -> None:
    controls = json.loads(CONTROLS.read_text())
    assert len(controls) == 10, "the lesson contract requires exactly 10 controls"

    rows = []
    for case in controls:
        candidate = candidate_scorer(case)
        row = {
            "case": case["case_id"],
            "expected": case["expected"],
            "official": official_substring_scorer(case),
            "candidate": candidate["overall"],
        }
        rows.append(row)

    print(f"{'case':24} {'expected':9} {'substring':10} {'candidate':10}")
    print("-" * 58)
    for row in rows:
        print(
            f"{row['case']:24} {row['expected']:9} "
            f"{row['official']:10} {row['candidate']:10}"
        )

    print("\nsubstring scorer:", dict(confusion(rows, "official")))
    print("candidate scorer:", dict(confusion(rows, "candidate")))

    mismatches = [row for row in rows if row["candidate"] != row["expected"]]
    if mismatches:
        raise SystemExit(f"candidate regression failures: {mismatches}")
    print("\nPASS: candidate matches all 10 adjudicated controls")


if __name__ == "__main__":
    main()
