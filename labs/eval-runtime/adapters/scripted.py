"""Deterministic exec probes. Relative path so Local cwd and Docker -w agree."""

from protocol import AgentCapabilities, AgentRun, EnvironmentLease, Recorder

VALID_CMD = "printf '42\\n' > answer.txt"
INVALID_CMD = "printf '41\\n' > answer.txt"


class ScriptedValidAgent:
    name = "scripted-valid"
    version = "1.0.0"
    capabilities = AgentCapabilities(supports_os=frozenset({"linux"}))

    async def setup(self, env: EnvironmentLease) -> None:
        return None

    async def run(
        self,
        instruction: str,
        env: EnvironmentLease,
        recorder: Recorder,
    ) -> AgentRun:
        recorder.delivered_instruction = instruction
        await env.exec(["sh", "-c", VALID_CMD])
        return AgentRun(ok=True, delivered_instruction=instruction)


class ScriptedInvalidAgent:
    name = "scripted-invalid"
    version = "1.0.0"
    capabilities = AgentCapabilities(supports_os=frozenset({"linux"}))

    async def setup(self, env: EnvironmentLease) -> None:
        return None

    async def run(
        self,
        instruction: str,
        env: EnvironmentLease,
        recorder: Recorder,
    ) -> AgentRun:
        recorder.delivered_instruction = instruction
        await env.exec(["sh", "-c", INVALID_CMD])
        return AgentRun(ok=True, delivered_instruction=instruction)
