# 第 4 课:τ³-bench

## 当对面坐着一个 LLM 扮演的用户,verifier 就得拆成四个

**Week 1 Day 4** · 源码课 · 建议 90 分钟

> ### 本课唯一命题
> # 一个 benchmark 里可以有四种 verifier,它们**相乘**
> # —— 而且每个 domain 用的还**不一样**
>
> Day 3 的 SWE-bench:一个 patch → 跑单元测试 → `bool`。
> τ³:一段多轮对话 → 四种 verifier 相乘 → `[0, 1]`。

> 📎 源码:`../code/tau2-bench/`(目录名沿用旧的 tau2,内容是 **τ³-bench v1.0.1**,`c339866`)
> 💻 lab:`../labs/tau3-verifier/`

---

## 零、复杂度阶梯上,τ³ 比 SWE-bench 多了什么

```
SWE-bench      repo state                              一个仓库,判它的测试过不过
τ³-bench       application state                       一个业务数据库,判它最后长什么样
             + user state                              用户自己的一套状态(手机、设备),他会动手改它
             + conversational trajectory                agent 说了什么,也算分
```

多出来的这三样,每一样都逼出一种新的 verifier。**这就是为什么 τ³ 有四个 evaluator 而 SWE-bench 只有一个。**

---

## 一、τ³ 的世界里有**三方**,其中一方是 LLM —— 与 SWE-bench 最根本的区别

SWE-bench 的 environment 是一个 Docker 容器:确定的文件系统、确定的依赖、`git apply` 之后跑 pytest。
**同样的输入永远给出同样的输出。**

τ³ 不是。但要说清它哪里不一样,得先把「environment」这个词的两个意思分开 ——
**这是本节最容易搞错、也最要紧的一点。**

### τ³ 自己的代码分了三方

`orchestrator/orchestrator.py:90-96`:

```python
def __init__(
    self,
    domain: str,
    agent: BaseAgentT,          # ← LLM
    user: BaseUserT,            # ← LLM
    environment: Environment,   # ← 零 LLM
    task: Task,
    ...
```

三个**并列**的参与方。而且注意:`Environment` 类里**一个模型调用都没有** ——
grep 整个 `environment/` 目录,和 LLM 沾边的只有 `tool.py` 里两句 docstring
(`"can be called by LLMs"`)和 `openai_schema`。它只管工具执行和数据库。

加上时钟被冻成常量(§五),**τ³ 的 `Environment` 类是完全确定性的。**

### 但 RL 意义上的 environment 不是这么划的

```
τ³ 代码里的 Environment    工具 + 数据库                        确定
RL 意义的 environment      agent 之外、它不能控制的一切          随机
                           ↑ 用户模拟器在这一边
```

从 agent 的视角看,那个会追问、会施压、会被说服的「用户」,和数据库一样是它无法控制、
只能观测和影响的外部世界。**在 MDP 的意义上,用户模拟器就是环境的一部分。**

而那个用户是一个 LLM:

```python
# user/user_simulator.py
class UserSimulator(...):
    def generate_next_message(self, message, state):
        ...
        generate(model=self.llm, ...)          # ← 一次真实的 LLM 调用
```
```python
# config.py:17-18
DEFAULT_LLM_AGENT = "gpt-4.1-2025-04-14"
DEFAULT_LLM_USER  = "gpt-4.1-2025-04-14"      # ← 用户模拟器
```

> ### ⚠️ 为什么这个区分不是文字游戏
> 它直接决定你对「τ³ 可不可复现」的判断:
> ```
> 只看 Environment 类   → 确定的 → 结论:跑两次结果一样   ❌
> 算上用户模拟器         → 随机的 → 结论:必须跑多次       ✅
> ```
> **τ³ 的随机性 100% 来自用户模拟器。** 数据库那边被刻意做成确定的(冻结时钟、写死 ID),
> 正是为了让随机源只剩这一个。pass^k(§六)就是为它准备的。

### 用户不只是「说话」,他还会动手

这一点最容易漏。用户模拟器**有自己的一套工具、自己的一个数据库**
(`environment/environment.py:44,59`):

```python
user_tools: Optional[ToolKitBase] = None
self.user_tools = user_tools
```

telecom domain 里,用户能干这些(`domains/telecom/user_tools.py`):

