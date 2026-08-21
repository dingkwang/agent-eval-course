# Agent Evaluation & Benchmark Engineering
## 从排行榜、统计推断到 RL Environment

> **12 周 · 每周 5 天 · 每天约 1 小时**。素材清单见 `MATERIALS.md`,第 1 周逐日见 `week01/PLAN.md`。
> 姊妹课:`../agent-sandbox-course`(Secure Agent Environments)· `../llm-rl-course`(LLM RL → PPO → GRPO)。

---

# 零、这门课要训练的四种能力

不是教「怎么跑一个 benchmark」,而是:

1. 能**读懂并质疑**排行榜
2. 能设计**有统计可信度**的 agent benchmark
3. 能搭建**可复现、隔离、可验证**的 agent environment
4. 能理解同一套 environment / verifier / trajectory infra 如何**同时服务 evaluation 与 on-policy RL**

## 全课最核心的公式

> ### 测得的性能 = Model × Agent Harness × Environment × Task Distribution × Budget × Scorer × Randomness

**推论:leaderboard 分数 ≠ 模型能力。** 七个因子里只有一个是 model。

---

# 一、Artificial Analysis 的定位:入口,不是教材

**可以**用它当课程入口(真实、持续更新、口径公开);**不能**当完整 agent-eval 教材。

已核实(`docs/aa-intelligence-benchmarking-methodology.md`,2026-08 抓取):
- **Intelligence Index v4.1.1** = 9 项 evaluation 加权:**Agents 34% · Coding 24% · Scientific Reasoning 24% · General 18%**
- Agent 类主要是 **GDPval-AA v2** 与 **τ³-Banking**;**Terminal-Bench / SciCode 归在 Coding**
- ⟹ 它是**混合的「总体智能指数」,不是纯 agent benchmark**

AA 另有一批更直接的 agent evaluations:
| 方向 | benchmark |
|---|---|
| 专业知识工作 / 文件交付 | GDPval-AA v2 · AA-Briefcase |
| 跨应用 / SaaS / 有状态企业流程 | APEX-Agents · AutomationBench · EnterpriseOps-Gym |
| 知识库检索 + 用户模拟 + 多步工具 | τ³-Banking |
| 终端 / 系统管理 / IT incident | Terminal-Bench · ITBench |
| 法律文件交付 + rubric grading | Harvey LAB |

**Coding Agent Index** 把 DeepSWE、Terminal-Bench v2、SWE-Atlas-QnA 等权组合,每任务跑 3 次,报 task-normalized pass@1,并**专门比较同一底层模型在不同 harness 下的表现**。
> ⟹ 这正是本课的立论依据:**model evaluation 与 agent-system evaluation 必须分开。**

---

# 二、现有课程吸收什么、缺什么

| 课程 | 值得学 | 缺口 |
|---|---|---|
| DeepLearning.AI **Evaluating AI Agents** | trace · 组件级 evaluation · code evaluator · LLM-as-a-judge · human annotation | 统计推断、benchmark validity、sandbox 较浅 |
| HuggingFace **Agents Course** | 用 GAIA 做完整项目;Bonus Unit 覆盖 OpenTelemetry、成本、延迟、实时/离线 eval | 偏入门与工具实践,不足以设计严谨 benchmark |
| LangChain Academy **Building Reliable Agents** | tracing · 构造 dataset · experiments · code judge · pairwise judge · online eval | 强绑定 LangSmith;benchmark science 与 RL 少 |
| W&B **LLM Apps: Evaluation** | programmatic checks · LLM judge · judge alignment | 偏 LLM application,缺复杂状态环境与长轨迹 |
| W&B **AI Engineering: Agents** | agent 架构;accuracy/latency/cost 联合评估 | 仅两小时,概览级 |

> **判断:现有课程能覆盖工具使用,但没有一门同时系统覆盖「统计学 + benchmark 设计 + environment/sandbox + evaluation integrity + on-policy RL」。** 这就是本课的存在理由。

---

# 三、12 周结构(v2 · 源码优先)

> **v1 的顺序错了**:一上来讲评价框架和统计,是在给一个你还没见过的东西算误差棒。
> **v2 的主线**:**先学 benchmark 作为一个软件系统是怎么工作的,再学如何测量它。**

