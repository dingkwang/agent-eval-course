# 第 2 课:Task Validity & Construct-Irrelevant Difficulty

## 同样是 10% pass rate,为什么有的 task 测到能力、有的只测到 artifact

**Week 5 Day 2** · task admission · 建议 80 分钟 + 30 分钟 audit exercise

> ### 本课唯一命题
> # 低通过率不是 task quality evidence。
> # 必须证明 task 的难度由目标 capability demand 产生,而不是 hidden information、reference-path lock-in、环境摩擦或无关格式。

> 📄 OpenAI, [*Separating signal from noise in coding evaluations*](https://openai.com/index/separating-signal-from-noise-coding-evaluations/), 2026
> 📄 OpenAI, [*Why SWE-bench Verified no longer measures frontier coding capabilities*](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/), 2026
> 📄 Wijk et al., [*RE-Bench*](https://arxiv.org/abs/2411.15114), 2024
> 📄 OpenAI & Tacit Labs, [*LifeSciBench*](https://cdn.openai.com/pdf/b4299379-0a97-4ffa-8b9b-c3fbb299caa9/lifescibench_preprint.pdf), 2026
> 📘 Anthropic, [*Demystifying evals for AI agents*](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), 2026

```diag
flow | 本课不是二分词汇课
观察到 task pass rate 很低
分解 task 实际施加的 demands
用 context、alternate paths、humans 与 perturbations 收集证据
判断低分能否归因给目标 capability
决定 keep / fix / quarantine / reject
```

「hard 与 broken 不同」一句话就能讲完。本课研究的是困难的部分:**面对边界案例,怎样用可重复的 evidence 解释 task 为什么难。**

---

## 零、同一个 10%,五种完全不同的解释

| task | 10% pass rate 的主要原因 | 支持目标 capability claim? |
|---|---|---:|
| A | 跨文件定位、修改与验证确实很难 | 是 |
| B | prompt 漏掉 hidden test 要求 | 否 |
| C | 只接受 gold patch 使用的 internal helper | 否 |
| D | 时间预算远低于 competent human 的最短路径 | 测到 speed/budget,需改 claim |
| E | 任务同时要求目标 planning 与无关冷门 CLI 语法 | 混合,需进一步分解 |

```diag
compare | difficulty 与 validity 是两条轴
Difficulty | Validity
目标对象在指定条件下多大概率成功 | outcome 是否能解释为目标 construct 的 evidence
随 model / harness / budget 改变 | 相对于 task contract 与 capability claim 判断
低 success 不等于有问题 | invalid task 可以很容易、也可以很难
```

难度是条件概率,不是 task 的永久标签:

```math
d_i(A,H,E,B)=1-P(Y=1\mid T_i,A,H,E,B)
```

同一题对不同 Agent population、harness、environment 与 budget 可以有不同难度。真正要审计的是:

```math
\text{observed difficulty}
=\text{target demand}+\text{realistic co-demand}+\text{irrelevant nuisance}+\text{task defect}
```

---

## 一、先冻结 task bundle,不要只读 prompt

Agent task 不是一段自然语言:

```diag
nest | Task bundle
Instruction · 可见要求与成功目标
  Initial state · repo / DB / files / UI
    Available information · docs / logs / nearby code / clarification
      Action surface · tools / permissions / network
        Resource policy · time / tokens / compute
          Success contract · accepted outcomes / prohibited side effects
```

task validity 是整个 bundle 的属性。只 proofread prompt,看不到这些错误:

```diag
grid | prompt 之外的 defect
Initial state | dependency 缺失、gold patch 已部分应用、数据过期
Information | 必要 requirement 只存在于 reviewer 私有上下文
Tools | 任务要求浏览,但 network policy 禁止访问
Budget | setup 已消耗大部分时限
Success | tests 绑定 reference implementation 或漏查副作用
```

W4 从 scorer 角度问 predicate 会不会误判一条 trajectory;本课从 benchmark admission 角度问:**这整个 task bundle 能不能进入声称测量某能力的数据集。**

---

## 二、Task-demand decomposition:先解释最短成功路径

对每个 task,至少写出一条合理的最短成功路径,再将步骤映射到 demands。

```diag
flow | repository bug task 的成功路径
理解 issue 与 reproduction
定位跨模块状态流
形成 failure hypothesis
修改 producer / consumer contract
运行 targeted tests
解释 regression 并修正
```

然后把 demands 分成三类:

```diag
grid | demand 分类
Target construct | 本来就想测的能力
Realistic co-demand | 现实完成任务不可避免、但不是主结论的能力
Irrelevant nuisance | 与 claim 无关,却显著影响 success 的因素
```

示例:

| demand | 分类 | 理由 |
|---|---|---|
| 跨文件 code localization | target | blueprint 明确要测 repository work |
| 阅读项目惯用 test structure | realistic co-demand | 真实 repo 工作的一部分 |
| 猜未记录的产品经理口头要求 | task defect | Agent 没有可获得 evidence |
| 使用某个未说明 helper 名称 | irrelevant nuisance | 功能等价实现不依赖它 |
| 构建系统偶发下载失败 | W6 infra noise | 不是本课的 capability demand |

### 2.1 名义 skill label 不算分解

```diag
compare | label 与 mechanism
「planning task」 | task 需要维护哪些依赖、在哪些 feedback 后重规划
「tool-use task」 | 成功需要选择什么 tool、参数错误怎样暴露
「long-horizon task」 | 有多少相互依赖的状态转换,而不只是 wall time 长
「research task」 | 需要提出、区分并更新哪些 hypotheses
```

如果 reviewer 不能说明低分是由哪段 mechanism 产生,`hard` 只是形容词。

---

## 三、Information sufficiency:可推导不等于显式写出

现实任务不会把所有信息都写进 prompt。把任何 ambiguity 都叫 broken,会把 benchmark 变成教科书题;把任何遗漏都叫「需要主动探索」,又会替 hidden requirements 开脱。

正确问题是:

```math
I_{required}\subseteq \operatorname{closure}(I_{observable},R_{reasonable})?
```

$I_{observable}$ 是 Agent 可以看到的信息,$R_{reasonable}$ 是目标对象应具备的合理推导规则。`closure` 表示通过 repository conventions、docs、tool observations 与允许的交互可以恢复的信息。

```diag
compare | reasonable ambiguity 与 true underspecification
Reasonable ambiguity | True underspecification
要求可从类型、邻近代码与公开 convention 恢复 | hidden test 引入任何可见材料都没有的要求
多个线索互相支持 | 只能从 gold patch 反推
目标专家通常会主动调查 | 独立专家给出互不兼容解释
澄清能减少时间,但不是唯一成功路径 | 缺少澄清就没有唯一可判定 outcome
```

OpenAI 对 SWE-Bench Pro 的深度 review 让 investigator agents 进入 repository、运行 tests、检查 model attempts 与 nearby conventions,正是为了区分可由 repo context 消解的合理 ambiguity 与真正的 underspecification。[audit methodology](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)

### 3.1 Information ledger

```yaml
requirement: "preserve backward-compatible timezone parsing"
visibility:
  prompt: absent
  public_docs: present
  nearby_code: present
  existing_tests: partial
  gold_patch_only: false
reasonable_for_target_agent: true
review_evidence:
  - docs/api.md#timezone-inputs
  - parser.py:41-68
```

每条 hidden assertion 都应能回到至少一个 Agent 可见 source。`gold patch says so` 不是充分来源。

---

## 四、Solution-space audit:gold solution 是 witness,不是定义

Reference solution 最多证明:

```math
\exists x:\;U(x)=1
```

它不证明只有这条 path 合法:

```math
\{x:U(x)=1\}=\{x_{gold}\}
```

```diag
compare | reference witness 与 reference lock-in
Witness | Lock-in
证明任务至少存在一条完成路径 | 把 gold patch 的实现细节当 success definition
帮助验证 feasibility | 拒绝不同 abstraction、顺序或数据结构
可用于构造 positive control | 把相似度当 correctness
```

### 4.1 画出 equivalence classes

对 coding task,合法 solution space 可能包含:

```diag
grid | 功能等价,实现不同
Patch A | 修改 parser,集中 normalize
Patch B | 修改 callers,在边界 normalize
Patch C | 引入兼容 wrapper,保留旧 API
Patch D | 重构内部表示,外部 behavior 不变
```

不能仅因为 D 与 gold diff 很远就拒绝;也不能仅因为 patch 与 gold 相似就认为完成。应由产品行为、invariants 与 prohibited side effects 定义 equivalence。

### 4.2 Alternate-valid controls

```diag
flow | solution-space audit
从 contract 写行为 invariants
让独立专家产生第二条合法路径
执行同一 scorer / tests
若 alternate-valid FAIL,定位绑定的实现细节
把它加入 task regression controls
```

这复用 W4 的 control 思想,但结论不同:W4 决定 scorer 是否升级;W5 决定 task 是否有资格代表目标能力。

---

## 五、Human feasibility 不是「找个人做出来」

一个 author 能运行自己的 gold solution,只证明作者知道自己的意图。更强的 feasibility evidence 包括:

```diag
grid | feasibility ladder
L0 | author solution 在 frozen environment 可运行
L1 | 独立专家只看 Agent-visible information 能完成
L2 | 多位专家对 requirement 与 success criteria 基本一致
L3 | completion time / clarification / failure traces 被记录
L4 | 专家提出的 alternate-valid solutions 也被接受
```

RE-Bench 不只发布七个 ML research engineering environments,还收集了 61 位不同专家的 71 次八小时 attempts。82% 的 expert attempts 得到 non-zero score,24% 达到或超过 strong reference solutions。[RE-Bench](https://arxiv.org/abs/2411.15114)

这些数据提供的不只是「人能做」:

- task 是否需要目标 expertise;
- 八小时预算是否让专家产生进展;
- reference solution 是否处在合理 performance range;
- humans 与 agents 的 strategy / time-return 怎样不同。

### 5.1 Human failure 不自动证明 broken

```diag
compare | 两个错误推断
一个专家失败 | 任务 broken
一个作者成功 | 任务 valid
```

需要检查 expertise、budget、可见信息、环境一致性和失败原因。Feasibility 是证据组合,不是单个 bool。

---

## 六、Controlled perturbations:用因果 probe 找出「为什么难」

如果一个因素理论上不属于目标 construct,改变它不应重写 benchmark 结论。构造保持核心任务不变的 variants:

```diag
grid | task perturbation suite
Information | 补充疑似遗漏 requirement / 去掉多余 hint
Surface | 改格式、命名、文件顺序、无关 prose
Environment | 固定无关 setup friction,保持可用 tools 不变
Solution | alternate-valid implementation / action order
Budget | 增加 time / tokens,观察 failure mode 转换
```

设 $Z$ 是目标 demand,$N$ 是 nuisance,$Y$ 是成功。我们希望 nuisance perturbation 的影响受控:

```math
\Delta_N=P(Y=1\mid Z,N_1)-P(Y=1\mid Z,N_0)
```

如果只改无关 formatting 就让成功率从 10% 变成 70%,原 task 的低分主要不能解释为目标能力。

### 6.1 三种 perturbation 结论

| 结果 | 解释 | 动作 |
|---|---|---|
| semantic-preserving variants 稳定 | 对 surface nuisance 较 robust | 支持 keep |
| 补充必要信息后大幅改善 | 原题可能 underspecified | fix / quarantine |
| 增加 budget 后逐步改善且策略相同 | task 测到 horizon / efficiency | 修改 claim 或分预算报告 |
| alternate-valid path 被拒绝 | solution-space 过窄 | 修 success contract |
| 去掉 irrelevant setup 后模型排名反转 | benchmark 混入 setup capability | 拆 slice 或 redesign |

不是所有 sensitivity 都是 bug。如果 benchmark 明确测 prompt robustness,format sensitivity 就是 construct;如果 benchmark 声称测 domain reasoning,它更可能是 nuisance。判断永远相对于 blueprint。

---

## 七、Pilot trajectories:不要只看 aggregate pass rate

至少选择三档 Agent / harness 做 pilot:

```diag
grid | pilot panel
Null / weak | 找 accidental pass、shortcut 与 constant criteria
Mid-level | 暴露 specification friction 与常见失败模式
Frontier / expert | 寻找 ceiling、alternate paths 与 task defects
```

对每道题保存 reason-coded failure attribution:

```yaml
task_id: repo-184
trial_id: frontier-agent-03
outcome: FAIL
attribution:
  primary: INFORMATION_GAP
  secondary: TEST_REFERENCE_LOCK
evidence:
  - "hidden test requires behavior absent from issue/docs/code"
  - "alternate expert patch rejected"
confidence: high
reviewer_ids: [r12, r19]
```

```diag
compare | aggregate 看不到的两种 0 分
Capability failure | Task-validity failure
Agent 看到了足够 evidence,但形成错误 hypothesis | requirement 不在 observable information set
Agent 选择了错误修改并产生 regression | 功能等价 patch 被 gold-specific test 拒绝
可以进入 capability analysis | 应进入 task QA queue
```

本课只要求 pilot 产生 task-level evidence。如何抽样、怎样避免自动筛查漏掉 unflagged tasks,留给 Lesson 3。

---

## 八、SWE-Bench audits:筛掉「难」会让 benchmark 更差

OpenAI 2026 对 SWE-bench Verified 的审计选择了 138 个 o3 经常失败的任务;至少 59.4% 被认为存在实质性 test design 或 problem-description 问题。这个样本是困难子集,不是 500 题的随机样本,所以不能外推成全 benchmark broken prevalence。[Verified audit](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)

SWE-Bench Pro 的后续 pipeline 在 731 个 public tasks 中先 flag 286 个候选,再通过 investigator-agent + researcher 与五名工程师 review,分别识别 200 与 249 个 broken tasks。[Pro audit](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)

四个主要 failure families:

```diag
grid | SWE-Bench Pro task-bundle failures
Overly strict tests | 强制 prompt 未要求的实现细节
Underspecified prompts | hidden tests 检查不可合理推导的要求
Low-coverage tests | 不完整修复也能通过
Misleading prompts | 可见要求把 Agent 引向错误 behavior
```

但正确治理动作不是删除所有低通过率 task:

```diag
flow | 错误的清洗策略
按 frontier pass rate 排序
删除最难的 30%
broken tasks 可能减少
真正 frontier-discriminating tasks 也被删除
benchmark 快速饱和
```

需要根据 defect evidence 而不是 difficulty threshold 做 admission。

---

## 九、Task admission rubric

每道候选 task 至少经过六个 gates:

| Gate | 核心问题 | Evidence |
|---|---|---|
| Construct alignment | 成功是否需要 blueprint 中的 target demand? | demand decomposition |
| Information sufficiency | 必要 requirement 能否从可见信息合理恢复? | information ledger |
| Feasibility | 独立目标专家能否在冻结条件下推进/完成? | human attempts |
| Solution breadth | 合法 alternate paths 是否被接受? | alternate-valid controls |
| Nuisance robustness | 无关 perturbation 是否主导结果? | variant outcomes |
| Diagnostic value | item 是否补 coverage hole 或区分能力区间? | pilot response matrix |

```diag
flow | admission decision
六个 gates 都有 evidence
KEEP
可定位且能修复 contract / data / tests
FIX → 重新走全部 gates
证据不足或 reviewer disagreement 未解决
QUARANTINE
核心 construct 不对齐或不可恢复
REJECT
```

### 9.1 不要静默修题

一旦 task 已发布,修 prompt、state 或 success criteria 都可能改变测量对象:

```text
task_id: repo-184
old_digest: sha256:aaa...
new_digest: sha256:bbb...
change_reason: INFORMATION_SUFFICIENCY
comparability: BREAKING
requires_rerun: true
```

完整 lifecycle 与 benchmark versioning 在 Lesson 4 展开;这里先保留 task lineage。

---

## 十、P3 checkpoint:解释一个任务为什么难

选择 [`METR/public-tasks`](https://github.com/METR/public-tasks) 中一个 task family,不要先运行 frontier model。提交以下材料。

### Step 1:写 success path

```text
initial observation
→ first information-gathering action
→ intermediate hypothesis
→ state-changing work
→ validation
→ submission
```

### Step 2:写 demand decomposition

| demand | target / realistic co-demand / nuisance | evidence |
|---|---|---|
| | | |

### Step 3:写 information ledger

列出每个 success criterion 所需信息在哪里可见。任何只存在于 solution / grader 的 requirement 都要 flag。

### Step 4:设计四个 variants

```text
V0 original
V1 semantic-preserving surface mutation
V2 suspected missing-information clarification
V3 alternate-valid solution or path
```

预注册每个 variant 可能支持或推翻的解释,不要看到结果后再编原因。

### Step 5:给 admission decision

```yaml
decision: KEEP | FIX | QUARANTINE | REJECT
claim_supported:
claim_not_supported:
primary_evidence:
remaining_uncertainty:
required_followup:
```

---

## 十一、验收

```text
[ ] 不把 hard vs broken 当成主要知识点
[ ] 把 difficulty 写成 Agent / harness / environment / budget 条件下的量
[ ] 审计完整 task bundle,而不只 proofread prompt
[ ] 能把 demands 分成 target、realistic co-demand 与 nuisance
[ ] 用 observable information closure 区分合理 ambiguity 与 underspecification
[ ] gold solution 只作为 feasibility witness,不定义唯一合法路径
[ ] 至少有一个独立 human attempt 与一个 alternate-valid control
[ ] 用 controlled perturbation 检查 difficulty attribution
[ ] pilot 同时包含 weak、mid 与 frontier / expert behavior
[ ] 根据 defect evidence 做 keep / fix / quarantine / reject,不按低 pass rate 删除
[ ] task 修订保留 digest、reason 与 comparability
```

> ## 本课结论
> **高质量 difficult task 的标准不是「frontier model 做不出来」,而是「在信息充分、solution space 合理、环境与 budget 明确的条件下,失败仍可归因给目标 capability demand」。**
>
> 低通过率只是现象;task admission 需要一条可以被 perturbation、human attempt 与 alternate path 攻击的因果解释。

---

## References

1. OpenAI. [Separating signal from noise in coding evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/), 2026. SWE-Bench Pro 的 task-bundle failure taxonomy 与 agent-assisted / human review 方法。
2. OpenAI. [Why SWE-bench Verified no longer measures frontier coding capabilities](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/), 2026. 困难子集中的 narrow / wide tests 与抽样解释边界;contamination 留给 W7。
3. Hjalmar Wijk et al. [RE-Bench: Evaluating frontier AI R&D capabilities of language model agents against human experts](https://arxiv.org/abs/2411.15114), 2024. 开放式 task、human expert attempts、budget 与 reference-solution evidence;[repo](https://github.com/METR/RE-Bench)。
4. OpenAI & Tacit Labs. [LifeSciBench](https://cdn.openai.com/pdf/b4299379-0a97-4ffa-8b9b-c3fbb299caa9/lifescibench_preprint.pdf), 2026. Question-rubric consistency、scientific ambition、fact checking、多轮 expert review 与 independent validation。
5. Anthropic. [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), 2026. Agent task / trial / outcome 定义、task design 与 transcript inspection 的工程实践。
6. METR. [Example Task Suite](https://github.com/METR/public-tasks) 与 [Task Standard](https://github.com/METR/task-standard). 本课 audit exercise 的源码对象。
