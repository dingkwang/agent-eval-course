# 第 3 课:Uncertainty for Structured Eval Data

## CI 必须重采样 estimand 所声明的随机单位

**Week 3 Day 3** · 统计推断课 · 建议 80 分钟 + coverage lab

> ### 本课唯一命题
> # Error bar 不是给 point estimate 加一根装饰线,而是一段可执行的重复实验说明。
> # 先决定什么会被重新抽样,再选择 Wilson、task bootstrap、cluster bootstrap 或 hierarchical model。

> 📄 Miller, *Adding Error Bars to Evals* · repeated answers、clustered questions
> 📄 Bowyer et al., *Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints*
> 📄 Xie, *Measuring all the noises of LLM Evals*
> 💻 输入:Lesson 1–2 的 canonical rows、task estimates 与 metric contract

```diag
flow | 一条可信 CI 的生成顺序
estimand · fixed bank 还是 new tasks
sampling design · task / cluster / attempt 怎样进入
estimator · macro mean / pass curve / weighted score
resampling or probability model
interval + assumptions + effective sample size
```

---

## 零、同样 400 行,为什么不能使用同一根 error bar?

考虑三个都产生 400 行的实验:

```diag
grid | 400 rows 的三种结构
400 tasks × 1 attempt | 400 个 task observations
40 tasks × 10 attempts | 40 个 task clusters,每组 10 行
10 repos × 4 tasks × 10 attempts | 10 个 repo clusters,再嵌套 task
```

若把后两种结构都当成 400 个独立 Bernoulli observations,会把共享 task 难度、repo 特征与 batch failure 当作 400 份新信息。行数没有造假,但 independent information 被夸大。

```diag
compare | Naive row CI 与 structure-aware CI
把每行 independently resample | 重采样 estimand 的 sampling unit
n = 400 | N_task = 40 或 N_repo = 10
打散同一 task / repo 的相关性 | descendants 一起移动
CI 往往过窄 | uncertainty 与推广范围一致
```

> **`len(df)` 是存储行数,不是自动成立的统计 sample size。**

Lesson 1 已经保留 `task_id`、`batch_id`、`infra_version` 与 category。本课解释为什么这些字段会改变 interval。

---

## 一、CI 在重复哪一个世界?

### 1.1 CI 不是「参数有 95% 概率在这里」

频率学派 95% CI 的 operational meaning 是:

> 如果按同一个 sampling design 反复采数据并重算 interval,长期约 95% 的 intervals 覆盖目标 estimand。

因此必须能回答:**下一次重复实验,哪些东西会重新抽?**

```diag
compare | 两个常见世界
Fixed bank B | Target distribution D
同一批 tasks 不变 | 从 sampling frame 重抽 tasks
重跑 attempts | task identity 也会变化
主要量化 execution noise | 同时量化 task selection + execution noise
不能自动推广到新题 | interval 支持声明范围内的新 task claim
```

fixed-bank mean:

```math
\mu_B=\frac{1}{N}\sum_{i=1}^{N}p_i
```

new-task mean:

```math
\mu_D=\mathbb E_{T\sim D}[p_T]
```

两个 point estimates 可能相同,CI 的重复机制却不同。对完整 fixed bank 做 task bootstrap,等于偷偷把固定 tasks 改成一个 hypothetical task population;这不是纯粹的技术选择,而是换了 estimand。

### 1.2 CI、prediction interval 与 sensitivity interval 不要混

```diag
grid | 三种 interval 回答三个问题
Confidence interval | 平均 performance estimand 有多精确
Prediction interval | 下一道 task 或下一次 rollout 可能落在哪里
Sensitivity interval | 换 prompt / judge / timeout rule 后结论怎样变化
```

一个均值的 95% CI 很窄,不表示下一次 rollout 几乎不会失败。对 binary task outcome,单次 prediction 仍然只有 0 或 1。prompt/judge sensitivity 也不会因为增加同一配置下的 tasks 自动消失。

---

## 二、两层 variance 决定「多加 task 还是多跑 attempt」

用最小 two-level model 表示 task $i$ 的 attempt $j$:

```math
Y_{ij}=\mu+u_i+\varepsilon_{ij}
```

其中 $u_i$ 表示 task-level deviation,$\varepsilon_{ij}$ 表示同一 task 的 run-to-run deviation。平衡设计下:

