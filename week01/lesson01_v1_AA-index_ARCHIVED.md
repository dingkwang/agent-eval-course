# 第 1 课:如何拆解一个现代 AI Benchmark
## 以 Artificial Analysis Intelligence Index 为例

**课程模块**:Agent Evaluation & Benchmark Engineering · Week 1 Day 1
**建议学习时间**:60–90 分钟
**资料版本**:Artificial Analysis Intelligence Index **v4.1.1**,2026 年 8 月

> 📎 **素材锚点**:`docs/aa-intelligence-benchmarking-methodology.md`(2026-08 headless 抓取的官方方法论页)。
> 本课**所有数字均已对该快照逐条核验**;凡未能核验的,文中显式标注为「待确认」。

---

## 一、本课学习目标

完成本课后,你应该能够:

1. 区分 **benchmark、evaluation、metric、scorer、agent harness 和 environment**;
2. 使用统一模板分析任一 benchmark:**Task 测什么?Repeat 为什么重复?Scorer 如何判断成功?Agent 能用什么工具和环境?**
3. 解释 Intelligence Index 如何由多个 benchmark 聚合而成;
4. 识别一个 leaderboard 分数中混合了哪些因素;
5. 初步判断一个 benchmark 的结果是否真的代表它声称的能力。

**重点不是记住九个 benchmark 的名字**,而是建立一套以后分析任何 benchmark 都能复用的框架。

---

## 二、为什么从 Artificial Analysis 开始

它提供公开排行榜,**同时披露** benchmark 构成、运行参数、评分方式、重复次数和部分 agent harness —— 这在业界并不常见,所以适合当解剖对象。

**已核验事实**(原文):
> *"Artificial Analysis Intelligence Index is a **text-only, English language** evaluation suite. We benchmark models for image inputs, speech inputs and multilingual performance **separately**."*
>
> *"Intelligence Index is calculated as a weighted average across four categories: **Agents (34%), Coding (24%), Scientific Reasoning (24%) and General (18%)**. The weighting **emphasizes agentic tasks**."*

它是一个**综合指数**,不是一个单独的 benchmark。因此:

> **一个模型的 Intelligence Index 分数,不代表某一种单独能力,而是九项评价经过人为选取和加权后形成的综合指标。**

读排行榜时不能只问「哪个模型分数最高?」,还要问:

> 它在哪些任务上得分?用了什么环境?运行了多少次?评分器是什么?**为什么这些 benchmark 被赋予这些权重?**

---

## 三、Benchmark 的基本组成

一次 evaluation 可以表示为:

```
Evaluation Result = f( Task, Model, Harness, Environment, Budget, Scorer, Randomness )
```

**这七个因子里只有一个是 Model。** 这是全课的第一性认识。

### 3.1 Task

Task 是交给被测系统完成的工作:回答选择题 · 编写 Python 函数 · 在 terminal 中修复系统 · 搜索知识库并修改银行账户状态 · 读多个长文档后回答 · 生成 PDF/Excel/PPT 文件。

任务决定了 benchmark **声称**测量的能力。但——

> ⚠️ **任务名称 ≠ 实际测量对象。**
> 一个叫 "scientific reasoning" 的 benchmark,可能同时测量:学科知识 · 数学推导 · Python 编程 · 输出格式遵循 · context window · grader 对答案的解析能力。

### 3.2 Repeat

Repeat = 同一任务被独立运行多少次。设 benchmark 有 N 个任务,每个跑 R 次:

```
y[i,r] = 1  若第 i 个任务的第 r 次运行成功
       = 0  否则
```

**Repeated pass@1** 本质上是:

```
Score = (1 / (N·R)) · Σ_i Σ_r  y[i,r]
```

例:一个任务跑五次成功三次,它对最终平均成功率的贡献是 60%。**这不是 pass@5。**

| | 定义 | 回答的问题 |
|---|---|---|
| **Repeated pass@1** | 独立跑 R 次,取平均成功率 | 随机运行**一次**,成功概率多大? |
| **pass@k** | R 次中**至少一次**成功即算成功 | 允许尝试 k 次,至少成功一次的概率多大? |

两者回答的问题**完全不同**。AA 通常使用 pass@1;有多次 repeat 的项目,将所有 repeat 的结果共同纳入平均。

> 📌 这个区别是 **Day 4 统计课**的入口,也是最常见的 leaderboard 误读来源。

### 3.3 Scorer(也叫 grader / verifier)

