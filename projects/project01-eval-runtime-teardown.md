# P1 · Eval Runtime Teardown
## W1–W2 · 从 benchmark 源码地图到可审计的 mini runtime

**正式提交次数:1** · **建议投入:10–12 小时** · **截止:W2 结束**

> 你接手了一套只会输出 leaderboard score 的 eval。你的任务不是再包一层 CLI，而是证明一条 observation 怎样从 task 被可靠地产生，并交付一个别人可以运行、追踪和审计的最小实现。

---

## 一、最终问题

交付物必须让 reviewer 能回答:

```text
给定同一份 resolved evaluation spec，
不同 Agent / backend 是否执行了同一个实验，
每次 action、environment effect、observation 与 result 是否可追溯，
异常、超时和取消是否仍会留下可解释的 terminal result？
```

```diag
flow | P1 的证据链
Benchmark source map
Resolved EvalSpec → immutable JobPlan
AgentAdapter ↔ EnvironmentBackend
Trajectory events → Verifier → TrialResult
Oracle / Null / Cheat / Fault controls
```

## 二、必须复用的课程 checkpoints

这些不是五份作业，只是 P1 的中间证据:

| 来源 | 进入 P1 的内容 |
|---|---|
| W1 Source Code Map | 一个真实 benchmark 的 task、runner、environment、verifier、result 源码路径 |
| SWE-bench teardown | gold / empty / malformed / partial prediction 的 harness 行为 |
| τ³ verifier teardown | trajectory、mutable state、reward basis 与 verifier failure |
| hello-bench | Task → Environment → Agent → Verifier → Result 的最小可运行实现 |
| W2 EvalRT Core | resolved plan、protocol boundary、causal events、terminal semantics、bounded execution |

## 三、实现范围

至少实现以下接口。名字可以改变，语义不能缺失。

```python
compile_eval(spec) -> JobPlan
run_trial(plan, agent, environment) -> TrialResult
verify(trial_evidence) -> ScoreResult
```

`JobPlan` 必须物化默认值、task version、Agent config、environment config、budget、attempt identity 与 scorer version。不能把墙钟时间或随机 job name 当作实验语义。

Trajectory 至少区分:

```text
ModelRequest · ModelResponse
ToolRequested · ToolCommitted · ToolObserved
EnvironmentChanged · TrialTerminated · VerifierCompleted
```

若 tool 已产生副作用但 response 丢失，日志必须表达 ambiguous outcome；不能悄悄重试并伪造一条干净轨迹。

## 四、必须运行的 controls

| Control | 预期 | 若不满足说明什么 |
|---|---|---|
| Oracle Agent | 满足可解任务 | task、setup、runtime 或 verifier 可能坏了 |
| Null Agent | 不应凭空成功 | setup 或 success condition 替 Agent 完成了任务 |
| Cheat / shortcut Agent | 被强 verifier 拒绝 | verifier 可能只测表面 proxy |
| HintInjecting Adapter | conformance test 必须失败 | adapter 改变了实验信息条件 |
| Timeout / crash | 有 terminal result 和 cleanup evidence | failure semantics 不完整 |
| 同 task 并发两次 | state 互不污染 | isolation 或 resource ownership 有问题 |

至少加入一个 fault-injection case，并保存预期与实际事件序列。

## 五、提交目录

```text
projects/p1-eval-runtime/
├── README.md
├── source-map.md
├── eval_spec.yaml
├── runtime/
├── tasks/
├── controls/
├── tests/
├── sample-runs/
│   ├── trajectory.jsonl
│   └── trial_result.json
└── design-decisions.md
```

`README.md` 必须给出一条从干净环境开始的运行命令。`design-decisions.md` 只记录会改变实验语义的决定，不写开发日记。

## 六、演示场景

现场或录屏演示同一 task 的四次运行:

1. Oracle 成功；
2. Null 失败；
3. Cheat 在弱 verifier 下成功、在强 verifier 下失败；
4. Agent 在产生副作用后超时，runtime 仍输出可解释的 terminal result。

Reviewer 应能从 `TrialResult` 反查完整 trajectory、resolved plan 与 verifier evidence。

## 七、验收 Rubric

| 维度 | 权重 | 满足标准 |
|---|---:|---|
| Source understanding | 15 | 源码地图能指到真实 entrypoint 与 observable state，不是概念图 |
| Experimental identity | 20 | resolved plan、version 与 attempt identity 可重建 |
| Protocol correctness | 20 | adapter 不增删 task information，environment lifecycle 明确 |
| Trajectory / failure semantics | 25 | effect、observation、termination、异常与 cleanup 可追溯 |
| Controls and reproducibility | 20 | 六类 controls 有自动化结果，干净环境可复跑 |

**通过线:80/100，且 Oracle / Null / HintInjecting / isolation 四项不能缺失。**

## 八、不要求做什么

- 不要求接入真实付费 LLM；Scripted Agent 足够证明 runtime correctness。
- 不要求实现分布式 queue、断点恢复或复杂 retry policy；这些属于 W6。
- 不要求实现 cgroups、seccomp 或完整云 sandbox。
- 不用重复提交每个 lesson lab；所有证据只进入这一份 P1。
