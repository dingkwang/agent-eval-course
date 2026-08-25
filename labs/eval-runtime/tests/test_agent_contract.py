"""Agent adapter contracts. Hidden verifier bytes never enter the adapter."""

import asyncio

import pytest

from adapters.hint_injecting import HINT, HintInjectingAdapter
from adapters.null_agent import NullAgent
from adapters.oracle import OracleAgent
from environments.local import LocalEnvironment, PathEscapeError
from protocol import Recorder
from task_sum import SUM_TASK
from trial import instruction_faithful, run_trial


class RaisingAgent(NullAgent):
    name = "raising"

    async def run(self, instruction, env, recorder):
        recorder.delivered_instruction = instruction
        raise RuntimeError("agent crashed")


def test_adapter_receives_exact_instruction() -> None:
    result = asyncio.run(run_trial(OracleAgent(), LocalEnvironment(), SUM_TASK, "t-instr"))
    assert instruction_faithful(result, SUM_TASK)


def test_adapter_never_receives_hidden_files() -> None:
    async def probe() -> None:
        env = LocalEnvironment()
        lease = await env.start(SUM_TASK, "t-hidden")
        try:
            with pytest.raises((FileNotFoundError, PathEscapeError, OSError)):
                await lease.read("/workspace/expected")
            listing = await lease.exec(["ls"])
            assert b"input.txt" in listing.stdout
            assert b"expected" not in listing.stdout
        finally:
            await lease.stop()

    asyncio.run(probe())


def test_null_agent_does_not_change_state() -> None:
    async def probe() -> str:
        env = LocalEnvironment()
        lease = await env.start(SUM_TASK, "t-null")
        before = await lease.snapshot()
        rec = Recorder()
        await NullAgent().run(SUM_TASK.instruction, lease, rec)
        after = await lease.snapshot()
        await lease.stop()
        return before if before == after else "changed"

    assert asyncio.run(probe()) != "changed"


def test_oracle_agent_changes_only_declared_paths() -> None:
    result = asyncio.run(run_trial(OracleAgent(), LocalEnvironment(), SUM_TASK, "t-oracle"))
    assert result.reward == 1.0
    assert result.status == "SUCCEEDED"


def test_hint_injecting_adapter_is_rejected() -> None:
    result = asyncio.run(
        run_trial(HintInjectingAdapter(), LocalEnvironment(), SUM_TASK, "t-hint")
    )
    assert result.reward == 1.0
    assert not instruction_faithful(result, SUM_TASK)
    assert HINT.strip() in (result.recorder.delivered_instruction or "")


def test_agent_error_is_not_normal_completion() -> None:
    result = asyncio.run(run_trial(RaisingAgent(), LocalEnvironment(), SUM_TASK, "t-raise"))
    assert result.status == "AGENT_ERROR"
    assert result.reward is None
    assert result.cleanup
