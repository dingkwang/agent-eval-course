# P3 · Benchmark Release Candidate
## W5–W7 · 从 capability claim 到 versioned、adversarially-tested RC

**正式提交次数:1** · **建议投入:14–16 小时** · **截止:W7 结束**

> 你要发布的不是“一批难题”，而是一套能支持特定决策的 measurement product。P3 要证明 task sample、success criteria、运行政策与 integrity controls 足以支撑预先声明的 capability claim。

---

## 一、最终问题

```text
为什么这些 tasks、在这些测试条件和 verifier 下产生的结果，
可以支持这个 capability claim；
哪些 inference 明确不被支持；
benchmark 在什么条件下必须 fix、quarantine、retire 或升版本？
```

```diag
flow | P3 release pipeline
Intended decision → capability construct
Target task distribution → candidate sampling
Task bundle audit → pilot + perturbations
Failure semantics → integrity controls
Immutable manifest → versioned release candidate
```

## 二、Scope

选择一个边界清楚的 agent capability，例如 repository bug fixing、terminal incident response、research brief production 或 permission-aware tool use。

最低规模:

- 10–20 个 candidate tasks；
- 至少 8 个进入 release candidate；
- 至少两个 task families / slices；
- 每个 task 都有可运行环境、success evidence 与 lineage；
- 至少一个真实失败模式来自现有 benchmark、产品 trace 或公开 incident。

小而可审计优于大而来历不明。

## 三、Benchmark blueprint

提交一页 validity argument，明确:

| 字段 | 必须回答 |
|---|---|
| Intended use | 谁用分数做什么决定 |
| Object | model、Agent system 还是 product |
| Construct | 目标能力的行为定义 |
| Target population | 希望推广到哪些 tasks / users / environments |
| Adaptation | tools、budget、context、harness 条件 |
| Evidence warrant | 什么 observation 支持什么 claim |
| Exclusions | 哪些外推明确不成立 |

## 四、Task admission audit

每个 candidate 必须有:

1. success path；
2. target / realistic co-demand / nuisance decomposition；
3. information ledger；
4. oracle 或 expert feasibility evidence；
5. alternate-valid solution/path；
6. semantic-preserving surface mutation；
7. suspected missing-information clarification；
8. `KEEP / FIX / QUARANTINE / REJECT` decision。

QA sampling 必须同时包含:

- 自动或规则筛查 flag 的 tasks；
- 从未被 flag 的 tasks 中随机抽样。

只审查自动系统挑出的可疑题会漏掉 false negatives，不能估计整个 release 的 defect risk。

## 五、Pilot 与 failure policy

Pilot 至少包含 weak、mid、frontier/strong 三档 Agent 或等价 scripted controls。低 pass rate 本身不能决定删除 task。

冻结以下政策:

```yaml
statuses: [success, task_failure, agent_error, infra_error, timeout, unscorable]
denominator_policy: ...
retry_policy: ...
quarantine_policy: ...
resource_limits: ...
```

至少做一次资源、timeout 或依赖变化实验，证明 infra 条件是否会改变 task outcome。

## 六、Integrity 与 adversarial controls

最低覆盖:

| 攻击面 | 必须有的 control |
|---|---|
| Hidden tests / gold leakage | Agent-visible 文件与 grader evidence 的边界检查 |
| Verifier tampering | grader / tests 在独立或可还原环境执行 |
| Network lookup | 明确网络政策并测试违规行为 |
| Credentials / tenants | fake secrets + unauthorized principal case |
| Tool-output injection | 至少一个恶意 observation |
| Reward hacking | 一个不完成目标但尝试拿分的 Agent |
| Contamination | task lineage、公开时间与 canary / overlap policy |

最终同时报告 task success 与 security violation；不能让“完成任务但泄漏 secret”进入普通 success。

## 七、提交目录

```text
projects/p3-benchmark-rc/
├── BENCHMARK_CARD.md
├── blueprint.md
├── manifest.yaml
├── tasks/
├── verifiers/
├── audits/
│   ├── admission.csv
│   ├── random-unflagged-review.csv
│   └── perturbations.md
├── integrity/
├── pilot-results/
├── CHANGELOG.md
└── reproduce.sh
```

Manifest 必须固定 task digests、environment image / dependencies、Agent adaptation、budget、scorer、aggregation 与 benchmark version。

## 八、验收 Rubric

| 维度 | 权重 | 满足标准 |
|---|---:|---|
| Validity argument | 20 | intended decision 到 evidence warrant 的链条完整 |
| Sampling and coverage | 20 | target distribution、slices、holes 与 audit sampling 可解释 |
| Task admission | 20 | information closure、alternate-valid path 与 perturbation 有证据 |
| Operations and versioning | 15 | failure、retry、quarantine、manifest、changelog 可执行 |
| Integrity | 20 | leakage、tampering、credential、injection、gaming controls 能运行 |
| Reproducibility | 5 | candidate 到 RC 可重建 |

**通过线:80/100；存在未处理的 unauthorized disclosure 或 grader tampering 时不得 release。**

## 九、不要求做什么

- 不要求追求 leaderboard 规模或模型覆盖数量。
- 不要求每道题都“极难”；任务应覆盖目标分布与诊断需求。
- 不把符合 packaging standard 等同于 construct-valid。
- W5 blueprint、task audit、W6 failure experiment 与 W7 integrity lab 不单独提交。
