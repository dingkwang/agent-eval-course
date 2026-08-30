"""P1 mini-eval.

    python run.py --task sum-numbers --agent oracle --verifier strong
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import agents
from environment import DeadlineExceeded, Environment
from task import Task

HERE = Path(__file__).parent
TASKS = HERE / "tasks"
ROOT = HERE.parent
AGENT_NAMES = ("oracle", "null", "cheat", "timeout")
VERIFIERS = ("weak", "strong")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="P1 mini-eval")
    ap.add_argument("--task", required=True, help="directory name under tasks/")
    ap.add_argument("--agent", required=True, choices=AGENT_NAMES)
    ap.add_argument("--verifier", required=True, choices=VERIFIERS)
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="directory for trajectory.jsonl + result.json",
    )
    return ap.parse_args(argv)


def test_file(task: Task, strength: str) -> Path:
    if strength == "strong":
        strong = task.path / "tests" / "test_strong.py"
        if strong.exists():
            return strong
    named = task.path / task.verifier
    if named.exists():
        return named
    return task.path / "tests" / "test_weak.py"


def run_verifier(path: Path, workspace: Path, timeout_sec: float) -> dict:
    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=timeout_sec + 5,
    )
    passed = proc.returncode == 0
    return {
        "passed": passed,
        "tests_total": 1,
        "tests_failed": 0 if passed else 1,
        "output": ((proc.stdout or "") + (proc.stderr or ""))[-1500:],
    }


def run_trial(task: Task, agent_name: str, verifier: str, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    agent = agents.AGENTS[agent_name]()
    events: list[dict] = []
    status = "ERROR"
    failure_reason: str | None = "internal"
    tests_total = 0
    tests_failed = 0
    notes: list[str] = []
    t0 = time.time()

    with Environment(timeout_sec=task.timeout_sec) as env:
        events.append(
            {
                "type": "trial_started",
                "task_id": task.id,
                "agent": agent_name,
                "verifier": verifier,
            }
        )
        try:
            if task.setup:
                env.exec(task.setup)
            notes = agent.perform(task, env) or []
            events.extend(env.log)
            for note in notes:
                events.append({"type": "note", "value": note})
            verdict = run_verifier(test_file(task, verifier), env.path, task.timeout_sec)
            tests_total = verdict["tests_total"]
            tests_failed = verdict["tests_failed"]
            events.append(
                {
                    "type": "verifier_result",
                    "passed": verdict["passed"],
                    "output": verdict["output"],
                }
            )
            if verdict["passed"]:
                status = "PASS"
                failure_reason = None
            else:
                status = "FAIL"
                failure_reason = "no action" if not notes else "tests failed"
        except DeadlineExceeded as exc:
            events.extend(env.log)
            status = "ERROR"
            failure_reason = "deadline exceeded"
            events.append({"type": "error", "value": str(exc)})
        except Exception as exc:
            events.extend(env.log)
            status = "ERROR"
            failure_reason = f"agent_error: {exc}"
            events.append({"type": "error", "value": str(exc)})
        events.append({"type": "trial_finished", "status": status})

    result = {
        "task_id": task.id,
        "agent": agent_name,
        "status": status,
        "tests_total": tests_total,
        "tests_failed": tests_failed,
        "duration_sec": round(time.time() - t0, 3),
        "failure_reason": failure_reason,
        "trajectory": "trajectory.jsonl",
    }
    (out_dir / "trajectory.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in events)
    )
    (out_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    args = parse_args()
    task_dir = TASKS / args.task
    loaded = Task.from_yaml(task_dir / "task.yaml")
    out = args.out or (ROOT / "sample-runs" / f"{args.agent}-{args.verifier}")
    result = run_trial(loaded, args.agent, args.verifier, out)
    reason = result["failure_reason"] or "expected state reached"
    print(
        f"{result['agent']:<10s} {args.verifier:<10s} {result['status']:<7s} {reason}"
    )
    print(f"-> {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
