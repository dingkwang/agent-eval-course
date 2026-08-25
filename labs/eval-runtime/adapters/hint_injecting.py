"""Illegal adapter: appends the answer to the instruction. Must be rejected."""

from adapters.oracle import OracleAgent
from protocol import AgentCapabilities, AgentRun, EnvironmentLease, Recorder

HINT = "\nexpected answer is 42"


class HintInjectingAdapter:
    name = "hint-injecting"
    version = "1.0.0"
    capabilities = AgentCapabilities(supports_os=frozenset({"linux"}))

    def __init__(self) -> None:
        self._inner = OracleAgent()

    async def setup(self, env: EnvironmentLease) -> None:
        await self._inner.setup(env)

    async def run(
        self,
        instruction: str,
        env: EnvironmentLease,
        recorder: Recorder,
    ) -> AgentRun:
        mutated = instruction + HINT
        recorder.delivered_instruction = mutated
        return await self._inner.run(mutated, env, recorder)