| 周 | 主题 | 核心问题 | 状态 |
|---|---|---|---|
| **1** | **Popular Benchmark Anatomy** | 现有 benchmark 是怎么工作的?(源码追通 task→…→result) | 🔨 进行中 |
| **2** | **Eval Runtime / Harness Engineering** | 我要自己实现一套通用 agent eval runtime,需要哪些 abstraction? | |
| **3** | **Metrics & Statistics** | 一个 observation 是什么?怎么算误差棒? | |
| **4** | **Scorers / Verifiers / LLM-as-Judge** | 成功如何被判定?judge 准不准? | |
| **5** | **Benchmark Construction & Task Quality** | 怎么造出好任务?怎么做质量控制? | |
| **6** | **Reproducibility / Infra Noise / Failure Taxonomy** | 同样的模型为什么跑出不同分?哪些失败不是模型的错? | |
| **7** | **Sandbox & Evaluation Integrity** | 怎么防污染、防作弊、防外泄? | |
| **8** | **Leaderboard / Aggregation / Artificial Analysis** | 成千上万个 task result 怎么压成一个数字? | 📄 已详细规划 |
| **9** | **Production / Online Evaluation** | 这个数字跟真实产品表现有什么关系? | |
| **10** | **Evaluation ↔ On-policy RL** | 同一套 environment 怎么同时服务 eval 与训练? | |
| **11** | **Kimi K3 / AgentENV / Harbor RL Case Study** | 前沿是怎么把这些拼在一起的? | |
| **12** | **Capstone Benchmark** | 自己从零做一个可运行、可复现、可评分的 benchmark | |

**三段式**:
```
W1–W2   benchmark 与 runtime 是怎么工作的   ← 工程
W3–W7   怎么正确地测量                      ← 方法论
W8–W12  怎么把测量变成结论,以及喂给训练      ← 系统与应用
```

## Week 2 · Eval Runtime Engineering(预告)

要抽象出来的东西:
```
Task → Environment → AgentAdapter → Rollout → Trajectory → Verifier → Result
```
对照研究三个真实框架 —— **不是「又学一个工具」,而是比较不同框架如何抽象同一个 runtime**:

| 框架 | 学什么 |
|---|---|
| **Harbor** | ⭐ 主 runtime:84 adapter × 20 执行后端的统一抽象;同时是 eval framework 和 RL environment framework |
| **SWE-bench harness** | Docker image layering(base → env → instance)· cache · parallel evaluation · **failure classification**(infra failure / ambiguous / unresolved 已被官方区分) |
| **Inspect AI** | 最干净的 API 抽象:`Task / Solver / Scorer / Sandbox` |

## Week 8 · From Rollouts to Leaderboards
> 📄 **逐日计划见 `week08/PLAN.md`** —— raw rollout → per-task → per-benchmark → normalization → 跨 benchmark 聚合 → index → ranking,含 weight sensitivity、rank uncertainty、versioning 与 Pareto frontier。


# 四、统计学要学到什么程度

## 必修

### 1. 二项分布与置信区间
agent task success 通常是 Bernoulli 结果。掌握:accuracy / success rate / partial success · 标准误 · **Wilson interval**(不要只用简单正态近似)。
> 关键直觉:**30/50 与 300/500 同为 60%,可信度完全不同。**

### 2. Paired comparison
比较两个 agent 要**跑相同任务**,然后用:paired bootstrap · permutation test · 二元结果的 **McNemar test** · **每任务差值**(而非只比两个总体均值)。

### 3. 多次 rollout
同一任务可能一次成功一次失败。要理解:pass@1 / pass@k · **「每任务多跑几次」与「增加更多任务」作用不同** · 方差分解(model sampling / environment nondeterminism / tool failure)。
> AA 本身就混用 1、3、5 次重复 —— 现成的统计案例。

### 4. Judge reliability
Cohen's κ · Krippendorff's α · rank correlation · precision/recall · judge calibration · **position bias / verbosity bias / self-preference** · rubric sensitivity · 人类 gold set 与 judge threshold 的选择。

### 5. 排名与聚合
Elo 与 Bradley–Terry · 加权平均如何改变排名 · micro vs macro average · **多重比较与 leaderboard overfitting** · cost-quality Pareto frontier。

## 进阶选修(第一版不必从这些开始)
hierarchical model · mixed-effects model · item response theory · Bayesian comparison · sequential testing · statistical power。

---

# 五、Agent environment / eval infrastructure 知识地图

```
Task specification
    ↓
Initial environment state
    ↓
Available tools / action schema
    ↓
Observation and permission model
    ↓
Agent rollout
    ↓
Termination and resource budget
    ↓
Final state + trajectory logs
    ↓
Independent verifier
    ↓
Metrics, confidence intervals, failure analysis
```

