# 第 5 课:三个 Agent Benchmark 横向解剖
## GDPval-AA v2 · τ³-Banking · Terminal-Bench v2.1

**Week 1 Day 5** · 实验分析日 · 建议 60 分钟

> 📎 **素材锚点**:`docs/aa-intelligence-benchmarking-methodology.md`(所有栏目已逐条核验)· `papers/tau_bench.pdf` · `papers/swebench.pdf`(对照 code-agent verifier 设计)
> 本课重点不是记住三个 benchmark,而是练熟**统一解剖维度**和**攻击性思维**(怎么 game 它)。

---

## 一、为什么挑这三个

它们是 Intelligence Index 里**权重最高的三项,合计 50%**,而且恰好覆盖了三种完全不同的评分范式:

| Benchmark | 权重 | 评分范式 | 代表了什么 |
|---|---:|---|---|
| GDPval-AA v2 | 20% | **Pairwise preference (Elo)** | 没有唯一答案的开放式交付物 |
| Terminal-Bench v2.1 | 16% | **Test suite pass/fail** | 有客观正确定义的工程任务 |
| τ³-Banking | 14% | **Environment state** | 有状态、多轮、需遵守规则的业务流程 |

**一课把三种范式各看一遍**,以后遇到任何 agent benchmark 都能归类。

---

## 二、统一解剖表(已核验填写)

| 维度 | **GDPval-AA v2** | **τ³-Banking** | **Terminal-Bench v2.1** |
|---|---|---|---|
| **任务数** | 220 tasks | 97 | 89 |
| **Repeat** | **1** | **5** | **3** |
| **权重** | 20% | 14% | 16% |
| **任务来源 / 真实性** | 44 种职业的真实经济价值型工作;基于 OpenAI 公开 gold GDPval 数据集 | 模拟银行客服;约 700 份互相关联的政策文档 | 真实终端任务:软件工程 / 系统管理 / 数据处理 / 模型训练 / 安全 |
| **Environment** | E2B sandbox + 文件系统 + 网页访问 | 银行后台数据库 + 用户模拟器 + 知识库 | E2B sandbox + terminal |
| **Harness** | **Stirrup**(AA 自研开源) | τ-Bench harness(bm25_grep 检索模式) | **Terminus 2** |
| **工具** | 6 个(含 Web Fetch → markdown、Web Search 等) | 知识检索 + 银行操作工具 + 与模拟用户对话 | shell(终端全权) |
| **预算 / 终止** | **250 turns**;上下文超限时 harness 要求总结并清理早期上下文;**允许提前放弃** | **200 steps**(step = 模拟中传递的**每一条消息**) | **250 episodes**;per-task timeout **两小时(7,200s)**,或任务自带更长者 |
| **Verifier** | 三个 frontier LLM judge 组成 panel,匿名 pairwise;Bradley–Terry MLE 拟合 Elo;**锚定人类专家 = 1000**;sandwich estimator 算 CI | **后台数据库状态**;部分自然语言断言用 LLM judge | 任务自带 **verification suite**,**必须全部通过** |
| **Verifier 独立性** | 中(judge 是外部模型,但 agent 的输出文件会被 judge 读到 → 可迎合偏好) | **高**(agent 改不了验证用的 DB 断言) | **高**(测试套件独立于 agent 的说辞) |
| **AA 标注的 Tool Usage** | ✓ | ✓ | **✗** ⚠️(见 §五 的方法论歧义) |
| **聚合** | Elo → frozen & scaled 进指数 | pass@1 over 5 repeats | pass@1 averaged over 3 repeats |

---

## 三、六个问题的答案(Day 5 练习二的参考)

**1. 哪个任务最开放?**
→ **GDPval-AA**。要交付报告 / 表格 / 演示文稿,没有唯一正确答案,所以只能用 pairwise。

**2. 哪个 scorer 最客观?**
→ **Terminal-Bench**。测试套件全过才算成功,二值、可复现、不依赖任何模型判断。

