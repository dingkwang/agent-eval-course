# 第 1 课:Observation、Experimental Unit 与 Estimand

## 一行 TrialResult 到底能支持什么结论?

**Week 3 Day 1** · 统计推断课 · 建议 60 分钟 + 小 lab

> ### 本课唯一命题
> # 在计算平均分之前,先说明一行数据代表什么,以及这个数字要推广到哪里。
> # `TrialResult` 是 observation;task 是主要独立采样单位;estimand 才是最终想知道的量。

> 📄 Evan Miller, *Adding Error Bars to Evals* §2、§3.1
> 📄 Bjarnason et al., *On Randomness in Agentic Evals* §2.3–2.4
> 💻 输入:Week 2 产生的 `TrialResult` rows

```diag
flow | Week 2 交给 Week 3 的东西
resolved Trial
Agent × Environment × Task × Attempt
Verifier score + terminal status
一行 TrialResult observation
```

Week 2 证明一条 observation 是怎样被正确地产生和记录的。Week 3 不再问 adapter 有没有加料、verifier 对不对;先假定每次有效 Trial 已得到 score,问:

**这些 score 的平均数在估计什么?不确定性来自 task 选择,还是同一 task 重跑时的随机性?**

---

## 零、先看一个「平均分完全正确,结论仍然错误」的例子

同一个 Agent 在两个 task 上运行次数不相同:

| task | successes / valid attempts | task-level success |
|---|---:|---:|
| `easy` | 10 / 10 | 100% |
| `hard` | 0 / 1 | 0% |

把 11 行直接 pooled:

```math
\frac{10}{11}=90.9\%
```

如果 estimand 是「从两个 task 中等概率抽一个,再运行一次」,正确的 task-macro estimate 是:

```math
\frac{100\%+0\%}{2}=50\%
```

两个数都没有算术错误。`90.9%` 回答的是「从现有 11 次 attempt 中等概率抽一行」;`50%` 回答的是「先等概率抽 task,再抽一次 attempt」。

> **聚合顺序不是实现细节。它定义了你在估计哪个量。**

---

## 一、Canonical TrialResult table:一行 = 一次执行

本周先把不同 runner 的原始输出转换成一张共同的事实表:

```diag
pipe | canonical 的含义
Inspect / Harbor / 自研 runner 原始结果 → 同一列名 + 同一类型 + 同一语义 → Week 3 唯一统计输入
```

`canonical` 不是数据库产品名,也不是「唯一正确的 schema」。它表示课程约定的**标准化权威格式**:heatmap、pass curves、CI 和 A/B comparison 都从它派生,不各自读取一份口径不同的 summary。

### 1.1 Grain

```text
one row = one (task_id, agent_id, attempt_id) execution
```

这就是表的 grain,也就是一行所代表的最小 observation。最小字段:

| column | 语义 | 不变量 |
|---|---|---|
| `task_id` | benchmark 中的 task 身份 | 同版本中稳定 |
| `agent_id` | 完整 Agent 配置身份 | 不能只写 model 名 |
| `attempt_id` | 该 Agent 在该 task 上的重复编号 | 在 `(task_id, agent_id)` 内唯一 |
| `score` | verifier 输出 | 无有效评分时为 null |
| `category` | 预先定义的 task 分组 | 不从本次结果反推 |
| `tokens` | 本次 token 用量 | 非负或 null |
| `latency` | 本次 wall-clock latency | 非负或 null |
| `terminal_status` | Trial 如何结束 | 与 `score` 分列 |

推荐再保留 `trial_id`、`benchmark_version`、`task_digest`、`agent_config_digest`、`seed`、`started_at`。尤其 `agent_id` 应代表 **model + harness + prompt/tools/config**,而不只是 `gpt-x`。

主键检查:

```python
assert not df.duplicated(["task_id", "agent_id", "attempt_id"]).any()
```

