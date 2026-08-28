# P4 · Evaluation Decision Report
## W8–W11 · 把 leaderboard evidence 转成采用、发布或训练决策

**正式提交次数:1** · **建议投入:10–12 小时** · **截止:W11 结束**

> 你不是来宣布“谁第一”。你要为一个具体决策构建 evidence package，说明结果怎样从 raw attempts 聚合而来、排名有多稳、成本和生产约束如何改变选择，以及 eval 能否安全地成为训练信号。

---

## 一、先选择一个决策

只选一个:

```text
ADOPT   为产品选择一个 Agent / harness
SHIP    判断新版本是否可以发布
TRAIN   判断一个 verifier / environment 是否适合作为 RL signal
```

报告开头写 decision owner、候选方案、最低有意义改进、成本/延迟约束、不可接受风险与截止时间。

## 二、数据最低要求

- 至少 3 个候选 Agent / systems；
- 至少 3 个 benchmarks 或 task families；
- 每个 task 有 repeated attempts，或明确标注单次观察限制；
- success、missing、infra error、cost、tokens、latency；
- benchmark、harness、grader、aggregation 与 index version。

数据可以来自真实 run、课程前面项目或可复现模拟；不得只抄 leaderboard 页面上的最终数字。

## 三、Aggregation pipeline

实现并保存:

```diag
flow | P4 aggregation
Raw attempts
Per-task reduction
Per-benchmark score
Normalization + weights
Composite index
Score / rank uncertainty
Cost-quality-risk decision
```

必须区分 attempt-weighted 与 task-weighted、micro 与 macro、pass@1 与 pass@k / reliability。任何 normalization anchor、clipping 和 missing policy 都要版本化。

## 四、Sensitivity 与 uncertainty

至少完成:

1. paired task comparison 或 matched bootstrap；
2. score intervals；
3. rank uncertainty 或 statistical ties；
4. 1,000 组以上合理 weight vectors 的 rank sensitivity；
5. 去掉一个 benchmark / slice 的 leave-one-component-out analysis；
6. grader 或 failure-policy 变化的 scenario analysis。

不能把 UI 排序当作统计结论。若 A=67.2、B=66.8，而 uncertainty 远大于 0.4pp，报告应显示 tie / inconclusive，而不是强行宣布 A 更强。

## 五、Production utility

至少同时报告:

```text
quality · reliability · cost/task · cost/success
latency · failure recovery · security / policy violations
```

给出 Pareto frontier 或明确的 dominated candidates。最终选择函数必须对应真实 use case，而不是默认 composite score 最大者获胜。

## 六、Eval → RL readiness

如果 decision 是 TRAIN，或报告建议未来用作 RL signal，必须回答:

- reward 是否只是 visible benchmark proxy；
- train / dev / hidden test environment 是否分开；
- scorer 被 policy 优化后会出现什么 reward hacking；
- partial rollout、pause/resume、snapshot 是否改变 trajectory identity；
- independent verifier 是否读取真实 environment state；
- 哪些指标只适合 evaluation，不适合逐步 reward。

结合 Kimi K3 / AgentENV / Harbor case 画出 environment、rollout、trajectory、verifier 在 eval 与 on-policy training 间的共享和边界。

## 七、提交目录与报告

```text
projects/p4-decision-report/
├── decision.md
├── attempts.csv|parquet
├── benchmarks.yaml
├── aggregate.py
├── bootstrap.py
├── sensitivity.py
├── figures/
├── model-system-cards/
└── reproduce.sh
```

`decision.md` 必须包含:

1. 一页 executive decision；
2. raw → index 的完整 lineage；
3. uncertainty 与 sensitivity；
4. cost / latency / reliability / risk；
5. 选中方案与被拒方案；
6. 何种新证据会推翻决定；
7. 若用于训练，明确 eval/RL isolation plan。

## 八、验收 Rubric

| 维度 | 权重 | 满足标准 |
|---|---:|---|
| Metric lineage | 20 | 任意总分可追溯到 raw attempts 与版本化 reduction |
| Uncertainty / sensitivity | 25 | rank、weights、components、grader policy 均被压力测试 |
| Multi-objective utility | 20 | quality、cost、latency、reliability、risk 共同进入决策 |
| Decision quality | 20 | 结论、边界、反事实与推翻条件明确 |
| Eval/RL boundary | 10 | hidden test、reward gaming 与 shared infra 边界清楚 |
| Reproducibility | 5 | 一条命令重建核心表格和图 |

**通过线:80/100；只提交一个排行榜截图或单一 composite score 不能通过。**

## 九、不要求做什么

- 不要求建立公开 leaderboard 网站。
- 不要求模型数量很多；三种有意义的 system configurations 足够。
- 不要求把不确定性伪装成唯一排名。
- W8 aggregation lab、weight sensitivity、W9 production analysis、W10 RL boundary 与 W11 case study 不单独提交。
