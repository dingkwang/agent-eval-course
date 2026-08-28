# 第 4 课:Paired Comparison、Power 与 Statistical Eval Report

## A 是否真的优于 B,以及证据是否足以支持发布决策?

**Week 3 Day 4** · 统计推断 + 综合 lab · 建议 100 分钟

> ### 本课唯一命题
> # 不要比较两个 headline scores;直接比较相同 task 上的 paired difference。
> # 在看结果前声明 meaningful effect、power 与 decision rule,最后把 estimate、uncertainty、missingness 和限制写进同一份可审计报告。

> 📄 Miller, *Adding Error Bars to Evals* · paired differences + power
> 📄 Xie, *Measuring all the noises of LLM Evals* · all-pairs paired noise
> 📄 Neuhof & Benjamini, *Quantifying Ranking Uncertainty in LLM Benchmarks*
> 💻 输出:Week 3 Statistical Eval Report

```diag
flow | 从两组 rows 到一个 decision
相同 task set 上运行 A 与 B
形成 per-task paired outcomes
估计 Δ = B - A + matched interval
对照预先声明的 meaningful margin
promote / reject / equivalent / inconclusive
连同 design、cost、missingness 与 limitations 发布
```

---

## 零、A=60%、B=63% 还不够

100 个相同 tasks,两种实验都有 A=60%、B=63%:

| paired outcomes | 实验 X | 实验 Y |
|---|---:|---:|
| both pass | 60 | 40 |
| B only passes | 3 | 23 |
| A only passes | 0 | 20 |
| both fail | 37 | 17 |
| marginal difference | +3 pp | +3 pp |

```diag
compare | 同样 +3pp,证据结构不同
实验 X · 3 discordant tasks | 实验 Y · 43 discordant tasks
绝大多数 task 完全相同 | A/B 经常互有胜负
差值来自 3 个 B-only | 23 个 B-only 对 20 个 A-only
小样本 exact inference 离散 | paired difference variance 很大
```

只看两个总体百分比,这两个实验完全一样。保留 task pairing 后,我们才知道差值来自哪些 tasks、discordance 有多大、以及该对什么进行 resampling。

> **A 与 B 的 uncertainty 不是两根 marginal error bars 的视觉关系。目标变量是同一 task 上的 $B-A$。**

---

## 一、先定义 comparison estimand

Agent A、B 在 task $i$ 上的条件成功率分别为 $p_{Ai}$、$p_{Bi}$。目标 task distribution $D$ 上:

```math
\Delta_D
=\mathbb E_{T\sim D}[p_{BT}-p_{AT}]
```

正值表示 B 更高。样本中先对每个 task 的 attempts 求均值:

```math
D_i=\bar Y_{Bi}-\bar Y_{Ai}
```

再跨 tasks 做 macro average:

```math
\hat\Delta=\frac{1}{N}\sum_{i=1}^{N}D_i
```

```diag
flow | Pairing 保留的结构
task i 的语义与难度
A 在 task i 的 attempts → task mean Aᵢ
B 在 task i 的 attempts → task mean Bᵢ
Dᵢ = Bᵢ - Aᵢ
跨 task 推断 Δ
```

若使用 production weights,对 $D_i$ 使用同一组预注册权重。若 A、B 的 missing tasks 不同,不能各自算一个分母后相减;必须报告 matched set、unmatched set 与 missing rule。

### 1.1 配对不是「刚好使用同一 benchmark 名」

```diag
grid | 合法 pairing contract
same task identity | benchmark version + task digest 相同
same target condition | environment、budget、verifier policy 可比
matched execution wave | provider / infra drift 尽量 block 或随机交错
preserved IDs | task_id、batch_id、attempt_id 不在 summary 中丢失
```

若 A 在周一、B 在三周后运行,期间 provider routing、runtime image 或 benchmark 修复发生变化,task_id 相同也不能自动消除 time confounding。可随机交错 A/B 顺序、按 batch block,并保留 run wave。

### 1.2 Attempt 是否也要一一配对?

