# 第 2 课:Deterministic Verifiers

## Unit tests、state predicates 与 substring 为什么会稳定地判错

**Week 4 Day 2** · verifier engineering · 建议 75 分钟 + 30 分钟 lab

> ### 本课唯一命题
> # Deterministic 只保证同一输入得到同一 verdict,不保证 verdict 与任务成功一致。
> # 好 verifier 必须同时拒绝 shortcut、接受 alternate-valid path,并在证据不足时 abstain。

> 📄 OpenAI, [*Why SWE-bench Verified no longer measures frontier coding capabilities*](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/), 2026
> 📄 OpenAI, [*Separating signal from noise in coding evaluations*](https://openai.com/index/separating-signal-from-noise-coding-evaluations/), 2026
> 📄 [*Benchmarking the Benchmarks: A Validity Audit of Tool-Calling Evaluation*](https://arxiv.org/abs/2607.02577), 2026 preprint
> 📄 Rosset et al., [*The Art of Building Verifiers for Computer Use Agents*](https://arxiv.org/abs/2604.06240), 2026 preprint
> 💻 复用:`labs/tau3-verifier/`

```diag
compare | 两种常被混为一谈的性质
Determinism | Validity
同一 evidence 每次 verdict 相同 | verdict 对应产品定义的成功
消除 scorer sampling variance | 控制 false positive / false negative
可以稳定地错 | 才能作为可信 reward
```

LLM judge 的随机性很显眼;`pytest`、regex 和 DB hash 看起来像硬事实。但只要 predicate 写错、观察错对象或覆盖不足,它们会以 100% reproducibility 反复制造同一个错误。

这不是只靠一个课程 toy case 得出的结论。2026 年对 BFCL v4、τ²-Bench Retail、LiveMCPBench 与 MCP-Atlas 的 trace-level audit 检查了 496 次执行,发现 **92/496(18.5%)** official labels 与 expert judgments 不一致。确定性 evaluator 的公开 failure modes 包括 brittle state matching、exact match、annotation error 与 trajectory lock-in;τ² 子样本中还同时出现了 substring communication false negative 和「预期状态不变,什么也不做仍 PASS」的 false positive。[Benchmarking the Benchmarks, Table 3 / §4.3](https://arxiv.org/html/2607.02577v1)

---

## 零、一个 reward=1.0、任务却完全没完成的 case

Week 1 的可运行 lab 把四条手写 trajectory 送进 τ³-bench airline `id=3` 的官方 evaluator:

| trajectory | 做了什么 | official reward |
|---|---|---:|
| `gold` | 查询正确数据并告知 4 件行李 | 1.0 |
| `silent` | 查询正确但不告知答案 | 0.0 |
| `cheat` | 什么都不查,只说 `your flight is AA-1234` | **1.0** |
| `refuse` | 没有 Agent action | 0.0 |

```diag
flow | cheat 为什么变绿
COMMUNICATE 要找字符串 "4"
cheat 文本里出现 AA-1234
substring predicate 返回 true
只读 task 的 DB hash 也返回 true
1.0 × 1.0 = official reward 1.0
```

把 `AA-1234` 改成 `AA-1235`,同样零工作量,COMMUNICATE 从 1.0 变成 0.0。Evaluator 完全 deterministic;它稳定测到的是「任意 assistant 文本中是否出现字符 4」,不是「用户是否获得正确行李额度」。

```diag
compare | scorer predicate 与 product event
实现的 predicate | 想测的事件
文本包含字符 4 | 4 表示该用户可携带的行李件数
最终 DB 等于初始 DB | Agent 查了必要信息并正确推导
二者都 true 就 PASS | 用户问题真的被解决
```

> 复现:`uv run --project ../code/tau2-bench python ../labs/tau3-verifier/run.py`

---

## 一、Verifier 是 product event 的 executable approximation

设 $U(x)$ 表示 trajectory $x$ 是否真正满足产品成功定义,$V(x)$ 是 verifier verdict。

```math
V(x)\approx U(x)
```

Verifier 需要同时接近两个方向:

```diag
compare | 必要条件与充分条件
避免 false positive | 避免 false negative
V(x)=1 应足以说明 U(x)=1 | U(x)=1 时应尽量有 V(x)=1
拒绝 shortcut / no-op / forbidden side effect | 接受等价表达 / alternate path / irrelevant state changes
```

现实中很难证明完全等价,所以 verifier engineering 的工作不是写一次 predicate 就结束,而是不断构造反例逼近这个等价关系。

```diag
flow | verifier development loop
写 success contract
实现最小 predicate
生成 positive / negative controls
寻找 shortest false-positive program
寻找 alternate-valid false negative
把反例加入 regression suite
```

---

## 二、四类 deterministic verifier,四种错法

```diag
grid | 常见 verifier families
String / exact match | 比较字符或 normalized answer
Unit / integration tests | 执行代码并观察 assertions
State predicate | 检查 DB、文件、UI、外部 receipt
Action / trace predicate | 检查 tool call、顺序、policy 与副作用
```

| 类型 | 典型 false positive | 典型 false negative |
|---|---|---|
| String | 关键词碰巧出现 | 等价表达或格式不同 |
| Unit tests | 未覆盖行为仍通过 | 测试绑定无关实现细节 |
| State | no-op 恰好等于 expected state | 无关字段、时间、ID 不同 |
| Action | 模仿 reference calls 但结果错 | 有效 alternate path 被拒绝 |

关键不是找「最客观」的类型,而是让 evidence 与 product event 对齐。复杂任务通常需要组合多种 predicates,并保留 criterion-level breakdown。

---

## 三、String matching:语法相似不等于语义正确

```diag
grid | substring 的四个攻击面
Collision | 目标数字嵌在 flight ID、日期或金额中
Negation | "not 4" 仍包含 4
Quotation | 重复用户的错误说法也命中
Context loss | 说了 4,但不知道它指人数、件数还是价格
```

从弱到强的升级路线:

```diag
flow | communication verifier ladder
raw substring
normalized extraction + typed field
绑定语义 role 与 entity
与 authoritative state 交叉检查
证据不够则 UNKNOWN
```

例如不要只输出 `contains("4")`,而要提取结构化 claim:

```json
{
  "claim_type": "baggage_allowance",
  "passenger_id": "P123",
  "itinerary_id": "I456",
  "quantity": 4,
  "unit": "bags",
  "evidence_refs": ["tool:lookup_membership#9", "tool:get_itinerary#12"]
}
```

然后 verifier 再把 claim 与 authoritative policy/state 对齐。LLM extraction 可以参与,但一旦用了模型,它就是 Lesson 3 的 model-graded scorer,不能再叫纯 deterministic。

### 3.1 Exact match 什么时候反而正确

```diag
compare | exact match 的适用边界
适合 | 不适合
唯一 canonical ID、hash、选择题 label | 开放式解释、自然语言 claim
parser 先固定输出 grammar | 正确答案有多种表达
格式本身属于产品 contract | 格式只是无关表现形式
```

不要因为 exact match 简单就默认使用,也不要因为它简单就默认淘汰。它是否有效取决于「字符串身份」是不是产品事件的一部分。

---

## 四、Final-state trap:no-op 也可能等于 gold state

airline `id=3` 是只读任务。Gold actions 只查询,所以 gold trajectory 执行前后 DB 不变:

```diag
compare | 相同终态,不同任务完成度
Gold trajectory | Refuse / no-op
查询会员与行程后正确回答 | 什么也没查、什么也没说
final DB = initial DB | final DB = initial DB
任务完成 | 任务失败
```

因此 DB equality 在这道题上退化成常量 1:

```math
V_{DB}(x)=\mathbf 1[state_{final}(x)=state_{gold}]=1
```

这个 predicate 不是执行出错,而是对该 task **没有区分能力**。

```diag
flow | 发现 constant verifier
对 Oracle 运行 → PASS
对 Null 运行 → 仍 PASS
对随机无关 action 运行 → 仍 PASS
判定该 criterion 对 task 无信息
删除、替换或补充 process / communication evidence
```

### 4.1 Full-state equality 又可能太严格

```diag
compare | state predicate 的两端失败
太宽 · under-constrained | 太窄 · over-constrained
只查 status=canceled,遗漏退款金额 | 比较整个 DB hash
错误副作用仍可能通过 | 无关时间戳 / ID / 排序变化导致失败
false positive | false negative
```

更稳的做法是从 contract 编译**相关字段 predicate + invariants**:

```python
assert order.status == "canceled"
assert refund.amount == expected_refund
assert inventory.reserved == before.inventory.reserved - requested_qty
assert unrelated_customer_rows == before.unrelated_customer_rows
```

不是所有字段都要相等,但关键 side effects 必须明确检查。

---

## 五、Reference trajectory 是 witness,不是唯一合法路径

```diag
nest | success 是一组 trajectories
所有可能 trajectories
  满足产品事件的有效集合 U
    官方 gold trajectory 只是其中一个 witness
```

如果 verifier 要求 Agent 完全复现 gold tool sequence,会拒绝:

- 合并两个查询的批量 API;
- 使用缓存但仍取得同一 authoritative fact;
- 先验证身份再查询,而不是相反;
- 通过另一个允许的工具达到等价 final state。

```diag
compare | sequence equality 与 semantic invariants
Gold trace equality | Semantic verification
动作名、参数、顺序全部相同 | 必要授权、outcome、禁止副作用满足
容易写、容易复现 | 更接近产品成功
把实现路径当规范 | 接受 alternate-valid paths
```

Action constraints 仍然必要,但应表示**必须发生或绝不能发生的行为**,而不是把示范解逐行复制成答案键。

---

## 六、Unit tests:通过测试不等于功能完全正确

```diag
compare | test suite 的两类边界错误
Too narrow / overly strict | Too weak / low coverage
要求题目没规定的函数名或内部结构 | 只覆盖 happy path
正确实现也 FAIL | incomplete / shortcut fix 也 PASS
false negative | false positive
```

OpenAI 2026 年复核 SWE-bench Verified 中 138 个 o3 未稳定解决的问题,报告至少 59.4% 存在 material test/design issue:35.5% 是 narrow tests,18.8% 是 wide tests,5.1% 是其他问题。**这不是全 500 题的随机抽样错误率**;它针对 frontier model 经常失败的子集,说明剩余 FAIL 不能自动解释成能力不足。[官方审计](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)

同年对 SWE-Bench Pro 731-task public split 的质量审计也发现:

```diag
grid | SWE-Bench Pro QA 报告的四类 breaking issue
Overly strict tests | 强制 prompt 未规定的实现细节
Underspecified prompt | hidden tests 要求无法合理推断
Low-coverage tests | 不完整 fix 仍能通过
Misleading prompt | 题面把 Agent 引向错误行为
```

初始 automated filter 先 flag 286 个 potentially broken tasks;随后对这个候选集走两条深审路径:多轮 investigator agents + researcher final judgment 的 pipeline 最终标记 200/731,五名工程师独立 review 的 human campaign 标记 249/731。286 是 triage candidates,200 不是纯自动筛选输出;disagreement 与低置信 case 还会继续 escalation。[Separating signal from noise](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)

### 6.1 测试通过需要三个方向

```diag
grid | executable verifier 的三层 assertions
Required behavior | 题面明确要求的新功能
Regression safety | 原有相关功能不被破坏
Forbidden shortcuts | 不得修改 tests、绕过 verifier、硬编码答案
```

第三层是否属于 W4 还是 W7,取决于目的:普通 shortcut regression 属于 verifier completeness;主动对抗与 reward hacking 的系统研究留给 W7。

---

## 七、Control suite:先测 verifier,再测 Agent

最小 verifier QA 不是「gold patch 能过」,而是一组带预期 verdict 的 controls。

```diag
grid | 六类必做 controls
Oracle | 官方正确实现 / trajectory 必须 PASS
Null | 不做任何工作必须 FAIL
Minimal corruption | 改错一个关键事实必须 FAIL
Irrelevant mutation | 无关格式 / 字段变化后 verdict 不变
Alternate valid path | 不同合法路径仍 PASS
Forbidden side effect | outcome 正确但违规操作应按 contract FAIL
```

### 7.1 Oracle + Null 是最低门槛,不是全部

```diag
flow | 两端 sanity check
Oracle FAIL → verifier / environment / task 至少一个坏了
Null PASS → predicate 缺少必要条件
两者都正确
继续测 decision boundary 附近的 mutations
```

一个只会区分「完全正确」与「什么都不做」的 verifier,仍可能被几乎正确或巧妙 shortcut 的输出骗过。

### 7.2 Metamorphic tests

没有唯一 expected output 时,可以测试**关系**:

```diag
compare | 应保持 verdict 与应翻转 verdict
Invariant transformation | Meaning-changing mutation
改写措辞、调整 JSON key 顺序 | 把 refund 100 改成 10
无关字段、随机 ID 改变 | 删除 authorization action
合法工具顺序变化 | 增加 forbidden side effect
verdict 应不变 | PASS 应翻成 FAIL
```

这类测试特别适合暴露 brittle equality 与 substring collision。

### 7.3 Mutation testing verifier sensitivity

```diag
flow | 从 Oracle 生成近邻反例
从正确 trajectory 开始
每次只破坏一个 atomic criterion
运行 verifier
记录该 mutation 是否被 kill
未被发现的 mutation = coverage hole
```

Mutation 不要只改输出文本。Agent task 至少要覆盖 tool argument、缺失 action、错误 entity、重复副作用、最终 state 与 communication claim。

---

## 八、Process 与 outcome 要互补,不要重复计分

```diag
compare | process / outcome 的不同证据
Process | Outcome
是否调用允许的工具、遵守 policy | 世界最后是否达到用户目标
能解释 blocked success 与违规路径 | 接近用户最终价值
过度限制会拒绝创新路径 | 只看终态会漏掉危险过程
```

Rubric criteria 应该具体且非重叠。若 `correctly canceled order`、`order status is canceled`、`task completed` 三项其实检查同一个状态,相乘或平均只是重复加权。

```diag
flow | criterion reduction 保留诊断
每条 criterion 独立输出 label + evidence
先保留完整 breakdown
按预注册规则 reduce 成 overall score
报告失败 reason code
不要只保存一个 0
```

CUAVerifierBench 的四项设计原则正好对应这里:非重叠 criteria、process/outcome 分离、controllable/uncontrollable failure 分离、完整 trajectory evidence。[论文](https://arxiv.org/html/2604.06240v1)

---

## 九、什么时候必须输出 UNKNOWN

```diag
grid | 不该硬判 PASS / FAIL 的情况
Missing evidence | 关键 log、state 或截图不存在
Ambiguous contract | 两个合理解释给出不同 verdict
Unsupported state | scorer parser 不认识新 schema / app version
Verifier failure | timeout、exception、judge malformed output
```

```diag
compare | UNKNOWN 的错误处理
错误做法 | 正确做法
exception → score=0 | `verifier_error` + score=null
缺截图 → 猜 FAIL | `insufficient_evidence`
parser 不认识 → 默认 PASS | fail closed 或 abstain,按 risk contract
丢掉该 row | 保留 observation,由 W6 决定分析口径
```

安全 gate 可能选择 fail closed;capability benchmark 通常应把 measurement failure 与 Agent failure 分列。两者没有通用答案,但必须在运行前写进 score contract。

---

## 十、Lab:把 τ³ airline `id=3` 变成 verifier regression suite

不要先换成 LLM judge。先为现有 deterministic verifier 建立可证明的 failure envelope。

### Step 1:固定现有四条 trajectories

```text
gold    → expected PASS
silent  → expected FAIL
cheat   → expected FAIL
refuse  → expected FAIL
```

### Step 2:再添加六条 controls

| case | mutation | expected |
|---|---|---:|
| `semantic-collision` | negation / quoted-user 文本含 4,但没有有效 claim | FAIL |
| `wrong-entity` | 另一位旅客确实可带 4 件 | FAIL |
| `paraphrase` | “four checked suitcases are included” | PASS |
| `format-noise` | 大小写、标点、换行变化 | PASS |
| `forbidden-side-effect` | claim 正确,但发生未授权操作 | FAIL |
| `missing-log` | communication 正确但查询 evidence 缺失 | UNKNOWN |

```diag
flow | regression gate
10 个 labeled controls
运行 candidate verifier
生成 confusion matrix
检查每个 criterion 的 mutation kill rate
所有 mandatory controls 通过才替换官方 scorer
```

### Step 3:输出可诊断 score

```json
{
  "overall": "FAIL",
  "criteria": {
    "identity_evidence": "FAIL",
    "itinerary_evidence": "FAIL",
    "communication": "PASS"
  },
  "reason_codes": ["UNSUPPORTED_CLAIM"],
  "evidence_refs": ["assistant:1"],
  "scorer_version": "airline-baggage-v2"
}
```

这里 communication 可以 PASS,overall 仍 FAIL。Breakdown 告诉我们 Agent 说出了正确数字,但没有证明它来自正确用户与行程。

### Step 4:写一个 verifier card

```text
Product event:
Allowed evidence:
Known blind spots:
Control suite commit:
Oracle pass rate:
Null rejection rate:
Alternate-path acceptance:
FPR / FNR on adjudicated audit set:
Unsupported / UNKNOWN policy:
```

仓库中的 `labs/scorer-audit/` 已实现这 10 条 controls、baseline substring scorer、contract-aware candidate scorer、confusion matrix 与 verifier card。运行:

```bash
python3 labs/scorer-audit/run.py
```

---

## 十一、验收

```text
[ ] 能解释 deterministic 为什么不等于 valid
[ ] 能从 product event 推出 predicate,而不是从方便读取的字段反推目标
[ ] 能识别 substring collision、no-op state equality 与 full-hash brittleness
[ ] 不把 gold trajectory 当唯一合法路径
[ ] Unit tests 同时覆盖 required behavior、regressions 与 shortcuts
[ ] Oracle PASS 且 Null FAIL
[ ] 有 minimal corruption、irrelevant mutation 与 alternate-valid-path controls
[ ] 每个 atomic criterion 都能指向 evidence
[ ] scorer exception / missing evidence 不静默变成 Agent FAIL
[ ] overall score 之外保留 criterion breakdown 与 reason codes
[ ] 所有外部 audit 数字都注明抽样范围,不越界外推
```

> ## 本课结论
> **好的 deterministic verifier 不是“更复杂的 if statement”,而是一组经反例验证的、与产品事件对齐的 executable claims。**
>
> 它必须同时回答两个问题:有没有失败却能变绿的最短路径?有没有真正成功却会被拒绝的另一条合法路径?

---

## References

1. OpenAI. [Why SWE-bench Verified no longer measures frontier coding capabilities](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/), 2026. Narrow / wide tests 与人工复核方法;污染部分留给 W7。
2. OpenAI. [Separating signal from noise in coding evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/), 2026. SWE-Bench Pro QA pipeline:自动 triage + agent-assisted audit + 五名工程师独立 review。
3. [Benchmarking the Benchmarks: A Validity Audit of Tool-Calling Evaluation](https://arxiv.org/abs/2607.02577), 2026. BFCL、τ²-bench 与 LiveMCPBench 的 scorer disagreement 实证。
4. Corby Rosset et al. [The Art of Building Verifiers for Computer Use Agents](https://arxiv.org/abs/2604.06240), 2026. Rubric、process/outcome、failure attribution 与 evidence coverage。
5. Jimenez et al. [SWE-bench: Can Language Models Resolve Real-World GitHub Issues?](https://arxiv.org/abs/2310.06770), 2023. FAIL_TO_PASS / PASS_TO_PASS executable verifier 的原始框架。
6. Course executable case: [`labs/tau3-verifier/`](../labs/tau3-verifier/) 与 [`week01/lesson04-tau3-bench.md`](../week01/lesson04-tau3-bench.md)。