```math
\operatorname{Var}(\hat\mu)
=\frac{\sigma_{\text{task}}^2}{N}
+\frac{\sigma_{\text{attempt}}^2}{NK}
```

```diag
compare | 预算投到哪里
增加 N tasks | 增加 K attempts/task
同时缩小 task 与 attempt 两项 | 只缩小 attempt 项
改善 new-task coverage | 更精确估计现有 task 的 pᵢ
通常更利于总体均值 | 更利于 reliability curve / unstable tasks
```

intraclass correlation 给出同 task 两行有多相似:

```math
\rho=\frac{\sigma_{\text{task}}^2}
{\sigma_{\text{task}}^2+\sigma_{\text{attempt}}^2}
```

若每组大小为 $K$,一个常用 diagnostic 是 design effect:

```math
\operatorname{DEFF}\approx 1+(K-1)\rho
```

于是 naive effective sample size 近似变成:

```math
n_{\text{eff}}\approx\frac{NK}{1+(K-1)\rho}
```

它只用于解释「为什么 400 rows 不是 400 份独立信息」,不是本课最终 CI 算法。真实 Agent eval 还可能不平衡、heteroskedastic,并有 batch / repo 等交叉依赖。

### 2.1 Agent eval 常常不只是两层 nesting

```diag
flow | 常见的 dependence path
repository / scenario family
task
attempt
trajectory outcome
```

```diag
grid | 还会横向穿过多道 task 的 shared shocks
provider batch | 同一时窗 routing / outage
infra batch | 同 image、host、resource pressure
judge batch | 同 judge version / prompt variant
experiment wave | deploy version 或 policy 在中途改变
```

repo → task → attempt 是 nested;provider batch × task 可能是 crossed。不要为了套一个简单公式把它们都叫 randomness。先画 design,保存 IDs;复杂 crossed design 可以用 multiway cluster、mixed-effects 或 Bayesian hierarchical model,并在报告中写清模型假设。

---

## 三、方法路由:不要默认 `mean ± 1.96 × SE`

Bowyer et al. 的 coverage experiments 表明,在小样本、clustered questions 与极端准确率下,CLT interval 可能严重 under-cover,越过 $[0,1]$,甚至在全对/全错时塌成零宽。bootstrap 在极小或 degenerate binary samples 中也不自动可靠。

```diag
flow | 选择 interval 的最短路径
先写 estimand 与最高 sampling unit
binary 且每 unit 一次?
是 · Wilson / exact / Beta posterior
否 · 保留完整 cluster 重算 estimator
units 足够?task / cluster bootstrap
units 很少或层级复杂?hierarchical model + sensitivity
```

| 数据与目标 | 默认起点 | 不能做什么 |
|---|---|---|
| i.i.d./exchangeable sampled tasks,每 task 一个 binary outcome | Wilson 或 exact binomial interval | Wald `p ± 1.96√p(1-p)/N` |
| new-task mean,每 task 多 attempts | task-level bootstrap;整组 attempts 随 task 移动 | 把 $NK$ rows 独立 resample |
| fixed bank,每 task 多 attempts | within-task model/bootstrap 后聚合;或 joint Beta simulation | 用 task bootstrap 假装重抽固定题库 |
| tasks 来自 repos / scenario families | cluster bootstrap at declared sampling unit | 在 task 层打散 repo correlation |
| 很少 clusters、稀疏或极端 outcomes | exact/Bayesian hierarchical model + prior sensitivity | 把 asymptotic cluster SE 当保证 |
| weighted / pass@k / custom metric | 每次 resample 重跑完整 estimator | 给旧 point estimate 套通用 SE |

### 3.1 Wilson 解决的是一个窄问题

当 $N$ 个从同一目标分布抽取的**独立/exchangeable task units**各产生一次 binary outcome,$c$ 个成功:

```math
\hat p=\frac{c}{N}
```

Wilson interval 比 Wald interval 在小样本和 $p$ 接近 0/1 时更稳健。但它不覆盖 arbitrary heterogeneous fixed bank 的 Poisson-binomial uncertainty;40 tasks × 10 attempts 也不是 `N=400` 的 Wilson 问题,因为同一 task 的 10 行相关。

### 3.2 Task bootstrap 必须搬动完整 task block

对 new-task macro mean:

```text
repeat B times:
  sample N task_ids with replacement
  bring every selected task's attempts, statuses and weights
  recompute task-level statistic
  recompute macro estimator
CI = quantiles of B replicated estimates
```

