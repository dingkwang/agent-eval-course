# P1 · Eval Runtime Teardown

Spec: [`project01-eval-runtime-teardown.md`](../project01-eval-runtime-teardown.md)

Reuse, do not rewrite: [`labs/hello-bench/`](../../labs/hello-bench/), [`labs/eval-runtime/`](../../labs/eval-runtime/).

```text
projects/p1-eval-runtime/
├── source-map.md
├── mini-eval/
├── sample-runs/
└── README.md
```

---

## 1. 怎么从干净环境运行？

Need Python 3 and PyYAML (`task.py` uses `yaml.safe_load`). No Docker, no pytest.

```bash
python3 -m pip install pyyaml
cd projects/p1-eval-runtime/mini-eval
python3 run.py --task sum-numbers --agent oracle --verifier strong
python3 run.py --task sum-numbers --agent null --verifier strong
python3 run.py --task sum-numbers --agent cheat --verifier weak
python3 run.py --task sum-numbers --agent cheat --verifier strong
python3 run.py --task sum-numbers --agent timeout --verifier strong
```

Each command writes `../sample-runs/<agent>-<verifier>/trajectory.jsonl` and `result.json`. The timeout trial waits about 3 seconds (`timeout_sec: 3`). There is no project-local `workspace/` folder to create; `Environment` makes a tempdir per trial and deletes it.

## 2. 一个 task 从哪里被读取？

From `mini-eval/tasks/<id>/task.yaml`. `--task sum-numbers` becomes `tasks/sum-numbers/task.yaml`. `run.py` calls `Task.from_yaml`; `task.py` does `yaml.safe_load` into `id`, `instruction`, `timeout_sec`, `verifier`, `setup`, plus `path` (the task directory, not in the yaml).

`--verifier weak|strong` does not load a second task. It only picks `tests/test_weak.py` vs `tests/test_strong.py` on the same yaml.

## 3. Agent 能看到什么、不能看到什么？

- **Instruction / id:** passed in as the `Task` object to `perform(task, environment)`.
- **Workspace:** `Environment` `mkdtemp`. `env.exec` runs with `cwd` there. For `sum-numbers`, `setup` writes `numbers.txt` (17/11/14) into that directory before the agent runs. `create-file` starts empty.
- **Not in the workspace:** `tasks/<id>/tests/`. Tests are never copied in. The agent's shell cannot see them.
- **Same process caveat:** Agent code could open `task.path / "tests"` in Python. Ours only touch the world through `env.exec`, so the shell view is the isolation.

Verifier reads the **same** workspace after `perform`. Each trial's directory is deleted on exit, so the next agent cannot see the previous files.

## 4. Verifier 实际检查什么状态？

`run_verifier` does not inspect files itself. It runs

```text
[sys.executable, str(path)]   # absolute path to tests/test_*.py
cwd=workspace
```

and treats `returncode == 0` as passed. That is the harness. It is not `python tests/test_xxx.py` from `mini-eval/`, because `cwd` is the temp workspace (no `tests/` there).

What is measured lives in the test scripts, against **final workspace state**, not the agent's return strings:

- `create-file` / `test_result.py`: `result.txt` exists and `strip() == "42"`.
- `sum-numbers` weak: `python3 sum.py` prints `42` on the setup input.
- `sum-numbers` strong: that, then rewrite `numbers.txt` with random ints and require the true sum (hardcoded `print(42)` fails).

## 5. PASS、FAIL、ERROR 分别是什么意思？

- **PASS:** agent finished before the deadline; test process exited 0.
- **FAIL:** agent finished before the deadline; test process exited non-zero. Null is FAIL (`no action`), not ERROR.
- **ERROR:** runtime stopped the trial. Timeout is `environment.exec("sleep 999")` hitting `timeout_sec` → `DeadlineExceeded` → `deadline exceeded`. Not a failed test.

## 6. 五个实验分别证明了什么？

All on `sum-numbers`. Saved under `sample-runs/`:

| experiment | status | proves |
|---|---|---|
| oracle + strong | PASS | task yaml, workspace, Oracle, strong test, TrialResult are wired |
| null + strong | FAIL | setup did not complete the task; empty `perform` is not success |
| cheat + weak | PASS | weak test only checks `42` on the setup input, so `print(42)` is a shortcut |
| cheat + strong | FAIL | regenerated `numbers.txt` catches that shortcut |
| timeout + strong | ERROR | deadline is distinct from test failure; trajectory still written |
