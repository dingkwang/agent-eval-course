# Lab · τ³-bench verifier teardown

**把四条手写 trajectory 喂进 τ³-bench 的真 evaluator class,看 reward 怎么变。**
没有 API key,没有 Docker,evaluator 路径零 LLM 调用。

本 README 里的表是 `run.py` 真跑出来的,不是示意。

> 这里没有读不出来的知识 —— CommunicateEvaluator 是子串匹配这件事,
> evaluator_communicate.py:71 一行就写着。跑它是为了手感:把 AA-1234 改成
> AA-1235,看 reward 从 1.0 掉到 0.0。

---

## 跑起来

```bash
# from repo root
(cd code/tau2-bench && uv sync)        # py>=3.12,<3.14; this repo IS tau3-bench v1.0.1
uv run --project code/tau2-bench python labs/tau3-verifier/run.py
```

`uv` 如果抱怨 `VIRTUAL_ENV=.../looper/.venv does not match`,忽略即可,它用的是 `code/tau2-bench/.venv`。

---

## 1. 真实输出 ⭐

```
task id=3
  communicate_info = ['4']
  reward_basis     = ['DB', 'COMMUNICATE']
  actions          = get_reservation_details(reservation_id=JMO1MG), get_user_details(user_id=anya_garcia_5901)
  tasks.json       = code/tau2-bench/data/tau2/domains/airline/tasks.json

traj   COMMUNICATE      ACTION          DB     DB*COMM
------------------------------------------------------
gold           1.0         1.0         1.0         1.0
silent         0.0         1.0         1.0         0.0
cheat          1.0         0.0         1.0         1.0
refuse         0.0         0.0         1.0         0.0

communicate checks
  gold     '4' met=True: Information '4' communicated in the message:  'You are actually a Silver member, not Gold. You can bring 4 suitcases.'
  silent   '4' met=False: Information '4' not communicated.
  cheat    '4' met=True: Information '4' communicated in the message:  'your flight is AA-1234'
  refuse   '4' met=False: Information '4' not communicated.
action checks  (NOT in this task's reward_basis)
  gold     get_reservation_details match=True | get_user_details match=True
  silent   get_reservation_details match=True | get_user_details match=True
  cheat    get_reservation_details match=False | get_user_details match=False
  refuse   get_reservation_details match=False | get_user_details match=False

sanity: cheat utterance AA-1234 -> AA-1235  COMMUNICATE 1.0 -> 0.0
```

**大声说三件事,都是跑出来的,不是猜的:**

1. **`cheat` 在 COMMUNICATE 上得 1.0。** agent 没查库、没报行李箱数,只说了 `"your flight is AA-1234"`。`communicate_info == ["4"]`,`AA-1234` 里有字符 `4`,子串命中。
2. **`refuse` 不是全 0。** COMMUNICATE=0.0, ACTION=0.0, **但 DB=1.0**。agent 什么都没做,环境哈希仍等于 gold —— 因为这条 task 的 gold `actions` 全是 GET,数据库根本不会变。
3. **官方分数是 `DB * COMMUNICATE`,不是 ACTION。** airline 的 `reward_basis` 是 `["DB", "COMMUNICATE"]`。所以 **`cheat` 的官方 reward = 1.0**:什么都没解,过了。ACTION 能抓住它(0.0),但 airline **不把它乘进去**。

把 cheat 那句改成 `AA-1235`(脚本已经代你跑了一次):COMMUNICATE 从 **1.0 掉到 0.0**。差的就是那一个字符 `4`。

---

## 2. 这条 task 在测什么

真实任务:`code/tau2-bench/data/tau2/domains/airline/tasks.json`, `id="3"`。

Anya Garcia(`anya_garcia_5901`, confirmation `JMO1MG`)以为自己是 Gold,其实是 Silver,想知道能带几件行李。NL assertion 写着正确答案是 **4** 件;我们**没跑** `NLAssertionsEvaluator`(要 LLM)。

