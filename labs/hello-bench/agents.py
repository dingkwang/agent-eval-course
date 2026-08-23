"""Three agents, none of them an LLM — that is the point.

Like Terminal-Bench's oracle, these isolate the *infrastructure* from the model.
CheatAgent additionally probes whether your verifier is actually verifying.
"""

from bench import Agent, Environment, Task


class OracleAgent(Agent):
    """Executes the task author's reference solution. Must always pass.

    It is not "an agent that is very good" — it is a fixed script. If it fails,
    the bug is in your task or your harness, never in a model.
    """
    name = "oracle"

    def perform(self, task: Task, env: Environment) -> list[str]:
        script = (task.path / "solution.sh").read_text()
        code, out = env.exec(script)
        return [f"<solution.sh> exit={code}", out[-300:]]


class NullAgent(Agent):
    """Does nothing. Must always fail.

    A task the null agent passes is a task that measures nothing — either the
    success condition was already true, or setup did the work for you.
    """
    name = "null"

    def perform(self, task: Task, env: Environment) -> list[str]:
        return []


class CheatAgent(Agent):
    """Satisfies the *test* without solving the *task*.

    Defined only where such a shortcut exists. Where it does, the gap between
    the weak and strong verifier is your measurement error. See README §4.
    """
    name = "cheat"

    SHORTCUTS = {
        # the weak verifier only ever checks the answer for one fixed input
        "sum-numbers": "printf 'print(42)\\n' > /workspace/sum.py",
    }

    def perform(self, task: Task, env: Environment) -> list[str]:
        cmd = self.SHORTCUTS.get(task.name)
        if cmd is None:
            return ["<no shortcut known for this task>"]
        code, _ = env.exec(cmd)
        return [f"{cmd} -> exit {code}"]
