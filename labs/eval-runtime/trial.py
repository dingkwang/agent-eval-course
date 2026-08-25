"""Explicit Trial lifecycle. Harbor analogue of trial.py run/prepare/finalize."""

import asyncio

from protocol import (
    AgentAdapter,
    AgentRun,
    EnvironmentBackend,
    EnvironmentLease,
    Recorder,
    TaskBundle,
    TrialResult,
)

ANSWER = "/workspace/answer.txt"

FAULTS = frozenset({
    "environment_start",
    "agent_setup",
    "agent_run",
    "artifact_collect",
    "verifier",
    "environment_stop",
    "cancelled",
})


class InjectedFault(RuntimeError):
    pass


class UnsupportedCapability(RuntimeError):
    pass


async def verify(lease: EnvironmentLease, task: TaskBundle) -> float:
    expected = task.hidden["expected"]
    try:
        got = await lease.read(ANSWER)
    except FileNotFoundError:
        return 0.0
    return 1.0 if got == expected else 0.0


def instruction_matches(recorder: Recorder, task: TaskBundle) -> bool:
    return recorder.delivered_instruction == task.instruction


def instruction_faithful(result: TrialResult, task: TaskBundle) -> bool:
    return instruction_matches(result.recorder, task)


async def run_trial(
    adapter: AgentAdapter,
    backend: EnvironmentBackend,
    task: TaskBundle,
    owner_id: str,
    fault_at: str | None = None,
) -> TrialResult:
    if fault_at is not None and fault_at not in FAULTS:
        raise ValueError(f"unknown fault_at={fault_at}")
    recorder = Recorder()
    lease: EnvironmentLease | None = None
    reward: float | None = None
    digest: str | None = None
    original: str | None = None
    cleanup_error: str | None = None
    status = "FAILED"
    ran_cleanup = False

    try:
        recorder.event("START")
        if fault_at == "environment_start":
            raise InjectedFault("environment_start")
        lease = await backend.start(task, owner_id)
        assert lease is not None
        recorder.event("ENVIRONMENT_START")

        if backend.capabilities.os not in adapter.capabilities.supports_os:
            raise UnsupportedCapability(
                f"os={backend.capabilities.os} not in {sorted(adapter.capabilities.supports_os)}"
            )

        if fault_at == "agent_setup":
            raise InjectedFault("agent_setup")
        await adapter.setup(lease)
        recorder.event("AGENT_SETUP")

        if fault_at == "cancelled":
            raise asyncio.CancelledError()
        if fault_at == "agent_run":
            raise InjectedFault("agent_run")
        run: AgentRun = await adapter.run(task.instruction, lease, recorder)
        recorder.delivered_instruction = run.delivered_instruction
        recorder.event("AGENT_RUN")

        if fault_at == "artifact_collect":
            raise InjectedFault("artifact_collect")
        digest = await lease.snapshot()
        recorder.event("COLLECT")

        if fault_at == "verifier":
            raise InjectedFault("verifier")
        reward = await verify(lease, task)
        recorder.event("VERIFY")
        if not instruction_matches(recorder, task):
            status = "ADAPTER_VIOLATION"
            recorder.event("ADAPTER_VIOLATION")
        else:
            status = "SUCCEEDED" if reward == 1.0 else "FAILED"
    except InjectedFault as exc:
        original = str(exc)
        status = {
            "environment_start": "ENVIRONMENT_ERROR",
            "agent_setup": "AGENT_SETUP_ERROR",
            "agent_run": "AGENT_ERROR",
            "artifact_collect": "AGENT_ERROR",
            "verifier": "VERIFIER_ERROR",
            "environment_stop": "FAILED",
        }[str(exc)]
        recorder.event(status)
    except UnsupportedCapability as exc:
        original = str(exc)
        status = "UNSUPPORTED"
        recorder.event("UNSUPPORTED")
    except asyncio.CancelledError:
        original = "cancelled"
        status = "CANCELLED"
        recorder.event("CANCELLED")
    except Exception as exc:
        original = f"{type(exc).__name__}: {exc}"
        status = "AGENT_ERROR"
        recorder.event(status)
    finally:
        if fault_at == "environment_stop" and original is None:
            original = "environment_stop"
            status = "CLEANUP_ERROR"
            recorder.event(status)
        if lease is not None:
            try:
                await lease.stop()
                ran_cleanup = True
                recorder.event("END")
            except Exception as exc:
                cleanup_error = f"{type(exc).__name__}: {exc}"
                ran_cleanup = False

    if recorder.delivered_instruction is None:
        recorder.delivered_instruction = task.instruction

    return TrialResult(
        status=status,
        reward=reward,
        owner_id=owner_id,
        cleanup=ran_cleanup or lease is None,
        recorder=recorder,
        original_error=original,
        cleanup_error=cleanup_error,
        final_digest=digest,
    )