### 1.2 `score=0` 不等于 `score=null`

```diag
compare | outcome 与 observation 缺失必须分开
terminal_status | score
completed,verifier 判失败 | 0
completed,verifier 判成功 | 1
infra_error,没有有效评分 | null
verifier_error,没有有效评分 | null
timeout | 按预注册规则;不能分析时临时决定
```

timeout、retry、infra failure 最终是否进分母是 Week 6 的 failure-semantics 问题。本课只要求:**原始表不丢行、不把缺失静默改成 0、也不把失败的 0 静默删掉。**

---

## 二、四层对象:row 不是结论

```diag
nest | 从 observation 到想推广的总体
目标 task population D
  当前 benchmark task set
    task i 的多次 attempts
      TrialResult Yᵢⱼ
```

| 层 | 符号 | 回答的问题 |
|---|---|---|
| Trial observation | $Y_{ij}$ | task $i$ 的第 $j$ 次运行发生了什么? |
| Task-level score | $\bar Y_i$ | 这个 task 上的平均表现怎样? |
| Benchmark estimate | $\hat\mu_{\mathrm{bench}}$ | 当前 task set 上的平均表现怎样? |
| Population estimand | $\mu_D$ | 从目标任务分布 $D$ 抽一个新 task,预期表现怎样? |

对 binary success:

```math
Y_{ij}\in\{0,1\},\qquad
p_i=P(Y_{ij}=1\mid T_i, A, C)
```

$A$ 是完整 Agent 配置,$C$ 是固定的 evaluation condition:prompt、tools、budget、environment、verifier policy 等。于是:

```math
\bar Y_i=\frac{1}{K_i}\sum_{j=1}^{K_i}Y_{ij}
```

```math
\hat\mu_{\mathrm{bench}}=\frac{1}{N}\sum_{i=1}^{N}\bar Y_i
```

若要推广到一个 task distribution $D$:

```math
\mu_D(A,C)=\mathbb E_{T\sim D}\left[P(Y=1\mid T,A,C)\right]
=\mathbb E_{T\sim D}[p_T]
```

### 2.1 Estimand、estimator、estimate 不要混

```diag
compare | 三个长得相近的词
Estimand | 想知道的总体量 · 例如 μ_D
Estimator | 从数据算它的规则 · 例如 task means 的平均
Estimate | 把本次数据代入后得到的数字 · 例如 61.4%
```

`61.4%` 本身没有完整含义。至少要补成一句:

> 对 Agent 配置 $A$、在条件 $C$ 下,从目标 task distribution $D$ 等概率抽取一个 task 并进行一次新 attempt,成功概率估计为 61.4%。

改一个词,estimand 就可能变:

```diag
grid | 常见的不同目标
fixed task set | 只描述当前 N 个 task
new task | 推广到 D 中未见过的 task
one attempt | 一次运行的预期成功率
up to k attempts | 允许 retry 后至少成功一次
all k attempts | 连续 k 次都成功的可靠性
production mix | 按真实流量权重,不是 benchmark 等权
```

后两项是 Lesson 2;production weighting 是 Week 8/9。本课默认目标是:**new task + one attempt + task-macro average**。

---

## 三、为什么同一个平均数有两类随机性

不同 task 难度不同;同一 task 重跑也可能一次成功、一次失败。

```diag
flow | observed score 的两层随机性
从目标分布抽到 task Tᵢ
该 task 有条件成功率 pᵢ
在同一 task 上抽到 attempt outcome Yᵢⱼ
```

```diag
compare | 不同来源,不同实验杠杆
Between-task variance | Within-task randomness
抽到了哪些 task | 同一 task 的 trajectory 走向
Var(p_T) | E[p_T(1-p_T)]
主要靠增加 tasks N 降低 | 可用 repeated attempts K 降低
```

对 Bernoulli score,全概率方差给出:

