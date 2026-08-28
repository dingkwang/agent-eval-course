# P2 · Measurement Audit
## W3–W4 · 一份报告同时审计统计结论与 scorer validity

**正式提交次数:1** · **建议投入:10–12 小时** · **截止:W4 结束**

> 你收到 A、B 两个 Agent 的 TrialResult，以及一个声称能判断成功或作品质量的 scorer。任务是回答:观测到的差异有多大、不确定性多大，以及 scorer 的错误是否足以改变发布决定。

---

## 一、最终问题

```text
在预先声明的 task population、attempt policy、budget 与 scorer version 下，
A 相对 B 的效应是否达到最小有意义差异，
且该结论在 scorer error、UNKNOWN、judge bias 与合理分析选择下是否仍成立？
```

P2 不允许把统计正确与测量正确分开交两份报告。最终结论必须同时穿过两道门:

```diag
flow | P2 release gate
Canonical TrialResult rows
Estimand + denominator contract
Paired estimate + uncertainty + MDE
Reference labels + scorer controls
Decision robustness → SHIP / HOLD / RERUN
```

## 二、输入

可以使用 P1 产生的数据或课程提供的固定 dataset。最低数据结构:

```text
experiment_id · benchmark_version · task_id · agent_id
attempt_id · seed/config · status · score · cost · latency
scorer_version · trajectory_ref · evidence_ref
```

至少包含:

- 40 个以上相同 tasks 上的 A/B paired outcomes；
- 每 task 至少 2 次 attempts，或明确解释为什么只有一次；
- success、task failure、infra failure、UNKNOWN / unscorable 的区分；
- 一个 deterministic verifier 或一个 LLM judge 的审计对象。

## 三、统计分析要求

### 3.1 冻结 estimand

先写清 object of evaluation、target task population、attempt policy、selector、denominator 与 reduction rule。不能看到结果后再在 pass@1、pass@k、micro、macro 之间挑最好看的。

### 3.2 必报结果

| 输出 | 最低要求 |
|---|---|
| Per-task table | 保留 task pairing 与 missingness |
| Point estimate | A、B 及 paired difference $\hat\Delta$ |
| Interval | 与抽样结构匹配的 CI / uncertainty interval |
| Reliability curve | pass@1 / pass@k / pass^k 或等价 resource curve |
| Decision threshold | 预先声明最小有意义差异 $\delta^*$ |
| Sensitivity | missing / UNKNOWN / infra failure 的至少两种合理政策 |
| Cost | 每 task 与每成功 task 的 cost / latency |

至少运行一次 coverage simulation，让一个错误 CI 方法在已知 data-generating process 下暴露失败。

## 四、Scorer audit 要求

先写 measurement contract:

```text
product event → observable evidence → reference label → scorer output → error policy
```

### Deterministic verifier 路线

必须覆盖 shortcut、alternate-valid path、content corruption、missing evidence 与 UNKNOWN。至少一个 case 要证明“确定性”仍可能稳定地判错。

### LLM judge 路线

必须明确目标 audience / reference population，并运行:

- A/B position swap；
- model identity blind；
- length-preserving 或 filler mutation；
- content corruption；
- repeat consistency；
- 与小型 human reference set 的 agreement。

开放式作品要分开 hard constraints、fidelity、craft 与 audience preference；不能用 style proxy 直接证明总体质量提升。

## 五、最终报告结构

```text
projects/p2-measurement-audit/
├── README.md
├── data-contract.md
├── canonical-results.parquet|csv
├── analysis/
├── scorer-controls/
├── figures/
├── measurement-audit.md
└── reproduce.sh
```

`measurement-audit.md` 必须按以下顺序:

1. Claim 与 decision；
2. Experimental unit、estimand 与 denominator；
3. Point estimate、paired uncertainty、MDE 与 cost；
4. Scorer reference process 与 error matrix；
5. Controls 失败在哪里；
6. 结论对 scorer error 是否稳健；
7. `SHIP / HOLD / RERUN` 以及下一步需要什么证据。

## 六、验收 Rubric

| 维度 | 权重 | 满足标准 |
|---|---:|---|
| Estimand and data contract | 20 | observation grain、population、denominator 与 selector 无歧义 |
| Statistical inference | 25 | paired structure、CI、MDE、missingness 与 sensitivity 正确 |
| Scorer validation | 25 | reference labels、error types 与 counterfactual controls 完整 |
| Decision integration | 20 | scorer error 被传播到发布结论，而非另附一张表 |
| Reproducibility | 10 | 一条命令重建主要表格和图 |

**通过线:80/100，且不能缺 paired estimate、reference labels 或 scorer controls。**

## 七、不要求做什么

- 不要求上 hierarchical Bayesian model；简单方法只要与 estimand 匹配即可。
- 不要求把所有指标压成一个总分。
- 不要求宣称 human label 是脱离人群和场景的 literary truth。
- 不另交 W3 Statistical Report 或 W4 Judge Lab；它们就是 P2 的组成部分。
