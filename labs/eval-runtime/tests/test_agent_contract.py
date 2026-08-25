"""Agent adapter contracts. Hidden verifier bytes never enter the adapter."""

import asyncio

import pytest

from adapters.hint_injecting import HINT, HintInjectingAdapter
from adapters.null_agent import NullAgent
from adapters.oracle import OracleAgent
from adapters.scripted import ScriptedValidAgent
from environments.local import LocalEnvironment, PathEscapeError
from protocol import AgentCapabilities, Recorder, TaskBundle
from task_sum import SUM_TASK, oracle
from trial import instruction_faithful, run_trial


class RaisingAgent(NullAgent):
    name = "raising"

    async def run(self, instruction, env, recorder):
        recorder.delivered_instruction = instruction
        raise RuntimeError("agent crashed")


class WindowsOnlyAgent(NullAgent):
    name = "windows-only"
    capabilities = AgentCapabilities(supports_os=frozenset({"windows"}))


def test_adapter_receives_exact_instruction() -> None:
    result = asyncio.run(run_trial(oracle(), LocalEnvironment(), SUM_TASK, "t-instr"))
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
    async def probe() -> tuple[bytes, bytes]:
        env = LocalEnvironment()
        lease = await env.start(SUM_TASK, "t-oracle-paths")
        before = (await lease.exec(["ls"])).stdout
        rec = Recorder()
        await oracle().run(SUM_TASK.instruction, lease, rec)
        after = (await lease.exec(["ls"])).stdout
        await lease.stop()
        return before, after

    before, after = asyncio.run(probe())
    assert b"input.txt" in before
    assert b"answer.txt" not in before
    assert b"answer.txt" in after


def test_oracle_does_not_need_input_file_contents() -> None:
    """Same constructor payload, wrong fixture: still PASS. That is the privilege."""
    mutated = TaskBundle(
        task_id=SUM_TASK.task_id,
        instruction=SUM_TASK.instruction,
        fixtures={"/workspace/input.txt": b"0 0\n"},
        hidden=SUM_TASK.hidden,
    )
    result = asyncio.run(
        run_trial(OracleAgent(mutated.hidden["expected"]), LocalEnvironment(), mutated, "t-priv")
    )
    assert result.reward == 1.0
    assert result.status == "SUCCEEDED"


def test_hint_injecting_adapter_is_rejected_even_if_reward_is_one() -> None:
    result = asyncio.run(
        run_trial(HintInjectingAdapter(), LocalEnvironment(), SUM_TASK, "t-hint")
    )
    assert result.reward == 1.0
    assert result.status == "ADAPTER_VIOLATION"
    assert not instruction_faithful(result, SUM_TASK)
    assert HINT.strip() in (result.recorder.delivered_instruction or "")


def test_scripted_valid_passes_via_exec() -> None:
    result = asyncio.run(
        run_trial(ScriptedValidAgent(), LocalEnvironment(), SUM_TASK, "t-sv")
    )
    assert result.reward == 1.0
    assert result.status == "SUCCEEDED"


def test_agent_error_is_not_normal_completion() -> None:
    result = asyncio.run(run_trial(RaisingAgent(), LocalEnvironment(), SUM_TASK, "t-raise"))
    assert result.status == "AGENT_ERROR"
    assert result.reward is None
    assert result.cleanup


def test_unsupported_os_is_rejected_before_run() -> None:
    result = asyncio.run(
        run_trial(WindowsOnlyAgent(), LocalEnvironment(), SUM_TASK, "t-win")
    )
    assert result.status == "UNSUPPORTED"
    assert result.reward is None
    assert result.cleanup
    assert "AGENT_RUN" not in result.recorder.events
