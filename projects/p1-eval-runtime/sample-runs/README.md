# sample-runs

These five directories must hold **real** `run.py` output, not hand-written JSON.

Each experiment: `trajectory.jsonl` + TrialResult JSON.

| dir | command | expected status |
|---|---|---|
| `oracle-strong/` | `--agent oracle --verifier strong` | PASS |
| `null-strong/` | `--agent null --verifier strong` | FAIL |
| `cheat-weak/` | `--agent cheat --verifier weak` | PASS |
| `cheat-strong/` | `--agent cheat --verifier strong` | FAIL |
| `timeout-strong/` | `--agent timeout --verifier strong` | ERROR |