task 是主要 pairing unit。只有当两系统共享一个有意义的随机条件——例如同一 environment snapshot、同一 simulator seed 或同一故障注入——attempt-level pairing 才成立。随便把 A 的 attempt 1 与 B 的 attempt 1 对齐不会凭空创造 covariance。

---

## 二、方法路由:直接对 paired object 做 inference

| Outcome / design | 推荐起点 | 统计对象 |
|---|---|---|
| binary,每 task 一次 | exact McNemar / paired binary interval | B-only 与 A-only discordance |
| bounded/continuous task score | paired task bootstrap | $D_i$ distribution |
| 每 task 多 attempts | task bootstrap 搬动 A/B 两边完整 attempts | per-task estimator difference |
| repo / scenario clusters | paired cluster bootstrap 或 hierarchical model | cluster 内所有 A/B task pairs |
| 很少 tasks / clusters | exact/randomization 或 Bayesian paired model | 明确 finite-sample assumptions |
| pass@k / weighted/custom metric | resample 后重算两边完整 metric 再相减 | metric-level $\Delta$ |

### 2.1 Binary paired table:McNemar 只看 discordant tasks

```diag
grid | Binary paired outcomes
A pass · B pass | concordant success
A fail · B fail | concordant failure
A fail · B pass | B-only · b
A pass · B fail | A-only · c
```

```math
\hat\Delta=\frac{b-c}{N}
```

在「A、B 对 discordant outcome 等可能」的 null 下,exact McNemar test 把 $b$ 看作 $b+c$ 次试验中的 Binomial$(b+c,1/2)$。它没有使用 both-pass/both-fail 来虚增 evidence。

```python
from scipy.stats import binomtest

discordant = b_only + a_only
result = (
    binomtest(b_only, discordant, p=0.5, alternative="two-sided")
    if discordant else None  # 完全无 discordance;不能制造 evidence
)
```

`p-value` 不是 effect size,也不是「null 为真的概率」。报告仍以 $\hat\Delta$ 与 paired CI 为主;test 只回答预先声明的 hypothesis。

### 2.2 Paired task bootstrap:一张可复用的模板

```python
import numpy as np

def paired_task_bootstrap(task_differences, *, reps=20_000, seed=7):
    d = np.asarray(task_differences, dtype=float)
    if d.ndim != 1 or len(d) < 2 or not np.isfinite(d).all():
        raise ValueError("need at least two finite paired task differences")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(reps, len(d)))
    draws = d[idx].mean(axis=1)
    return d.mean(), np.quantile(draws, [0.025, 0.975])
```

真实 pipeline 不应只传一列已经不可追溯的 differences。每个 bootstrap replicate 应从 matched task IDs 搬动 A/B 两边的完整 attempts,再重算 task metric、weights、eligibility 与 $\Delta$。

### 2.3 Paired permutation / sign-flip 需要 exchangeability

在 sharp null 下交换同一 task 的 A/B labels,或对 $D_i$ 随机乘 $+1/-1$,可以构造 randomization distribution。但成立条件是 null 下 treatment labels exchangeable。若 A/B 使用不同预算、不同运行期或 adaptive policies,不能只因方法 non-parametric 就忽略 design。

### 2.4 为什么 pairing 通常更有 power

```math
\operatorname{Var}(B-A)
=\operatorname{Var}(B)+\operatorname{Var}(A)
-2\operatorname{Cov}(A,B)
```

相近 systems 往往在相同 easy/hard tasks 上一起成功或失败,使 covariance 为正。paired analysis 保留这部分共同难度,差值 variance 因而更小。Miller 的实证分析发现多个 eval 上 frontier model question scores 的 correlation 明显为正;这解释了 pairing 为什么常是近乎免费的 variance reduction。

---

## 三、`statistically > 0` 还不是发布标准

在看结果前定义 smallest meaningful improvement $\delta_*$。它可以来自产品价值、额外成本、风险容忍度或 migration cost,不能由本次 point estimate 倒推。

```diag
grid | Decision margins
Superiority | 需要证明 Δ > δ*
Any improvement | 特例 δ* = 0
Non-inferiority | 需要证明 Δ > -m
Equivalence | 整个 CI 落在 [-m, +m]
```

令 paired interval 为 $[L,U]$:

