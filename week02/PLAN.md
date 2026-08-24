# Week 2 — Eval Runtime & Trajectory Engineering
## 4 节深课 + 1 个综合 Lab

> **本周唯一命题**
> 不同 benchmark / Agent / backend 必须经过**同一个** runtime;
> trajectory 是可重放的事件日志,不是聊天记录。

Harbor 贯穿四节。Inspect 是对照。Gymnasium / BrowserGym / τ³ 只当接口参考。
**Agent ≠ Model 是第 1 课开头 10 分钟,不是单独一课。**

产出:一张对照表 + `labs/eval-runtime/`(EvalRT Core)。不是论文笔记。

---

## 固定 commit

```
Harbor     harbor-framework/harbor@b37833221e27435a18d7acdd41d875cdc2831893
Inspect    UKGovernmentBEIS/inspect_ai@499e6152e7b8fc8cbd8ac5283536572aa6e4ab17
Gymnasium  Farama-Foundation/Gymnasium@3f0476a8cc224dcce2167cc4b6971ae0f04d5cfc
BrowserGym ServiceNow/BrowserGym@9e779f087de9a65668b6974d11f9ce9816026e96
τ³         本仓库 code/tau2-bench/
```

---

## 四节 + Lab

每课解决**一个**系统问题。读材料只答三问:定义了哪些 abstraction / 生命周期是什么 / 拿掉它会出现什么具体错误。

| Day | 讲义 | 核心问题 | 当天 Lab |
|---|---|---|---|
| **1** | `lesson01-eval-spec-to-trial.md` | 分数解释的是哪一个实验对象?编译后锁死的 Trial,还是 YAML 里的 model 名? | `compile_eval(spec) -> JobPlan` |
| **2** | `lesson02-protocol-boundary.md` | 换 Agent 或 backend 后,怎样证明仍在执行同一个任务? | Null / Oracle / LLM adapter + Local / Docker env + conformance + 生命周期注入异常 |
| **3** | `lesson03-trajectory-causality.md` | 工具已改环境、Agent 没收到 response 时,trajectory 怎么记?能不能安全重试? | canonical events + causal validation / tamper / replay |
| **4** | `lesson04-concurrency.md` | 100 个 Trial 并发时,并发只提高吞吐、不改变实验语义? | hanging agent、rate limit、crash、Ctrl-C |
| **5** | `lesson05-evalrt-lab.md` | 把前四节拼成 EvalRT Core | 五个强不变量 |

### 第 1 课 · 从 Eval Spec 到可执行 Trial

可解释单位是编译后锁死的 Trial(`Task × Agent × Attempt`),不是 Task,也不是 model 名。10 分钟前置:Agent ≠ Model。然后:SUT 边界;乘积公式;身份字段进 lock 不进相等;Harbor vs Inspect 执行模型。

源码:Harbor `job_plan.py` · `models/trial/config.py` · `job.py`;Inspect `Task` / sample planning。不读 CLI/UI。

### 第 2 课 · Agent、Environment 与 Runtime 的协议边界

Adapter 是否改变 Agent 看到的信息;canonical observation/action;capability negotiation;`setup/reset/step/teardown`;Trial 状态机;resource ownership;verifier 与 Agent 的环境边界;cancellation-safe cleanup。

源码:Harbor `agents/base.py` + `nop.py` + `oracle.py`;`environments/base.py`(只抽 API);`trial/trial.py` 生命周期,不通读。不读 `environments/*` backends、`agents/installed/*`。

### 第 3 课 · Trajectory、因果关系与副作用(本周最重)

trajectory 不能只是 messages;tool call / effect / observation;correlation;commit point;response 丢失后的 ambiguous outcome;idempotency key;parent/subagent;compaction 如何记录;replay / offline rescoring / audit;ATIF schema evolution。

源码:ATIF RFC(Introduction + metadata + Step/ToolCall/Observation/FinalMetrics + subagent/continuation **理由**,不是 600 行全文)。τ³ `orchestrator.py` 只看编排。选读 RFC 0002。不读 τ³ verifier。

事件 schema(lab):

```
ModelRequest · ModelResponse
ToolRequested · ToolCommitted · ToolObserved
EnvironmentChanged · TrialTerminated · VerifierCompleted
```

### 第 4 课 · 并发执行与 Runtime Correctness

structured concurrency;bounded pool;backpressure;resource lease;timeout 与 cancellation;partial result;event ordering;teardown under cancellation;differential testing;fault injection。

**不进** retry policy、resume、失败分母 → W6。不进 network policy / verifier isolation → W7。

### 第 5 天 · EvalRT Core

```
EvalSpec → Immutable JobPlan → Concurrent Trial Executor
  (AgentAdapter · EnvironmentBackend · Trial SM · Event Recorder)
  → Trajectory + TrialResult
```

五个强不变量(只验这些):

1. 同一 config 产生相同的 resolved plan
2. Adapter 不增加或丢失 task information
3. 每个 observation 都能追溯到 action 和 environment effect
4. 成功 / 异常 / 超时 / 取消都有 terminal result
5. 并发不改变相互隔离任务的语义

```
labs/eval-runtime/
  compile.py          # L1
  adapters/           # L2
  environments/       # L2
  events.py           # L3
  executor.py         # L4
  run.py              # L5
```

---

## 本周不要读

| 内容 | 放到 |
|---|---|
| Harbor adapters / parity | W5 |
| metrics、pass@k、aggregation | W3 / W8 |
| queue、retry、regrade、artifact failure | W6 |
| network policy、verifier isolation | W7 |
| Reward Kit、training workflows | W10 |
| 云 environment backend | W11 |
| Viewer;几十种 installed agents | 非必修 |

尤其不要通读:`src/harbor/environments/*` · `agents/installed/*` · `adapters/*` · `apps/viewer/*`。
