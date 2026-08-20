# 第 3 课:为什么 Agent 分数不是 Model 分数

**Week 1 Day 4** · 写作日 · 建议 60 分钟

> 本课是**产出日**:先闭卷复述 Day 1–3,再写出自己的一页讲义。
> 这份文件同时是**参考答案**——写完你自己的版本后再对照,别先读完再写(那样只是抄)。

> 📎 素材锚点:`docs/aa-coding-agents-leaderboard.md` · `docs/aa-intelligence-benchmarking-methodology.md`(均 2026-08 快照,已核验)

---

## 今日流程

| 时间 | 做什么 |
|---|---|
| 10 min | **合上所有材料**,凭记忆写下:七因子是什么?四种评价单位是什么? |
| 35 min | 写你自己的《为什么 agent 分数不是 model 分数》(800–1,200 字) |
| 15 min | 对照本文补例子 + 做练习 |

---

## 一、核心命题

```
Evaluation Result = f( Task, Model, Harness, Environment, Budget, Scorer, Randomness )
```

> **七个自变量,只有一个是 Model。**
> 所以「模型 X 在 benchmark Y 上得了 Z 分」这句话,严格说测的是**一整套系统**,不是模型。

下面逐个因子给一个「只改它、分数就变」的例子。

---

## 二、逐因子:改它,分数就变

### 1. Task(任务分布)
**同一个 benchmark 名字,任务集可能不同。**

已核验的真实例子 —— **Terminal-Bench 在 AA 的两个产品里任务数不一样**:

| 出现位置 | 版本 | 任务数 |
|---|---|---|
| Intelligence Index v4.1.1 | Terminal-Bench **v2.1** | **89 tasks** |
| Coding Agent Index | Terminal-Bench **v2** | **84 tasks** |

> ⟹ 看到「Terminal-Bench 得分 X%」时,**必须问是哪个版本、哪个子集**。跨来源直接比较同名 benchmark 的分数是不安全的。

### 2. Model(被测模型)
唯一一个大家以为在测的东西。但注意:**同一模型不同 reasoning effort / 采样参数,是不同配置**。AA 在方法论中把 reasoning effort 作为显式配置项(Kimi K3 论文里更是把它当训练维度)。

### 3. Harness(执行框架)⭐ 本课重点

**已核验**:AA 的 Coding Agent Index 页面单独提供 **"Harness Comparison"** 视图 —— 也就是说,**同一底层模型换 harness,结果值得单列一张图来比**。

harness 决定了:
```
上下文怎么管(满了是截断?总结?清理早期?)
tool call 怎么解析(格式错了重试还是判死?)
最大轮数多少
工具报错怎么呈现给模型
何时判定「结束」
能不能提前放弃
```

**GDPval-AA 的真实证据**:AA 用自研 harness **Stirrup**,并在 v2 中把 **turn 上限提到 250**,还新增了「模型认为做不完时可以提前退出」的能力。这两项都是 harness 特性 —— 换个 harness,同一模型的分数必然移动。

> **推论**:一个 benchmark 如果不公开 harness,它的分数**不可复现**。

### 4. Environment(环境)
Terminal-Bench 跑在 **E2B sandbox**;τ³-Banking 跑在带约 700 份政策文档的模拟银行后台。环境的**版本、镜像、网络可达性、依赖**全都影响结果。
> 跨课呼应:`../agent-sandbox-course/docs/agentic/anthropic-infra-noise.md` —— **runtime 配置本身能让 agentic coding eval 成绩变化数个百分点**。runtime 已经是被测内容的一部分。

### 5. Budget(预算)
已核验的三个真实预算:
```
GDPval-AA v2     250 turns
τ³-Banking       200 steps  (step = 模拟中传递的每一条消息)
Terminal-Bench   250 episodes,per-task timeout 两小时(7,200 秒)
```
**把预算翻倍,分数会变** —— 这测的是「在预算内完成」的能力,不是「能否完成」的能力。

### 6. Scorer(评分器)
已核验:v4.1.1 在 **2026-08-06** 把 HLE、AA-LCR、AA-Omniscience 的 grader 统一改成 **GPT-5.6 Luna (medium)**。
> **模型没变,分数可能变** —— 因为尺子换了。历史分数的可比性因此需要显式标注 grader 版本。

### 7. Randomness(随机性)
同一任务多次运行结果可能不同。来源至少三处:**模型采样** · **环境非确定性** · **工具偶发失败**。
> 这就是为什么要 repeat;也是为什么 repeat 不同的 benchmark 不能简单比较稳定性。

---

## 三、一个决定性的实证:等权、三次、task-normalized

AA Coding Agent Index 的口径(**已核验原文**):

> *"Composite index of 3 benchmarks: **DeepSWE** (Software engineering tasks, **113 tasks**, by Datacurve) · **Terminal-Bench v2** (Agentic terminal use, **84 tasks**, by Laude Institute) · **SWE-Atlas-QnA** (Technical Q&A, **124 tasks**, by Scale AI). Each benchmark score averages **pass@1 across three attempts per task**. The Index gives **equal weight** to its 3 benchmark components."*
>
> *"For each benchmark, we **first average the three evaluated attempts for each task, then average those task-level scores so every task has equal weight**."*

这段话里藏着三个独立的设计选择,**每一个都会改变排名**:

