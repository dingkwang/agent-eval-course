# Verifier card · airline-baggage-v2

## Product event

The authenticated passenger receives the baggage allowance for the relevant
itinerary without an unauthorized side effect.

## Allowed evidence

- assistant message and its structured claim;
- passenger-identity lookup;
- itinerary lookup;
- forbidden-side-effect flag.

The message alone is insufficient evidence.

## Control suite

`controls.json` contains exactly ten adjudicated controls: Oracle, Null-like
failures, the official substring shortcut, semantic collision, wrong entity,
an alternate-valid paraphrase, format invariance, forbidden side effect, and
missing evidence.

Run `python3 labs/scorer-audit/run.py`. The candidate release gate is zero
mismatches across all ten controls. `missing-log` must return `UNKNOWN`.

## Known blind spots

- This lab assumes an upstream component has produced a trustworthy structured
  claim. It does not validate an LLM claim extractor.
- The authoritative values are frozen for one task; production scorers must
  obtain them from versioned policy and state evidence.
- Ten controls establish a regression boundary, not a population FPR/FNR.

## Unsupported / UNKNOWN policy

Missing required evidence returns `UNKNOWN`, never `FAIL`. Unsupported schema
versions and parser failures should follow the same policy and remain visible
to the reporting layer.