```diag
compare | 正确与错误的 bootstrap
Task bootstrap | Row bootstrap
抽 task_id | 抽 TrialResult row
同 task attempts 一起复制 | attempts 被拆散
每个 replicate 重跑 estimator | 只对 pooled score 求 mean
保留 macro / missing rule | 改变原实验语义
```

若 sampling design 是「先抽 repo,再抽 repo 内 tasks」,bootstrap 也应镜像这个过程。cluster 数很少时 percentile bootstrap 可能离散且不稳定;此时报告 cluster count,并用 hierarchical model、exact/randomization method 或 sensitivity analysis 交叉检查。

### 3.3 Hierarchical model 的价值是 partial pooling,不是自动正确

binary outcome 的一个起点:

```math
Y_{ij}\sim\operatorname{Bernoulli}(p_i)
```

```math
\operatorname{logit}(p_i)=\alpha+u_i,
\qquad u_i\sim\mathcal N(0,\sigma_{\text{task}}^2)
```

它能对 attempts 少的 task 做 partial pooling,还能扩展 repo、batch 与系统交互。但 credible interval 条件于 likelihood、prior 与 exchangeability assumptions。必须报告 prior sensitivity 与 posterior predictive checks;不要把「Bayesian」当成免除 design audit 的标签。

---

## 四、Variance components 是实验设计工具,不只是解释结果

*Measuring all the noises of LLM Evals* 把 total noise 分为:

```math
\operatorname{Var}_{T,\epsilon}[Y]
=\operatorname{Var}_{T}\!\left(\mathbb E_{\epsilon}[Y\mid T]\right)
+\mathbb E_T\!\left[\operatorname{Var}_{\epsilon}(Y\mid T)\right]
```

```diag
compare | 两个组件
Task / data noise | Prediction / execution noise
抽到哪些 task | 固定 task 上走到哪条 trajectory
更多 tasks 才能缩小 | repeated attempts 可估计并缩小
决定 new-task generalization | 决定 run-to-run stability
```

论文在其数据上发现 paired prediction noise 往往大于 paired data noise;这是经验结果,不是所有 Agent benchmark 的常数。课程的做法是先用 pilot 估组件,再做 budget projection:

```diag
flow | Pilot → design
小规模 N₀ × K₀ balanced pilot
估 task / attempt / batch variance
预测候选 N × K 的 CI width
加入 cost 与 latency constraint
选择满足 precision 的 design
```

*Hidden Measurement Error in LLM Pipelines* 进一步指出 prompt、judge choice 与 temperature 等未建模因素会造成 under-coverage。W3 的边界是:

- 若 claim 条件于一个冻结 prompt/verifier,把它们写进 $C$,CI 只覆盖该配置;
- 若 claim 要跨 prompt / judge generalize,它们必须成为 design 中被抽样或系统变化的 factors;
- judge 是否判对属于 Week 4 scorer validation,不能靠扩大 W3 error bar 修复。

---

## 五、四个常见但错误的 error bars

```diag
grid | Failure gallery
400-row Wald | 忽略 40 个 task clusters
bootstrap rows | 打散 task / repo dependence
bootstrap fixed bank | 把描述题库偷偷改成 new-task inference
CI over successful rows | missing / timeout 先改变了 denominator
```

### 5.1 Error bars 不重叠不是差异检验

A、B 各自的 marginal CI 描述两个单独 estimands。`A-B` 的 uncertainty 还取决于两者在相同 tasks 上的 covariance。下一课直接对 paired differences 建 CI。

### 5.2 More rows 不会修复 omitted factor

若每个 task 都只使用同一个 prompt 和 judge,增加到一百万 tasks 也不能估计 prompt/judge sensitivity。sample size 只缩小 design 实际随机化过的维度。

### 5.3 Narrow CI 不等于 valid claim

CI 不覆盖 task validity、verifier correctness、data contamination 或 deployment shift。它是「在已声明 statistical model 内有多精确」,不是整条 validity argument。

---

## 六、Coverage lab:让错误方法亲自失败

### 6.1 Synthetic data-generating process

```text
for simulation in 1..S:
  draw N task probabilities p_i from a heterogeneous distribution
  draw K Bernoulli attempts for each task
  compute the true target mean
  construct candidate 95% intervals
  record whether each interval covers the target
```

至少比较:

