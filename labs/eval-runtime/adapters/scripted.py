"""Fixed wrong answer. Execution-equivalence probe (should FAIL verifier)."""

from protocol import AgentCapabilities, AgentRun, EnvironmentLease, Recorder

ANSWER = "/workspace/answer.txt"


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
        await env.write(ANSWER, b"41\n")
        return AgentRun(ok=True, delivered_instruction=instruction)
