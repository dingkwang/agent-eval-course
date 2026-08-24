"""Compile an EvalSpec into a recorded JobPlan.

Teaching compiler aligned with Harbor @b378332:

    resolve → validate → expand → freeze

Expansion loop order matches job_plan.py:140-168
(n_attempts × tasks × agents). The snapshot matches JobLock.__eq__:
an unordered TrialLock collection (lock.py:277-292), not a positional
checksum. Harbor TrialConfig has no attempt_index; multiplicity of
identical trials is the teaching stand-in for n_attempts.
"""

import hashlib
import json
from dataclasses import dataclass


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class TaskInput:
    id: str
    instruction: str


@dataclass(frozen=True, slots=True)
class AgentInput:
    name: str | None
    model: str = ""
    prompt: str = ""


@dataclass(frozen=True, slots=True)
class EvalSpec:
    tasks: tuple[TaskInput, ...]
    agents: tuple[AgentInput, ...]
    n_attempts: int = 1


@dataclass(frozen=True, slots=True)
class ResolvedTask:
    id: str
    instruction_digest: str


@dataclass(frozen=True, slots=True)
class ResolvedAgent:
    name: str
    model: str
    prompt_digest: str


@dataclass(frozen=True, slots=True)
class ResolvedSpec:
    tasks: tuple[ResolvedTask, ...]
    agents: tuple[ResolvedAgent, ...]
    n_attempts: int


@dataclass(frozen=True, slots=True)
class TrialSpec:
    """One expanded trial. No attempt index: Harbor has none."""

    task: ResolvedTask
    agent: ResolvedAgent


@dataclass(frozen=True, slots=True)
class JobPlan:
    trials: tuple[TrialSpec, ...]
    snapshot: str


def resolve(spec: EvalSpec) -> ResolvedSpec:
    """Materialize defaults and content digests. Empty agent name → oracle."""
    tasks = tuple(
        ResolvedTask(id=task.id, instruction_digest=_digest(task.instruction))
        for task in spec.tasks
    )
    agents = tuple(
        ResolvedAgent(
            name=agent.name if agent.name else "oracle",
            model=agent.model,
            prompt_digest=_digest(agent.prompt),
        )
        for agent in spec.agents
    )
    return ResolvedSpec(tasks=tasks, agents=agents, n_attempts=spec.n_attempts)


def validate(resolved: ResolvedSpec) -> None:
    if resolved.n_attempts < 1:
        raise ValueError("n_attempts must be >= 1")
    if not resolved.tasks:
        raise ValueError("tasks must be non-empty")
    if not resolved.agents:
        raise ValueError("agents must be non-empty")
    ids = [task.id for task in resolved.tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate task id")


def expand(resolved: ResolvedSpec) -> tuple[TrialSpec, ...]:
    """Cartesian product. Loop order matches Harbor."""
    return tuple(
        TrialSpec(task=task, agent=agent)
        for _ in range(resolved.n_attempts)
        for task in resolved.tasks
        for agent in resolved.agents
    )


def freeze(trials: tuple[TrialSpec, ...]) -> str:
    """Unordered multiset of trials, matching JobLock trial-set equality."""
    keys = sorted(
        (
            t.task.id,
            t.task.instruction_digest,
            t.agent.name,
            t.agent.model,
            t.agent.prompt_digest,
        )
        for t in trials
    )
    blob = json.dumps(keys, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def compile_eval(spec: EvalSpec) -> JobPlan:
    resolved = resolve(spec)
    validate(resolved)
    trials = expand(resolved)
    return JobPlan(trials=trials, snapshot=freeze(trials))


def _self_check() -> None:
    spec = EvalSpec(
        tasks=(
            TaskInput("sum", "add two numbers"),
            TaskInput("copy", "copy a file"),
        ),
        agents=(
            AgentInput("oracle"),
            AgentInput("null"),
        ),
        n_attempts=2,
    )
    a = compile_eval(spec)
    b = compile_eval(spec)
    assert a == b
    assert len(a.trials) == 2 * 2 * 2
    assert a.trials[0].agent.name == "oracle"
    print(f"trials={len(a.trials)} snapshot={a.snapshot[:12]}…")
    for t in a.trials:
        print(f"  task={t.task.id} agent={t.agent.name}")


if __name__ == "__main__":
    _self_check()
