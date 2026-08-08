# Week 1 — Evaluation 基本框架
## model vs system vs agent · offline vs online · 四种评价单位

> **5 天 × 1 小时**。周节奏:2 天概念与论文 · 1 天编码 · 1 天实验分析 · 1 天写自学讲义。
> **本周交付**:为一个 agent 画出**完整 evaluation stack**。

**本周主命题**(全课的第一课):
> ### 测得的性能 = Model × Agent Harness × Environment × Task Distribution × Budget × Scorer × Randomness
> 七个因子里只有一个是 model —— 所以 **leaderboard 分数 ≠ 模型能力**。

**四种评价单位**(本周必须能区分并各举一例):
```
turn        单次交互是否正确
trajectory  整条轨迹的过程质量(工具选择、冗余步骤、违规动作)
task        任务最终是否达成(由 independent verifier 判定)
session     跨多轮/多用户的长期表现(状态、记忆、权限)
```

---

## Day 1 · 概念 —— 拆解一个真实排行榜的口径
**目标:先看清「一个分数背后到底有多少可调旋钮」。**

| 时间 | 做什么 |
|---|---|
| 40 min | 精读 Artificial Analysis Intelligence Index methodology |
| 20 min | 制表:每个 benchmark 的 **task · repeat · scorer · tool usage** |

📎 素材:`docs/aa-intelligence-benchmarking-methodology.md`(116k 字,已抓取核实)

**已核实的事实**(读的时候对照验证):
```
Intelligence Index v4.1.1 = 9 项 evaluation 加权
Agents 34% · Coding 24% · Scientific Reasoning 24% · General 18%
Agent 类主要:GDPval-AA v2 · τ³-Banking
Terminal-Bench / SciCode 归在 Coding,不在 Agents
```

**必须回答**:
- 哪些 benchmark 跑 1 次?哪些 3 次?哪些 5 次?**为什么不同?**
- scorer 是 exact match、程序化 verifier,还是 LLM/rubric judge?
- agent 有没有工具?工具是谁提供的(benchmark 还是 harness)?
- budget 怎么定(步数 / token / wall time)?

📁 → `notes/day1-aa-benchmark-catalog.md`(一张表 + 3 个疑问)

---

## Day 2 · 概念 —— 组件级 evaluation 与 trace
**目标:补上「怎么评一个 agent 的内部」,而不只是最终对错。**

| 时间 | 做什么 |
|---|---|
| 45 min | DeepLearning.AI *Evaluating AI Agents* 前半部分(trace · 组件级 eval · code evaluator · LLM-as-a-judge) |
| 15 min | **闭卷**记:3 个核心概念 · 2 个没懂的问题 · 1 个能进课程的案例 |

📎 交叉素材:`papers/survey_agent_eval_2025.pdf`(A Survey on Evaluation of LLM-based Agents)—— 看它怎么把领域切成 capability / application benchmark / generalist benchmark / benchmark dimensions / 开发框架。

**必须带走的区分**:
```
component-level eval  router 选对工具了吗?检索到对的文档了吗?
end-to-end eval       任务成了吗?
online vs offline     线上采样 trace 评 vs 固定数据集离线评
```
📁 → `notes/day2-component-eval.md`

---

## Day 3 · 写讲义 —— 《为什么 agent 分数不是 model 分数》
**目标:把 Day 1–2 的认知固化成一页能给别人看的东西。这天不读新材料。**

| 时间 | 做什么 |
|---|---|
| 10 min | **不看笔记**,凭记忆复述 Day 1–2 |
| 35 min | 写讲义 |
| 15 min | 补例子 + 练习题 |

**必须包含**:
1. 七因子公式,逐项举一个「换它会让分数变」的例子
2. **同一模型换 harness 分数就变** —— 用 AA Coding Agent Index 的做法佐证(`docs/aa-coding-agents-leaderboard.md`)
3. 四种评价单位各一例
4. 一段自己的定义:「什么叫 agent-system evaluation,它与 model evaluation 的边界在哪」

📁 → `sec1-why-agent-score-is-not-model-score.md`(800–1,200 字)

---

## Day 4 · 编码 —— Bernoulli / 标准误 / Wilson 区间
**目标:第一次亲手算出「这个分数能不能信」。**

| 时间 | 做什么 |
|---|---|
| 20 min | 概念:Bernoulli · 标准误 · 正态近似为什么在极端比例处失效 · Wilson interval |
| 40 min | 写代码 |

📎 素材:⭐ `papers/error_bars_in_evals.pdf`(*Adding Error Bars to Evals*,Anthropic —— 本周最重要的一篇)