| 选择 | 换一种做法会怎样 |
|---|---|
| **三次取平均**(repeated pass@1) | 若改成 pass@3(至少一次成功),**分数会系统性变高**,且高方差模型受益最大 |
| **task-normalized**(先按任务平均,再按任务等权) | 若改成「所有 attempt 直接平均」,**任务数多的 benchmark 会被隐性加权** |
| **三个组件等权** | 若按任务数加权(113 : 84 : 124),**Terminal-Bench 的影响会被压低** |

> ⟹ **聚合方式本身就是一个自变量。** 同一批原始 rollout 数据,换聚合口径就能产出不同的第一名。

---

## 四、那到底什么是「model evaluation」,什么是「agent-system evaluation」?

| | Model evaluation | Agent-system evaluation |
|---|---|---|
| 被测对象 | 模型权重 + 采样参数 | Model + Prompt + Harness + Tools + Environment |
| 典型 benchmark | GPQA Diamond · HLE(无工具) | GDPval-AA · τ³-Banking · Terminal-Bench |
| 分数可归因于模型吗 | 大体可以 | **不可以** |
| 换 harness 分数会变吗 | 不会(没有 harness) | **会,而且可能很大** |
| 它回答的问题 | 这个模型知道/会推什么? | **这套系统能不能把活干完?** |

在 AA 的九项里,**明确带 Tool Usage ✓ 的只有 Agents 类的两项**(GDPval-AA、τ³-Banking)。其余七项没有 agent 工具 —— 它们更接近 model evaluation。

> 📌 **建议你自己写下的定义**(参考版):
> **Agent-system evaluation 测量的是「模型 + prompt + harness + 工具 + 环境 + 预算」这一整套配置在给定任务分布上的成功率;它的结论只在该配置下成立,换掉其中任何一项都需要重新测量。**

---

## 五、四种评价单位(再强调一次,因为它决定你报什么数)

| 单位 | 例句 |
|---|---|
| **Turn** | 「它调用了正确的 API」 |
| **Trajectory** | 「它用 47 步完成了本可 6 步完成的事」 |
| **Task** | 「数据库里确实创建了 dispute」 |
| **Session** | 「第二个用户提问时,它复述了第一个用户的私有数据」 |

**benchmark 几乎只报 task 层。** 你的产品如果关心成本(trajectory)或多用户安全(session),**排行榜第一名对你可能毫无意义**。

---

## 六、写作任务(今天的主产出)

写一页 **800–1,200 字**的《为什么 agent 分数不是 model 分数》,交付到 `sec1-why-agent-score-is-not-model-score.md`。

**必须包含**:
1. 七因子公式,并**逐项**给一个「改它就改分数」的例子(可以直接用本文核验过的真实例子)
2. 同一模型换 harness 分数会变 —— 用 AA 单列 Harness Comparison 这一事实佐证
3. 四种评价单位各一例
4. **一段你自己的定义**:agent-system evaluation 是什么,与 model evaluation 的边界在哪
5. 一句「所以我读排行榜时会先问什么」

**自检**:写完后确认——
```
[ ] 全文没有出现「模型 X 的能力是 Y%」这种表述
[ ] 每个因子都有具体例子,不是只列名词
[ ] 有至少一个带出处的真实数字(版本号/任务数/预算)
[ ] 结尾能落到「对我的产品意味着什么」
```

---

## 七、练习

### 练习一:找出隐含假设
下面每句话都隐含了一个未言明的假设,指出来:
```
a. 「Model A 在 Terminal-Bench 上比 Model B 高 3 个点,所以 A 更适合做编码 agent。」
b. 「我们的 agent 在 SWE-bench 上达到了 SOTA。」
c. 「换了新模型后分数涨了,说明新模型更强。」
d. 「这个 benchmark 跑了 5 次,所以结果很稳。」
```
<details><summary>参考</summary>
a. 假设两者用同一 harness/预算/版本,且你的任务分布 ≈ Terminal-Bench 分布<br>
b. 假设 SOTA 归因于模型而非 harness/scaffold;且未说明是否 contamination<br>
c. 假设其他六个因子都没动(常见的是同时也升级了 harness 或 prompt)<br>
d. 5 次只压低了「模型采样随机性」,压不掉 task selection bias / scorer bias / contamination
</details>

### 练习二:设计一次公平比较
你要比较 harness X 与 harness Y 哪个更好。列出**必须固定**的所有变量,以及**必须报告**的所有元数据。

### 练习三:重算排名
三个 benchmark 的任务数为 113 / 84 / 124。某模型分数分别为 40% / 60% / 80%。
1. 按**组件等权**,总分是多少?
2. 按**任务数加权**,总分是多少?
3. 差多少?这说明什么?
<details><summary>答案</summary>
① (40+60+80)/3 = <b>60.0%</b><br>
② (113×40 + 84×60 + 124×80)/(113+84+124) = (4520+5040+9920)/321 = 19480/321 ≈ <b>60.7%</b><br>
③ 相差约 0.7 个点。看似小,但在排行榜上 0.7 点常常就是好几个名次 —— <b>聚合口径是自变量。</b>
</details>

---

## 本课一句话总结

> **排行榜分数不是模型的属性,是一次测量的属性。** 报分数时不报 harness、预算、grader 版本和聚合口径,等于报了一个无法复现的数。

---

**下一课(Day 6)**:第一次亲手算「这个分数能不能信」—— Bernoulli、标准误、Wilson 置信区间。
