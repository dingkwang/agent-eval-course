# 第 1 课:From Capability Claim to Benchmark Blueprint

## Benchmark 不是一袋题;它是一条从决策到证据的推理链

**Week 5 Day 1** · benchmark validity · 建议 80 分钟 + 25 分钟 blueprint exercise

> ### 本课唯一命题
> # 一个分数只能支持预先写清的能力主张。
> # 在收集 task 之前,先写 intended use、capability definition、target task distribution 与 validity argument。

> 📄 Liu et al., [*ECBD: Evidence-Centered Benchmark Design for NLP*](https://arxiv.org/abs/2406.08723), ACL 2024
> 📄 Bean et al., [*Measuring What Matters: Construct Validity in Large Language Model Benchmarks*](https://arxiv.org/abs/2511.04703), NeurIPS 2025 Datasets & Benchmarks
> 📄 Kwa et al., [*Measuring AI Ability to Complete Long Software Tasks*](https://arxiv.org/abs/2503.14499), 2025, updated 2026
> 📄 OpenAI & Tacit Labs, [*LifeSciBench*](https://cdn.openai.com/pdf/b4299379-0a97-4ffa-8b9b-c3fbb299caa9/lifescibench_preprint.pdf), 2026
> 💻 [METR Task Standard](https://github.com/METR/task-standard) · [METR public tasks](https://github.com/METR/public-tasks) · [HELM](https://github.com/stanford-crfm/helm)

```diag
flow | Week 4 与 Week 5 的接缝
Week 4 固定 task,审计 scorer 是否判对一次 outcome
冻结一把通过审计的尺子
Week 5 改问这些 task 为什么能代表目标能力
只有 validity argument 成立,aggregate score 才能支持 capability claim
```

Week 4 已经说明 `score != ground truth`。但就算每个 rollout 都被完美判分,下面这个箭头仍然没有自动成立:

```diag
pipe | 最危险的省略
在 500 道题上得到 72% → Agent 具备「真实软件工程能力」
```

中间至少缺少:能力定义、任务总体、抽样规则、测试条件、可观察证据和外推边界。本课把它们写成一份可审计 blueprint。

---

## 零、先从报告结论倒推

假设团队准备发布:

> Agent A 可以独立完成真实的软件工程工作。

这句话至少有五个尚未回答的问题:

```diag
grid | 一句 capability claim 隐藏的五个选择
对象 | model、model + harness、还是完整 product
工作 | bug fix、feature、migration、incident、research task
条件 | tools、network、budget、human help、repository access
成功 | outcome、process、policy compliance、还是用户价值
外推 | 哪些 repo、语言、难度、时间长度与组织环境
```

如果不回答,benchmark creator 可以在看到结果后随意移动解释:

```diag
flow | post-hoc claim inflation
只测 Python bug fix
得到高 pass rate
写成 coding capability
再写成 software engineering
最后写成 autonomous knowledge work
```

正确顺序相反:先冻结要支持的决策与结论,再设计能产生相应证据的任务。

---

## 一、Intended use:谁要用分数做什么决定

ECBD 的起点不是 capability 名称,而是 benchmark 的 intended use。

```diag
compare | 相同任务,不同 intended use
用途 | 需要的证据
回归测试 Agent 新版本 | 稳定覆盖已知产品失败模式
比较两个 harness | paired、相同 task 与预算、公平协议
预测真实部署价值 | 与 production task distribution 的外部效度
触发安全门槛 | 保守阈值、elicitation、极端能力与 false negative
研究能力结构 | item-level responses、任务属性与可解释构念
```

一份 benchmark 可以适合 regression,却不适合发布 leaderboard;也可以适合发现危险能力,却不适合估计普通用户成功率。

### 1.1 先写允许的 decision

```yaml
intended_use:
  user: "coding-agent release committee"
  decision: "whether candidate agent replaces production version"
  comparison: "candidate vs current agent under equal budget"
  target_context: "internal Python monorepos, issue-to-tested-patch workflow"
  unacceptable_uses:
    - "claiming general software-engineering autonomy"
    - "comparing scores produced with different tool or resource policies"
```

`unacceptable_uses` 不是礼貌性 disclaimer。它限定了结果可以进入哪些产品或安全决策。

---

## 二、Capability 是不可直接观察的 construct

「planning」「reasoning」「software engineering」都不能像 CPU time 一样直接读出来。我们只能看到 Agent 在特定条件下做出的行为。

```diag
nest | construct 隔着任务与证据被测量
Capability construct · 想知道但看不见
  Task demand · 用任务诱发能力
    Agent behavior · actions / artifacts / final state
      Observable evidence · trajectory / tests / state delta
        Score · 对 evidence 的编码
```

因此高分不是 capability 本身,而是支持某个 capability interpretation 的 evidence。

```math
C\longrightarrow P(Y\mid T,H,E,B)\longrightarrow S
```

$C$ 是目标能力,$T$ 是 task,$H$ 是 agent harness,$E$ 是 environment,$B$ 是预算,$S$ 是 scorer 产出的 observation。反向从 $S$ 推断 $C$,必须证明中间条件没有引入主导性 confounder。

### 2.1 用行为语言定义 capability

```diag
compare | 不可审计与可审计的定义
标签式定义 | 行为式定义
「长程规划能力」 | 在目标变化和中间失败下维护依赖关系、重规划并完成多阶段 outcome
「会用工具」 | 在给定 schema、权限与成本下选择工具、构造合法参数并使用返回状态推进任务
「软件工程能力」 | 从 issue 与 repository state 诊断问题、修改实现、验证行为并避免回归
```

行为式定义仍不是 task,但它开始说明 task 应该诱发哪些 observable demands。

### 2.2 Capability tree 不是词汇表

```diag
nest | coding-agent capability tree 示例
Repository-level task completion
  Problem understanding · 从 issue 与 repo 恢复要求
  Localization · 找到相关代码与状态
  Change planning · 跨文件依赖与修改顺序
  Implementation · 产生正确、可维护的 patch
  Validation · 运行检查、解释失败、避免 regression
  Recovery · 工具失败或假设错误后的重规划
```

树上的父子关系是一组假设:完成 repository task 是否真的依赖这些 sub-capabilities?某项 task success 能否区分 localization 与 implementation?这些关系要靠理论、专家判断或 item-level evidence 支持,不能因为图画得整齐就当成事实。

---

## 三、ECBD:把隐含选择变成六个可审计模块

Evidence-Centered Benchmark Design 要求每个设计选择回答三类问题:

```diag
grid | ECBD 的三列审计
Describe | 实际选择了什么
Justify | 为什么这个选择连接目标能力
Support | 什么理论或数据支持这个连接
```

课程采用一个面向 Agent 的六段版本:

| 模块 | 必答问题 | 典型产物 |
|---|---|---|
| Intended use | 谁用结果做什么决定? | decision contract |
| Capability | 要推断什么不可见能力? | construct definition / tree |
| Content | 哪些候选 task 能诱发相关行为? | task universe / item schema |
| Adaptation | Agent 在什么测试条件下作答? | harness、tools、budget policy |
| Assembly | 从候选池怎样组成发布集? | sampling / coverage plan |
| Evidence | 从 behavior 怎样得到 claim? | scorer contract + aggregation |

```diag
flow | 设计方向与证据方向
Intended use → Capability → Content → Adaptation → Assembly → Evidence
Evidence → observed score → capability interpretation → intended decision
```

第一行是设计;第二行是推断。如果推断链中的某个 warrant 不成立,最终 score 仍然可以 reproducible,但不能支持原定解释。

---

## 四、Target task distribution:不是「收集一些代表性题」

Benchmark 的目标不是覆盖所有可能任务,而是对一个定义清楚的 task population 取样。

```math
T_i\sim P_{target}(T\mid D,C)
```

$D$ 是目标 deployment context,$C$ 是纳入条件。`representative` 必须相对于这个分布说,不能脱离目标总体单独成立。

### 4.1 先定义 task universe 的轴

```diag
grid | repository agent 的候选 coverage axes
Work type | bug fix · feature · refactor · migration · investigation
Horizon | minutes · hours · multi-session
Scope | one function · one package · cross-service
Evidence | issue text · docs · tests · logs · user clarification
Tools | search · shell · compiler · browser · external API
Outcome | patch · diagnosis · artifact · deployed state
```

只有列出轴,才能发现 benchmark 其实只覆盖了一条窄带:

```diag
compare | headline 与实际支持范围
Headline claim | Observed task support
autonomous software engineering | public Python repositories
long-horizon agency | self-contained terminal tasks
real-world knowledge work | single-turn artifact production
tool use | canonical API calls with fixed schemas
```

### 4.2 现实频率与诊断覆盖不是同一目标

```diag
compare | 两种合理但不可混报的 assembly
Prevalence-weighted suite | Diagnostic / stress suite
按生产任务频率取样 | 故意放大罕见但关键 failure mode
估计平均产品表现 | 定位边界、回归与安全风险
需要 sampling weights | 不代表真实 prevalence
```

一个 benchmark 可以同时包含两部分,但报告必须分开。否则 rare stress cases 会扭曲平均部署成功率,而高频简单任务又会淹没重要能力边界。

---

## 五、Content module:每个 task 必须声明它诱发什么 evidence

候选 task 不是因为「很真实」「很难」就自动进入 benchmark。每一题都要写一条 item-level warrant:

```text
task features
→ required agent behaviors
→ observable evidence
→ capability interpretation
```

例如:

```diag
flow | item-level warrant 示例
跨三个 package 的状态不一致 bug
Agent 必须定位生产者与消费者的契约差异
trajectory 显示跨文件检索,patch 修复 invariant,regression tests 通过
为 repository-level localization + integration 提供一条 evidence
```

反例:

```diag
flow | 名字像能力,task 却没有诱发它
题目标签写着「planning」
最短解只需调用一个明显工具
所有成功轨迹都是单步 lookup
该题不能为 multi-step planning 提供 evidence
```

### 5.1 保存 item-level metadata

```yaml
task_id: payments-timezones-004
source: internal_issue_tracker
target_capabilities:
  localization: 2
  state_reasoning: 3
  change_planning: 2
nuisance_demands:
  repository_familiarity: 1
  build_complexity: 1
required_evidence:
  - cross_module_state_consistency
  - regression_suite_passes
validity_support:
  - expert_review
  - two_independent_human_completions
  - pilot_trajectory_analysis
```

没有 item-level mapping,coverage 只能停留在 benchmark 名称和总体分数上,无法检查某类 capability 是否只由两道题承担。

---

## 六、Coverage matrix:把「多样」变成可检查的结构

设 $M_{ic}$ 表示 task $i$ 对 capability $c$ 的需求强度:

```math
M_{ic}\in\{0,1,2,3\}
```

```diag
grid | task × capability demand matrix
task | localization · planning · tool-use · recovery
T01 bug fix | 3 · 2 · 2 · 1
T02 migration | 2 · 3 · 2 · 2
T03 log diagnosis | 3 · 1 · 3 · 2
T04 greenfield feature | 1 · 3 · 2 · 1
```

这个矩阵至少能发现四类问题:

```diag
grid | coverage audit
Hole | 某个目标 capability 没有 task
Token coverage | 名义上有一题,不足以支持稳定结论
Confounding | 两项 capability 永远一起出现,无法区分
Nuisance dominance | 所有难题同时依赖无关 setup / formatting
```

2026 年 Nature 的 *General Scales* 工作进一步给每个 item 建 demand profile,用 18 个 rubrics 研究 benchmark sensitivity、specificity 与新 item performance。[paper 与 ADeLe code/data](https://www.nature.com/articles/s41586-026-10303-2)。本课不要求复现其完整模型,但采用同一个关键方向:**从 benchmark label 下沉到 item demands。**

---

## 七、Adaptation module:测试条件也是能力定义的一部分

同一道 task 在不同测试条件下不是同一个测量:

```diag
grid | adaptation choices
Prompting | zero-shot · examples · policy reminder
Harness | plain loop · coding scaffold · planner / subagents
Tools | shell · browser · IDE · domain APIs
Resources | token · time · CPU · memory · parallelism
Assistance | clarification · hints · retries · human approval
```

这里不重复 W2 的 runtime implementation,而是问 validity:

> 这些条件是在合理 elicitation 目标能力,还是引入了另一种能力或优势?

```diag
compare | adaptation 改变了被测对象
声明 | 实际对象
比较两个 models | 比较 model + 各自不同 coding harness
测 autonomous completion | 中途提供 human clarification
测 tool selection | prompt 直接告诉正确工具顺序
测 robust planning | 失败后自动恢复 checkpoint 且隐藏代价
```

Blueprint 必须冻结 object of evaluation。否则 capability claim 会在 model、agent 和 product 之间漂移。

---

## 八、Assembly module:从候选池到发布集

有 10,000 道候选题、只能运行 300 道时,「随机抽 300」不一定解决 coverage;「每类挑最难的」也不代表目标分布。

```diag
flow | assembly 不是文件拼接
定义 target cells
估计候选池每个 cell 的数量与质量
设置 minimum coverage 与 sampling weights
按预注册规则抽取
冻结 release manifest
```

最小 manifest:

```yaml
benchmark_id: repo-agent-internal
release: 1.0.0
population: "eligible Python monorepo tasks closed in 2026-Q2"
sampling:
  design: stratified
  strata: [work_type, horizon, scope]
  seed: 20260825
  inclusion_rule: "self-contained under frozen repository snapshot"
coverage_minimums:
  migration: 20
  incident_diagnosis: 30
task_manifest_digest: sha256:...
```

W3 已经教统计 estimand;这里应用它:如果 sample design 与 target population 不同,要保存 inclusion probability / weights,不能把 curated stress set 的简单平均伪装成 population estimate。

---

## 九、Evidence module:把 W3 与 W4 接回来

```diag
pipe | 完整 validity chain
Intended decision → Capability construct → Target task distribution → Item demands → Agent behavior → Scorer evidence → Estimand → Claim
```

每一段分别可能断裂:

| 断点 | 结果 |
|---|---|
| task 不诱发目标能力 | construct underrepresentation |
| task 主要依赖无关因素 | construct-irrelevant variance |
| scorer 漏看或误判 evidence | measurement error · W4 |
| aggregation 与 sample design 不匹配 | estimand error · W3 |
| deployment 与 task population 不同 | external-validity failure |

这说明 benchmark validity 不是 scorer accuracy 的别名。W4 可以让最后一段更可信,但救不了错误的 capability definition 或 task distribution。

---

## 十、三个真实 benchmark 怎样做 blueprint

### 10.1 LifeSciBench:从 practitioner workflow 建 taxonomy

LifeSciBench 没有从现成 biology QA 开始。它调查 practicing scientists 的工作流,归纳七类 workflow,再跨七个 biological domains 组装 750 道 expert-authored tasks。

```diag
flow | LifeSciBench construction argument
真实使用目标:支持 life-science research
调查从业科学家的 recurring workflows
建立 workflow × domain taxonomy
173 位专家写 prompt + artifacts + rubric
独立专家验证 relevance / alignment / grounding / usefulness
```

它还公开边界:单轮 self-contained task 不能替代 live research workflow;真实科研会持续收集新证据、调整假设并迭代实验。承认边界反而让 capability claim 更可信。[LifeSciBench §3–4 与 Limitations](https://cdn.openai.com/pdf/b4299379-0a97-4ffa-8b9b-c3fbb299caa9/lifescibench_preprint.pdf)

### 10.2 METR time horizon:把抽象 autonomy 连接到 human duration

METR 把「Agent 能独立工作多久」操作化为:

```math
h_{50}=\text{human task duration where fitted Agent success}=0.5
```

```diag
flow | METR 的 operationalization
抽象主张:完成更长任务的能力
用有相关经验的人类完成时间作 task 属性
收集跨分钟到多小时的 technical tasks
拟合 success 对 duration 的关系
报告 50% task-completion horizon
```

这比一个无单位 leaderboard score 更容易解释,但仍受 task distribution 约束。论文任务以软件、ML、cyber 与可通过 text/bash 完成的工作为主;不能直接写成「任意人类工作时长」。

### 10.3 HELM:覆盖更多 scenario 与 desiderata

HELM 把 evaluation space 拆成 scenarios 与 metrics/desiderata,避免只看 accuracy。它是 coverage design 的经典起点。[HELM paper](https://arxiv.org/abs/2211.09110)

但 ECBD 对 HELM 的 case study 也指出:从「practical utility」到 accuracy、calibration、robustness、fairness 等维度的连接仍需要进一步论证。**列出更多维度不等于已经证明 construct validity。**

---

## 十一、Blueprint:在第一道 task 之前提交

```yaml
benchmark:
  id: repo-agent-capability-v1
  owner: evals-team

intended_use:
  decision: "compare candidate and production coding agents"
  users: [release_committee, agent_engineers]
  target_context: "internal issue-to-patch workflow"
  prohibited_claims: ["general intelligence", "all software engineering"]

object_of_evaluation:
  unit: "model + frozen agent harness"
  tools: [shell, repository_search, editor]
  assistance: none
  budget: {wall_minutes: 120, token_limit: 200000}

construct:
  name: "autonomous repository task completion"
  definition: "recover requirements, modify a repository, and validate a functional outcome"
  subcapabilities: [localization, planning, implementation, validation, recovery]

task_population:
  source: "eligible internal issues"
  inclusion: [reproducible, self_contained, rights_cleared]
  exclusions: [visual_only, requires_private_human_context]
  axes: [work_type, horizon, scope, tool_demand]

assembly:
  design: stratified
  target_n: 300
  weights: deployment_prevalence
  stress_slice_reported_separately: true

evidence:
  required: [trajectory, patch, test_results, final_state]
  scorer_contract: scorer-contract-v3
  estimand: task_macro_pass_1

validity_plan:
  content_review: two_domain_experts
  human_feasibility: required
  pilot_models: [weak, mid, frontier]
  item_demand_annotation: required
  known_limitations: []
```

这份文件不是最终答案。它是一组可以被 reviewer 攻击、被数据推翻、被版本化的假设。

---

## 十二、P3 checkpoint:审计 METR public task suite

打开:

- [`METR/public-tasks/suite_manifest.yaml`](https://github.com/METR/public-tasks/blob/main/suite_manifest.yaml)
- `complex_payments/`
- `hypothesis_testing/`
- `local_research/`
- [`METR/task-standard/STANDARD.md`](https://github.com/METR/task-standard/blob/main/STANDARD.md)

完成三张表。

### A. Claim ledger

| 字段 | 回答 |
|---|---|
| intended user / decision | |
| object of evaluation | |
| capability definition | |
| supported inference | |
| unsupported inference | |

### B. Item-demand matrix

```text
                    planning  coding  research  tool-use  recovery
complex_payments        ?        ?        ?         ?         ?
hypothesis_testing      ?        ?        ?         ?         ?
local_research          ?        ?        ?         ?         ?
```

每个数字旁边必须写 task evidence,不能只凭目录名。

### C. Standard ≠ validity

回答:

1. METR Task Standard 保证了哪些 task-package properties?
2. 哪些 capability / coverage 问题完全不在 standard 的职责内?
3. 一个符合 standard 但 construct-invalid 的 task 会是什么样?

---

## 十三、验收

```text
[ ] 先写 intended decision,再选择 task
[ ] 明确 object of evaluation 是 model、agent 还是 product
[ ] 用行为语言定义 capability,不只贴 reasoning / planning 标签
[ ] 写出 target task distribution 与禁止外推范围
[ ] 每个 task 有 item-level demand → evidence warrant
[ ] 区分 prevalence-weighted suite 与 diagnostic stress suite
[ ] coverage matrix 能显示 hole、confounding 与 nuisance dominance
[ ] adaptation / budget 被视为测量定义的一部分
[ ] assembly 规则、seed、weights 与 manifest 可追溯
[ ] 能解释 portable task standard 为什么不等于 valid benchmark
[ ] blueprint 的每项关键选择都有 describe / justify / support
```

> ## 本课结论
> **Benchmark 不是「dataset + scorer」,而是一条从 intended decision 到 capability evidence 的推理链。**
>
> 下一课不再重复显然的 hard vs broken,而是审计更难的问题:一个低通过率 task 的难度,究竟来自目标能力,还是来自 prompt、信息、环境和 solution-space artifact?

---

## References

1. Yu Lu Liu et al. [ECBD: Evidence-Centered Benchmark Design for NLP](https://arxiv.org/abs/2406.08723), ACL 2024. Intended use、capability、content、adaptation、assembly 与 evidence 的设计骨架;[worksheet repo](https://github.com/isle-dev/ECBD)。
2. A. M. Bean et al. [Measuring What Matters: Construct Validity in Large Language Model Benchmarks](https://arxiv.org/abs/2511.04703), NeurIPS 2025 Datasets & Benchmarks. 445 个 benchmark 的系统审查;[review code/data](https://github.com/am-bean/benchmark_review)。
3. Thomas Kwa et al. [Measuring AI Ability to Complete Long Software Tasks](https://arxiv.org/abs/2503.14499), 2025, updated 2026. Human-duration operationalization、task suite 与 external-validity 边界。
4. OpenAI & Tacit Labs. [LifeSciBench: Evaluating Language Models on Realistic, Expert-Level Tasks in the Life Sciences](https://cdn.openai.com/pdf/b4299379-0a97-4ffa-8b9b-c3fbb299caa9/lifescibench_preprint.pdf), 2026. Practitioner-derived taxonomy、expert construction 与 independent validation。
5. Percy Liang et al. [Holistic Evaluation of Language Models](https://arxiv.org/abs/2211.09110), 2022/2023. Scenario × metric taxonomy;[HELM repository](https://github.com/stanford-crfm/helm)。
6. Lujia Zhou et al. [General scales unlock AI evaluation with explanatory and predictive power](https://www.nature.com/articles/s41586-026-10303-2), Nature 2026. Item demand profiles、benchmark sensitivity/specificity 与 [ADeLe code/data](https://kinds-of-intelligence-cfi.github.io/ADELE/)。
7. METR. [Task Standard](https://github.com/METR/task-standard), [Example Task Suite](https://github.com/METR/public-tasks), and [RE-Bench](https://github.com/METR/RE-Bench). 可执行 Agent task、task families 与 human baselines 的源码材料。
