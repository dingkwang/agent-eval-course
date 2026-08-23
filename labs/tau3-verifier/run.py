"""Load airline task id=3 and score four hand-written trajectories.

No API key, no Docker. Calls the real CommunicateEvaluator, ActionEvaluator,
and EnvironmentEvaluator classmethods.

    cd code/tau2-bench && uv sync
    uv run --project code/tau2-bench python labs/tau3-verifier/run.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from loguru import logger

logger.remove()  # tau2 logs registry init; the table is the artifact

from tau2.data_model.tasks import RewardType, Task
from tau2.evaluator.evaluator_action import ActionEvaluator
from tau2.evaluator.evaluator_communicate import CommunicateEvaluator
from tau2.evaluator.evaluator_env import EnvironmentEvaluator
from tau2.registry import registry

from trajectories import TRAJECTORIES, cheat

REPO = Path(__file__).resolve().parents[2]
TASKS_JSON = (
    REPO / "code" / "tau2-bench" / "data" / "tau2" / "domains" / "airline" / "tasks.json"
)
TASK_ID = "3"
COLS = ("COMMUNICATE", "ACTION", "DB", "DB*COMM")


def load_task(task_id: str = TASK_ID) -> Task:
    raw = json.loads(TASKS_JSON.read_text())
    for item in raw:
        if item["id"] == task_id:
            return Task.model_validate(item)
    raise SystemExit(f"task id={task_id!r} not in {TASKS_JSON.relative_to(REPO)}")


def _fmt(value: float | None) -> str:
    if value is None:
        return "SKIP"
    return f"{value:.1f}"


def _comm_justification(info) -> str:
    checks = info.communicate_checks or []
    if not checks:
        return info.info.get("note", "") if info.info else ""
    return " | ".join(
        f"{c.info!r} met={c.met}: {c.justification.replace('\n', ' ').strip()}"
        for c in checks
    )


def _action_summary(info) -> str:
    checks = info.action_checks or []
    if not checks:
        note = (info.info or {}).get("note", "")
        return note or "(no action_checks)"
    return " | ".join(
        f"{c.action.name} match={c.action_match}" for c in checks
    )


def score_one(task: Task, messages: list) -> dict[str, float | None]:
    comm = CommunicateEvaluator.calculate_reward(task, messages)
    action = ActionEvaluator.calculate_reward(task, messages)
    db: float | None
    try:
        env = EnvironmentEvaluator.calculate_reward(
            environment_constructor=registry.get_env_constructor("airline"),
            task=task,
            full_trajectory=messages,
            solo_mode=False,
        )
        db = env.reward_breakdown.get(RewardType.DB) if env.reward_breakdown else env.reward
    except Exception as exc:
        print(f"  EnvironmentEvaluator raised: {type(exc).__name__}: {exc}", file=sys.stderr)
        db = None
    basis = None if db is None else db * comm.reward
    return {
        "COMMUNICATE": comm.reward,
        "ACTION": action.reward,
        "DB": db,
        "DB*COMM": basis,
        "_comm": comm,
        "_action": action,
    }


def print_table(rows: list[tuple[str, dict]]) -> None:
    name_w = max(len("traj"), max(len(n) for n, _ in rows))
    col_w = 12
    header = f"{'traj':{name_w}s}" + "".join(f"{c:>{col_w}s}" for c in COLS)
    print(header)
    print("-" * len(header))
    for name, scores in rows:
        line = f"{name:{name_w}s}"
        for c in COLS:
            line += f"{_fmt(scores[c]):>{col_w}s}"
        print(line)


def main() -> None:
    task = load_task(TASK_ID)
    criteria = task.evaluation_criteria
    print(f"task id={task.id}")
    print(f"  communicate_info = {criteria.communicate_info}")
    print(f"  reward_basis     = {[x.value for x in criteria.reward_basis]}")
    print(
        "  actions          = "
        + ", ".join(a.get_func_format() for a in (criteria.actions or []))
    )
    print(f"  tasks.json       = {TASKS_JSON.relative_to(REPO)}")
    print()

    rows: list[tuple[str, dict]] = []
    for name, traj in TRAJECTORIES.items():
        scores = score_one(task, traj)
        rows.append((name, scores))

    print_table(rows)

    print()
    print("communicate checks")
    for name, scores in rows:
        print(f"  {name:8s} {_comm_justification(scores['_comm'])}")
    print("action checks  (NOT in this task's reward_basis)")
    for name, scores in rows:
        print(f"  {name:8s} {_action_summary(scores['_action'])}")

    cheat_scores = next(s for n, s in rows if n == "cheat")
    mutated = [
        cheat[0],
        cheat[1].model_copy(update={"content": "your flight is AA-1235"}),
    ]
    mutated_comm = CommunicateEvaluator.calculate_reward(task, mutated)
    print()
    print(
        "sanity: cheat utterance AA-1234 -> AA-1235  "
        f"COMMUNICATE {_fmt(cheat_scores['COMMUNICATE'])} -> {_fmt(mutated_comm.reward)}"
    )


if __name__ == "__main__":
    main()