```diag
grid | Lab methods
naive row Wald | 假装 NK independent
row bootstrap | 错误 resampling unit
task bootstrap | resample task blocks
hierarchical interval | partial pooling + declared prior
```

### 6.2 输出不只是一张 coverage bar chart

```text
coverage · nominal target = 95%
median interval width
failure rate outside [0,1]
behavior at all-pass / all-fail boundaries
coverage by N, K and task heterogeneity
```

```diag
flow | Lab 最终判断
method nominal coverage 是否接近 95%
若否 · 是 finite-sample、clustering 还是 misspecification
若是 · interval 是否宽到无法支持 decision
把诊断带入 Lesson 4 power / MDE
```

### 6.3 Implementation gates

```text
[ ] random seed 固定,simulation truth 单独保存
[ ] resample key 是 task_id / declared cluster,不是 dataframe row index
[ ] 每个 replicate 重跑完整 aggregation 与 missing rule
[ ] 同时报告 coverage 和 width,不只挑一个好看的指标
[ ] 至少包含 p 接近 0 / 1 与少 clusters 的 stress case
[ ] fixed-bank 与 new-task simulation 分开,不共用同一个 truth
```

---

## 七、读材料时只回答这些问题

### Miller + Anthropic research note

- repeated answers 为什么先形成 question/task mean,再进入总体分析?
- clustered SE 的 cluster key 应由数据结构还是方便的字段决定?
- 原文推荐 CLT interval;Bowyer et al. 后来的 coverage experiments 对 small $N$ 加了什么限制?

### *Don't Use the CLT...*

- 为什么 Wald/CLT interval 在 all-pass 时会塌成零宽?
- Wilson、exact、bootstrap 与 Bayesian method 各在哪些设计下比较?
- 为什么「bootstrap」不是不看 resampling unit 的万能答案?

### 2025–2026 variance papers

- *Measuring all the noises* 的 data noise / prediction noise 如何映射成 task / attempt?
- 哪些结论是其大规模数据上的 empirical pattern,而不是定理?
- *Hidden Measurement Error* 中哪些因素在本课只是 sensitivity axis,哪些需要进入 target population?

来源与代码:

- [Adding Error Bars to Evals](https://arxiv.org/abs/2411.00640) · [Anthropic research note](https://www.anthropic.com/research/statistical-approach-to-model-evals)
- [Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints](https://arxiv.org/abs/2503.01747) · [Bayesian library](https://github.com/sambowyer/bayes_evals) · [reproduction code](https://github.com/sambowyer/no_clt_paper)
- [Measuring all the noises of LLM Evals](https://arxiv.org/abs/2512.21326) · [interactive analyses](https://all-the-noises.github.io/)
- [Hidden Measurement Error in LLM Pipelines](https://arxiv.org/abs/2604.11581) · [totalevalerror](https://github.com/SolomonMg/totalevalerror)
- [ReasonBENCH](https://arxiv.org/abs/2512.07795) · [code](https://github.com/au-clan/ReasonBench)

---

## 本课自检

```text
[ ] 能先说出 CI 重复抽样的世界,再解释 95% coverage
[ ] 能区分 fixed-bank、new-task 与 next-rollout uncertainty
[ ] 能解释为什么 40×10 不是 Wilson interval 的 n=400
[ ] 能写出 task / attempt variance 对 N 与 K 的依赖
[ ] 能用 ICC / design effect 解释 effective sample size,但不把它当最终算法
[ ] 能根据 design 选择 Wilson、task bootstrap、cluster bootstrap 或 hierarchical model
[ ] 能写出 task bootstrap:抽 task_id 并搬动完整 descendants
[ ] 能识别少 clusters、extreme outcomes 与 omitted factors 的风险
[ ] 能说明 CI 不覆盖 verifier validity、task validity 或 deployment shift
[ ] 能用 coverage simulation 比较方法,同时报告 coverage 与 width
```

---

## 本课一句话

> **Error bar 是 sampling design 的可执行摘要。**
> **重采样 task、repo、attempt 还是配置不是软件细节;它决定 interval 覆盖哪个 estimand,以及 400 行究竟包含 400、40 还是 10 份独立信息。**

下一课:有了 structure-aware uncertainty,才能直接估计 paired $\Delta=B-A$,预先写 meaningful improvement 与 power,并把整周结果压成一份可审计 Statistical Eval Report。