```math
\mathrm{Var}(Y)
=\underbrace{\mathrm{Var}_T(p_T)}_{\text{between-task}}
+\underbrace{\mathbb E_T[p_T(1-p_T)]}_{\text{within-task}}
```

若从 $D$ 独立抽 $N$ 个 task,每个 task 独立运行 $K$ 次,再先按 task 求均值:

```math
\mathrm{Var}(\hat\mu)
=\frac{1}{N}
\left(
\mathrm{Var}_T(p_T)
+\frac{\mathbb E_T[p_T(1-p_T)]}{K}
\right)
```

这条式子给出 Day 1 最重要的设计直觉:

```diag
compare | 同样多买一次 Trial,作用不一样
增加一个新 task | 给旧 task 增加一个 attempt
同时获得新的难度样本 | 只减少该 task 的 sampling noise
降低两项对均值的影响 | 只缩小 within-task 项
用于推广到更多 tasks | 用于看清 pᵢ 与可靠性
```

当 between-task variance 占主导时,把 $K$ 从 5 加到 10 可能远不如增加 task 数。反过来,如果目标就是某个固定 task set 的可重复表现,重复 attempts 仍很重要。

Miller 的论文把 evaluation question 视为来自一个未观察的 super-population,并用 total variance 区分 question selection 与 conditional sampling variance。本课把它映射到 agent task;这一步是课程的建模选择,不是论文声称所有 benchmark task 都真由随机抽样生成。

---

## 四、Agent eval 为什么即使 temperature=0 也需要这层模型

*On Randomness in Agentic Evals* 在 SWE-bench Verified 上收集 60,000 条 trajectories(3 个模型、2 个 scaffolds、两种 temperature 设置)。同一 Agent 配置只选一次 run 时,reported pass@1 的跨度为 **2.2–6.0 percentage points**;temperature 0 的 run-to-run standard deviation 仍可超过 **1.5 pp**。

论文进一步发现 trajectory 往往在很早的 token 位置分叉,随后 tool calls、environment observations 与后续生成通过 autoregressive loop 放大差异。

```diag
flow | temperature=0 不是「实验没有随机性」
微小 inference / runtime 差异
早期 token 或 tool call 分叉
不同 environment observation
不同后续策略
不同 final score
```

因此 $p_i$ 不是「temperature 大于 0 才存在」的概念。它是:**在声明好的重复运行机制下,这个 Agent 对 task $i$ 成功的条件概率。**

本课不把所有非确定性都叫 model randomness。`terminal_status=infra_error` 仍单独保留,到 Week 6 再决定其 failure semantics。

---

## 五、四个会让后续统计失效的 schema 错误

### 5.1 把 $N\times K$ 当作 $NK$ 个独立 task

```text
40 tasks × 10 attempts = 400 TrialResult rows
                       ≠ 400 independent task draws
```

同一 task 下的 attempts 共享 task 难度 $p_i$,因此相关。把 400 行直接送进普通 Bernoulli CI,会虚构 task sample size。Lesson 3 会比较 naive CI 与 task-aware CI 的 coverage。

### 5.2 只保存 summary,丢掉 task identity

`agent_A=58%`,`agent_B=61%` 不足以做 paired comparison。Lesson 4 需要知道 A、B 是否在**相同 task**上成功,因此必须保留 `task_id`。

### 5.3 用运行次数给 task 偷偷加权

若一个 task 有 20 次有效 attempt、另一个只有 2 次,pooled row mean 会让前者权重变成十倍。默认 task-macro estimand 应先算 $\bar Y_i$,再跨 task 平均。

### 5.4 从 outcome 反推 category 或删除「难看的」task

按结果创建 `hard_tasks` 再只报告其分数,改变了目标分布。category、过滤规则与 estimand 应在看结果前定义;探索性切片可以做,但必须标成 exploratory。

---

## 六、Lab:从 TrialResult rows 建立统计事实表

### 6.1 输入与输出