```
toggle_airplane_mode · turn_airplane_mode_on / off
run_speed_test       · check_network_status
set_network_mode_preference · check_status_bar
```

**这是一个会照着 agent 的指示去动手机的用户。** agent 说「请开一下飞行模式再关掉」,
用户模拟器真的会调那个工具,手机状态真的会变。

所以判分时是**两个数据库分别 hash**(`evaluator_env.py:118-123`):

```python
agent_db_hash            = gold_environment.get_db_hash()        # 运营商侧
user_db_hash             = gold_environment.get_user_db_hash()   # 用户手机侧
predicted_agent_db_hash  = predicted_environment.get_db_hash()
predicted_user_db_hash   = predicted_environment.get_user_db_hash()
agent_db_match = agent_db_hash == predicted_agent_db_hash
user_db_match  = user_db_hash  == predicted_user_db_hash
```

> **「user state」不是比喻,是一个真的会被 hash 的数据库。**
> 这就是 §零 里 τ³ 比 SWE-bench 多出来的那一层的实体形态。

### 用户模拟器照着什么演

看一条真任务(`data/tau2/domains/airline/tasks.json`,`id=0`):

```json
"user_scenario": {
  "instructions": {
    "known_info":  "You are Emma Kim. Your user id is emma_kim_9957.",
    "reason_for_call": "You want to cancel reservation EHGLP3.
                        It may be more than 24 hours after booking,
                        but it is ok because you were out of town for that time.",
    "task_instructions": "If Agent tells you that cancellation is not possible,
                          mention that you were told that you didn't need to get insurance…
                          You don't want to cancel if you don't get a refund."
  }
}
```

这段话不是给 agent 看的,是**给用户模拟器看的剧本**。它会照着这个剧本施压。

### 后果:没有离线 rollout 这条路

想不花钱跑一遍?没有。已经确认过两条看起来可行的路都是死的:

| 看起来可以 | 实际 |
|---|---|
| `DummyUser`(`user_simulator.py:269`) | 只用于 solo 模式,`generate_next_message` 直接抛 `NotImplementedError` |
| `LLMGTAgent`(`llm_agent.py:166`) | 名字是 GroundTruth,但它是**被告知标准答案的 LLM**,照样要 key |

**能离线跑的只有 evaluator。** 这也正是本课 lab 的形状。

---

## 二、四个 evaluator 各查什么,以及为什么必须是「相乘」

`src/tau2/evaluator/` 下四个,`evaluator/AGENTS.md` 自带对照表:

| Evaluator | 查什么 | RewardType |
|---|---|---|
| `EnvironmentEvaluator` | 重放 gold actions 得到 DB hash,和 agent 跑完的 DB hash 比 | `DB` / `ENV_ASSERTION` |
| `ActionEvaluator` | 工具调用的名字和参数对不对 | `ACTION` |
| `CommunicateEvaluator` | agent 有没有把指定信息**说出来** | `COMMUNICATE` |
| `NLAssertionsEvaluator` | **LLM judge** 判自然语言断言 | `NL_ASSERTION` |

对应 §零 那三样新东西:

```
application state      →  EnvironmentEvaluator 的 agent_db_hash
user state             →  EnvironmentEvaluator 的 user_db_hash      ← 同一个 evaluator,第二个 hash
conversational traj.   →  CommunicateEvaluator + NLAssertionsEvaluator
(过程本身)             →  ActionEvaluator
```

### 相乘,不是加权平均

`evaluator.py:222-256`:

```python
## Combine all the rewards.
reward = 1.0
...
if task_reward_basis & env_bases:        reward *= env_reward_info.reward
if task_reward_basis & action_bases:     reward *= action_reward_info.reward
if task_reward_basis & nl_bases:         reward *= nl_reward_info.reward
if task_reward_basis & comm_bases:       reward *= communicate_reward_info.reward
```

`AGENTS.md` 规则 3 说得很直白:

> *"Reward is multiplicative. **A 0 in any component zeroes the total.**"*

**为什么不能是平均?** 因为这些分量之间不是「哪个更重要」的关系,是**合取**关系:

```
把订单改对了,但没告诉用户改成什么       → 任务没完成
说对了话,但数据库里什么都没变            → 任务没完成
```

