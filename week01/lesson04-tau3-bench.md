# 第 4 课:τ³-bench

## 四种 verifier,由 `reward_basis` 选出再相乘;User LLM 在尺子里

**Week 1 Day 4** · 源码课 · 90 分钟 = 核心 60 + 进阶 30

> ### 本课唯一命题
> # τ³ 定义了四种 verifier;每道任务由 `reward_basis` 选择其中一部分,并将选中的分量相乘
>
> Day 3 的 SWE-bench:一个 patch → 跑单元测试 → `bool`。
> τ³:一段多轮对话 → `reward_basis` 选出 verifier → 相乘 → `[0, 1]`。

```diag
compare | 尺子怎么判
SWE-bench | τ³
patch → 单元测试 → bool | 对话 → reward_basis 选出 → 相乘 → [0,1]
尺子里没有 LLM | User LLM 在尺子里
```

```diag
nest | 一次 rollout 三个角色
τ³ Trial
  Agent · 被测 SUT
  User LLM · 测量仪器,会进分数
  Environment · 可变状态 + verifier
```

```
核心 60  名字 · 阶梯 · 三方 · 测了谁 · 四种 verifier + reward_basis · 子串 · lab
进阶 30  终止闸 · 整库 hash · pass^k
W3 再处理  方差 · 置信区间 · User LLM confounding · judge reliability
```

> 📎 源码:`../code/tau2-bench/`(目录名沿用旧的 tau2,内容是 **τ³-bench v1.0.1**,`c339866`)
> 💻 lab:`../labs/tau3-verifier/`

---

## 零、名字先说清楚:³ 不代表三方

```
τ-bench (2024)   Agent 与模拟用户对话并使用工具
τ²-bench (2025)  dual-control,Agent 和用户都能操作环境
                 (RELEASE_NOTES.md: *"realistic, dual-control environments"*)
τ³-bench (2026)  Knowledge · Voice · 75+ 任务修订
                 (README *"What's New in τ³-bench"*)
```

README 原文:*"How do you say τ³-bench? We just say **tau three**"*.
**³ 是第三代,不是参与方数量。** 仓库仍叫 `tau2-bench`,是历史目录名。

---

## 一、复杂度阶梯上,τ³ 比 SWE-bench 多了什么

```
SWE-bench      repo state                              一个仓库,判它的测试过不过
               尺子里没有 LLM                          单元测试 + 行首 regex
τ³-bench       application state                       一个业务数据库,判它最后长什么样
             + user state                              用户自己的一套状态,他会动手改它
             + conversational trajectory                agent 说了什么,也算分
             + 尺子两边都有 LLM                         用户模拟器住在尺子里;retail 再加 LLM judge
```

多出来的前三样,每一样都逼出一种新的 verifier。但不是每道题四个全用 ——
**先由 `reward_basis` 选择,再把选中的相乘**(§四)。

最后那一行是另一类差别:每个 agent benchmark 的被测对象都是 LLM;
τ³ 特别的地方是 **尺子里也有**。

---

## 二、一次 rollout 三个角色,其中两个通常由 LLM 驱动

`orchestrator.py:90-96` 并列三个角色:

```
agent         通常是被测 LLM
user          也是 LLM simulator(默认 gpt-4.1,config.py:17-18)
environment   工具与数据库,Environment 类不含 LLM
```

不是「其中一方是 LLM」。三个角色里,**两个通常由 LLM 驱动**。

和 SWE-bench 的差别不在「有没有 LLM」,在 **LLM 在尺子的哪一边**。
SWE-bench harness 零模型调用。当 Docker image、patch、test patch 和 runner 固定时,
它被设计成**近似确定**的(仍可能有 flaky test、timeout、硬件差异)。
τ³ 把另一个在线 LLM 放进 rollout loop,随机性是系统设计的一部分。

