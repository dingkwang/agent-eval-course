# 第 1 课:Scorer Is a Measurement Instrument

## Score 不是 ground truth;先写 measurement contract

**Week 4 Day 1** · scorer validation · 建议 70 分钟 + 20 分钟小 lab

> ### 本课唯一命题
> # Scorer 是一台测量仪器,不是事实本身。
> # 在相信 `score=1` 之前,必须写清它看到了什么证据、要判断哪个产品事件、允许犯什么错。

> 📄 Rosset et al., [*The Art of Building Verifiers for Computer Use Agents*](https://arxiv.org/abs/2604.06240), 2026 preprint
> 📄 Dong et al., [*How Benchmarks Mis-Score Computer-Use Agents*](https://arxiv.org/abs/2607.28367), 2026 preprint
> 📘 UK AISI, [Inspect Scorers](https://inspect.aisi.org.uk/scorers.html) 与 [Scoring workflow](https://inspect.aisi.org.uk/scoring.html)
> 💻 输入:固定的 task spec、完整 trajectory / final state、scorer output

```diag
flow | Week 3 与 Week 4 的接缝
Week 3 把 verifier score 当 observation
冻结 Agent 输出与 Trial evidence
Week 4 改问 scorer 有没有把 outcome 判对
只有 scorer 通过审计,score 才能回到统计 pipeline
```

Week 3 的均值、CI、paired comparison 可以全部算对,但如果 scorer 把成功判成失败,统计只会更精确地总结一把坏尺子。Week 4 固定 task 与 Agent trajectory,不再重跑 Agent;把 scorer 自己当作 system under test。

---

## 零、先看一个不能被 `accuracy` 掩盖的事实

2026 年一项 computer-use benchmark 复核抽查了 **150 条官方标为 FAIL 的公开 trajectories**。组合后的 blind-adjudication labels 认为其中 **15.3% 的 FAIL verdict 不正确**:10.7% 是 evaluator false negative,4.7% 是 broken task;另有 3.3% 因公开证据不足无法确定。

```diag
compare | 150 条 failure-scored trajectories 的复核
官方标签 | 复核后发现
全部写着 FAIL | 81.3% 仍可解释为 genuine failure
没有进一步原因 | 10.7% evaluator false negative
没有 UNKNOWN | 4.7% broken task · 3.3% evidence unclear
```

这组数字来自**只抽 FAIL 的审计样本**,不能写成「整个 benchmark 的 scorer 错误率是 15.3%」,也不能估计 false-positive rate。它能支持的结论更窄、也更重要:

> **一个确定的 FAIL 标签,仍可能来自 Agent、task、evidence 或 scorer 四个不同位置。**

来源:[How Benchmarks Mis-Score Computer-Use Agents, §4](https://arxiv.org/html/2607.28367v1)。论文报告的 15.3% Wilson CI 为 [10.4%, 22.0%]。

这里的 final labels 也不是「150 条全部由人类逐条复核」:两个 vision-enabled LLM annotators 先独立标全部 150 条;两组人类对所有 LLM disagreement 加分层抽取的 agreement rows 共 104 条做盲审;其余 46 条采用两个 LLM 的一致标签。课程保留这个构成,因为 reference standard 本身也有 measurement process。

---

## 一、四阶段 measurement pipeline

```diag
pipe | verdict 从哪里来
Task intent → Agent 与 environment 产生 trajectory → Logger 保存 evidence → Scorer 读取 evidence → Score 进入报告
```

四个阶段的问题不能混成一句「这题有 bug」:

```diag
grid | 四个阶段,四种责任
Task construction | 任务是否可解、要求是否明确 → W5
Trajectory observation | 必要 action / state / screenshot 是否被记录 → W2/W6
Scoring | 给定充分 evidence,规则是否判对 → W4
Reporting | score 是否被正确聚合、解释 → W3/W8
```

本周只做第三格。我们暂时接受一份经过人工澄清的 task intent,并问:

> 给定同一份 evidence,自动 scorer 的 verdict 是否与独立 reference adjudication 一致?

### 1.1 三个对象必须分开

```diag
nest | scorer 实际隔着证据测 outcome
Task intent · 用户到底要什么
  Reference outcome Z · 人工审定是否完成
    Observable evidence E · log / state / screenshots / output
      Automated score S · scorer(E, rubric, version)
```

这里的 $Z$ 是**昂贵、经过审定的 reference label**,不是上帝视角的绝对真理。人类也会分歧,所以 reference label 必须保留 annotator、证据和 adjudication 过程。

```math
Z_i\in\{0,1\},\qquad S_i=g(E_i,R,V)
```

$E_i$ 是 scorer 可见证据,$R$ 是 rubric,$V$ 是 scorer 完整版本。Scorer validation 研究的是 $S_i$ 与 $Z_i$ 的差异,而不是让 scorer 自己解释「我为什么很有信心」。

---

## 二、先定义产品事件,再定义 success label

「Agent 表现很好」不是可执行的评分条件。必须先写成用户可观察的事件。

```diag
compare | 同一 trajectory 可以对应不同产品事件
产品事件 | 可能的 success condition
订单最终被正确取消 | final database state 正确
订单取消且遵守授权政策 | outcome 正确 + forbidden action 未发生
正确告知用户但第三方服务宕机 | process 正确 · outcome blocked
生成可运行 patch | required tests pass + regressions 不增加
```

同一条 trajectory 可能「过程正确但 outcome 被环境阻断」,也可能「outcome 看似正确但过程违规」。把两者压成一个 bool 之前,要说明产品究竟关心哪个事件。

```diag
flow | product event 到 score 的编译
自然语言目标
拆成可判断的 atomic criteria
为每条 criterion 指定 evidence
定义 PASS / FAIL / PARTIAL / UNKNOWN
实现 scorer
```

Microsoft 的 2026 CUA verifier 工作把 **process reward** 与 **outcome reward** 分开,并区分 controllable 与 uncontrollable failure。原因不是为了多几个字段,而是避免一次外部阻塞把后续所有 criteria 连锁判错。[论文 §1](https://arxiv.org/html/2604.06240v1)

---

## 三、Score contract:写在 scorer code 之前

```diag
grid | 最小 score contract
Evaluation unit | 一条 response、完整 trajectory、还是最终 environment state
Allowed evidence | output · actions · logs · screenshots · DB diff
Criteria | 具体、互不重叠、能指向 evidence
Label space | PASS / FAIL / PARTIAL / UNKNOWN
Error policy | missing evidence、parse error、scorer crash 怎样记录
Identity | code + rubric + prompt + judge model + environment version
```

推荐机器可读格式:

```yaml
scorer_id: order_cancel_v3
evaluation_unit: trial
product_event: "requested order is canceled without unauthorized side effects"
evidence:
  required: [tool_calls, final_order_state, policy_snapshot]
criteria:
  - id: outcome
    predicate: final_order_state.status == "canceled"
  - id: authorization
    predicate: no_action_after_authorization_denied
labels: [PASS, FAIL, UNKNOWN]
missing_evidence: UNKNOWN
aggregation: all_required_criteria
version:
  code_commit: abc123
  rubric_digest: sha256:...
```

### 3.1 `UNKNOWN` 不是失败

```diag
compare | Agent failure 与 measurement failure
FAIL | UNKNOWN
证据充分,任务没有完成 | 无法可靠判断是否完成
记在 capability outcome | 记在 scorer / evidence coverage
可以进入 success-rate 分母 | 是否入分母要预注册,不能静默变 0
```

如果最后一张关键 screenshot 没被保存,scorer 没有资格猜 FAIL。`UNKNOWN` 会降低 coverage,但能阻止 measurement failure 被错误归因给 Agent。

---

## 四、Evidence contract:scorer 看不到的事实无法被验证

```diag
nest | agent task 的 evidence ladder
Final answer
  Structured tool calls
    Environment state delta
      Full event log
        Screenshots / artifacts / external receipts
```

证据越多不一定越好。无关 evidence 会增加 token overload、错误匹配和隐私风险。正确问题是:

> **对每条 criterion,最小充分 evidence 是什么?**

```diag
compare | evidence 不足与 evidence 过载
Too little | Too much
只看 Agent 自述「已完成」 | 把 200 张截图原样塞给 judge
遗漏瞬时错误与中间违规 | 关键状态淹没在长 context
容易 false positive | 容易漏看、截断、成本暴涨
```

CUAVerifierBench 的设计经验之一是让 verifier 覆盖完整 screenshot evidence,同时用 divide-and-conquer 管理长 trajectory,而不是只看最后几帧。[The Art of Building Verifiers, §1](https://arxiv.org/html/2604.06240v1)

### 4.1 每条 verdict 都应能回到 evidence

```json
{
  "label": "FAIL",
  "criteria": {
    "outcome": "PASS",
    "authorization": "FAIL"
  },
  "evidence_refs": ["event:17", "db-diff:orders/841"],
  "reason_code": "ACTION_AFTER_DENIAL",
  "scorer_version": "order_cancel_v3@abc123"
}
```

自由文本 explanation 可以保留,但不能替代 `criteria`、`evidence_refs` 和稳定的 `reason_code`。

---

## 五、Scorer error 不是一个数字

对 binary scorer,至少区分两种方向:

| | Reference success $Z=1$ | Reference failure $Z=0$ |
|---|---:|---:|
| Scorer PASS $S=1$ | TP | **FP**:失败被放过 |
| Scorer FAIL $S=0$ | **FN**:成功被拒绝 | TN |

```math
\mathrm{FPR}=\frac{FP}{FP+TN},\qquad
\mathrm{FNR}=\frac{FN}{FN+TP}
```

```diag
compare | 两个方向,两种产品损失
False positive | False negative
没有完成却得分 | 已完成却被判失败
夸大 capability · 污染训练 reward | 压低 capability · 惩罚有效策略
Null / shortcut controls 最容易暴露 | alternate-valid-path tests 最容易暴露
```

总体 accuracy 可能掩盖代价完全不同的错误。例如 95% 都是失败样本时,永远输出 FAIL 就有 95% accuracy,却识别不了任何成功。

### 5.1 `agreement` 也不等于 `validity`

```diag
grid | scorer 需要同时回答的四件事
Correctness | 与 reference label 是否一致
Consistency | 同一 evidence 重评是否稳定
Invariance | 无关变换后 verdict 是否不变
Coverage | 有多少 case 能给出非 UNKNOWN verdict
```

Cohen's $\kappa$ 可以扣除一部分偶然一致,但仍要和 confusion matrix、分类别错误率一起报告。一个 scorer 可以 $\kappa$ 尚可,却在高风险类别集中产生 false positive。

---

## 六、Reference labels 怎样产生

Human label 不是把工程师的第一反应写进 CSV。

```diag
flow | blind adjudication pipeline
冻结 task intent 与完整 evidence
隐藏 Agent / model identity
两名 annotator 独立判定 criteria
先记录 disagreement,不先互相说服
第三人或规则化会议 adjudicate
保存 final label + evidence refs + disagreement
```

最小 reference record:

```text
case_id
task_id
trial_id
reference_label
criterion_labels
annotator_ids
initial_disagreement
adjudication_status
evidence_refs
notes
```

```diag
compare | gold answer 与 reference standard
Gold answer | Reference standard
一条官方示范 trajectory / patch | 对 success contract 的审定标签
可能只是众多有效路径之一 | 接受所有满足 criteria 的路径
不能自动证明其他路径错 | 需要 evidence 与 adjudication 过程
```

这一区分对 Agent 特别重要:trajectory 空间巨大,reference action sequence 通常只是**一个**可行解,不应被误写成唯一允许路径。

---

## 七、Audit sample 怎样抽

只随机抽容易样本,会得到漂亮但无用的 accuracy;只抽 disagreement,又不能直接估计全体错误率。

```diag
compare | 两种样本,两种用途
Representative sample | Stress / disagreement sample
按 benchmark 分布抽取 | 过采样 borderline、长轨迹、官方 FAIL
估计实际 error prevalence | 找 failure modes、加速修 scorer
需要 task-cluster-aware CI | 不能把样本比例直接当总体比例
```

建议两张表分开报告:

```text
audit_representative   → overall FPR / FNR / coverage
audit_stress           → failure taxonomy / regression suite
```

若分层抽样后需要总体估计,必须保留 inclusion probability 并加权。Week 3 的不确定性规则继续有效:同一 task 的多条 trajectories 仍然是 cluster。

---

## 八、Scorer identity 必须可冻结

```diag
pipe | 一个可复现的 scorer_id
code commit + rubric digest + parser version + judge model snapshot + judge prompt + decoding config → scorer version
```

只写 `grader=gpt-x` 不够。模型 alias、system prompt、模板、输出 parser 任一变化都可能移动历史 score。

```diag
flow | scorer upgrade 不能静默覆盖历史
冻结原始 Trial evidence
旧 scorer 离线重放
新 scorer 离线重放
逐 case 比较 score flips
通过 regression gate 后发布新版本
```

Inspect 把 solver 与 scorer 分开,支持 custom / multiple / model-graded scorers,也支持对已有 eval log 使用 `inspect score` 离线重新评分。这正是 W4 需要的架构:修尺子时不重跑 Agent。[Inspect Scorers](https://inspect.aisi.org.uk/scorers.html)

---

## 九、Lab:给 Week 1 的 τ³ case 写 score contract

沿用 `labs/tau3-verifier/` 的 airline task `id=3`。先不要修 evaluator,只写 contract。

```diag
grid | 四条固定 trajectories
gold | 查会员与行程,正确告知可带 4 件
silent | 查对了,但没有告诉用户答案
cheat | 不查任何信息,只说 AA-1234
refuse | 没有 Agent action
```

### Step 1:写产品事件

```text
用户获得基于自己真实会员等级和行程的正确行李额度。
```

### Step 2:拆 criteria

```text
identity_evidence     找到了正确用户
itinerary_evidence    找到了相关行程
policy_reasoning      使用真实等级而非用户自述等级
communication        明确告知“4 件”且语义指向行李额度
```

### Step 3:给四条轨迹做 reference labels

| trajectory | reference | 原因 |
|---|---:|---|
| `gold` | PASS | criteria 全满足 |
| `silent` | FAIL | 没完成 communication 产品事件 |
| `cheat` | FAIL | `4` 只是 flight number 的一部分 |
| `refuse` | FAIL | 没有完成任务 |

### Step 4:定义 scorer contract

```diag
flow | contract 不是实现
先冻结产品事件
再列 atomic criteria
再绑定 evidence
再决定 label reduction
最后才选择 substring / predicate / judge
```

产物保存为 `labs/scorer-audit/contracts/airline-3.yaml`。下一课再用同目录的 Null、Oracle、mutation 和 alternate-valid-path controls 攻击实现。

---

## 十、验收

```text
[ ] 能解释 score 为什么不是 ground truth
[ ] 能画出 task intent → evidence → scorer → report 四阶段
[ ] 能区分 scorer error、broken task、missing evidence 与 Agent failure
[ ] 能写出 evaluation unit、product event、allowed evidence 和 label space
[ ] 不把 UNKNOWN 静默改成 FAIL
[ ] 同时报告 FPR 与 FNR,不只报 accuracy
[ ] reference labels 隐藏 Agent identity 并保留 adjudication
[ ] 分开 representative audit 与 stress audit
[ ] scorer identity 包含 code、rubric、prompt、model 与 parser version
[ ] scorer upgrade 使用固定 trajectories 离线重放
```

> ## 本课结论
> **`score=1` 不是事实;它是 `scorer_version` 对一份有限 evidence、按照一份 rubric 做出的测量。**
>
> 下一课研究最容易被误认为「绝对客观」的一类尺子:unit tests、substring、state predicate 与 database hash。

---

## References

1. Corby Rosset et al. [The Art of Building Verifiers for Computer Use Agents](https://arxiv.org/abs/2604.06240), 2026. 最新 Agent verifier 架构案例;核心是 criteria、process/outcome、failure attribution 与完整 evidence。
2. Zihan Dong et al. [How Benchmarks Mis-Score Computer-Use Agents](https://arxiv.org/abs/2607.28367), 2026. 对 150 条 failure-scored trajectories 的 blind audit;注意抽样与 adjudication 边界。
3. UK AI Security Institute. [Inspect Scorers](https://inspect.aisi.org.uk/scorers.html). Scorer 类型、custom / multiple scorers 与 offline scoring workflow。
4. τ³-bench course teardown: [`week01/lesson04-tau3-bench.md`](../week01/lesson04-tau3-bench.md) 与 [`labs/tau3-verifier/`](../labs/tau3-verifier/)。本课 contract case 的可运行来源。
