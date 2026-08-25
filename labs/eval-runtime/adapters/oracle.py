"""Positive control: privileged payload, not a leaderboard SUT.

Harbor OracleAgent.__init__ takes task_dir and uploads the reference
solution. This lab constructor takes the hidden bytes instead — the
answer does not come from /workspace.
"""

from protocol import AgentCapabilities, AgentRun, EnvironmentLease, Recorder

ANSWER = "/workspace/answer.txt"


class OracleAgent:
    name = "oracle"
    version = "1.0.0"
    capabilities = AgentCapabilities(supports_os=frozenset({"linux"}))

    def __init__(self, solution: bytes) -> None:
        self._solution = solution

    async def setup(self, env: EnvironmentLease) -> None:
        return None

    async def run(
        self,
        instruction: str,
        env: EnvironmentLease,
        recorder: Recorder,
    ) -> AgentRun:
        recorder.delivered_instruction = instruction
        await env.write(ANSWER, self._solution)
        return AgentRun(ok=True, delivered_instruction=instruction)
