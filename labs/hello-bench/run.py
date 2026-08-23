"""Run hello-bench.

    python3 run.py                          # all tasks × all agents, weak verifier
    python3 run.py --strong                 # sum-numbers uses the STRONG verifier
    python3 run.py -t sum-numbers -a cheat  # one cell
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents import CheatAgent, NullAgent, OracleAgent  # noqa: E402
from bench import Result, Task, Verifier, ensure_image, rollout, save  # noqa: E402

ALL_TASKS = ["create-file", "start-server", "sum-numbers"]
ALL_AGENTS = {"oracle": OracleAgent, "null": NullAgent, "cheat": CheatAgent}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--tasks", nargs="+", default=ALL_TASKS)
    ap.add_argument("-a", "--agents", nargs="+", default=list(ALL_AGENTS))
    ap.add_argument("--strong", action="store_true",
                    help="use the strong verifier for sum-numbers (regenerates input)")
    args = ap.parse_args()
    ensure_image()

    results: list[Result] = []
    for tname in args.tasks:
        task = Task.load(tname)
        tf = ("test_outputs_strong.py"
              if args.strong and tname == "sum-numbers" else "test_outputs.py")
        verifier = Verifier(tf)
        for aname in args.agents:
            r = rollout(task, ALL_AGENTS[aname](), verifier)
            results.append(r)
            print(r.row(), flush=True)

    out = Path(__file__).parent / ("results_strong.json" if args.strong else "results.json")
    save(results, out)

    print(f"\n{'':4s}{'task':16s}" + "".join(f"{a:10s}" for a in args.agents))
    for tname in args.tasks:
        row = f"    {tname:16s}"
        for aname in args.agents:
            hit = next((r for r in results if r.task == tname and r.agent == aname), None)
            row += f"{'PASS' if hit and hit.success else 'fail':10s}"
        print(row)
    print(f"\n→ {out.name}")


if __name__ == "__main__":
    main()