| 规则 | 结论 | 应说什么 |
|---|---|---|
| $L>\delta_*$ | meaningful improvement supported | B 至少改善声明阈值 |
| $U<\delta_*$ | required improvement not supported | 数据排除所需收益 |
| $L\le\delta_*\le U$ | inconclusive | 当前 design 分不清 |
| equivalence 且 $-m<L<U<m$ | practically equivalent | 差异小于容忍区间 |

```diag
compare | 两种经常被混淆的失败
No significant difference | Evidence of equivalence
CI 仍跨过 0 / margin | 整个 CI 已落入 equivalence band
可能只是 underpowered | 需要专门的 equivalence design
不能说 A=B | 可以在 margin 内说 practically equivalent
```

### 3.1 把 accuracy gain 与 resource cost 放在同一 decision 上

若 B 多用 5 倍 tokens 才提高 2pp,决策不是纯 accuracy hypothesis。至少并列报告:

```diag
grid | Outcome-resource decision
quality Δ | paired score / success difference
cost ratio | tokens、dollars、tool calls
latency Δ | mean + tail quantiles
failure risk | timeout / invalid / safety gate
```

不要把这些维度事后压成一个未经声明的 composite score。先给 Pareto view,只有存在稳定业务 trade-off 时才定义 utility function。

---

## 四、Power 与 MDE:运行之前问「这个实验看得见什么」

power 是在真实 effect 达到目标时,design 作出预期判断的概率。minimum detectable effect(MDE) 是给定 $N$、$K$、variance、$\alpha$ 与 power 后能可靠看见的最小差异。

对近似独立的 per-task differences,一个 planning approximation 是:

```math
N\approx
\left(
\frac{(z_{1-\alpha/2}+z_{1-\beta})s_D}{\delta_*}
\right)^2
```

$s_D$ 应来自 pilot 或相近历史 comparison,不是从最终实验倒推。binary、clustered、weighted、pass@k 或 sequential design 优先使用 simulation-based power:完整模拟 data-generating process 与最终 estimator。

```diag
flow | Simulation-based power
声明真实 Δ 与 task heterogeneity
模拟 A/B paired attempts + missing / batch structure
运行最终 estimator、CI 与 decision rule
重复 many experiments
power = 正确支持 decision 的比例
```

### 4.1 N tasks 与 K attempts 的预算搜索

```text
for candidate design (N, K):
  estimate power or expected CI width from pilot components
  estimate tokens, dollars and wall-clock
  reject designs below task/category coverage requirements
  keep Pareto-efficient designs
```

若目标是 new-task mean,增加 $N$ 通常同时减少 task 与 attempt noise;增加 $K$ 只减少 within-task noise。但如果 A/B 的 paired prediction noise 很大,适量增加 $K$ 可能显著缩小 $D_i$ noise。不要依赖通用的 “3 runs per task”;用 pilot components 决定。

### 4.2 Underpowered 结果的正确措辞

```diag
compare | 不显著之后
错误 | 正确
A 和 B 一样 | CI 仍允许 -4pp 到 +7pp;当前 design 无法区分
B 没有提升 | 未达到预注册 superiority criterion
再多跑一点直到显著 | 按 fixed plan 结束,或使用预注册 sequential method
```

---

## 五、比较越多、查看结果越频繁,越容易偶然找到「显著提升」

这里有三种不同但相关的行为:

```diag
grid | 偶然赢家从哪里来
同时比较很多 models | 10 个 models 已有 45 组 A/B pairs
查看很多 task slices | category、repo、难度、语言各做一次检验
反复查看中途结果 | 每完成一些 tasks 就检查,一显著便停止
```

它们的共同点是:**给随机波动很多次成为“好消息”的机会。** 即使每一次检验的 false-positive rate 都是 5%,做很多次后「至少出现一个假阳性」的概率也会升高。

### 5.1 先定义哪些比较共同对应一个结论

10 个 models 有 45 个 unordered pairs;再乘 categories、metrics 与 prompts,偶然赢家很快出现。