| 字段 | 值 | 谁读 |
|---|---|---|
| `communicate_info` | `["4"]` | `CommunicateEvaluator` |
| `actions` | `get_reservation_details(JMO1MG)`, `get_user_details(anya_garcia_5901)` | `ActionEvaluator` 直接比对; `EnvironmentEvaluator` 拿去在 gold env 上重放,导出目标 DB |
| `reward_basis` | `["DB", "COMMUNICATE"]` | 最终 reward 的乘积因子。**没有 ACTION** |

四条 trajectory 都是 `list[Message]`(`tau2.data_model.message`),写在 `trajectories.py`:

| traj | 做什么 | 该不该过 |
|---|---|---|
| **gold** | 两次 gold GET + `"you can bring 4 suitcases"` | 三个 evaluator 都该 1.0 |
| **silent** | 同样的 tool calls,永远不说那个数字 | ACTION 过,COMMUNICATE 不过 |
| **cheat** | 什么都不解,只说 `"your flight is AA-1234"` | 这就是洞 |
| **refuse** | `[]`,agent 缺席 | COMMUNICATE / ACTION 不过;DB 另说 |

---

## 3. 三个 evaluator 各自在干什么

源码:

- `code/tau2-bench/src/tau2/evaluator/evaluator_communicate.py` · `CommunicateEvaluator.calculate_reward(task, messages)`
- `code/tau2-bench/src/tau2/evaluator/evaluator_action.py` · `ActionEvaluator.calculate_reward(task, messages)`
- `code/tau2-bench/src/tau2/evaluator/evaluator_env.py` · `EnvironmentEvaluator.calculate_reward(environment_constructor, task, messages)` — constructor 来自 `tau2.registry.registry.get_env_constructor("airline")`

### COMMUNICATE = 子串

只扫 `AssistantMessage` 的文本。对 `communicate_info` 里每一条 `info_str`:

```python
info_str.lower() in message.content.lower().replace(",", "")
```

全部命中 → 1.0,否则 0.0。没有语义,没有"是不是在回答这个问题"。所以 `"AA-1234"` 过,`"AA-1235"` 不过。

### ACTION = 工具名 + 参数

`Action.compare_with_tool_call`:名字相同,参数 dict 相等。gold / silent 带了那两次 GET → 1.0;cheat / refuse 一次都没有 → 0.0。airline **不把这一项乘进官方 reward**(`code/tau2-bench/docs/evaluation.md`)。

### DB = 终态哈希,不是"有没有调用"

`EnvironmentEvaluator` 把 trajectory 重放到一份 env,把 `actions` 重放到另一份 gold env,比两边的 DB hash。这条 task 的 gold actions 全是只读 GET,hash 从一开始就等于初始库。所以 **四条 trajectory 的 DB 全是 1.0**,包括 `refuse`。

这不是 lab 写错了。这是 `reward_basis` 含 `DB`、但任务根本不改库时的真实行为:DB 检查是空操作,官方分数塌缩成「assistant 文本里有没有字符 `4`」。

`EnvironmentEvaluator` 没有打架:gold/silent 里每个 tool call 后面跟一条同 id 的 dummy `ToolMessage`(`{}`)。只读 tool 在 `set_state` 里被 skip,不会拿 dummy 去跟真输出比。

没调用 `NLAssertionsEvaluator`。

---

## 4. 结论(写进脑子)

```
oracle/gold PASS + refuse.COMMUNICATE=0  ⟹  pipeline 通了,空 agent 过不了 COMMUNICATE
cheat.COMMUNICATE = 1.0                  ⟹  这个 scorer 在测子串,不在测「说对了行李箱数」
refuse.DB = 1.0                          ⟹  只读任务上,DB 检查挡不住什么都不做
ACTION 能抓住 cheat,但 airline 不乘它    ⟹  官方分数 = DB × COMMUNICATE = 1.0 × 1.0
```

同一个 cheat,同一个 `"AA-1234"`,换一个字符,分数从 1.0 变 0.0。变的只有 verifier 看到的字符串。这就是 `× Scorer`。