`Environment` 类本身是确定的(时钟冻死,§八)。
**不要说「随机性 100% 来自用户模拟器」。**
在固定 Agent trajectory、关闭 NL judge、文本模式、业务库冻结的条件下,
环境**新增**的主要随机源是 User LLM;
完整 evaluation 还可能来自 Agent LLM 的采样、`NLAssertionsEvaluator` 的 judge、
timeout / provider / voice pipeline。temperature=0 也不保证远程模型 bitwise deterministic。
pass^k 在 §九。

τ³ 自己知道尺子会犯错:有个 judge 抓用户模拟器出错
(`review_llm_judge_user_only.py`),但默认不改分。模拟器幻觉了,分仍记在 agent 头上。

SWE-bench 判的是真仓库、真测试。τ³ 判的是「一个读剧本的 gpt-4.1 满不满意」
(`user_scenario` 给模拟器看,不给 agent 看)。离真顾客有多远 → **W9**。

---

## 三、被测对象是 Agent;User LLM 是测量仪器

```
被测对象    Agent LLM
测量环境    User LLM + scenario + tools + databases + verifier

Score = P(success | agent, user model, scenario, environment, verifier, run config)
```

| 能力 | τ³ 是否直接测量 | 实际可观测信号 |
|---|---|---|
| 理解用户需求 | 否,间接 | 最终任务是否成功 |
| 遵循企业政策 | 部分 | DB、NL assertion、拒绝行为 |
| 正确调用工具 | 取决于 `reward_basis` | `ACTION` 或最终 DB |
| 与用户协作 | 间接 | user state、最终 outcome |
| 正确沟通结果 | 部分 | `COMMUNICATE`、NL assertion |
| 可靠性 | 多次 rollout 后 | `pass^k` |

> **User LLM 不是 leaderboard 想评价的对象,但它的能力会进入分数。
> 它既是环境,也是一个可能失准的测量仪器。**

更硬的证据:代码只排除 `infrastructure_error`(`agent_metrics.py:138-145`);
`user_error` 在 evaluator 里直接 0 分(`evaluator.py:119-129`),且**算进模型成绩**(§七)。
模拟用户失败可以记在 Agent 名下。这是 construct validity 的现场。

---

## 四、四种 verifier;每道 task 由 `reward_basis` 选出再相乘

```diag
pipe | 先选,再乘
四种 verifier → reward_basis 选出子集 → 相乘 → [0, 1]
```

```
先由 reward_basis 选择适用的 verifier
                 ↓
再把选中的 reward 相乘
```

四个(`evaluator/AGENTS.md`):

| Evaluator | 查什么 | RewardType |
|---|---|---|
| `EnvironmentEvaluator` | 终态 DB hash(agent 库 + 用户库各一份) | `DB` / `ENV_ASSERTION` |
| `ActionEvaluator` | 工具调用的名字和参数 | `ACTION` |
| `CommunicateEvaluator` | 指定信息有没有**说出来** | `COMMUNICATE` |
| `NLAssertionsEvaluator` | LLM judge 判自然语言断言 | `NL_ASSERTION` |

对应 §一 多出来的三层:应用状态、用户状态、对话。过程另用 ActionEvaluator。

**相乘,不是平均。** `evaluator.py:222-256` 只对 `task_reward_basis` **选中的**分量 `*=`。
规则 3:*"A 0 in any component zeroes the total."*
订单改对了但没告诉用户 → 没完成。说对了但库没变 → 没完成。平均给 0.5,相乘给 0。**0.5 会骗你。**
代价:总分 0 看不出差在哪,所以必须留 `reward_breakdown`。

尺子写在**每一道 task** 的 `evaluation_criteria.reward_basis` 上,不是 domain 配置。
按这个字段把四个 `tasks.json` 数一遍,domain 只是聚类:

| domain | tasks | reward_basis(按 task 计) | 判分靠 |
|---|---:|---|---|
| **airline** | 50 | 50/50 `DB + COMMUNICATE` | hash + **子串** |
| **retail** | 114 | **112/114** `DB + NL_ASSERTION` | hash + **LLM judge** |
| **telecom** | 114 | `ENV_ASSERTION`(2253 条) + `ACTION`(32 条) | 环境断言 |
| **banking_knowledge** | 97 | **88 道 `DB` / 9 道 `ACTION`** | 两种尺子 |