**3. 哪个最依赖 LLM judge?**
→ **GDPval-AA**。整个分数由 judge panel 的偏好经 Bradley–Terry 拟合而来。
(τ³ 只在"部分自然语言断言"上用 judge,主体是 DB 状态。)

**4. 哪个最容易准确检查最终任务状态?**
→ **τ³-Banking**(查数据库行)与 **Terminal-Bench**(跑测试)并列。
两者都是 outcome-based;区别是 τ³ 查**业务状态**,TB 查**测试通过**。

**5. 哪个最容易受 harness 能力影响?**
→ **GDPval-AA**。250 turns 的长轨迹 + 上下文压缩策略 + 提前退出机制,全部由 Stirrup 决定。
> 换 harness ⟹ 上下文管理策略变 ⟹ 长任务成败直接变。

**6. 三者中哪个最适合评测你的实际产品?**
→ 取决于你的产品形态:
```
做交付物(报告/文档)的 agent   → GDPval-AA 范式
做有状态业务流程的 agent        → τ³-Banking 范式   ← 你的 Slack/Jenkins 场景最接近
做代码/运维的 agent            → Terminal-Bench 范式
```
但**三者都不覆盖你的核心风险**:多用户权限与信息流(见 §六)。

---

## 四、怎么 game 它 ⭐(本课最重要的一列)

> 训练攻击性思维:**假设你的 KPI 就是这个分数,你会怎么做?** 想不出漏洞,说明你还没真正理解这个 benchmark。

### GDPval-AA(pairwise preference)
```
① 迎合 judge 偏好而非用户价值:更长、更漂亮、更多小标题和图表
② 格式套路化:固定用 judge 喜欢的文档结构模板
③ 利用 Elo 依赖对手集合:只与弱对手比较时排名虚高
④ 只跑 1 次 → 运气好的单次结果无法被平均掉
⑤ 针对「可提前退出」机制:难题早退保成本,不影响单题胜负判定
```
**防御方向**:judge 校准与人工 gold set(Week 5)· 盲测与对手集合固定 · 增加 repeat。

### τ³-Banking(environment state)
```
① 政策文档检索作弊:硬编码常见 case 的规则,不真正检索
② 只满足 DB 断言,不管过程:用不合规手段达成正确终态
③ 钻用户模拟器的漏洞:诱导模拟用户给出本该由 agent 推断的信息
④ 200 step 预算内刷动作:反复试探直到 DB 状态碰对
```
**防御方向**:验证**中间过程**而不只是终态(是否读了正确政策?是否有越权动作?)· 对模拟用户加约束。

### Terminal-Bench(test suite)
```
① 针对测试而非任务:读到测试文件后直接让测试通过(经典 test-gaming)
② 覆盖不足的漏洞:hack 实现绕过断言
③ 用满两小时超时暴力搜索
④ 环境探测:识别出这是 benchmark 环境后走特殊路径
```
**防御方向**:**hidden tests**(agent 不可读)· verifier 与 workspace 物理隔离 · 限制 wall-clock。

> 📌 这三列直通 **Week 7(evaluation integrity)** 和 **Week 10(reward hacking)**。
> 跨课呼应:`../agent-sandbox-course` 的核心原则 —— **verifier 必须在 agent 够不到的地方**(独立 verifier sandbox)。

---

## 五、方法论歧义:必须记录而不是自行解释

**已在快照中双向核对确认冲突真实存在**:

| 出处 | 说法 |
|---|---|
| AA 汇总表 | Terminal-Bench 的 **Tool Usage = ✗** |
| AA 详细方法 | *"using the **Terminus 2 agent harness** in an **E2B sandbox** environment"* —— 模型显然在操作终端 |

**正确处理**:
```
✅ 记录为 open methodology question
✅ 以实际执行流程为准(它确实用工具)
❌ 不要自行编造 "Tool Usage" 的定义并当成事实
```