```diag
grid | Multiplicity policy
Primary contrast | 一个预注册 A vs B + primary metric
Confirmatory family | Holm 等 FWER control
Exploratory slices | BH-FDR 或明确标 exploratory
Post-hoc discovery | 新实验确认,不在同一数据上重新宣布 confirmatory
```

`p<0.05` 不是每个 slice 各自拥有的免费预算。也不要把所有 diagnostics 粗暴塞进一个 family;family 应对应同一组要共同保证的 claims。

### 5.2 排名是很多组 A/B 比较的压缩

raw leaderboard rank 没有 error bar。*Quantifying Ranking Uncertainty in LLM Benchmarks* 用 directional pairwise tests + multiple-comparison correction 构造 rank intervals:

```diag
flow | Rank interval 的来源
每个 model pair 的 directional test
控制 comparison family error
数出明确高于 / 低于 model j 的集合
得到 model j 仍可能处于的 rank range
```

若 model 的 rank interval 是 `[2,7]`,报告单一的 `rank=3` 会制造不存在的精确度。完整 leaderboard aggregation 留到 Week 8;本课只要求不要把 point rank 当统计结论。

### 5.3 不要每完成一些 tasks 就查看结果,一显著便停止

普通 fixed-sample CI / p-value 在反复查看并按显著性停止时失去标称 error control。选择之一:

- 固定 $N$ 与 stopping rule,只在计划终点作 confirmatory decision;
- 使用预注册的 group-sequential / always-valid method;
- 把 partial run 标为 monitoring,最终仍按 fixed analysis 报告。

2026 的 ParEvalLayer 与 Bayesian optimal stopping 是值得讨论的 frontier examples:它们把 threshold、task-group coverage、unresolved/abstain 与 resource limit 写进 stopping policy。它们不是「看到领先就停」的许可证。

---

## 六、P2 checkpoint:Statistical Eval Report

Day 5 不再单独占一课。本节后半直接把 Week 3 的 artifacts 组装成 report。

### 6.1 必须交付的证据链

```diag
flow | Report evidence chain
SUT + benchmark manifest
estimand + sampling / pairing contract
canonical TrialResult rows
task-level estimates + missing flow
point estimate + matched interval
paired Δ + margin + power / MDE
decision + robustness + limitations
```

### 6.2 一页 executive table

| field | 必填内容 |
|---|---|
| Claim | 要支持的 deployment / benchmark decision |
| SUT A / B | model + harness + tools + budget + runtime / routing |
| Target | fixed bank $B$ 或 task distribution $D$ |
| Primary outcome | one attempt、pass@k、pass^k 或其他明确 event |
| Design | $N$ tasks、$K$ attempts、clusters、pairing、run order |
| Denominators | planned / executed / scored / excluded + reasons |
| A / B estimates | point + structure-matched interval |
| Paired result | $\hat\Delta$、CI、meaningful margin $\delta_*$ |
| Power | planned power 或 achieved CI width/MDE;不要 post-hoc observed power |
| Resource | tokens、cost、latency、timeouts |
| Decision | promote / reject / equivalent / inconclusive |
| Limitations | sampling frame、dependence、measurement与 validity 边界 |

### 6.3 四张核心图

```diag
grid | Statistical Eval Report figures
task × attempt heatmap | stochasticity、missingness、batch pattern
paired difference plot | 每 task Dᵢ + overall CI
outcome-resource curve | quality 与 cost / latency 随预算变化
decision interval | CI 相对 0、δ* 或 equivalence band
```

不要再放两根独立 bar + marginal error bars 作为主要 A/B 图。paired difference plot 应让读者看到 improvement 是否集中在少数 categories/tasks。

### 6.4 Robustness matrix

| axis | primary analysis | sensitivity analysis |
|---|---|---|
| task target | declared macro / weights | alternative pre-specified weights |
| missingness | registered denominator rule | best/worst-case bounds |
| uncertainty | task/cluster bootstrap | exact or hierarchical cross-check |
| run structure | all valid planned waves | leave-one-batch/repo-out |
| metric | primary outcome | declared secondary metrics |

敏感性分析若改变结论,最终 decision 应标 unstable;不能挑支持预期的一格当 headline。

### 6.5 Audit manifest