retail 不是 114/114,banking 直接劈成两把。**同一 domain 里,task 的尺子都可以不一样。**
airline 的分和 retail 的分也不是同一种量(子串 vs `gpt-4.1`)。τ³ 总分还是把它们加在一起。

NL assertions 标着 `# WIP`,但 `evaluator.py:215-216` 只要这道 task 的 `reward_basis` 含 `NL_ASSERTION` 就跑;
runner 默认 `ALL`。retail 112 道带着 judge 方差,airline 不带。
反方向:58 道写了 `nl_assertions` 却不在 `reward_basis` 里 —— 写了不算数。
airline `id=0` 那句 *Agent should refuse to proceed with the cancellation* 读起来像判分标准,一分不占。

看 benchmark 的固定动作:不要只看它**定义**了哪些 criteria,要看 `reward_basis` 里**实际用了**哪些。

---

## 五、⭐ `CommunicateEvaluator` 是子串匹配

`evaluator_communicate.py:64-71`:

```python
for message in full_trajectory:
    if not isinstance(message, AssistantMessage):
        continue
    if not message.has_text_content():
        continue
    if info_str.lower() in message.content.lower().replace(",", ""):
        found = True
        break
```

后面还跟着一行原文注释:

```python
    ):  # TODO: This could be improved!
```

**判据就是「这个字符串有没有在 agent 的任何一句话里出现过」。**

现在看 airline `id=3` 这道题。用户以为自己是 Gold 会员,其实是 Silver,要问能带几件行李:

```json
"communicate_info": ["4"],
"reward_basis": ["DB", "COMMUNICATE"]
```

**`communicate_info` 就是一个字符 `4`。** 于是 COMMUNICATE 这一分的实际判据是:

> agent 说过的任何一句话里,出现过字符 `4`。

`"your flight is AA-1234"` —— 过。
`"that'll be $412"` —— 过。
`"I'll transfer you at 4 PM"` —— 过。

**agent 可以完全没搞懂会员等级、没算行李额度,只要嘴里蹦出过一个 4。**

### 这不是孤例

把四个 domain 的 `communicate_info` 全量拉出来:

```
共 73 条
其中长度 ≤ 3 的:8 条  ——  "4"  "IL"  "10"  "60"
```

最短的一批长这样:

```
4 · IL · 10 · 60 · 327 · 1786 · 9.89 · 1286 · 1000 · 64GB · full · 5244 …
```

`"IL"` 不是随手挑的。它来自 retail `id=43` —— 用户要求 agent 把发货地址念回来:

```json
"communicate_info": ["840887978435", "943 Maple Drive", "Suite 356",
                     "Chicago", "IL", "60621", "64GB"]
```

`IL` 是州名缩写,而判据是 `"il" in message.content.lower()`。于是 agent 只要说过
`available`、`while`、`email`、`until` 里的**任何一个词**,这一项就算念对了州。

> ### 🔁 这就是 Day 6 那道题的真实版本
> hello-bench 的 `sum-numbers` 里,弱 verifier 只判 `out.strip() == "42"`,
> `print(42)` 就能过。当时的结论是:
>
> > **你以为在测「会不会读文件求和」,实际在测「知不知道答案是 42」。**
>
> 这里一模一样,只不过发生在一个被广泛引用的 benchmark 上:
>
> > **你以为在测「算没算对行李额度」,实际在测「说没说过字符 4」。**
>
> 每写一个 verifier,都要先问那句话:**有没有一个不解决问题、却能让它变绿的最短程序?**

> 💻 **这个洞有多大,§六 有实测**:在满足正常 termination 的手工 `Simulation` 上,
> 官方 evaluator 对只说 `"your flight is AA-1234"` 的 cheat 返回 `reward=1.0`。