| 类型 | 做法 | 优点 | 局限 |
|---|---|---|---|
| **Exact match** | 字符串完全一致 | 简单、确定 | 拒绝语义正确但表达不同的答案 |
| **Regex extraction** | 先抽 A/B/C/D 再比对 | 适合选择题 | 受输出格式与 extraction logic 影响 |
| **Unit tests** | 跑代码看是否通过测试 | 接近功能正确性 | 覆盖不足时,错误实现也能通过 |
| **Environment-state verifier** | 直接检查结束后的数据库/文件系统/应用状态 | **不看 agent 怎么说,只看世界变成什么样** | 环境构建成本高;可能只验最终态,不验中间过程 |
| **LLM-as-a-judge** | 让另一个模型评价或比较 | 适合开放式回答与复杂文件 | judge bias · position bias · verbosity bias · rubric ambiguity · **grader version drift** |
| **Human evaluation** | 人类专家评价 | 贴近真实价值 | 昂贵、慢、也不一定一致 |

### 3.4 Tool / Harness / Environment —— 必须分开的三个概念

**Tool**:模型可调用的具体动作(搜索知识库 · 执行 shell · 读文件 · 改数据库 · 浏览网页 · 提交最终答案)。

**Agent harness**:包裹模型的执行框架,负责——把观察结果给模型 · 解析 tool call · 执行工具 · 返回结果 · 管理上下文 · 控制最大轮数 · 判断何时结束。
> **相同模型放进不同 harness,结果可能明显不同。**

**Environment**:工具实际操作的外部状态(Linux container · Git repo · 银行后台数据库 · 文件系统 · SaaS 模拟服务器 · Kubernetes incident snapshot)。

对 agent benchmark,真正被评价的往往不是裸模型,而是:

```
Model + Prompt + Harness + Tools + Environment
```

---

## 四、Intelligence Index v4.1.1 的九项 Evaluation

> ✅ **下表逐格核验自 `docs/aa-intelligence-benchmarking-methodology.md` 的官方表格**,权重合计 = 100%。