**要实现**(`labs/wilson.py`):
```python
def wilson_ci(k, n, z=1.96) -> tuple[float,float]   # 不用正态近似
def normal_ci(k, n, z=1.96) -> tuple[float,float]   # 对照组
```
**要跑出的三个结论**:
```
① 30/50 与 300/500 同为 60%,CI 宽度差多少?
② n=20、成功 20 次(100%):正态近似给出什么荒谬结果?Wilson 给什么?
③ 要把 CI 宽度减半,n 要变成几倍?
```
📁 → `labs/wilson.py` · `notes/day4-ci-findings.md`

---

## Day 5 · 实验分析 —— 三个 benchmark 的横向解剖
**目标:用统一维度比较,并练习「怎么 game 它」这种攻击性思维。**

| 时间 | 做什么 |
|---|---|
| 45 min | 对比 **GDPval · τ³-Banking · Terminal-Bench** |
| 15 min | 写结论 + 下周问题 |

📎 素材:`docs/aa-intelligence-benchmarking-methodology.md` · `docs/aa-evaluations.md` · `papers/tau_bench.pdf` · `papers/swebench.pdf`(对照 code-agent 的 verifier 设计)

**统一比较表**:
| 维度 | GDPval | τ³-Banking | Terminal-Bench |
|---|---|---|---|
| 任务来源与真实性 | | | |
| environment(有无状态 / 可重置?) | | | |
| 工具与 action schema | | | |
| **verifier**(程序化 / rubric / human?) | | | |
| verifier 独立性(agent 能否碰到它?) | | | |
| repeat 次数与聚合方式 | | | |
| **可被 game 的方式** ⭐ | | | |
| 失败模式(infra fail vs model fail 可分吗?) | | | |

> 「可被 game 的方式」这一列是重点 —— 它直通 **W7 evaluation integrity** 和 **W10 reward hacking**。

📁 → `sec2-benchmark-teardown.md` · `notes/day5-next-week-questions.md`

---

# 本周交付:Evaluation Stack 图

把五天收敛成一张图(`figures/evaluation-stack.txt`),自上而下必须出现:

```
Task distribution / sampling
        ↓
Agent harness(prompt · scaffold · tool schema · retry · budget)
        ↓
Model(+ decoding params · reasoning effort)
        ↓
Environment(state · tools · reset · isolation)
        ↓
Rollout(trajectory logs · token · cost · wall time)
        ↓
Scorer / Verifier(程序化 or judge;独立性?)
        ↓
Aggregation(pass@1/pass@k · micro/macro · 加权)
        ↓
Uncertainty(CI · paired comparison)
        ↓
Leaderboard 分数
```
每一层标注:**它是七因子里的哪一个 · 换掉它分数会怎么变。**

---

# 第 1 周验收

```
[ ] 1. 能背出七因子公式,并对每个因子举一个改变它就改变分数的例子
[ ] 2. 能区分 model eval / agent-system eval,并说清 AA 为什么要单列 Coding Agent Index
[ ] 3. 能区分 turn / trajectory / task / session 四种评价单位,各举一例
[ ] 4. 能说清 online vs offline evaluation 的用途差异
[ ] 5. 手算/编程给出任一 k/n 的 Wilson CI,并解释为何不用正态近似
[ ] 6. 能回答「30/50 vs 300/500」的可信度差异
[ ] 7. 对三个 benchmark 各说出一种 game 它的方法
[ ] 8. 画出完整 evaluation stack,并标出每层属于哪个因子
```

---

# 本地素材(全部已下载并核验)

| 天 | 素材 |
|---|---|
| D1 | ⭐ `docs/aa-intelligence-benchmarking-methodology.md`(v4.1.1 权重已核实) |
| D2 | `papers/survey_agent_eval_2025.pdf`(arXiv 2503.16416) |
| D3 | `docs/aa-coding-agents-leaderboard.md`(同模型不同 harness 的对比) |
| **D4** | ⭐ `papers/error_bars_in_evals.pdf`(arXiv 2411.00640)· `papers/codex_passk.pdf`(pass@k 出处) |
| D5 | `docs/aa-evaluations.md` · `papers/tau_bench.pdf` · `papers/swebench.pdf` |
| 备用 | `papers/gaia.pdf` · `papers/webarena.pdf` · `papers/llm_as_judge_mtbench.pdf`(W5)· `papers/chatbot_arena.pdf`(W5 排名)· `papers/kimi_k3.pdf`(W11) |

> **D2 唯一的外部依赖**:DeepLearning.AI 课程需在线看(免费,需注册)。若不想注册,用 `survey_agent_eval_2025.pdf` 的对应章节替代即可,不影响进度。