**留一个洞给 W3**:一个真的失败了的 agent,它的回复里会不会**碰巧**出现 `4`?
这决定了这个洞到底有多严重。回答它需要几十次 rollout 再做统计 —— 那是 W3 的事。

---

## 六、Hands-on:四条手写轨迹喂进真实的 evaluator

无需 API key:能离线跑的只有 evaluator(`DummyUser` / `LLMGTAgent` 都走不通)。

这不是端到端跑官方 benchmark。是**手工构造 trajectory,再调用官方 evaluator**。

```bash
(cd ../code/tau2-bench && uv sync)
uv run --project ../code/tau2-bench python ../labs/tau3-verifier/run.py
```

四条轨迹,全部针对 airline `id=3`(`communicate_info: ["4"]`):

```
gold     两次 gold GET + 说「You can bring 4 suitcases」
silent   同样两次 GET,但从不说那个数字
cheat    什么都不查、什么都不解,只说了一句 "your flight is AA-1234"
refuse   空的,agent 缺席
```

### 真实输出

```
traj   COMMUNICATE      ACTION          DB     DB*COMM
------------------------------------------------------
gold           1.0         1.0         1.0         1.0
silent         0.0         1.0         1.0         0.0
cheat          1.0         0.0         1.0         1.0     ← ⚠️
refuse         0.0         0.0         1.0         0.0

  cheat  '4' met=True: Information '4' communicated in the message: 'your flight is AA-1234'

sanity: cheat utterance AA-1234 -> AA-1235   COMMUNICATE 1.0 -> 0.0
```

### 三件比 §五 更狠的事

**① 在满足正常 termination 的手工 `Simulation` 中,官方 evaluator 为 cheat 返回 `reward=1.0`。**
airline 这道题的 `reward_basis` 是 `["DB", "COMMUNICATE"]`,所以 `1.0 × 1.0 = 1.0`。
这是 evaluator 层的洞,不是已经跑完一遍端到端 agent 之后的 leaderboard 分。

**② `refuse` 的 DB 也是 1.0。**
这条 task 的 gold `actions` 全是只读 GET,数据库从头到尾不变 —— 所以「终态 hash 等于 gold」
对**任何**轨迹都成立,包括空轨迹。

```
DB 这个因子在只读任务上是恒等于 1 的空操作
⟹ 官方 reward = 1.0 × COMMUNICATE = COMMUNICATE
⟹ 这道题的判分,塌缩成了「assistant 文本里有没有字符 4」
```

**③ `ActionEvaluator` 抓得住 `cheat`,但 airline 这道题的 `reward_basis` 不用它。**

```
cheat 的 ACTION = 0.0     ← 一次工具都没调
这道题 reward_basis      = ["DB", "COMMUNICATE"]      ← 没有 ACTION
```

**benchmark 手里有一把能识破这个作弊的尺子,而这道 task 选择了不用。**
这就是 §四 的代价 —— `reward_basis` 写在 task 上,**它直接决定哪些作弊会被抓到。**

### 拨弄它

把 `trajectories.py` 里 `cheat` 那句的 `AA-1234` 改成 `AA-1235`,重跑:
COMMUNICATE 从 **1.0 掉到 0.0**。同一个 agent、同一份工作量(零),**差的只有一个字符。**

---

## 七、进阶 · 没正常结束就是 0;`user_error` 记在 Agent 头上

在任何 evaluator 跑之前(`evaluator.py:119-129`):不是 `AGENT_STOP` / `USER_STOP` 就直接 `reward=0`。
`TerminationReason` 10 种(`simulation.py:1254-1264`),只有这 2 种算正常收尾。

`infrastructure_error` 拿 0 分,但**不算进模型成绩**(`agent_metrics.py:138-145`)。
Day 3 的 `empty patch` 是混在总分里的。这是 **W6** 的正面教材。