| 类别 | Benchmark | Questions | Repeat | Scoring | 权重 | Tool Usage |
|---|---|---|---:|---|---:|:---:|
| **Agents (34%)** | GDPval-AA v2 | 220 tasks | 1 | Pairwise comparison (Elo) by judge panel,锚定人类专家 = 1000,frozen & scaled | **20%** | ✓ |
| | τ³-Banking | 97 | 5 | **Backend database state evaluation**, pass@1 | **14%** | ✓ |
| **Coding (24%)** | Terminal-Bench v2.1 | 89 | 3 | Test suite pass/fail, pass@1 | **16%** | ✗ ⚠️ |
| | SciCode | 288 subproblems | 3 | Code execution, pass@1, sub-problem scoring | **8%** | ✗ |
| **General (18%)** | AA-LCR | 100 | 3 | Equality Checker LLM, pass@1 | **6%** | ✗ |
| | AA-Omniscience | 6,000 | 1 | **Accuracy (8%) + (1 − Hallucination Rate) (4%) 两个独立分量** | **12%** | ✗ |
| **Scientific Reasoning (24%)** | HLE (Humanity's Last Exam) | 2,158 | 1 | Equality Checker LLM, pass@1 | **12%** | ✗ |
| | GPQA Diamond | 198 | 5 | Regex extraction, pass@1 | **6%** | ✗ |
| | CritPt | 70 | 5 | Official grading server, pass@1 | **6%** | ✗ |

> 🔍 **核验补充(比常见转述更精确的三点)**
> 1. **AA-Omniscience 的 12% 不是一个整块**,官方表写明是 `Accuracy (8%)` 与 `1 − Hallucination Rate (4%)` **两个独立分量** —— 也就是说,**「敢于承认不知道」被单独计分**。
> 2. Terminal-Bench 的 **Tool Usage 列标注为 ✗**(见 §5.3 的方法论歧义)。
> 3. 权重校验:20+14+16+8+6+12+12+6+6 = **100%** ✓

---

## 五、三个典型案例

### 5.1 GDPval-AA v2:开放式 agent 任务如何评分

测试来自 **44 种职业**的经济价值型工作。模型不是答一道题,而是要在 sandbox 中完成任务并**提交一个或多个文件**(报告、表格、演示文稿等)。

**已核验的执行细节**:
- Agent harness:**Stirrup**(AA 自研开源,`github.com/ArtificialAnalysis/Stirrup`)
- 环境:**E2B sandbox**;harness 内提供 **6 个工具**,含 Web Fetch(网页转 markdown)、Web Search 等
- 预算:**250 turns**(原文:*"Turn limits expanded to 250 turns to allow for even longer-horizon agent trajectories"*),且**允许模型在认为无法完成时提前退出**
- 数据集:基于 OpenAI 公开的 gold GDPval 数据集;论文 arXiv:2510.04374

#### 为什么不能用简单 pass/fail?

许多专业文件**不存在唯一正确答案**。要求做一份市场分析报告时,很难写 unit test 判断:分析是否深入 · 图表是否清楚 · 是否正确使用参考材料 · 结论是否有商业价值 · 文件是否专业。

所以用 **pairwise comparison**:
1. 同一任务的两个模型输出匿名标为 A / B
2. 从**三个 frontier LLM judge 组成的 panel** 中抽取一个 judge 判断哪个更好(原文明确:*"A panel of three frontier LLM judges from leading labs, **replacing a single judge**"*)
3. 汇总大量两两比较
4. 用 **Bradley–Terry** 模型(最大似然)拟合 Elo
5. **锚定人类专家输出 = 1000 Elo**
6. 用 **sandwich estimator** 计算 Elo 的置信区间

#### 它实际测量了什么?

不只是模型推理能力,还混合了:长周期规划 · 文件操作 · 工具选择 · 信息搜索 · Office 文档制作 · context management · **agent harness** · **judge 对文件质量的偏好**。

> 因此 GDPval-AA 的分数更接近:
> **「一个配置好的 agent system,在给定 sandbox 和预算下完成专业工作的能力」** —— 不是纯粹的 base model intelligence。

---

### 5.2 τ³-Banking:为什么要检查最终状态

模拟银行客服。Agent 需要:理解请求 → 在约 700 份互相关联的政策文档中找到适用规则 → 判断哪些操作被允许 → 与**模拟用户**沟通获取信息 → 调用工具修改后台账户状态。

**已核验细节**:每个任务最多 **200 steps**;原文对 step 的定义很关键 —— *"A 'step' here is the τ-Bench harness definition — **every message passed within the simulation**"*;跑 **5 次**;用 **bm25_grep** 模式做知识检索。

评分主要看**后台数据库状态**(是否真的创建了 dispute、是否真的发放了 provisional credit),而不是聊天内容听起来对不对。

#### 为什么 environment-state verifier 更可靠

| | 表现 | 数据库 | 谁真的完成了? |
|---|---|---|---|
| **Agent A** | 「我已成功为您提交争议申请」 | ❌ 没调用工具 | 否 |
| **Agent B** | 回复简短 | ✅ 真的创建了 dispute | **是** |

只看自然语言,A 更像优秀客服;检查数据库,B 才完成任务。

> **对可客观验证的 agent 任务,优先验证 `Final Environment State`,而不是 `Agent's Claim About the Final State`。**

---

### 5.3 Terminal-Bench:任务成功不是「代码看起来合理」

89 个 terminal 任务,覆盖软件工程、系统管理、数据处理、模型训练和安全。

**已核验细节**(原文):*"We evaluate the full Terminal-Bench v2.1 dataset (**89 tasks**) using the **Terminus 2** agent harness in an **E2B sandbox** environment, with **pass@1 scoring averaged over 3 repeats** per task. Each task ships with a **verification suite** that the agent must satisfy."*
预算:episodes 上限 **250**;per-task timeout **two hours (7,200 秒)**,或任务自带的更长超时。

因此:
```
写出看起来合理的命令      ≠ 成功
模型声称任务完成          ≠ 成功
部分测试通过              可能仍是零分
最终环境符合测试条件       = 成功
```
这是严格的 **outcome-based evaluation**。

#### ⚠️ 一个值得记录的方法论歧义(已确认属实)

AA 总表把 Terminal-Bench 的 **Tool Usage 标为 ✗**,但其详细方法明确说明模型**通过 Terminus 2 在 E2B sandbox 中操作 terminal**。

> 我已在快照中**同时核对到这两处**,冲突真实存在。
> 因此这里的 "Tool Usage" 很可能是 AA 内部的一种特定元数据定义(例如「是否由 AA 的 Stirrup harness 提供 API 级工具」),而不是「模型是否与环境交互」的通用定义。方法页没有解释这一列。

**正确做法**:把它记录为一个**待确认的 methodology ambiguity**,而不是自行强行解释。这也是读 benchmark 文档的重要习惯:

> **当摘要表与实现细节冲突时,以实际执行流程为准,并明确记录不确定性。**

---

## 六、同一个指数混合了五种评分范式

| 范式 | 代表 | 优势 | 局限 |
|---|---|---|---|
| **客观选择题** | GPQA Diamond | 简单 · 可重复 · 不依赖 judge | 存在猜测概率 · 无法验证 reasoning · 格式错误造成假阴性 |
| **代码执行** | SciCode · CritPt | 验证功能而非表达 · scorer 确定 · 可大规模自动化 | test coverage 决定质量 · 可针对测试漏洞得分 · 环境依赖导致非能力性失败 |
| **环境状态** | τ³-Banking · Terminal-Bench | 接近真实成功 · 不依赖自我报告 · 能抓「说完成了但没做」 | 环境构建成本高 · reset/并发/确定性复杂 · **verifier 自身可能有漏洞** · 可能只验最终态 |
| **LLM equality checker** | AA-LCR · HLE · AA-Omniscience | 接受多种正确表述 · 适合开放式 | judge 也会错 · **换 judge 可能改变历史分数** · 被测模型与 judge 可能共享偏差 |
| **Pairwise preference** | GDPval-AA v2 | 能评没有唯一答案的成果 · 比绝对打分更易判断 | **Elo 取决于对手集合** · judge 偏好 ≠ 真实用户价值 · 受 verbosity/格式影响 · 新模型加入会改变比较图谱 |

> 📌 **grader 版本会漂移**:v4.1.1 在 2026-08-06 把 HLE、AA-LCR、AA-Omniscience 的 grader 统一改用 **GPT-5.6 Luna (medium)**;τ³-Banking 也更新到上游 v1.0.1 数据集与 grader。
> ⟹ **benchmark 的分数不仅因被测模型变化,也因 grader 版本变化。**

---

## 七、为什么 repeat 数量不一样

```
1 次:GDPval-AA · AA-Omniscience · HLE
3 次:Terminal-Bench · SciCode · AA-LCR
5 次:τ³-Banking · GPQA Diamond · CritPt
```

**问题**:repeat 数量是根据统计需要决定的,还是根据 evaluation 成本决定的?

benchmark 设计要在三者间权衡:

```
Statistical Precision  ⟷  Task Diversity  ⟷  Evaluation Cost
```

| 方案 | 做法 | 更适合估计 |
|---|---|---|
| A | 更多任务,每题 1 次 | 整个任务分布上的**平均能力** |
| B | 更少任务,每题多次 | 同一任务上的**随机性与稳定性** |
| C | 部分任务多次 | 两者兼顾,但分析更复杂 |

GDPval-AA 每任务只跑 1 次,**很可能**与其 trajectory 长(250 turns)、文件解析与 pairwise grading 成本高有关 —— 这是**合理推断**,AA 方法页并未明确说明 repeat 数量的成本决策过程。**(标注为推断,不当作事实。)**

---

## 八、如何解读综合指数

权重最高的三项:

| 排名 | Benchmark | 权重 |
|---|---|---|
| 1 | GDPval-AA v2 | 20% |
| 2 | Terminal-Bench v2.1 | 16% |
| 3 | τ³-Banking | 14% |
| | **合计** | **50%** |

Agents 类占 34%,Coding 占 24%。**v4.1 之后明显提高了 agentic workload 的重要性**(该次调整包括升级 Terminal-Bench 与 τ-Bench、GDPval-AA 升到 v2、移除已饱和的 IFBench)。

假设某模型:agentic 很强 · scientific QA 一般 · hallucination 较高 —— 它**仍可能**因 agent 类权重高而取得较高综合分。反过来,知识丰富但不擅用工具的模型,可能在综合指数中落后。

> **综合指数隐含一个价值判断:哪些能力更重要,以及每种应该重要到什么程度。**
> **权重不是自然定律,是 benchmark 设计者的产品与研究选择。**

---

## 九、阅读任何 Leaderboard 的七个问题 ⭐

> 这七问是本课最该带走的东西。以后看到任何 benchmark,先回答它们。

1. **Evaluation unit 是什么?** 一个问题 / 一次 trajectory / 一个文件 / 一段 conversation / 最终 environment state?
2. **被测对象是什么?** Base model / Chat model / Model+system prompt / **Model+harness** / 完整 agent product?
3. **Agent 有什么资源?** tool list · 网络访问 · 文件 · context window · token budget · step limit · wall-clock timeout
4. **成功如何定义?** exact match / unit test / database state / LLM judge / human preference / rubric
5. **运行了多少次?** 每任务 1 次还是多次?报的是 repeated pass@1 还是 pass@k?**有没有置信区间?**
6. **分数如何聚合?** 任务等权?类别等权?是否 normalization?是否人为加权?
7. **可能被怎样误解或 game?** 数据泄漏 · test contamination · grader hacking · output-format exploitation · benchmark-specific prompt · harness tuning · 超大 token budget · **对 judge preference 的优化**

---

## 十、核心结论

**结论一 · Leaderboard 排名不是模型本体属性。**
它是模型在特定 prompt、harness、environment、预算和 scorer 下产生的**测量结果**。

**结论二 · Agent evaluation 的核心对象通常是整个 agent system。**
GDPval-AA、τ³-Banking、Terminal-Bench 的结果**无法简单归因于裸模型**。

**结论三 · 优先验证真实结果,而不是 agent 的语言声明。**
能检查 database / filesystem / test suite / application state 时,尽量用 outcome-based verifier。

**结论四 · Repeat 不能消除所有不确定性。**
它能估计随机性,但解决不了:task selection bias · scorer bias · benchmark contamination · environment mismatch · weighting choice。

**结论五 · 综合指数包含价值判断。**
选哪些 benchmark、删哪些、如何分组、如何加权,都会影响最终排名。

---

## 十一、课堂练习

### 练习一:Benchmark Anatomy
从九项 evaluation 中选一项,填写:

| 项目 | 回答 |
|---|---|
| Benchmark 名称 | |
| 被测系统 | |
| Evaluation unit | |
| Task distribution | |
| Initial state | |
| Available actions/tools | |
| Step/token/time budget | |
| Number of repeats | |
| Scorer/verifier | |
| Aggregation method | |
| 主要 failure modes | |
| **这个分数不能说明什么** | |

### 练习二:比较三个 Agent Benchmark
比较 GDPval-AA、τ³-Banking、Terminal-Bench,回答:
1. 哪个任务最开放?
2. 哪个 scorer 最客观?
3. 哪个最依赖 LLM judge?
4. 哪个最容易准确检查最终任务状态?
5. 哪个最容易受 harness 能力影响?
6. 三者中哪个最适合评测**你的**实际产品?为什么?

### 练习三:Repeat 实验
两个 agent 在 20 个任务上各运行 5 次。**Agent A**:100 次中成功 60 次。**Agent B**:100 次中成功 65 次。

1. 两者的 repeated pass@1 分别是多少?
2. 仅凭 60% 和 65%,能否确定 B 更强?
3. 是否需要知道它们跑的是**相同任务**?
4. 如果 B 多出的成功**全部集中在一个简单任务上**,这会怎样影响判断?
5. 下一步应该用什么统计方法比较?

> 本练习**暂不要求计算显著性** —— Day 4 与 Week 4/5 会学 paired bootstrap、McNemar test 和置信区间。

---

## 十二、课后作业

阅读 `docs/aa-intelligence-benchmarking-methodology.md`,完成**一页 benchmark review**:

> **Benchmark Review:______ 到底测量了什么?**

必须包括:① 一句话描述 task ② 被测对象是 model 还是 agent system ③ repeat 数量 ④ scorer 类型 ⑤ tool 与 environment ⑥ budget 和 termination condition ⑦ 一个设计优点 ⑧ **两个 validity threat** ⑨ 一个可能被误读的 leaderboard 结论 ⑩ 一个你希望作者进一步公开的信息。

---

## 十三、Benchmark Review 模板(以后一直用)

```text
Benchmark:
Version:
Claimed capability:

Task:
Evaluation unit:
Task distribution:

Model configuration:
Agent harness:
Tools:
Environment:
Resource budget:
Termination rule:

Number of tasks:
Repeats per task:
Metric:
Scorer/verifier:
Aggregation:

Strengths:
1.
2.

Validity threats:
1.
2.
3.

Possible benchmark gaming:
1.
2.

What the score supports:
What the score does not support:

Open methodology questions:
1.
2.
```

---

## 本课一句话总结

> **不要把 benchmark 当作一套题;要把它看成一套由「任务分布 + 执行环境 + agent harness + 资源预算 + 随机过程 + 评分器 + 统计聚合」共同组成的测量系统。**

---

**下一课(Day 2)**:组件级 evaluation 与 trace —— 怎么评一个 agent 的**内部**,而不只是最终对错。
**Day 4 会做的小实验**:用模拟的多次 rollout 数据,直观看出 **single-run score、repeated pass@1 和 pass@k** 为什么会给出完全不同的结论。
