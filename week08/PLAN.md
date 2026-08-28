# Week 8 — From Rollouts to Leaderboards

> **Assessment policy**:本周的 aggregation 与 sensitivity labs 都进入 [P4 Evaluation Decision Report](../ASSESSMENTS.md)。W8 不新增独立作业；P4 在 W11 结束时统一提交。

**一个个 task 的结果,最后是怎样变成「Claude 63、GPT 61」这种排行榜数字的?**

> 这一周**不学 benchmark 怎么运行**(W1–W2 已学)。研究后半条 pipeline:

```
raw attempts → per-task score → per-benchmark score → normalization
→ cross-benchmark aggregation → index → ranking → leaderboard
```

**主 case study**:Artificial Analysis —— 它恰好把很多真实世界的问题放在同一个 leaderboard 里。
**本周位置**:前面学「怎么产生一个 task result」,这周学「怎么把成千上万个 result 压成一个数字」,W9 再问「这个数字跟真实产品表现有什么关系」。

---

## Day 1 · 从 raw rollout 到 benchmark score

> 1000 次 agent rollout,最后那个「72.4」到底是怎么算出来的?

**三个聚合层级**。设 100 tasks × 3 runs = 300 rollouts:
```
task_id  run  success
A        1      1
A        2      0
A        3      1
```
```
① Task A = (1+0+1)/3 = 0.667
② Benchmark score = mean(task scores)      ← 每道 task 等权
```
AA Coding Agent Index 正是这个口径:每 task 跑 3 次 → **先在 task 内平均,再在所有 task 上平均**。

**必须区分**:
```
attempt-weighted  vs  task-weighted
micro average     vs  macro average
pass@1  vs  pass@k  vs  pass^k / reliability
```
> 陷阱:task1 跑 10 次、task2 跑 1 次,直接平均所有 rollout → task1 拿到 10 倍权重。
> **benchmark aggregation 本身就是一个 estimator design 问题。**

**Lab** `labs/leaderboard/aggregate_attempts.py`:输入 `model,task,attempt,success` CSV,输出 per-task score / benchmark score / valid attempts。

---

## Day 2 · 从 benchmark score 到 Composite Index(本周最重要)

```
Terminal-Bench 70 · SWE 60 · GPQA 85 · HLE 40 · GDPval ???   →   Index = 63
```

### ① Normalization
原始 metric 甚至不同尺度:pass rate(0–100)· accuracy(0–100)· **Elo**。不能直接 `mean([70, 85, 1050])`。

AA 的 GDPval-AA v2 是绝佳真实案例 —— Elo 以 human expert = 1000 为 anchor,进 Index 时用:
```
clamp( (Elo − 500) / 2000 )
```
引出:**anchor · scaling · clipping/clamping · frozen score · score comparability**。

### ② Weighting
AA Intelligence Index v4.1.1 类别权重:`Agents 34% · Coding 24% · Scientific Reasoning 24% · General 18%`
```
I = Σⱼ wⱼ sⱼ
```
数学很简单,真正的问题是:**为什么是这些 wⱼ?**
若 `Agents 34%→10%`、`Scientific 24%→48%`,排名可能立刻改变。

> ### 本课核心
> **Composite index 不是客观存在的物理量,是一组 measurement choices + value judgments。**

---

## Day 3 · 排名为什么会随聚合方式改变

| Model | Terminal | SWE | QA |
|---|---:|---:|---:|
| A | 90 | 80 | 30 |
| B | 70 | 70 | 70 |
| C | 40 | 60 | 95 |

```
等权:      A=66.7  B=70.0  C=65.0   → B 第一
Coding 重:  A > B > C
QA 重:      C > B > A
```
**raw benchmark results 完全没变,只是 aggregation function 变了。**

**要学**:
- **Weight sensitivity**:`Rₘ(w₁,…,w_k)`,观察权重变化时 rank 怎么变
- **Rank robustness**:不要问「谁第一」,要问「**在一组合理的 weighting assumptions 下,谁仍然第一**」

**Lab** `labs/leaderboard/sensitivity.py`:
```bash
leaderboard.py --weights terminal=0.33,swe=0.33,qa=0.34
# 再跑 10,000 组随机权重
→ Model A ranked #1: 31% | B: 57% | C: 12%
```

---

## Day 4 · Leaderboard uncertainty(把 W3 的统计用上)