输入 Week 2 的 TrialResult。输出两张表:

```diag
flow | 先保留 observation,再派生 task-level table
raw runner outputs
canonical_trial_results · 一行一次 execution
task_estimates · 一行一个 task × agent
```

`task_estimates` 至少包含:

```text
task_id
agent_id
n_planned_attempts
n_valid_attempts
n_missing_attempts
task_mean_score
category
```

不要覆盖 raw rows;派生表可以重建。

### 6.2 Validation gates

```text
[ ] (task_id, agent_id, attempt_id) 唯一
[ ] score 只在声明的范围内;binary eval 为 0 / 1 / null
[ ] terminal_status 使用枚举,不是自由文本
[ ] score=null 的行没有被静默删除
[ ] 每个 agent 的 task set 差异被显式报告
[ ] agent_id 能解析到完整 config 或 config digest
[ ] category 不随 attempt 改变
```

### 6.3 第一张图:task × attempt heatmap

每个 Agent 单独画一张或 facet:

```text
rows    = task_id(可按 task_mean_score 排序)
columns = attempt_id
color   = pass / fail / missing
```

```diag
grid | heatmap 应让人一眼看见什么
全绿 task | 稳定成功
全红 task | 稳定失败
红绿相间 | within-task randomness 大
灰色格子 | missingness / terminal-status 问题
整列异常 | 某次 run 或 infra 可能有系统性问题
```

这张图不是装饰。它决定 Lesson 2 是否值得讨论 reliability,也决定 Lesson 3 为什么必须保留 task 层级。

---

## 七、读论文时只回答四个问题

### Miller, *Adding Error Bars to Evals*

- §2 的 super-population assumption 在 agent benchmark 中对应什么?
- conditional mean $x_i$ 怎样映射成 task success probability $p_i$?
- §3.1 为什么要求先形成 question-level mean,而不是把 $KN$ 个 answers pooled 成独立样本?
- 哪些 benchmark task 明显不是随机抽自真实 production distribution?这会限制什么结论?

### Bjarnason et al., *On Randomness in Agentic Evals*

- §2.3 的 single-run resolution rate 与本课 $Y_{ij}$ 怎样对应?
- temperature 0 时还有哪些来源使 trajectories 分叉?
- 60,000 trajectories 证明的是某些 coding-agent 配置的实证现象,还是所有 agent benchmark 的普遍常数?
- 为什么这篇论文的 multi-run 数据仍不能自动解决 task-population validity?

来源:

- [Adding Error Bars to Evals](https://arxiv.org/abs/2411.00640)
- [On Randomness in Agentic Evals](https://arxiv.org/abs/2602.07150)

---

## 本课自检

```text
[ ] 能说出 canonical table 的 grain:一行 = 一个 task × agent × attempt execution
[ ] 能解释 score=0 与 score=null 为什么必须分开
[ ] 能区分 TrialResult、task-level score、benchmark estimate、population estimand
[ ] 能区分 estimand、estimator、estimate
[ ] 能写出默认 estimand:在条件 C 下,从 D 抽新 task 并运行一次的预期成功率
[ ] 能解释 Var(Y) 的 between-task 与 within-task 两项
[ ] 能解释为什么增加 tasks 与增加 attempts 不是同一种预算
[ ] 能解释为什么 40 tasks × 10 attempts 不是 400 个独立 task draws
[ ] 能从 canonical rows 生成 task_estimates 与 task-attempt heatmap
```

---

## 本课一句话

> **平均分之前先定 grain,误差棒之前先定 estimand。**
> **一行 TrialResult 是一次 observation;先在 task 内汇总,再跨 task 推断,才能说清这个数字究竟代表当前题集、一次新运行,还是目标任务分布。**

下一课:同一个 $p_i$,产品可能关心「多试几次能不能成功」,也可能关心「每次都能不能成功」——`pass@k` 与 `pass^k` 会把这两个问题分开。
