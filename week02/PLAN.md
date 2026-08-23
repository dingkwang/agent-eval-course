# Week 2 — Eval Runtime & Trajectory Engineering
## 5 课,不是 6 课;主源码是 Harbor,不是六个仓库

> **本周唯一命题**
> 不同 benchmark / Agent / backend 必须经过**同一个** runtime;
> trajectory 是可重放的事件日志,不是聊天记录。

本周产出:**一张 Harbor vs Inspect 对照表**,加上 `labs/eval-runtime/`
(3 tasks × 3 agents × 2 environments × 2 trials)。不是一叠论文笔记。

日历:`PLAN.md` 写每周 5 天 × ~1 小时。W1 开成 6 天是因为六个标本 + DIY。
W2 是**一条**故事,第五天后半做 lab。第六课只会把「本周不要读」的东西塞进来。

核心阅读 6–8 小时。其余只在写讲义时查阅。

---

## 固定 commit(不要漂)

```
Harbor     harbor-framework/harbor@b37833221e27435a18d7acdd41d875cdc2831893
Inspect    UKGovernmentBEIS/inspect_ai@499e6152e7b8fc8cbd8ac5283536572aa6e4ab17
Gymnasium  Farama-Foundation/Gymnasium@3f0476a8cc224dcce2167cc4b6971ae0f04d5cfc
BrowserGym ServiceNow/BrowserGym@9e779f087de9a65668b6974d11f9ce9816026e96
τ³         本仓库 code/tau2-bench/(v1.0.1,c339866)
```

---

## 五天

每课一个能当标题的命题。读任何材料只答三问:

```
1. 它定义了哪些 abstraction?
2. 每个 abstraction 的生命周期和状态是什么?
3. 拿掉它会出现什么具体错误?
```

| Day | 讲义(未写) | 本课唯一命题 | 学生读 | 不读 |
|---|---|---|---|---|
| **1** | `lesson01-trial-not-task.md` | Harbor 的单位是 **Trial,不是 Task**。Task ≠ Trial ≠ Job;Agent ≠ Model;Environment 是接口,不是 Docker 类 | [Core Concepts](https://www.harborframework.com/docs/core-concepts) 只读概念 | 任何 `.py` |
| **2** | `lesson02-job-expands.md` | **Job 展开成 Trial**;AgentAdapter 的输出**不是 reward**。`JobConfig → Task×Agent×Model×Attempt → TrialConfig[] → TrialQueue`。nop / oracle 是测 runtime 的 | `models/trial/config.py` · `job_plan.py` · `job.py` · `agents/base.py` · `nop.py` · `oracle.py` | CLI、UI、`agents/installed/*` |
| **3** | `lesson03-env-lifecycle.md` | Environment **先声明 capability**;Trial 有明确生命周期。identity ≠ content hash。SingleStep / MultiStep / SimulatedUser | `environments/base.py`(只抽 API) · `trial/trial.py`(只追生命周期,不通读) · `single_step.py` · `multi_step.py` · `models/trial/result.py` | 各 backend、queue / retry |
| **4** | `lesson04-atif.md` | **Trajectory ≠ stdout**;Trial 必须装得下 Agent↔User。session ≠ trajectory;message ≠ tool_call ≠ observation;step ≠ LLM call | ATIF RFC(Introduction + Root metadata + Step / ToolCall / Observation / FinalMetrics + subagent/continuation 的**理由**)。重读 `../code/tau2-bench/src/tau2/orchestrator/orchestrator.py`,只看编排,不看 verifier。选读 RFC 0002、`simulated_user.py` | τ³ evaluator;ATIF 全文 600+ 行 |
| **5** | `lesson05-inspect-gym-lab.md` | Inspect 的 `Task = Dataset+Solver+Scorer` **不是** Harbor 的 `Trial = Task×Agent×Environment`。Gym `step()` 不是容器生命周期。BrowserGym 证明 runtime 不能只适配 terminal。**后半:lab** | Inspect 教程 + `task.py` / `run.py` / `_task_state.py` / `_solver.py`(不读 scorer/sandbox)。Gymnasium `core.py`。BrowserGym `env.py` **一个文件**。论文:BrowserGym、AgentBench、Gymnasium interface(不背分数)。选读 τ²-bench(只编排)、Unified Framework(**当质疑材料,不当规范**) | Inspect scorer/sandbox;Harbor Reward Kit / 云 backend / viewer |

### Day 5 lab 形状

```
labs/eval-runtime/
├── models.py
├── runner.py
├── recorder.py
├── adapters/{oracle,shell_agent,function_agent}.py
├── environments/{local,docker}.py
└── schemas/{task,trial,trajectory,result}.py
```

矩阵:`3 Tasks × 3 Agents × 2 Environments × 2 Trials` → `job.json`
(configs、trajectories、artifacts、termination、reward、duration/tokens/cost、reproducibility metadata)。

---

## 本周不要读(后移)

| 内容 | 放到 |
|---|---|
| Harbor adapters 与 parity experiment | W5 |
| metrics、pass@k、aggregation | W3 / W8 |
| queue、retry、regrade、artifact failure | W6 |
| network policy、verifier isolation | W7 |
| Reward Kit、training workflows | W10 |
| 所有云 environment backend | W11 |
| Viewer 前端;几十种 installed agents | 非必修 / 最多一个实例 |

尤其不要通读:`src/harbor/environments/*` · `src/harbor/agents/installed/*` · `adapters/*` · `apps/viewer/*`。

---

## 阅读清单(学生自检)

```
必读文档
[ ] Harbor Core Concepts
[ ] Inspect Introduction / Tutorial
[ ] Gymnasium Env API

必读 Harbor 源码
[ ] models/trial/config.py
[ ] job_plan.py + job.py
[ ] agents/base.py + nop.py + oracle.py
[ ] environments/base.py
[ ] trial/trial.py + single_step.py + multi_step.py
[ ] RFC 0001 ATIF(指定章节,不是全文)

对照源码
[ ] Inspect Task / TaskState / Solver
[ ] Gymnasium core.py
[ ] BrowserGym env.py
[ ] τ³ orchestrator.py

论文
[ ] BrowserGym (arXiv:2412.05467)
[ ] AgentBench (arXiv:2308.03688)
[ ] Gymnasium interface (arXiv:2407.17032)
[ ] τ²-bench(选读,arXiv:2506.07982,只编排)
[ ] Unified Framework(选读,arXiv:2605.27898,当质疑)
```

讲义尚未写。先按这张表读;写课是下一件事。