同一道闸,`user_error` **不会**被剔除。模拟用户挂了 → 0 分 → 记在 Agent 名下(§三)。

---

## 八、进阶 · 整库 hash,以及它反过来对 environment 提的要求

判的是「世界变成什么样」,不是「你走了哪条路」(`evaluator_env.py:118-123`)。
gold 环境是把任务里的参考 actions 重放一遍。`AGENTS.md` 规则 6:
*"`evaluation_criteria.actions` is **one** reference trajectory… Other agent trajectories producing an equivalent end state also pass."*

但 `get_db_hash` 是**整个库**(`toolkit.py:242-244`:`get_dict_hash(self.db.model_dump())`)。
跟 agent 无关却会变的字段(时钟、随机 ID、自增计数器)会毁掉判分。
τ³ 的解法是冻死它们(`domains/airline/tools.py:98-102`:支付 ID 写死,时间是常量 `"2024-05-15T15:00:00"`)。

> **verifier 的选择,反过来约束了 environment 的设计。**
> 选了整库 hash ⟹ 不许有路径依赖字段 ⟹ 时钟必须冻结。
> 这是设计顺序:先想清楚怎么判,才能决定环境怎么造。Day 6 会立刻撞上。

---

## 九、进阶 · pass^k 不是 pass@k

尺子里住着 User LLM,再加 Agent 采样和(部分 task 的)NL judge,同一道题跑一次不够。
τ-bench 提出了 pass^k(`agent_metrics.py:113-127`,论文 https://arxiv.org/pdf/2406.12045):

```
pass@k    跑 k 次,至少成功一次      —— 乐观,问「能力上限在哪」
pass^k    随机抽 k 次,全部成功       —— 悲观,问「能不能交给它去做」
```

**k 越大,pass@k 往上走,pass^k 往下掉。** 客服场景要后者。

源码用的估计是 `C(success, k) / C(trials, k)`。它和 plug-in 概率 `p^k` / `1-(1-p)^k` **不是同一个算法**,
不能把两种算法的数字放在一起比。estimator 的差别、要跑多少次、置信区间 —— **全部留给 W3**。

---

## 十、本课自检

```
[ ] 0. 能说出 ³ 为什么不代表三方,以及仓库为什么还叫 tau2-bench
[ ] 1. 能说出一次 rollout 的三个角色,以及其中哪两个通常由 LLM 驱动
[ ] 2. 能说清 SWE-bench 和 τ³ 的 LLM 分别在尺子的哪一边,以及随机性不能写成「100% 来自用户模拟器」
[ ] 3. 能画出 Score 的条件概率,并说出「User LLM 既是环境也是测量仪器」
[ ] 4. 能列出四个 evaluator,并画出「reward_basis 选择 → 再相乘」
[ ] 5. 能举出同一 domain 里两把尺子的例子
[ ] 6. 能说出 CommunicateEvaluator 的实际判据,并举出一个能骗过它的回复
[ ] 7. 能说出 lab 里 cheat 的 1.0 是手工 Simulation + 官方 evaluator,不是端到端 leaderboard
[ ] 8. 能说出 10 种 TerminationReason 里只有哪 2 种算正常收尾
[ ] 9. 能对比 infrastructure_error(剔除)和 user_error(记在 Agent 头上)
[ ] 10. 能解释「整库 hash」为什么逼得 airline 把时钟冻成常量
[ ] 11. 能说清 pass@k 和 pass^k 的概念差,并知道算法细节留给 W3
```

---

## 本课一句话总结

> **τ³ 想测 Agent 能否完成真实任务,但实际分数是 Agent、User Simulator、业务环境和 verifier 的联合产物;
> 阅读源码的任务,就是找出其中哪些变量真正进入了分数。**

---

**上一课(Day 3)**:[SWE-bench](lesson03-swe-bench.md)。
**下一课(Day 5)**:OSWorld · WebArena —— 把**整台电脑**当 environment,以及 verifier
从「查数据库」变成「查屏幕和文件系统」之后会发生什么。
