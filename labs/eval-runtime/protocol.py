"""Canonical Agent / Environment / Trial contracts for the Week 2 Day 2 lab.

Not a Harbor import. Semantics follow Harbor @b378332 BaseAgent / BaseEnvironment
and Inspect @499e615 SandboxEnvironment.exec as the contrast, not a copy.
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class TaskBundle:
    task_id: str
    instruction: str
    fixtures: dict[str, bytes]
    hidden: dict[str, bytes]


@dataclass(frozen=True, slots=True)
class AgentCapabilities:
    supports_os: frozenset[str]
    supports_resume: bool = False


@dataclass(frozen=True, slots=True)
class EnvironmentCapabilities:
    isolation: str
    os: str = "linux"
    fail_fast_unsupported: bool = True


@dataclass
class ExecResult:
    return_code: int
    stdout: bytes
    stderr: bytes


@dataclass
class AgentRun:
    ok: bool
    delivered_instruction: str
    notes: str = ""


@dataclass
class Recorder:
    events: list[str] = field(default_factory=list)
    delivered_instruction: str | None = None

    def event(self, name: str) -> None:
        self.events.append(name)


@dataclass
class TrialResult:
    status: str
    reward: float | None
    owner_id: str
    cleanup: bool
    recorder: Recorder
    original_error: str | None = None
    cleanup_error: str | None = None
    final_digest: str | None = None


@runtime_checkable
class EnvironmentLease(Protocol):
    owner_id: str
    stopped: bool

    async def exec(
        self,
        argv: list[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecResult: ...

    async def read(self, path: str) -> bytes: ...

    async def write(self, path: str, data: bytes) -> None: ...

    async def snapshot(self) -> str: ...

    async def stop(self) -> None: ...


@runtime_checkable
class EnvironmentBackend(Protocol):
    capabilities: EnvironmentCapabilities

    async def start(self, task: TaskBundle, owner_id: str) -> EnvironmentLease: ...


@runtime_checkable
class AgentAdapter(Protocol):
    name: str
    version: str
    capabilities: AgentCapabilities

    async def setup(self, env: EnvironmentLease) -> None: ...

    async def run(
        self,
        instruction: str,
        env: EnvironmentLease,
        recorder: Recorder,
    ) -> AgentRun: ...