平均会给出 0.5,相乘给出 0。**0.5 会骗你,0 不会。**

> ⚠️ 但相乘有个代价:**你再也说不出「差在哪」了。** 最终分数 0,可能是 DB 错、也可能是话没说到。
> 所以 `RewardInfo` 里必须同时留一份 `reward_breakdown`(`evaluator.py:243`)。
> 这和 Day 3 「只报 resolved% 会把三类失败压成一个数字」是同一件事。

### 还有一道更早的闸:没正常结束就是 0

`evaluator.py:119-129`,在任何 evaluator 跑之前:

```python
if simulation.termination_reason not in {
    TerminationReason.AGENT_STOP,
    TerminationReason.USER_STOP,
}:
    return RewardInfo(reward=0.0, ...)
```

`TerminationReason` 一共 **10 种**(`data_model/simulation.py:1254-1264`),只有 2 种算正常收尾:

```
✅ user_stop  agent_stop
❌ max_steps · timeout · too_many_errors · agent_error · user_error
   infrastructure_error · context_window_exceeded · unexpected_error
```

### ⭐ 但 τ³ 在这里比 SWE-bench 更讲究

`infrastructure_error` 拿 0 分很合理 —— 可它不该算进模型的成绩。τ³ 在算指标时把它**剔掉了**:

```python
# metrics/agent_metrics.py:138-145
infra_count = (df.termination_reason == TerminationReason.INFRASTRUCTURE_ERROR).sum()
if infra_count > 0:
    logger.warning(f"Excluding {infra_count} infrastructure error simulation(s) from metrics.")
    df = df[df.termination_reason != TerminationReason.INFRASTRUCTURE_ERROR]
```

> 对照 Day 3:SWE-bench 的 `empty patch`(通常是 agent runtime 挂了)是**混在总分里**的。
> τ³ 明确地把「基础设施坏了」和「模型不行」分开。
> **这是 W6 Failure Taxonomy 的正面教材**,而 SWE-bench 那边是反面教材。

---

## 三、⭐ 每个 domain 一把不同的尺子

这是本课最反直觉的地方。把四个 domain 的 `tasks.json` 全量数一遍
(`data/tau2/domains/*/tasks.json` 的 `evaluation_criteria.reward_basis`):

| domain | base tasks | reward_basis | 也就是说,判分靠 |
|---|---:|---|---|
| **airline** | 50 | `DB + COMMUNICATE`(50/50) | 数据库 hash + **子串匹配** |
| **retail** | 114 | `DB + NL_ASSERTION`(112/114) | 数据库 hash + **LLM judge** |
| **telecom** | 114 | `ENV_ASSERTION`(2253)+ `ACTION`(32) | 在环境里跑断言函数 |
| **banking_knowledge** | 97 | `DB`(88)/ `ACTION`(9) | 数据库 hash / 工具调用匹配 |

> ### 读懂这张表
> **airline 的分数和 retail 的分数,不是同一种量。**
> 一个是确定性字符串匹配得出的,一个是 `gpt-4.1` 判出来的。
> 拿它们求平均、放进同一个 leaderboard 列,等于**拿卡尺量出来的数和拿手掂出来的数相加**。

τ³ 自己在总分里就是这么合的。这不是它的 bug —— 是所有 multi-domain benchmark 的固有困难。
**但你必须知道这件事,才能读懂那个总分。**

### 顺带:112 个 task 的分数里有 LLM judge

`evaluator/AGENTS.md` 和 enum 注释都把 NL assertions 标成 `# WIP`,容易让人以为它不生效。
但代码是这么写的(`evaluator.py:215-216`):

```python
task_needs_nl = RewardType.NL_ASSERTION in task.evaluation_criteria.reward_basis
if evaluation_type == EvaluationType.ALL_WITH_NL_ASSERTIONS or task_needs_nl:
```

runner 默认就是 `EvaluationType.ALL`(`run.py:85`、`runner/batch.py:349`),而 retail 有
**112 个 task 把 `NL_ASSERTION` 写进了 `reward_basis`**。判官是:

```python
# config.py:24-26
DEFAULT_LLM_NL_ASSERTIONS = "gpt-4.1-2025-04-14"
DEFAULT_LLM_NL_ASSERTIONS_TEMPERATURE = 0.0
```

