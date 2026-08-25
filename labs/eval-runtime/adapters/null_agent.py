"""Negative control: no side effects. Harbor NopAgent analogue."""

from protocol import AgentCapabilities, AgentRun, EnvironmentLease, Recorder


class NullAgent:
    name = "null"
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
        return AgentRun(ok=True, delivered_instruction=instruction)