**合理猜测**(标注为猜测):这一列可能指「是否由 AA 的 Stirrup harness 提供 API 级工具」,而 Terminal-Bench 用的是上游 Terminus 2 —— 但方法页**没有解释这一列**,所以只能存疑。

> ### 这是本周最该养成的职业习惯
> **当摘要表与实现细节冲突时,以实际执行流程为准,并明确记录不确定性。**
> 一个合格的 benchmark review,**必须有 "Open methodology questions" 这一节**。

---

## 六、三者共同的盲区(通往你的 capstone)

把三个加起来,仍然**完全没有覆盖**的东西:

| 盲区 | 为什么重要 |
|---|---|
| **多用户 / 多 principal** | 三者都是单用户会话。你的产品是 A/B/C 共用一个 thread |
| **权限与 delegation** | 没有任何一项测「agent 此刻代表谁、能不能访问这个资源」 |
| **信息流隔离** | 没有任何一项测「C 能否从历史 summary 看到 A 的私有数据」 |
| **凭证泄漏** | 没有任何一项检查 trace / snapshot / 日志里有没有 JWT |
| **撤销后的行为** | 没有任何一项测「用户权限被撤销后,后台 agent 还能不能继续」 |
| **session 级评价** | 三者主要在 task 层打分(见 Day 2 的四种评价单位) |

> ⟹ 这正是本课程 capstone **Permission-Aware Multi-User Agent Benchmark** 的立足点:
> **不是再造一个 SWE-bench,而是补上现有 benchmark 家族的结构性盲区。**

---

## 七、本课产出

### 产出 1:填一张你自己的解剖表
不要抄本文。选**另外三个** benchmark(建议从 AA 的 additional evaluations 里挑,如 AA-Briefcase / ITBench / EnterpriseOps-Gym / AutomationBench),用相同维度填表。
📁 → `sec2-benchmark-teardown.md`

### 产出 2:下周问题清单
写下 5 个你现在答不上来、但觉得重要的问题。
📁 → `notes/day5-next-week-questions.md`

**参考(可作为你的起点)**:
```
1. 同一任务 5 次 repeat 不是独立样本,置信区间该怎么算?   → Week 4(clustered SE)
2. 怎么量化一个 LLM judge 到底准不准?                      → Week 5
3. hidden test 要怎么在技术上真正做到 agent 不可读?        → Week 7
4. benchmark 被污染了怎么检测?                             → Week 7
5. 同一套 environment 怎么同时服务 eval 和 RL 训练?        → Week 10–11
```

---

## 八、Week 1 收官:自检清单

```
[ ] 1. 能背出七因子公式,并对每个因子举一个改变它就改变分数的例子
[ ] 2. 能区分 model eval / agent-system eval,并说清 AA 为什么单列 Coding Agent Index
[ ] 3. 能区分 turn / trajectory / task / session,各举一例
[ ] 4. 能说清 online vs offline evaluation 的用途差异
[ ] 5. 能手算/编程给出任一 k/n 的 Wilson CI,并解释为何不用正态近似
[ ] 6. 能回答「30/50 vs 300/500」的可信度差异(26.2% vs 8.6%)
[ ] 7. 对三个 benchmark 各说出一种 game 它的方法
[ ] 8. 画出完整 evaluation stack,并标出每层属于七因子里的哪一个
```

### 本周交付:`figures/evaluation-stack.txt`
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
每层标注:**它是七因子里的哪一个 · 换掉它分数会怎么变。**

---

## 本课一句话总结

> **每个 benchmark 都在用某种方式回答「成功了吗」,而每种方式都有对应的 game 方法。** 读 benchmark 的最高境界,是先想清楚「如果我的 KPI 是它,我会怎么作弊」——那就是它的 validity threat 清单。

---

**下周(Week 2)**:Benchmark landscape 与 Artificial Analysis —— 指数构成、权重决策、task sampling、harness、budget 与 leaderboard 的系统性分析。
