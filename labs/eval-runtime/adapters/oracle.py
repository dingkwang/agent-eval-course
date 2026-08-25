"""Positive control: compute the sum from the fixture. Not a leaderboard SUT."""

from protocol import AgentCapabilities, AgentRun, EnvironmentLease, Recorder

INPUT = "/workspace/input.txt"
ANSWER = "/workspace/answer.txt"


class OracleAgent:
    name = "oracle"
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
        raw = await env.read(INPUT)
        a, b = raw.decode().split()
        await env.write(ANSWER, f"{int(a) + int(b)}\n".encode())
        return AgentRun(ok=True, delivered_instruction=instruction)
