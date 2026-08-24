"""Compile an EvalSpec into an immutable JobPlan.

Mirrors Harbor's expansion at harbor@b378332 job_plan.py:140-168:

    n_attempts × tasks × agents  →  TrialConfig[]

Checksum covers the resolved (task, agent, attempt) list only — not wall-clock
job names. Same spec twice must match. That is Week 2 invariant 1 in seed form.
"""

import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvalSpec:
    tasks: tuple[str, ...]
    agents: tuple[str, ...]
    n_attempts: int = 1

    def __post_init__(self) -> None:
        if self.n_attempts < 1:
            raise ValueError("n_attempts must be >= 1")
        if not self.tasks:
            raise ValueError("tasks must be non-empty")
        if not self.agents:
            raise ValueError("agents must be non-empty")


@dataclass(frozen=True, slots=True)
class TrialSpec:
    task: str
    agent: str
    attempt: int


@dataclass(frozen=True, slots=True)
class JobPlan:
    trials: tuple[TrialSpec, ...]
    checksum: str


def compile_eval(spec: EvalSpec) -> JobPlan:
    """Deterministic cartesian expansion. Loop order matches Harbor."""
    trials = tuple(
        TrialSpec(task=task, agent=agent, attempt=attempt)
        for attempt in range(spec.n_attempts)
        for task in spec.tasks
        for agent in spec.agents
    )
    payload = [{"task": t.task, "agent": t.agent, "attempt": t.attempt} for t in trials]
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    checksum = hashlib.sha256(blob.encode()).hexdigest()
    return JobPlan(trials=trials, checksum=checksum)


def _self_check() -> None:
    spec = EvalSpec(
        tasks=("sum", "copy"),
        agents=("oracle", "null"),
        n_attempts=2,
    )
    a = compile_eval(spec)
    b = compile_eval(spec)
    assert a == b, "same spec must compile to the same plan"
    assert len(a.trials) == 2 * 2 * 2
    assert a.trials[0] == TrialSpec("sum", "oracle", 0)
    # Harbor order: attempt, then task, then agent
    assert [t.agent for t in a.trials[:2]] == ["oracle", "null"]
    print(f"trials={len(a.trials)} checksum={a.checksum[:12]}…")
    for t in a.trials:
        print(f"  attempt={t.attempt} task={t.task} agent={t.agent}")


if __name__ == "__main__":
    _self_check()
