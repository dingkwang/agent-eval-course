"""Scripted agents. Oracle solves the task; cheat solves the weak test."""

from environment import Environment


class Agent:
    name = "base"

    def perform(self, task, environment: Environment) -> list[str]:
        raise NotImplementedError


class OracleAgent(Agent):
    name = "oracle"

    def perform(self, task, environment: Environment) -> list[str]:
        if task.id == "create-file":
            environment.exec("printf '42\\n' > result.txt")
            return ["wrote result.txt"]
        if task.id == "sum-numbers":
            environment.exec(
                "cat > sum.py << 'PY'\n"
                "from pathlib import Path\n"
                "print(sum(int(x) for x in Path('numbers.txt').read_text().split()))\n"
                "PY"
            )
            return ["wrote sum.py that reads numbers.txt"]
        raise NotImplementedError(task.id)


class NullAgent(Agent):
    name = "null"

    def perform(self, task, environment: Environment) -> list[str]:
        return []


class CheatAgent(Agent):
    name = "cheat"

    def perform(self, task, environment: Environment) -> list[str]:
        if task.id == "sum-numbers":
            environment.exec("printf '%s\\n' 'print(42)' > sum.py")
            return ["hardcoded print(42)"]
        return []


class TimeoutAgent(Agent):
    name = "timeout"

    def perform(self, task, environment: Environment) -> list[str]:
        environment.exec("sleep 999")
        return []


AGENTS = {
    "oracle": OracleAgent,
    "null": NullAgent,
    "cheat": CheatAgent,
    "timeout": TimeoutAgent,
}
