# EvalRT Core — Week 2 labs

Teaching runtime, not a Harbor import. Semantics follow Harbor `@b378332`.

```
compile.py     L1  EvalSpec → JobPlan (unordered Trial snapshot)
protocol.py    L2  Agent / Environment / Trial contracts
trial.py       L2  lifecycle + ADAPTER_VIOLATION / UNSUPPORTED / CANCELLED
adapters/      L2  Null · Oracle(privileged) · Scripted · HintInjecting
environments/  L2  Local tempdir · Docker bind-mount + docker run --rm
```

```bash
python3 -m pytest labs/eval-runtime/tests/test_compile.py
python3 -m pytest labs/eval-runtime/tests/test_agent_contract.py \
  labs/eval-runtime/tests/test_environment_contract.py \
  labs/eval-runtime/tests/test_lifecycle.py \
  labs/eval-runtime/tests/test_differential.py
```

Docker tests skip unless `docker run --rm python:3.12-slim-bookworm python3 -c "print('ok')"` works.
L2 unique prop: an adapter that mutates instruction is `ADAPTER_VIOLATION` even if reward is 1.