```
Agent A = 67.2%     1. A
Agent B = 66.8%     2. B
```
视觉上像 A > B,但真正的问题是:**0.4 个百分点相对于 sampling uncertainty 有多大?**
```
A: 67.2 ± 2.3
B: 66.8 ± 2.1        → 「A #1」更多是 UI ordering,不是统计结论
```
AA 自己也说明:单项 evaluation 的置信区间可能宽于 ±1%。

**要学**:score uncertainty · rank uncertainty · CI · paired task comparison · statistical tie · leaderboard churn

> ### ⭐ Score uncertainty ≠ Rank uncertainty
> 10 个模型分数都挤在 61–64,即使每个 score 的 CI 不算宽,**rank uncertainty 也可能极大**。

---

## Day 5 · Artificial Analysis Teardown

前四天学完再拆 AA。不问「Claude 为什么第一」,而是**画完整 pipeline**:
```
                        raw generations
        ┌─────────────────────┼─────────────────────┐
   Terminal-Bench          GDPval              GPQA …
   89 tasks ×3           220 tasks
        │                     │
 test verifier          pairwise judge
        │                     │
   task pass rate              Elo
        │                normalization
        └────────────┬────────┘
                     ▼
               benchmark scores → weighting → Intelligence Index v4.1.1 → ranking
```

**回答七个问题**:
```
1. 每个 benchmark 的 raw unit 是什么?
2. 每个 task 跑几次?
3. task 内如何 aggregation?
4. benchmark 输出是不是同一个 scale?
5. 哪些需要 normalization?
6. 每个 benchmark 权重多少?
7. 如果 grader / benchmark / weight 改了,历史 score 怎么解释?
```

---

## Day 6 · Leaderboard Versioning

AA 提供了绝佳 case study:

**2026-06 v4.1**:Terminal-Bench Hard → 2.1 · τ² Telecom → τ³ Banking · GDPval-AA → v2 · 删除已饱和的 IFBench · 加大 agentic 权重
**2026-08-06 v4.1.1**:τ³-Banking → v1.0.1 · HLE/AA-LCR/AA-Omniscience 换 grader · **因 grader 更新,部分模型 Index 本身发生变化**

```
model weights 没变 · inference system 可能没变
但 leaderboard score 变了 —— 因为 measurement system 变了
```

**要全部保存的版本**:
```yaml
model: foo-v3
benchmark: {terminal_bench: 2.1}
harness:   {terminus: 2.x}
grader:    {version: abc123}
attempts_per_task: 3
aggregation: {type: task_macro_average}
index:     {version: aa-v4.1.1}
```
> 否则半年后你不知道:**这个 63 到底是什么 63?**

---

## 收尾 · Performance ≠ Utility

AA Coding Agent leaderboard 同时报告 `pass@1 · cost/task · tokens/task · execution time/task`。

| Agent | Success | Cost/task | Time |
|---|---:|---:|---:|
| A | 75% | $8 | 12 min |
| B | 73% | $1 | 3 min |
| C | 60% | $0.2 | 1 min |

A 第一 ≠ A 是实际系统的最佳选择。
```
Utility = f(accuracy, cost, latency, reliability)
```
**Pareto frontier** —— 为 W9 Production Eval 铺路。

---

## 知识树

```
Leaderboard Engineering
├── 1. Raw Results          attempt · errors/missing runs
├── 2. Within-task Agg      repeated pass@1 · pass@k · reliability
├── 3. Within-benchmark     task weighting · micro vs macro · subsets
├── 4. Cross-benchmark      normalization · anchors · weighting · composite indices
├── 5. Ranking              score uncertainty · rank uncertainty · ties
├── 6. Sensitivity          weights · task composition · scorer changes
├── 7. Versioning           dataset · grader · harness · index
└── 8. Multi-objective      quality · cost · latency · Pareto frontier
```

## P4 checkpoint(不是新的独立作业)

```
labs/leaderboard/
├── attempts.csv        5 agents × 4 benchmarks × 多次 rollout(模拟数据)
├── benchmarks.yaml
├── aggregate.py
├── bootstrap.py
├── sensitivity.py
└── README.md
```
把以下结果并入 P4 Evaluation Decision Report:
```
Model  Index   95% CI
A      68.3    [66.1, 70.4]
B      67.9    [65.8, 70.0]
C      61.2    [59.0, 63.5]
```
然后回答:**A 真的比 B 强吗?** 再改权重,发现:
```
original weights: A > B      agent-heavy: B > A      coding-heavy: A > B
```

> 到这里,你才真正**理解**了 leaderboard,而不是会**看**leaderboard。
