```text
Terminal-Bench:  /home/dingkwang/sci/terminal-bench @ f50d4be3
Harbor runtime:  /home/dingkwang/sci/llm-rl-course/code/harbor @ 0f0a5b6
SWE-bench Pro:   /home/dingkwang/sci/agent-eval-homework/SWE-bench_Pro-os @ ca10a60
Concrete TB task: tasks/bun-sourcemap-leak
Concrete Pro task: instance_NodeBB__NodeBB-04998908ba6721d64eba79ae3b65a351dcfbc5b5-vnan
```

### 1. task 定义在哪里

* **Terminal-Bench:** 完整 task 是整个目录 `tasks/<name>/`，不是单份 instruction。
  * `task.toml` — 超时、CPU/内存、`[verifier].environment_mode`
  * `instruction.md` — 给 Agent 的题面
  * `environment/` — 镜像配方（Dockerfile）
  * `tests/` — verifier 脚本
  * 例子：`tasks/bun-sourcemap-leak/`

* **SWE-bench Pro:** `helper_code/sweap_eval_full_v2.jsonl`（731 行，每行一个 task）；官方源头还有 HuggingFace `ScaleAI/SWE-bench_Pro`。

| 字段 | 作用 |
|---|---|
| `instance_id` | 任务 id（如 `instance_NodeBB__NodeBB-...`） |
| `repo` / `repo_name` | 目标仓库；容器内路径通常 `/app` |
| `base_commit` | Agent 起始 commit |
| `problem_statement` | 给 Agent 的 issue 描述 |
| `hints_text` | 可选提示 |
| `patch` | 官方 gold patch |
| `test_patch` | 评测用测试补丁 |
| `FAIL_TO_PASS` | 必须由失败变为通过的测试 |
| `PASS_TO_PASS` | 必须保持通过的测试 |
| `selected_test_files_to_run` | 要跑的测试文件 |

---

### 2. environment 怎么启动

* **Terminal-Bench:**
  * 配方：`tasks/<name>/environment/Dockerfile`
  * 真正 `docker compose build/up`：Harbor `src/harbor/environments/docker/docker.py` → `DockerEnvironment.start()`（约 L832：`compose up --detach --wait`）
  * 工作区挂到容器 `/app`。`scripts/runs/launch.sh` 只调用 `harbor run`，不是启动环境。

* **SWE-bench Pro:** 同一套预构建镜像 `jefzda/sweap-images:<tag>`，两个入口：
  * 出 patch：SWE-agent / mini-swe-agent 起容器，`/app` checkout 到 `base_commit`
  * 打分：`swe_bench_pro_eval.py` 的 `eval_with_docker()` / `eval_with_modal()`

---

### 3. Agent 从哪里接收 instruction

* **Terminal-Bench（Harbor 注入，Agent 不自己读文件）：**
  1. `src/harbor/models/task/task.py`：读 `instruction.md`，`strip_canary()` 去掉 `# harbor-canary GUID ...`，可再拼 `extra_instruction_paths`
  2. `src/harbor/trial/single_step.py` `_run_agent()` → `trial.py` `_run_agent_phase()` → `self.agent.run(instruction=..., environment=..., context=...)`
  3. 所有 Harbor Agent 实现 `BaseAgent.run(instruction, environment, context)`（`agents/base.py`）

* **SWE-bench Pro:** `helper_code/create_problem_statement.py` 把 `problem_statement` + `requirements` + `interface` 拼成 prompt；`generate_sweagent_instances.py` 交给 SWE-agent。

---

### 4. rollout loop 在哪里

* **Terminal-Bench:** 不在题库仓库。当前 `terminal-bench` 没有 `terminal_bench/harness/`。循环在 Harbor：

```text
SingleStepTrial._run()
  → _run_agent()
  → Trial._run_agent_phase()
  → BaseAgent.run(instruction, environment, context)
  → 具体 Agent 自己的 loop
       Terminus 2: terminus_2._run_agent_loop
       Claude Code / ACP: exec --instruction=...
```

* **SWE-bench Pro:** `SWE-agent/` 或 `mini-swe-agent/` 的 step loop：观察终端 → bash/编辑 → 直到提交 `.pred` patch。官方默认不是 Harbor。

---

### 5. verifier 检查什么状态

* **Terminal-Bench:** 测的是最终世界状态（通常 `/app`），不是 Agent 说了什么。
  * 题库入口：`tasks/<name>/tests/test.sh`
  * 调度：Harbor `SingleStepTrial._run_verifier()` → `Verifier.verify()`
  * shared：同一容器里 `upload /tests` 再 `exec test.sh`
  * separate（如 `bun-sourcemap-leak`）：`tests/Dockerfile` 另起容器，只拷 `task.toml` 声明的 artifacts，跑镜像内 `/tests/test.sh`
  * Harbor 不解析 pytest，只认 `/logs/verifier/reward.txt` 或 `reward.json`

* **SWE-bench Pro:** `run_scripts/<instance_id>/run_script.sh` 跑测试，`parser.py` 解析输出；`FAIL_TO_PASS` 须全过，`PASS_TO_PASS` 无回归。

---

### 6. 最终 result 从哪里产生

* **Terminal-Bench:**
  * 容器：`/logs/verifier/reward.txt` 或 `reward.json`
  * host：`trials/<trial>/verifier/reward.txt` + `trials/<trial>/result.json`（Harbor `TrialPaths`）

* **SWE-bench Pro:** `swe_bench_pro_eval.py` 写出
  * 每条：`{output_dir}/{uid}/{prefix}_output.json`（从容器 `/workspace/output.json` 拷出）
  * 汇总：`{output_dir}/eval_results.json`，形如 `{instance_id: true/false}`