重点覆盖:
- **可重复性**:固定 image、dependency、seed、tool schema
- **状态管理**:reset · snapshot · fork · resume
- **隔离**:filesystem · network · credential · process · tenant
- **可观测性**:每次 tool call、状态变更、token、cost、wall time
- **verifier independence**:agent 不能修改 grader、测试或 hidden state
- **真实性 vs 可控性**:真实网站会漂移,模拟环境会失真
- **评价完整性**:防 benchmark contamination · test leakage · grader tampering · reward hacking

---

# 六、Evaluation 与 on-policy RL 的关系

| Evaluation | On-policy RL |
|---|---|
| 固定 policy,运行后不更新参数 | 当前 policy 生成 trajectory,随后更新参数 |
| 目标:估计 held-out performance | 目标:最大化 expected reward |
| scorer 输出 **measurement** | reward/verifier 输出 **learning signal** |
| 强调独立 test set | 强调持续生成当前 policy 分布下的数据 |
| 不应让 agent 看见 hidden grader | 训练时通常允许通过 reward 间接适应 verifier |

**共享**:environment · task generator · sandbox · rollout engine · trajectory storage · verifier · cost accounting。
**边界**:**evaluation 的输出用于判断,RL 的输出用于更新 policy。**

> ⚠️ 最危险的错误:**直接把 benchmark 当训练 reward,然后继续在同一 benchmark 上宣布性能提升。**

正确结构:
```
Train environments      / visible rewards
Dev environments        / diagnostics
Hidden test environments/ independent verifiers
Production shadow evaluation
```

---

# 七、Kimi K3 在课程里的位置(W11)

不适合当第一篇 eval 教材,但**非常适合作为综合 case study**。
> ✅ 已下载并核实:`papers/kimi_k3.pdf`(arXiv:2607.24653,47 页)。文中确证含 partial rollout ×5 · AgentENV ×7 · generative reward model ×2 · multi-teacher on-policy distillation ×6 · microVM ×3 · snapshot ×5 · verifier ×8。

post-training 三段:① SFT 建 cold-start agent ② 在 general / agentic / coding 三类 domain 上做**多个 reasoning-effort 水平**的 RL ③ **Multi-Teacher On-Policy Distillation** 合并 expert。

与本课最相关:
- long-horizon trajectory 可能含**数百到数千次 tool call**
- **partial rollout**:暂停未完成 trajectory,先用已完成样本更新
- 非确定性任务用 **Agentic Generative Reward Model**
- autonomous execution 用 **independent verifier**,以**真实 environment state** 而非 agent 自报完成作为 reward
- **AgentENV** 用隔离 microVM,支持 pause/resume、fork、snapshot,**同时服务 training 与 evaluation**

> ### 核心认识
> **前沿 agent RL infrastructure,本质上也是大规模、可暂停、可验证、强隔离的 evaluation infrastructure。**

---

# 八、结课项目

## **Permission-Aware Multi-User Agent Benchmark**

模拟 Slack 中多个用户共同指挥 agent,连接 Jenkins / 日志系统 / 内部工具。
(与 `agent-sandbox-course` 的 A/B/C 案例同源 —— 两门课的 capstone 互相咬合)

**任务集至少包含**:
```
· A、B 有权限读某 trace,C 没有
· C 询问前一个 session 中出现过的敏感内容
· 同一问题由不同用户发起时必须使用各自 credential
· 用户中途加入、退出或权限变化
· tool 返回错误、超时和部分结果
· agent 必须完成任务,但不得泄漏 JWT、trace 或跨租户状态
```

**评价指标**:
```
task success · unauthorized disclosure rate · incorrect-principal tool-call rate
cross-session leakage rate · recovery success · token/cost/latency
轨迹级 policy violation
```

> 它同时展示 **benchmark design · sandbox · authz · statistics · verifier · RL-ready environment**,比单纯复现 GAIA 或 SWE-bench 更有辨识度。

---

# 进度
```
[ ] W1  评价框架       [ ] W5  统计II judge     [ ] W9   production eval
[ ] W2  landscape/AA   [ ] W6  environment      [ ] W10  eval ↔ on-policy RL
[ ] W3  任务与指标     [ ] W7  sandbox/integrity[ ] W11  Kimi K3 case study
[ ] W4  统计I 二元     [ ] W8  benchmark 家族   [ ] W12  capstone
```
