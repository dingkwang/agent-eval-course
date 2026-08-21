"""Dissect one SWE-bench instance: what the agent sees vs what the grader sees.

Stage 1 of the teardown — no Docker required.
Run:  python3 labs/swe-bench-teardown/teardown.py [instance_id]
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT = "astropy__astropy-13398"
DATASET = "princeton-nlp/SWE-bench_Verified"

# Fields the agent is allowed to see. Everything else is grader-only.
AGENT_VISIBLE = {"instance_id", "repo", "base_commit", "problem_statement", "version"}
GRADER_ONLY = {"patch", "test_patch", "FAIL_TO_PASS", "PASS_TO_PASS", "environment_setup_commit"}


def fetch(instance_id: str) -> dict:
    cached = HERE / f"{instance_id}.json"
    if cached.exists():
        print(f"(cached) {cached.name}")
        return json.loads(cached.read_text())
    url = (
        "https://datasets-server.huggingface.co/filter"
        f"?dataset={DATASET.replace('/', '%2F')}&config=default&split=test"
        f"&where=%22instance_id%22%3D%27{instance_id}%27"
    )
    row = json.load(urllib.request.urlopen(url, timeout=60))["rows"][0]["row"]
    cached.write_text(json.dumps(row, indent=1))
    print(f"fetched → {cached.name}")
    return row


def files_in(patch: str) -> list[str]:
    return re.findall(r"diff --git a/(\S+)", patch)


def main() -> None:
    iid = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    x = fetch(iid)

    print(f"\n{'=' * 72}\nINSTANCE  {iid}\n{'=' * 72}")

    print("\n── ① AGENT SEES ──────────────────────────────────────────")
    for k in sorted(AGENT_VISIBLE & x.keys()):
        v = str(x[k])
        print(f"  {k:24s} {v[:60] + '…' if len(v) > 60 else v}")
    print(f"  {'(problem_statement)':24s} {len(x['problem_statement']):,} chars")

    print("\n── ② GRADER ONLY (agent must never see) ──────────────────")
    print(f"  {'patch (gold)':24s} {len(x['patch']):,} B, {len(files_in(x['patch']))} files")
    for f in files_in(x["patch"]):
        print(f"  {'':26s}{f}")
    print(f"  {'test_patch':24s} {len(x['test_patch']):,} B, {len(files_in(x['test_patch']))} files")
    for f in files_in(x["test_patch"]):
        print(f"  {'':26s}{f}")
    f2p, p2p = json.loads(x["FAIL_TO_PASS"]), json.loads(x["PASS_TO_PASS"])
    print(f"  {'FAIL_TO_PASS':24s} {len(f2p)}  (改完必须由失败转通过)")
    for t in f2p:
        print(f"  {'':26s}{t}")
    print(f"  {'PASS_TO_PASS':24s} {len(p2p)}  (本来就过,不许弄坏)")
    print(f"  {'environment_setup_commit':24s} {x['environment_setup_commit'][:12]}…  ← 装依赖用的 commit,与 base_commit 不同")

    print("\n── ③ 判分契约 ────────────────────────────────────────────")
    print(f"  resolved = 全部 {len(f2p)} 个 FAIL_TO_PASS 通过  AND  全部 {len(p2p)} 个 PASS_TO_PASS 仍通过")
    print(f"           = {len(f2p) + len(p2p)} 个断言全绿")

    # Four prediction files, each probing a different harness outcome.
    #
    # NOTE (a real mistake worth keeping): the first attempt at "broken" was
    #   x["patch"].replace("+", "-", 1)
    # That hits the `+++ b/...` *header*, not the code — git apply tolerated it
    # and the instance still RESOLVED. Corrupting a diff is harder than it looks;
    # to make a patch fail you must change what it does, not how it is spelled.
    first_file = x["patch"].split("\ndiff --git ")[0]  # only the __init__.py hunk
    preds = {
        "gold": x["patch"],                 # → resolved
        "empty": "",                        # → counted as "empty patch", NOT unresolved
        "partial": first_file,              # → applies, but breaks the import → unresolved
        "malformed": "diff --git a/nope.py b/nope.py\n@@ -1 +1 @@\n-x\n+y\n",  # → cannot apply
    }
    for name, patch in preds.items():
        out = HERE / f"preds_{name}.jsonl"
        out.write_text(json.dumps({
            "instance_id": iid,
            "model_name_or_path": f"teardown-{name}",
            "model_patch": patch,
        }) + "\n")
    print("\n── ④ 生成三份 prediction ─────────────────────────────────")
    for name in preds:
        p = HERE / f"preds_{name}.jsonl"
        print(f"  {p.name:22s} {p.stat().st_size:>7,} B   ({name})")

    print("\n下一步:bash labs/swe-bench-teardown/run.sh gold")


if __name__ == "__main__":
    main()
