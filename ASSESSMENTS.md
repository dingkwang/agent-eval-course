# Assessment Contract
## 4 个阶段项目 + 1 个 Capstone

这门课只认下面五项为**正式交付物**。讲义里的 `lab`、`exercise`、实验、验收清单和代码检查都是阶段 checkpoint，不单独提交、不单独评分，也不增加作业总数。

> **总数固定为:4 个阶段项目 + 1 个 Capstone。没有独立 quiz 或 written exam。**

| ID | 周次 | 正式交付物 | 合并的 checkpoints | 截止点 |
|---|---|---|---|---|
| **P1** | W1–W2 | [**Eval Runtime Teardown**](projects/project01-eval-runtime-teardown.md):一个可运行的 mini benchmark + 架构说明 | Source Code Map、SWE-bench teardown、τ³ verifier、hello-bench、EvalRT Core | W2 结束 |
| **P2** | W3–W4 | [**Measurement Audit**](projects/project02-measurement-audit.md):一份可重建的统计与 scorer validity 审计报告 | canonical rows、resource curves、coverage simulation、paired comparison、deterministic controls、LLM-judge audit | W4 结束 |
| **P3** | W5–W7 | [**Benchmark Release Candidate**](projects/project03-benchmark-release-candidate.md):一个经过 QA、版本化并带 adversarial controls 的 benchmark RC | blueprint、task-demand audit、sampling QA、failure policy、integrity tests | W7 结束 |
| **P4** | W8–W11 | [**Evaluation Decision Report**](projects/project04-evaluation-decision-report.md):支持一次采用、发布或训练决策的 evidence package | aggregation、weight sensitivity、rank uncertainty、production utility、eval/RL boundary、AgentENV case | W11 结束 |
| **C1** | W12 | [**Permission-Aware Multi-User Agent Benchmark**](projects/capstone-permission-aware-benchmark.md) | 前四个项目中可复用的 runtime、measurement、release 与 decision artifacts | W12 结束 |

## 提交规则

1. **一个阶段只交一次。** 中间 checkpoint 可以存在于同一个目录或报告草稿中，但不产生新的 submission。
2. **后面的项目复用前面的 artifact。** P2 使用 P1 的 TrialResult；P3 复用 P1 runtime 与 P2 measurement contract；C1 复用全部四个项目。
3. **不重复写报告。** lesson lab 只要求产生能进入阶段项目的证据，不再另写总结。
4. **checklist 是自检，不是考试。** 单元测试、verifier regression tests 和 coverage tests 是项目证据，不是面向学生的独立 test。
5. **正式计数只看本页。** 其他文件即使出现 `lab` 或 `exercise`，也不得把总数重新解释成五项以上。

## 每个项目的最小验收

| 项目 | 必须能证明 |
|---|---|
| P1 | task → environment → agent → trajectory → verifier → result 能运行、能追踪、能复现 |
| P2 | estimand、denominator、uncertainty 与 scorer error 对最终结论的影响都被报告 |
| P3 | capability claim、task sampling、admission、versioning 与 integrity controls 形成闭环 |
| P4 | leaderboard 数字能转化成带 uncertainty、cost、risk 与适用边界的决策 |
| C1 | benchmark 同时满足可运行、可复现、可评分、权限正确与统计可解释 |