⟹ **retail 的分数带着 LLM judge 的方差,airline 不带。**

反方向也有一个坑:**58 个 task 写了 `nl_assertions` 但没放进 `reward_basis`** —— 写了不算数,
纯文档。比如 airline `id=0` 里那句 `"Agent should refuse to proceed with the cancellation."`
读起来像判分标准,其实一分不占。

> 🔍 **看 benchmark 的固定动作**:不要只看它**定义**了哪些 criteria,要看 `reward_basis`
> 里**实际用了**哪些。写了不用的字段,在任何 benchmark 里都比你想的多。

---

## 四、⭐ `CommunicateEvaluator` 是子串匹配

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

> 💻 **这个洞有多大,§七 有实测**:一个完全没干活、只说了 `"your flight is AA-1234"`
> 的 agent,在这道题上拿到的**官方 reward 是 1.0** —— 不是「过了一项」,是满分通过。

**留一个洞给 W3**:一个真的失败了的 agent,它的回复里会不会**碰巧**出现 `4`?
这决定了这个洞到底有多严重。回答它需要几十次 rollout 再做统计 —— 那是 W3 的事。

---

## 五、`EnvironmentEvaluator`:整库 hash,以及它反过来对 environment 提的要求

### 判的是「世界变成什么样」,不是「你走了哪条路」

`evaluator_env.py:118-123`:

```python
agent_db_hash           = gold_environment.get_db_hash()
predicted_agent_db_hash = predicted_environment.get_db_hash()
agent_db_match = agent_db_hash == predicted_agent_db_hash
```

gold 环境是**把任务里的参考 actions 重放一遍**得到的。`AGENTS.md` 规则 6:

> *"`evaluation_criteria.actions` is **one** reference trajectory, not a per-action requirement…
> Other agent trajectories producing an equivalent end state also pass."*

对照 Day 3:SWE-bench 判「测试过不过」,τ³ 判「数据库长什么样」。**换了一类 verifier。**

### ⭐ 但「整库 hash」是一个很强的要求

`toolkit.py:242-244`:

```python
def get_db_hash(self) -> str:
    """Get the hash of the database."""
    return get_dict_hash(self.db.model_dump())      # ← 整个数据库 dump 进哈希
```

**整个库。** 那么库里任何一个「跟 agent 干得好不好无关、但会变」的字段,都会毁掉判分:
真实时钟、随机 ID、自增计数器 —— 两条正确的轨迹会算出两个不同的 hash。

τ³ 的解法是把它们全部**冻死**(`domains/airline/tools.py:98-102`):

```python
def _get_payment_ids(self):
    return [3221322, 3221323, 3221324]        # ← 支付 ID 写死

def _get_datetime(self) -> str:
    """Get the current datetime."""
    return "2024-05-15T15:00:00"              # ← 时间是个常量
```

> ### 本节的真正收获
> **verifier 的选择,反过来约束了 environment 的设计。**
>
> ```
> 选了「整库 hash」当 verifier
>       ⟹ environment 里不许有任何路径依赖的字段
>       ⟹ 时钟必须冻结、ID 必须写死
> ```
>
> 这不是实现细节,这是**设计顺序**:先想清楚怎么判,才能决定环境怎么造。
> 你在 Day 6 造自己的 benchmark 时会立刻撞上同一件事。

---

## 六、pass^k 不是 pass@k

因为 environment 里住着一个 LLM(§一),同一个 agent 跑同一道题,结果会不一样。
所以「跑一次拿到的分」意义有限。τ-bench 提出了 pass^k(`metrics/agent_metrics.py:113-127`):

```python
def pass_hat_k(num_trials: int, success_count: int, k: int) -> float:
    """... from https://arxiv.org/pdf/2406.12045"""
    return math.comb(success_count, k) / math.comb(num_trials, k)
```

```
pass@k    跑 k 次,至少成功一次的概率      —— 乐观,问「能力上限在哪」
pass^k    随机抽 k 次,全部成功的概率       —— 悲观,问「能不能交给它去做」
```

同一份数据(8 次成功 / 10 次):

```
pass@1 = 0.8      pass^1 = 0.8
pass@3 ≈ 0.99     pass^3 = C(8,3)/C(10,3) = 56/120 ≈ 0.47
```

