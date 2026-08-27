# 第 3 课:LLM-as-a-Judge for Open-Ended Artifacts

## 文学写作没有 gold answer 时,judge 究竟代表谁?

**Week 4 Day 3** · creative writing · preference evaluation · 建议 85 分钟 + 35 分钟 audit lab

> ### 本课唯一命题
> # 开放式作品没有唯一正确答案,但这不等于只能凭感觉打分。
> # 先分开约束、内容保持、作品技艺与受众偏好,再验证 judge 对哪一种人类判断有效。

> 📄 Wu et al., [*WritingBench: A Comprehensive Benchmark for Generative Writing*](https://arxiv.org/abs/2503.05244), NeurIPS 2025 Datasets & Benchmarks
> 📄 Fein et al., [*LitBench: A Benchmark and Dataset for Reliable Evaluation of Creative Writing*](https://aclanthology.org/2026.eacl-long.362/), EACL 2026
> 📄 Pauli et al., [*Mind the Style Gap: Meta-Evaluation of Style and Attribute Transfer Metrics*](https://arxiv.org/abs/2502.15022), Findings of EMNLP 2025
> 💻 [WritingBench](https://github.com/X-PLUG/WritingBench) · [LitBench](https://github.com/SAA-Lab/LitBench) · [EQ-Bench Creative Writing](https://github.com/EQ-bench/creative-writing-bench)
> 🔬 审计对象:[`lieflat-less-ai-tone`](https://github.com/larashero3-dotcom/lieflat-less-ai-tone)

```diag
compare | 两类 eval 的证据形状
Math / coding | 文学 / 报告 / presentation
唯一答案或 executable tests | 多个完全不同的好答案
Verifier 接近事实判断 | Judge 逼近带人群条件的质量判断
Alternate path 是边界问题 | 整个有效输出空间都是 alternate paths
主要担心漏测与 shortcut | 还要面对审美分歧与偏好代表性
```

前两课问的是:给定 task 与 evidence,deterministic verifier 有没有把 outcome 判对。本课删除一个最方便的假设:**任务可能根本没有 canonical answer、gold state 或足够表达质量的 unit tests。**

Agent 越来越常交付的不是一个 bool outcome,而是一份 artifact:研究报告、文学作品、产品文案、slide deck、设计方案。格式是否符合要求可以测试;作品是否清楚、有洞见、有声音、适合目标读者,不能靠一个 exact match 回答。

---

## 零、先把四个不同问题拆开

以「去 AI 味」为例,下面四个问题经常被压成一句「这篇写得像不像人」:

```diag
grid | 同一篇文本的四种 estimand
Source detection | 能否预测作者是人还是模型
Style characterization | 哪些形式特征在两组语料中频率不同
Intervention effect | 改写是否减少目标特征且保存内容
Artifact quality | 目标读者是否认为作品更好
```

它们需要不同数据、reference labels 与 scorer:

| 问题 | evaluation unit | reference | 典型 metric |
|---|---|---|---|
| 来源识别 | 一篇未知来源文本 | 真实 provenance | precision / recall / AUROC |
| 风格特征 | 文档或段落 | 对照语料 | feature density / effect size |
| 改写效果 | 原文—改写 paired artifact | 约束与人工审定 | preservation + target-style shift |
| 作品质量 | 一篇作品或作品 pair | 目标读者偏好 | rubric vector / pairwise preference |

[`lieflat-less-ai-tone`](https://github.com/larashero3-dotcom/lieflat-less-ai-tone)主要做第二项:以 300 篇模型文本和 329 篇人类文本检验 26 个候选特征,保留 11 项。它把这些特征编译成改写规则,因此开始触及第三项;但**特征命中率下降不自动证明第四项改善**。

```diag
flow | 不能静默跨过的推断
某特征在 AI 语料中更常见
该特征可用于描述当前语料差异
删除该特征让文本更少命中规则
目标读者更喜欢改写结果
```

前三个箭头都可能成立,最后一个仍可能失败。一篇文章可以没有破折号、翻案腔和提示性冒号,同时人物扁平、节奏无聊;优秀散文也可能有意大量使用这些结构。

> **Style proxy 不是 quality oracle。优化 proxy 之后必须重新测最终产品事件。**

---

## 一、开放式 artifact 不是「完全主观」,而是多层测量

不要问一个 judge「整体打几分」后就结束。先把证据拆成四层:

```diag
nest | open-ended artifact 的评价层级
Audience value · 目标读者是否愿意读、信、采用
  Craft quality · 结构、论证、人物、节奏、语言控制
    Fidelity · 事实、设定、因果、语气强度是否保留
      Hard constraints · 格式、长度、必含元素、引用规范
```

### 1.1 Hard constraints:能执行就不要交给 taste

字数范围、JSON schema、必须出现的角色、slide 数量、引用是否存在,可以用 deterministic checks。它们是必要条件,通常不是作品质量本身。

```diag
compare | 同一份作品的 constraint 与 quality
Constraint | Quality
必须为第一人称 | 第一人称声音是否可信
包含三个给定事实 | 事实是否自然进入叙事
不超过 1500 字 | 节奏是否紧凑
引用两个来源 | 论证是否真正使用来源
```

把 hard constraints 混入一个「写作质量 8.4」会丢失失败原因。更糟的是,judge 可能因文笔漂亮而原谅漏掉硬要求。

### 1.2 Fidelity:改写任务有 source,但 source 不是 reference answer

Style transfer / editing 的核心约束是:

```math
\text{change intended style}\quad\land\quad\text{preserve non-style content}
```

词面相似度会把必要的风格变化也当成损失;普通 semantic similarity 又可能漏掉数字、否定、人物关系与判断强度的改变。`Mind the Style Gap` 的 meta-evaluation 说明,content-preservation metric 必须对目标 style shift 有条件地解释差异,不能把所有变化混成一个距离。

最小 fidelity contract 至少拆出:

```diag
grid | 改写的 preservation checks
Facts | 姓名、数字、日期、来源
Relations | 谁做了什么、人物与实体关系
Logic | 因果、否定、条件、先后
Force | 可能 / 通常 / 必须等判断强度
Structure | 用户要求保留的标题、段落、列表
```

### 1.3 Craft quality:criteria 必须针对作品与任务

小说的角色发展、研究 brief 的证据综合、广告的受众说服力不是同一 construct。「正确、相关、流畅」三个通用词不足以覆盖它们。

WritingBench 收集 1,000 个写作任务,覆盖 6 个一级领域和 100 个子领域,并为每个 query 生成五条 instance-specific criteria。论文报告其 query-dependent framework 与人类判断达到 84% agreement,高于两种 static-criteria baseline;这不是证明 84% 可以外推到任何写作任务,而是说明**criteria 与当前任务的要求对齐会改变 judge validity**。

### 1.4 Audience preference:reference label 属于某个 population

文学评价中的分歧不总是 annotation error。同一作品可以适合类型小说读者、不适合文学期刊编辑;适合 Reddit WritingPrompts、不适合中文散文读者。

```math
Z_{i,g}=\text{preference of audience group }g\text{ on artifact }i
```

没有 $g$ 的「人类偏好」是不完整的 estimand。需要写清:

- 谁是目标读者;
- 他们在什么阅读情境下判断;
- 看见哪些背景、prompt 与 source material;
- 评价个人喜好、专业技艺、购买意愿还是任务用途;
- disagreement 如何保存,而不是怎样尽快平均掉。

---

## 二、Rubric 是局部 measurement contract

Rubric 不是形容词列表。每一项都要说明对象、证据和锚点。

```yaml
criterion_id: narrative_consistency
claim: "人物行动与已建立的动机和世界状态一致"
evidence_unit: "完整故事"
anchors:
  1: "关键行动与已建立信息直接矛盾"
  3: "主要行动可解释,但有局部断裂或未铺垫转折"
  5: "关键行动均有前文依据,变化得到充分铺垫"
abstain_when:
  - "截断导致结尾不可见"
  - "prompt 未提供必要设定"
```

### 2.1 Criteria 要分解,但不能重复计票

```diag
compare | 可诊断 criteria 与同义重复
分开测 | 重复加权
Instruction adherence | Overall quality
Content fidelity | Writing quality
Narrative coherence | Coherence and logic
Voice / style control | Professional polish
Audience fit | Overall effectiveness
```

右栏的 criteria 边界模糊且高度重叠。Judge 可能因为同一个优点连续加三次分,最后的平均值看起来精细,实际只是隐含权重。

### 2.2 Static rubric 与 query-dependent rubric

```diag
compare | 两种 rubric 的 trade-off
Static | Query-dependent
跨任务口径稳定 | 能捕捉题目特有要求
容易审计与比较 | criteria generator 本身也要验证
可能漏掉领域技艺 | 可能随被测输出或 judge 漂移
适合少量统一核心维度 | 适合多样 artifact tasks
```

实用结构是**少量固定核心维度 + task-specific criteria**。动态 criteria 必须只根据 task、intended audience 与 source material 生成,不能先看到候选模型的作品再决定评分标准。

```diag
flow | 防止 post-hoc rubric
冻结 task 与 intended use
生成 / 人工审定 criteria
冻结 anchors 与 aggregation
隐藏 model identity
生成并评分 artifacts
```

---

## 三、Absolute score 与 pairwise preference 回答不同问题

### 3.1 Absolute rubric score

Judge 单独看一篇作品,按每项 1–5 分评分。

优点:能给 criterion breakdown,方便诊断。缺点:不同 judge 的「4 分」尺度不同,同一 judge 也会随样本上下文漂移;总分常出现拥挤和虚假精度。

### 3.2 Pairwise comparison

Judge 同时看 A/B,回答哪篇更符合预先定义的 preference target。

```math
P(A\succ B)=\sigma(r_A-r_B)
```

Pairwise 通常比绝对打分容易,也能用 Bradley–Terry / Elo 聚合;但它引入 position、长度、对比集合和 intransitivity。A 胜 B、B 胜 C 不保证 A 胜 C。

```diag
compare | 什么时候用什么
Rubric score | Pairwise preference
需要知道哪里失败 | 需要稳定选出两个候选中较好者
跨版本保留诊断维度 | 排序与 best-of-N selection
需要校准 scale anchors | 需要控制顺序与 matchup graph
容易重复计权 | 难解释为什么赢
```

好的 writing eval 往往同时保留 rubric vector 与 pairwise choice,而不是把其中一个伪装成全部事实。

---

## 四、LitBench:「人类标签」也要写 measurement contract

LitBench 把同一 Reddit prompt 下的两篇故事组成 pair,用 upvote 信号确定 preferred story。最终 test set 有 2,480 pairs,training corpus 有 43,827 pairs。

这不是把 upvote 直接当真理。作者做了三项关键控制:

```diag
grid | LitBench preference-data controls
Engagement floor | 故事至少 10 个 upvotes
Temporal control | winner 必须发布得更晚,减轻曝光时间优势
Length balancing | 对 length difference 分桶裁剪,让长 / 短 winner 对称
```

未经这些处理的 preference data 会训练出 shortcut:更多曝光、更长文本 → 更高 reward。LitBench 的 ablation 显示,未处理长度的 reward model 会强烈偏好更长故事。

### 4.1 Judge performance 是 agreement,不是 literary truth

在这个特定 reference process 上:

- 最强 zero-shot judge Claude 3.7 Sonnet 与 labels 一致约 **73%**;
- 训练过的 Bradley–Terry / generative reward model 约 **78%**;
- 新生成故事的人类实验中,46 位美国 / 英国 crowd-workers 对 reward-model winner 的选择率为 57%,对 loser 为 41%,仍有约四成 disagreement。

这些数字不能外推成「judge 有 78% 概率认出好文学」。它们估计的是:

```text
在 LitBench 的 Reddit prompt、过滤规则、读者信号与 pair construction 下,
scorer 预测该 reference preference label 的能力。
```

论文也明确承认 Reddit 用户人口结构与社交 upvote 动机的限制。Reference standard 不是脱离文化和场景的 gold truth。

---

## 五、LLM judge 的 control suite

同一个 judge prompt 在一批正常样本上与人类相关,仍可能依赖 shortcut。至少要跑以下 counterfactual controls。

```diag
grid | open-ended judge 的六类 controls
Position swap | A/B 交换后 preference 应翻转身份但不翻转作品
Identity blind | 隐藏 / 伪造 model name,verdict 不应跟品牌走
Length perturbation | 加无信息 filler 不应稳定获胜
Style laundering | 只去掉表面 AI markers 不应自动提升 craft
Content corruption | 文风不变但改错事实 / 人物关系,分数应下降
Repeat | 固定输入重复评分,估计 verdict consistency
```

### 5.1 Position bias 不是只跑两次然后取平均

对每个 pair 运行 `(A,B)` 与 `(B,A)`:

| 第一次 | 交换后 | 解释 |
|---|---|---|
| A | A 对应作品仍胜 | order-consistent |
| A | 新位置 A 胜 | position-sensitive |
| tie | A / B | 决策边界不稳定 |
| parse error | 任意 | scorer failure,不是作品 FAIL |

既要报告经 permutation 汇总的 preference,也要报告 swap inconsistency rate。后者是 scorer coverage / reliability metric。

### 5.2 Length bias 要用 meaning-preserving 与 meaning-damaging mutation 分开测

```diag
compare | 两种 length mutation
无信息扩写 | 有意义扩写
重复已知结论、华丽同义句 | 补足必要铺垫、证据或人物动机
Quality 不应仅因更长上升 | Quality 可能合理上升
用于检测 verbosity shortcut | 用于测试 rubric 是否识别真实增益
```

只计算「长文本胜率」无法区分偏差与真实质量差异。需要从同一 artifact 出发构造 controlled mutations。

### 5.3 Judge explanation 不是 correctness evidence

一段流畅 rationale 可以合理化错误 verdict。LitBench 甚至发现,在其 trained generative reward models 上加入 chain-of-thought 后 accuracy 从约 78% 降至约 72%。Judge 的 explanation 适合错误分析,不能代替和 reference labels 的比较。

---

## 六、`lieflat` case:测到 style shift 以后还缺什么

该仓库公开了六次 operator failure,其中最适合本课的是:

```diag
compare | 同一个「AI 味」主张的 measurement failures
旧测量 | 修正后
Markdown 表格 / 列表被当成长句 → 句长均匀 51× | 清理正文后 CV ratio 0.87
问句小标题按每千字 → 32× | 按全部小标题占比 → 无差异
冒号正则包含标题 / 列表 / 对话 → 无差异 | 按目标语义缩窄后 ratio 3.8
```

这些例子证明 feature scorer 也需要 validation。但即使 11 个 feature operators 全部有效,一个 rewriting agent 的 eval 仍需两条独立证据链:

```diag
flow | intervention evaluation
原文 → Style editor → 改写文
Feature scorer 测目标特征是否减少
Fidelity scorer 测信息与语气是否保存
Human / validated judge 测目标读者偏好与 craft
```

### 6.1 不要用同一 proxy 同时训练与宣布成功

如果 Skill 明知规则是「少用破折号、翻案腔、提示性冒号」,再用同一批 regex 为改写结果打分,它当然容易变好。这只证明执行器适应了 visible reward。

```diag
compare | Dev signal 与 held-out outcome
Visible dev scorer | Independent test outcome
11 条 feature hits | 盲测 reader preference
定位具体改写位置 | 内容保持与语气强度
快速 regression | held-out model / topic / genre
允许 Agent 针对性优化 | 规则与 labels 对 Agent 隐藏
```

正确设计要有 held-out models、topics、genres,还要保留**人类原稿 false-positive edit rate**:一个去 AI 味 Agent 若不断修改本来很好的真人文字,产品仍然失败。

---

## 七、Model writing eval 与 Writing Agent eval

让模型一次性响应「写一篇小说」,测的是 model + decoding + prompt。Writing Agent 则可能执行:

```diag
flow | writing agent trajectory
解释 brief
构思与大纲
收集 / 核对材料
起草 artifact
批评与 revision
交付最终版本
```

Agent eval 需要同时保存 final artifact 与 revision trace:

| 层 | 可观察问题 |
|---|---|
| Brief recovery | 是否识别受众、目的、硬约束与 source facts |
| Planning | 是否形成可用结构,不是计划写得越长越好 |
| Evidence use | 是否引用 / 使用正确材料,有没有编造 |
| Revision | 是否响应反馈并修复目标问题 |
| Regression | revision 是否破坏已经正确的内容 |
| Final value | 目标读者是否愿意采用最终 artifact |

但不要把 reference workflow 当唯一合法过程。优秀作者可以先写场景再发现结构,也可以先做严密大纲。Process criteria 只约束必须发生或绝不能发生的事件,不要求复刻某一位作者的创作习惯。

---

## 八、不要太早压成一个总分

一个最小 writing eval row 应保留:

```json
{
  "artifact_id": "story-017-candidate-b",
  "hard_constraints": {"label": "PASS", "violations": []},
  "fidelity": {"facts": 1.0, "relations": 0.8, "force": 1.0},
  "craft": {"coherence": 4, "voice": 3, "pacing": 2, "originality": 4},
  "audience_preference": {"wins": 7, "losses": 4, "ties": 1},
  "judge_reliability": {"swap_consistent": false, "repeat_agreement": 0.67},
  "scorer_version": "writing-audit-v1"
}
```

```diag
compare | 总分相同,产品含义不同
Artifact A | Artifact B
约束全满足、事实正确 | 漏一项硬约束
声音普通、节奏稳定 | 文笔惊艳
目标读者多数愿意采用 | 读者喜欢但无法直接采用
```

是否允许 B 胜出取决于 intended use。发布 gate、创意探索和 best-of-N selection 会有不同 reduction policy。先报告 vector、disagreement 与 Pareto frontier;只有决策必须单排序时才冻结 aggregation。

---

## 九、Lab:审计一个「去 AI 味后写得更好」的 claim

目标不是训练一个文学 judge,而是证明现成 judge 到底测到什么。

### Step 1:冻结三个 claim

```yaml
claims:
  style: "edited text has fewer pre-registered AI-tone features"
  fidelity: "editing preserves facts, relations, logic and epistemic force"
  preference: "target readers prefer the edited artifact for the stated use"
```

不能用 style scorer 支持 preference claim。

### Step 2:构造 12 个 paired controls

从 4 篇短文各造三个 mutation:

| mutation | 预期保持 | 预期变化 |
|---|---|---|
| `marker-only` | 内容、结构 | 删除一个已注册 style marker |
| `fact-corrupt` | 表面文风 | 数字、否定或人物关系被改错 |
| `filler-long` | 核心命题 | 增加 30% 无信息文字 |

至少一半原文来自人类写作,用来估计 false-positive editing harm。

### Step 3:比较三种 judge protocol

```text
A. static rubric absolute 1–5
B. task-specific rubric absolute 1–5
C. blinded pairwise preference + tie
```

每种 protocol 都执行 A/B swap;随机隐藏原文 / 改写文身份;至少重复两次。

### Step 4:收集一个小 reference set

三名读者独立判断,先保留每个人的 label 与理由。只有当 intended audience 相同且 aggregation 预先写定时,才计算 majority preference。

### Step 5:输出 scorer audit table

| 必报项 | 问题 |
|---|---|
| Human agreement | 人类自己是否共享同一 preference target |
| Judge–human agreement | judge 预测哪类人类判断 |
| Swap inconsistency | 位置变化导致多少 verdict 改变 |
| Length shortcut | filler-long 获胜多少次 |
| Fidelity sensitivity | fact-corrupt 是否被稳定拒绝 |
| Proxy gaming | marker-only 是否无条件获胜 |
| Coverage | parse error / UNKNOWN / tie 有多少 |

### Step 6:写结论边界

合格结论示例:

```text
在 4 篇短中文非虚构文本、三名目标读者与 writing-audit-v1 judge 下,
marker-only edits 降低了预注册 feature hits;
现有样本不足以证明总体读者偏好提升。
Judge 对 fact corruption 的 sensitivity 为 ...,
但 swap inconsistency 与 filler preference 表明它不能直接用于 release gate。
```

不合格结论:

```text
去 AI 味 Skill 已被证明能让任何文章更像人写、质量更高。
```

---

## 十、验收

```text
[ ] 不把 source detection、style characterization、intervention effect 与 artifact quality 混为一个 estimand
[ ] Hard constraints、fidelity、craft 与 audience preference 分层评分
[ ] 每条 rubric criterion 有 evidence unit 与 scale anchors
[ ] 动态 criteria 在看到候选输出前冻结
[ ] Reference preference 写明 audience population 与 collection process
[ ] Pairwise evaluation 同时报告 position-swap inconsistency
[ ] 用 controlled mutation 区分 length bias 与真实内容增益
[ ] Judge explanation 不代替 judge–human validation
[ ] Style proxy 改善后仍独立检查 fidelity 与 reader preference
[ ] Writing Agent 同时保存 final artifact 与 revision trace
[ ] 不把 reference writing process 锁成唯一合法路径
[ ] 汇总前保留 criterion vector、disagreement、tie 与 UNKNOWN
```

> ## 本课结论
> **开放式作品不是没有 ground truth 就无法评测,而是 reference 从「唯一答案」变成了「有明确人群、任务和程序的人类判断」。**
>
> LLM judge 不是审美事实的廉价替身。它是一台 preference-prediction instrument;必须用目标人群的 labels、反事实 controls 与独立 outcome 来验证。

---

## References

1. Yuning Wu et al. [WritingBench: A Comprehensive Benchmark for Generative Writing](https://arxiv.org/abs/2503.05244), NeurIPS 2025 Datasets & Benchmarks. 1,000 queries、6 domains、100 subdomains 与 query-dependent criteria;[repo](https://github.com/X-PLUG/WritingBench)。
2. Daniel Fein et al. [LitBench: A Benchmark and Dataset for Reliable Evaluation of Creative Writing](https://aclanthology.org/2026.eacl-long.362/), EACL 2026. 2,480 held-out pairs、43,827 training pairs、length / temporal controls、judge 与 reward-model meta-evaluation;[repo](https://github.com/SAA-Lab/LitBench)。
3. Amalie Brogaard Pauli et al. [Mind the Style Gap: Meta-Evaluation of Style and Attribute Transfer Metrics](https://arxiv.org/abs/2502.15022), Findings of EMNLP 2025. Style-aware content preservation 与 metric test-set validity。
4. Carlos Gómez-Rodríguez and Paul Williams. [A Confederacy of Models: a Comprehensive Evaluation of LLMs on Creative Writing](https://aclanthology.org/2023.findings-emnlp.966/), Findings of EMNLP 2023. 基于 creative-writing pedagogy rubric 的早期系统人类评测。
5. EQ-Bench. [Creative Writing Benchmark v3](https://github.com/EQ-bench/creative-writing-bench) 与 [Longform Creative Writing Benchmark](https://github.com/EQ-bench/longform-writing-bench). Rubric + pairwise + Glicko 与 planning / revision / long-form workflow 的工程实现。
6. Lara. [`lieflat-less-ai-tone`](https://github.com/larashero3-dotcom/lieflat-less-ai-tone). 283 万字中文对照语料、26 个候选特征、11 条规则与六次 operator failure;本课把它用作 style proxy → intervention → outcome 的审计案例。
