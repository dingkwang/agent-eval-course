# Lab · scorer audit

This lab turns the τ³ airline `id=3` verifier teardown into an executable
regression gate. It compares the vulnerable substring predicate with a
contract-aware candidate verifier over ten adjudicated controls.

```bash
python3 labs/scorer-audit/run.py
```

Expected final line:

```text
PASS: candidate matches all 10 adjudicated controls
```

Files:

- `contracts/airline-3.yaml` — score and evidence contract;
- `controls.json` — the ten labeled controls;
- `run.py` — baseline, candidate, confusion matrices, and release assertion;
- `VERIFIER_CARD.md` — evidence boundary, gate, and known blind spots.

The existing `labs/tau3-verifier/` still runs the real τ³ evaluator and proves
that `AA-1234` receives official reward 1.0. This lab starts from that observed
failure and tests a replacement contract; it does not pretend to re-run τ³.