**k 越大,pass@k 往上走,pass^k 往下掉。** 一个衡量「最好能做到什么」,
一个衡量「每次都做到的可能性」。客服场景显然要后者。

> 📌 本课到此为止。**pass^k 的统计性质、要跑多少次才够、置信区间怎么算 —— 全部留给 W3。**

---

## 七、Hands-on:四条手写轨迹喂进**真实的** evaluator

```bash
(cd ../code/tau2-bench && uv sync)                                   # 无需 API key
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

### 三件比 §四 更狠的事

**① `cheat` 拿到的不是「COMMUNICATE 那一分」,是满分。**
airline 的 `reward_basis` 是 `["DB", "COMMUNICATE"]`,所以官方 reward = `1.0 × 1.0 = 1.0`。
**一个什么都没做的 agent,在这道题上完整通过。**

**② `refuse` 的 DB 也是 1.0。**
这条 task 的 gold `actions` 全是只读 GET,数据库从头到尾不变 —— 所以「终态 hash 等于 gold」
对**任何**轨迹都成立,包括空轨迹。

```
DB 这个因子在只读任务上是恒等于 1 的空操作
⟹ 官方 reward = 1.0 × COMMUNICATE = COMMUNICATE
⟹ 这道题的判分,塌缩成了「assistant 文本里有没有字符 4」
```

**③ 最扎心的:`ActionEvaluator` 抓得住 `cheat`,但 airline 不用它。**

```
cheat 的 ACTION = 0.0     ← 它一次工具都没调,查得清清楚楚
airline reward_basis      = ["DB", "COMMUNICATE"]      ← 没有 ACTION
```

**benchmark 手里有一把能识破这个作弊的尺子,而它选择了不用。**
这就是 §三「每个 domain 一把不同的尺子」的代价 —— `reward_basis` 不是配置项,
**它直接决定哪些作弊会被抓到。**

### 拨弄它

把 `trajectories.py` 里 `cheat` 那句的 `AA-1234` 改成 `AA-1235`,重跑:
COMMUNICATE 从 **1.0 掉到 0.0**。同一个 agent、同一份工作量(零),**差的只有一个字符。**

---

## 八、本课自检

```
[ ] 1. 能说清 τ³ 代码里的 `Environment` 类和 RL 意义的 environment 差在哪,以及为什么这个差别决定了「τ³ 可不可复现」
[ ] 1b. 能说出 τ³ 的随机性来自哪里,以及 user state 为什么是一个真的数据库
[ ] 2. 能列出四个 evaluator 各查什么
[ ] 3. 能解释为什么是相乘而不是加权平均,以及相乘的代价是什么
[ ] 4. 能说出 10 种 TerminationReason 里只有哪 2 种算正常收尾
[ ] 5. 能说出 τ³ 在指标层怎么处理 infrastructure_error,以及为什么这比 SWE-bench 讲究
[ ] 6. 能说出 airline / retail / telecom 各自用哪种 verifier,以及为什么这让总分难解释
[ ] 7. 能说出 CommunicateEvaluator 的实际判据,并举出一个能骗过它的回复
[ ] 8. 能解释「整库 hash」为什么逼得 airline 把时钟冻成常量
[ ] 9. 能说清 pass@k 和 pass^k 的区别,以及客服场景为什么要后者
[ ] 10. 能说出为什么 airline id=3 的 DB 因子是个空操作,以及它对官方分数意味着什么
[ ] 11. 能说出「benchmark 手里有一把抓得住这个作弊的尺子却没用」指的是什么
```

---

## 本课一句话总结

> **SWE-bench 的 verifier 是一个函数,τ³ 的 verifier 是一个乘积 —— 而乘积里每一项,
> 都是它多实例化的那一层现实逼出来的。**
> environment 里放进一个用户,你就得判对话;放进一个数据库,你就得判状态;
> 而只要判据里出现「说了什么」,子串匹配这种洞就迟早会出现。

---

**上一课(Day 3)**:[SWE-bench](lesson03-swe-bench.md)。
**下一课(Day 5)**:OSWorld · WebArena —— 把**整台电脑**当 environment,以及 verifier
从「查数据库」变成「查屏幕和文件系统」之后会发生什么。
