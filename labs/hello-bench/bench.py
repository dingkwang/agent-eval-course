"""hello-bench — the smallest agent benchmark that actually runs.

Five abstractions, one file:

    Task  →  Environment  →  Agent  →  Verifier  →  Result

Deliberately simple. The point is to have written each one yourself, so the
abstractions in Terminal-Bench / SWE-bench / Harbor stop looking like magic.

Trust boundary (this is the whole lesson of Day 3, made concrete):
the agent's containers mount ONLY the workspace; the verifier's container also
mounts `tasks/<name>/tests` at /verifier. The agent never has a path to the
tests. Enforced by which `-v` flags each `docker run` gets — see Environment.run.
"""

import json
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).parent
TASKS_DIR = HERE / "tasks"
IMAGE = "hello-bench:py312"


# ── ① Task ────────────────────────────────────────────────────────────────
@dataclass
class Task:
    name: str
    instruction: str
    path: Path
    setup: str = ""          # shell run in the workspace before the agent starts

    @classmethod
    def load(cls, name: str) -> "Task":
        d = TASKS_DIR / name
        spec: dict[str, str] = {}
        key, buf = "", []
        for line in (d / "task.yaml").read_text().splitlines():
            if line.lstrip().startswith("#"):
                continue
            if line and not line[0].isspace() and ":" in line:      # top-level key
                if key:
                    spec[key] = "\n".join(buf).strip()
                key, rest = line.split(":", 1)
                key, rest = key.strip(), rest.strip()
                buf = [] if rest in ("|", "|-") else [rest]
            elif key:
                buf.append(line.strip())
        if key:
            spec[key] = "\n".join(buf).strip()
        return cls(name=name, instruction=spec["instruction"], path=d,
                   setup=spec.get("setup", ""))


# ── ② Environment ─────────────────────────────────────────────────────────
class Environment:
    """A host directory mounted into throwaway containers at /workspace.

    File state persists across calls; process state does not. That is a real
    design choice with a real consequence — see tasks/start-server/task.yaml.
    """

    def __init__(self) -> None:
        self.state = Path(tempfile.mkdtemp(prefix="hb-"))

    def __enter__(self) -> "Environment":
        return self

    def __exit__(self, *_exc) -> None:
        shutil.rmtree(self.state, ignore_errors=True)

    def run(self, command: str, mounts: dict[Path, str] | None = None,
            timeout: int = 300) -> tuple[int, str]:
        import os
        argv = ["docker", "run", "--rm",
                "--user", f"{os.getuid()}:{os.getgid()}",
                "-v", f"{self.state}:/workspace", "-w", "/workspace"]
        for src, dst in (mounts or {}).items():
            argv += ["-v", f"{src}:{dst}:ro"]           # verifier mounts are read-only
        argv += [IMAGE, "bash", "-lc", command]
        try:
            r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return 124, "<timeout>"
        return r.returncode, (r.stdout + r.stderr)

    # convenience for agents
    def exec(self, command: str, timeout: int = 300) -> tuple[int, str]:
        return self.run(command, timeout=timeout)


# ── ③ Agent ───────────────────────────────────────────────────────────────
class Agent:
    """Contract: given an instruction and a live environment, do the work."""
    name = "base"

    def perform(self, task: Task, env: Environment) -> list[str]:
        raise NotImplementedError


# ── ④ Verifier ────────────────────────────────────────────────────────────
@dataclass
class Verdict:
    passed: bool
    total: int
    failed: int
    output: str


class Verifier:
    """Runs hidden pytest in a container the agent never had access to."""

    def __init__(self, test_file: str = "test_outputs.py") -> None:
        self.test_file = test_file

    def run(self, task: Task, env: Environment) -> Verdict:
        code, out = env.run(
            f"python3 -m pytest -q -p no:cacheprovider /verifier/{self.test_file}",
            mounts={task.path / "tests": "/verifier"},
        )
        failed = int(m.group(1)) if (m := re.search(r"(\d+) failed", out)) else 0
        passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", out)) else 0
        return Verdict(passed=(code == 0 and failed == 0 and passed > 0),
                       total=passed + failed, failed=failed, output=out[-1500:])


# ── ⑤ Result ──────────────────────────────────────────────────────────────
@dataclass
class Result:
    task: str
    agent: str
    success: bool
    trajectory: list[str] = field(default_factory=list)
    duration: float = 0.0
    tests_total: int = 0
    tests_failed: int = 0
    failure_mode: str = ""      # "" | agent_error | no_action | tests_failed
    verifier_output: str = ""

    def row(self) -> str:
        mark = "PASS" if self.success else "FAIL"
        extra = f"  [{self.failure_mode}]" if self.failure_mode else ""
        return (f"{mark}  {self.task:14s} {self.agent:8s} "
                f"{self.tests_total - self.tests_failed}/{self.tests_total} tests "
                f"{self.duration:5.1f}s{extra}")


# ── the rollout ───────────────────────────────────────────────────────────
def rollout(task: Task, agent: Agent, verifier: Verifier) -> Result:
    t0, traj, mode = time.time(), [], ""
    with Environment() as env:
        if task.setup:
            env.exec(task.setup)
        try:
            traj = agent.perform(task, env)
        except Exception as e:
            mode, traj = "agent_error", [f"<exception> {e}"]
        if not traj and not mode:
            mode = "no_action"
        v = verifier.run(task, env)
    if not v.passed and not mode:
        mode = "tests_failed"
    return Result(task=task.name, agent=agent.name, success=v.passed, trajectory=traj,
                  duration=time.time() - t0, tests_total=v.total, tests_failed=v.failed,
                  failure_mode="" if v.passed else mode, verifier_output=v.output)


def ensure_image() -> None:
    if subprocess.run(["docker", "image", "inspect", IMAGE],
                      capture_output=True).returncode != 0:
        print(f"building {IMAGE} …", flush=True)
        subprocess.run(["docker", "build", "-q", "-t", IMAGE, str(HERE)], check=True)


def save(results: list[Result], path: Path) -> None:
    path.write_text(json.dumps([r.__dict__ for r in results], indent=1, default=str))
