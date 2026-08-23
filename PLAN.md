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
> **素材配比**:约 30% 论文,70% RFC / 官方文档 / 源码。Eval runtime 的设计知识通常不在论文正文里。

| 周 | 主题 | 核心问题 | 状态 |
|---|---|---|---|
| **1** | **Popular Benchmark Anatomy** | 拿到 repo,源码追通 task → environment → agent → rollout → verifier → result | 🔨 4/6 |
| **2** | **Eval Runtime & Trajectory Engineering** | 不同 benchmark / Agent / backend 怎么经同一个 runtime 正确跑?Trajectory 是可重放事件日志,不是聊天记录 | |
| **3** | **Metrics & Statistics** | 一个 observation 是什么?误差棒怎么算? | |
| **4** | **Scorers / Verifiers / LLM-as-Judge** | 成功如何被判定?judge 准不准? | |
| **5** | **Benchmark Design, Audit & Dataset Lifecycle** | 成功/失败反映的是能力,还是题目和测试写坏了? | |
| **6** | **Reproducibility, Failure Semantics & Experiment Operations** | 同一 Agent、同一 benchmark,为什么改一点 infra 分数就变?哪些失败进分母? | |
| **7** | **Evaluation Integrity & Adversarial Validation** | 怎样防止 Agent、数据和基础设施破坏测量本身?(不讲 cgroups/seccomp) | |
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

W2 / W5 / W6 / W7 处理的是四种不同的失败,不要压成「runtime 一周」:
```
W2  observation 怎么被可靠地产生
W5  它是否测到了目标能力
W6  它是否被运行噪声污染
W7  测量本身是否被泄漏、攻击或 game
```

## Week 2 · Eval Runtime & Trajectory Engineering(预告)

核心不是「写个 for-loop 跑任务」,而是:怎样让不同 benchmark、不同 Agent、不同 execution backend,通过同一个 runtime 正确运行?

```
Task → Environment → AgentAdapter → Rollout → Trajectory → Verifier → Result
```

对照两套真实抽象(不是「又学一个工具」):

| | Inspect | Harbor |
|---|---|---|
| 被测逻辑 | Solver / Agent | Agent |
| 一次运行 | Sample execution | Trial |
| 环境 | Sandbox | Environment |
| 评分 | Scorer | Verifier / reward |
| 批量实验 | Eval set | Job |
| 主要场景 | 广义 model / agent eval | 容器化 Agent 与 RL rollout |

Harbor 的层级是 Task / Dataset / Agent / Environment / Trial / Job。Inspect 是 `Task = Dataset + Solver + Scorer`。

**Trajectory 不是聊天记录,而是一份可重放、可归因、可训练的事件日志。**

源码 / RFC(讲义未写,指针先放这):
- [Harbor Core Concepts](https://www.harborframework.com/docs/core-concepts)
- [Inspect 官方文档](https://inspect.aisi.org.uk/)
- [Harbor ATIF RFC](https://github.com/harbor-framework/harbor/blob/main/rfcs/0001-trajectory-format.md)
- [BrowserGym](https://arxiv.org/abs/2412.05467)(非 terminal environment 的统一 observation/action)
- `../llm-rl-course/code/harbor` · `../agent-sandbox-course/code/inspect_ai` · SWE-bench harness

## Week 5 · Benchmark Design, Audit & Dataset Lifecycle(预告)

问题:如何证明成功和失败反映的是 Agent 能力,而不是题目或测试写坏了?
OpenAI 2026 审计 SWE-Bench Pro 时估计约 30% 任务存在破坏性问题(测试过严、prompt 缺信息、覆盖不足、误导)。

源码 / 文档:
- [OpenAI SWE-Bench Pro 审计](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)
- [Anthropic Agent Evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [SWE-bench Verified 创建](https://openai.com/index/introducing-swe-bench-verified/)
- [后续污染与测试缺陷](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)

## Week 6 · Reproducibility, Failure Semantics & Experiment Operations(预告)

问题:同一个 Agent、同一个 benchmark,为什么换一点 infra 配置,分数就变?哪些失败进分母、哪些允许 retry?
Anthropic 在 Terminal-Bench 2.0 上只改变 resource headroom,infra error 从 5.8% 降到 0.5%;放开资源后 success rate 约 +6pp。CPU / 内存 / timeout 会改变 Agent 能做的策略。

源码 / 文档:
- [Anthropic Infrastructure Noise](https://www.anthropic.com/engineering/infrastructure-noise)

## Week 7 · Evaluation Integrity & Adversarial Validation(预告)

**不讲**容器 / cgroups / seccomp(那是 `agent-sandbox-course`)。只讲 eval 特有的攻击面:hidden tests、verifier、credentials、tenants、test-set 污染、tool-output injection、网络查 gold、trajectory 里的 secrets、reward hacking。
最终不能只报成功率:`Valid Success = Task Success × No Security Violation`。Lab 形状服务 W12 Permission-Aware capstone。

源码 / 文档:
- [AgentDojo](https://arxiv.org/abs/2406.13352)
- [Inspect Sandboxing Toolkit](https://www.aisi.gov.uk/blog/the-inspect-sandboxing-toolkit-scalable-and-secure-ai-agent-evaluations)(实现参考,不讲内核)

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
[x] W1  Benchmark Anatomy (4/6)     [ ] W5  Benchmark design / audit     [ ] W9   production eval
[ ] W2  Eval runtime / trajectory   [ ] W6  Repro / failure semantics    [ ] W10  eval ↔ on-policy RL
[ ] W3  Metrics & statistics        [ ] W7  Eval integrity / adversarial [ ] W11  Kimi K3 case study
[ ] W4  Scorers / judges            [ ] W8  Leaderboards (plan exists)   [ ] W12  capstone
```
