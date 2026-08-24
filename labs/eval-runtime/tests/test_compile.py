"""Plan-compiler invariants. Run from repo root:

    python3 -m pytest labs/eval-runtime/tests/test_compile.py
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from compile import AgentInput, EvalSpec, TaskInput, compile_eval, expand, resolve, validate


def _spec(
    *,
    tasks: tuple[TaskInput, ...] | None = None,
    agents: tuple[AgentInput, ...] | None = None,
    n_attempts: int = 1,
) -> EvalSpec:
    if tasks is None:
        tasks = (
            TaskInput("sum", "add two numbers"),
            TaskInput("copy", "copy a file"),
        )
    if agents is None:
        agents = (
            AgentInput("oracle", model="none", prompt="solve"),
            AgentInput("null", model="none", prompt="skip"),
        )
    return EvalSpec(tasks=tasks, agents=agents, n_attempts=n_attempts)


def test_same_spec_same_semantic_digest() -> None:
    a = compile_eval(_spec())
    b = compile_eval(_spec())
    assert a.snapshot == b.snapshot
    assert a.trials == b.trials


def test_agent_order_does_not_change_semantic_digest() -> None:
    forward = compile_eval(_spec())
    backward = compile_eval(_spec(
        agents=(
            AgentInput("null", model="none", prompt="skip"),
            AgentInput("oracle", model="none", prompt="solve"),
        ),
    ))
    assert forward.snapshot == backward.snapshot
    assert [t.agent.name for t in forward.trials] == ["oracle", "null", "oracle", "null"]
    assert [t.agent.name for t in backward.trials] == ["null", "oracle", "null", "oracle"]


def test_prompt_change_changes_digest() -> None:
    base = compile_eval(_spec())
    changed = compile_eval(_spec(
        agents=(
            AgentInput("oracle", model="none", prompt="solve differently"),
            AgentInput("null", model="none", prompt="skip"),
        ),
    ))
    assert base.snapshot != changed.snapshot


def test_task_content_change_changes_digest() -> None:
    base = compile_eval(_spec())
    changed = compile_eval(_spec(
        tasks=(
            TaskInput("sum", "add two numbers, extra clause"),
            TaskInput("copy", "copy a file"),
        ),
    ))
    assert base.snapshot != changed.snapshot


def test_attempts_change_multiplicity() -> None:
    once = compile_eval(_spec(n_attempts=1))
    twice = compile_eval(_spec(n_attempts=2))
    assert len(once.trials) == 4
    assert len(twice.trials) == 8
    assert once.snapshot != twice.snapshot


def test_empty_tasks_or_agents_rejected() -> None:
    with pytest.raises(ValueError, match="tasks"):
        compile_eval(_spec(tasks=()))
    with pytest.raises(ValueError, match="agents"):
        compile_eval(_spec(agents=()))
    resolved = resolve(_spec(n_attempts=0))
    with pytest.raises(ValueError, match="n_attempts"):
        validate(resolved)


def test_empty_agent_name_materializes_oracle() -> None:
    plan = compile_eval(_spec(agents=(AgentInput(None, prompt="x"),)))
    assert all(t.agent.name == "oracle" for t in plan.trials)


def test_expand_order_matches_harbor() -> None:
    resolved = resolve(_spec(n_attempts=2))
    trials = expand(resolved)
    assert [t.agent.name for t in trials[:2]] == ["oracle", "null"]
    assert trials[0].task.id == "sum"