```text
benchmark_id + benchmark_version + task digests
agent config digests for A and B
runtime image / infra / provider versions
verifier version + scoring policy
analysis code commit + dependency lock
random seeds + bootstrap replicates
all exclusions and protocol deviations
generated report timestamp
```

### 6.6 Release gates

```text
[ ] primary claim、Δ direction 与 meaningful margin 在看结果前写下
[ ] A/B 使用 matched task set;unmatched rows 单独列出
[ ] CI resampling unit 与 estimand / design 一致
[ ] point estimate、CI、N tasks、K attempts 与 cluster count 同时报告
[ ] p-value 没有替代 effect size 与 interval
[ ] no-significance 没有被写成 equality
[ ] 多 comparisons / slices 有 family policy
[ ] fixed stopping rule 或 sequential method 事先声明
[ ] cost、latency、timeout 与 quality 使用同一 eligible population
[ ] report 可由 canonical rows + pinned analysis code 重建
```

---

## 七、读材料时只回答这些问题

### Miller + *Measuring all the noises*

- paired covariance 为什么可以减少 question/task difficulty noise?
- repeated attempts 怎样改变 paired prediction noise 与 MDE?
- all-pairs empirical patterns 能否替代自己 eval 的 pilot?

### Ranking uncertainty

- 为什么 rank CI 需要 directional pairwise tests 与 multiplicity control?
- inference unit 选 task 还是 subject/repo 时,rank interval 为什么会变化?
- indifference zone 与本课 $\delta_*$ 有什么关系?

### Frontier stopping work

- partial score 为什么不能单独支持 decision?
- task order、category coverage 与 unresolved rate 为什么必须进入 stopping policy?
- Bayesian stopping 的 credible-width criterion 是否与产品 meaningful margin 对齐?

来源与代码:

- [Adding Error Bars to Evals](https://arxiv.org/abs/2411.00640) · [Anthropic research note](https://www.anthropic.com/research/statistical-approach-to-model-evals)
- [Measuring all the noises of LLM Evals](https://arxiv.org/abs/2512.21326) · [interactive analyses](https://all-the-noises.github.io/)
- [Don't Use the CLT in LLM Evals](https://arxiv.org/abs/2503.01747) · [bayes_evals](https://github.com/sambowyer/bayes_evals)
- [Quantifying Ranking Uncertainty in LLM Benchmarks](https://arxiv.org/abs/2607.16259) · [code](https://github.com/BityaNeuhof/quantifying-rank-uncertainty)
- [RuBench](https://arxiv.org/abs/2607.06411) · 小样本 paired comparison 的 agent case study
- [When Partial LLM-Agent Evaluations Support a Decision](https://arxiv.org/abs/2608.02444)
- [Bayesian Optimal Stopping for LLM Evaluations](https://arxiv.org/abs/2608.14425)

---

## 本课自检

```text
[ ] 能从相同 task outcomes 构造 Dᵢ 与 Δ_hat
[ ] 能解释为什么两个 marginal CIs 重叠/不重叠不是 paired comparison
[ ] 能对 binary paired outcomes 写出 b、c 与 exact McNemar logic
[ ] 能让 task / cluster bootstrap 同时搬动 A/B descendants
[ ] 能说明 attempt-level pairing 需要共享且有意义的随机条件
[ ] 能区分 significance、superiority、non-inferiority 与 equivalence
[ ] 能在实验前声明 δ*、power、N/K budget 与 stopping rule
[ ] 能识别 multiple models / slices / peeking 带来的 error inflation
[ ] 能解释 rank interval 为什么比 raw rank 更诚实
[ ] 能交付包含 design、denominators、paired Δ、MDE、cost 与 limitations 的可重建报告
```

---

## 本课一句话

> **比较的 observation 不是 A 的平均分和 B 的平均分,而是相同 task 上的 paired difference。**
> **可信结论必须同时回答:差多少、区间多宽、多少差异才有意义、实验原本看得见多小的 effect,以及哪些统计与 validity 限制仍未被解决。**

Week 3 到这里结束。Week 4 不再假定 verifier score 正确,而是把 scorer 本身当作 measurement instrument 进行 validation。
