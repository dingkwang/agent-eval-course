# 第 5 课:OSWorld · WebArena

## 整机 VM + 键鼠/截图 + getter(状态)+metric(期望)

**Week 1 Day 5** · 源码课 · 90 分钟 = 核心 60 + 进阶 30

> ### 本课唯一命题
> # OSWorld 的 environment 是一整台可复位的电脑;observation 是屏幕(+ a11y tree),action 是键鼠;分数来自对**最终应用/OS 状态**的 getter+metric
>
> Day 2 的 Terminal-Bench:容器文件系统 → `reward.txt`。
> Day 4 的 τ³:业务数据库 + 对话 → `reward_basis` 相乘。
> OSWorld:整台桌面 → 屏幕观察、键鼠动作 → **getter 抽出状态,metric 对照期望**。

```diag
compare | 观察 vs 尺子
Agent 看见 | 分数来自
screenshot + 可选 a11y tree | getter 抽出的应用/OS 状态
键鼠 / pyautogui | metric 对 expected
```

```diag
pipe | 本课追的线
task json → snapshot reset → screenshot/键鼠 loop → getter+metric → float
```

```
核心 60  阶梯 · Chrome DNT json · snapshot reset · 观察–动作环 · getter+metric · 对照表
进阶 30  WebArena 网站即环境;2.0 同一台机器、更细的尺子粒度
W5 再处理  长程任务 · checkpoint 部分分 · reward-hacking 审计 · leaderboard 数字
```

> 📎 源码:`../code/OSWorld-V2/`(`8b6b596`,`main`)。`paper.pdf` 与 `OSWorld2.0.pdf` 是**同一份** OSWorld 2.0(XLANG, 2026-06-26, arXiv 2606.29537),不是 2024 的 1.0。
> 💻 本课**不启动 VM**。证据全是源码路径。Day 1 已经扫过 OSWorld 的名字;本课从 `reset → obs/action → evaluate` 追进去。

---

## 零、阶梯上多了什么:容器文件系统 → 整机 GUI 状态

```
Terminal-Bench   一个容器里的文件/进程                    shell 命令改它;pytest 判它
SWE-bench        一个仓库的测试是否过                     契约是 patch 文件
τ³-bench         一个业务库 + 一段对话                    reward_basis 选出 verifier 再相乘
OSWorld          一整台可复位的桌面                       键鼠改它;getter 读最终应用/OS 状态
```

多出来的不是「有 GUI」三个字,是 **state 住在整台机器里**:Chrome 设置、LibreOffice 文档、文件系统、剪贴板、自托管网站。观察是像素,尺子不是。

看:`desktop_env/desktop_env.py` · `evaluation_examples/examples/chrome/` · `lib_run_single.py`。Agent 实现(`mm_agents/`)只作为 `env.step(action)` 的调用方出现。

---

## 一、一个 task json 是什么:Chrome Do Not Track

课堂探针:`evaluation_examples/examples/chrome/030eeff7-b492-4218-b312-701ec99ee0cc.json`

| 字段 | 这道题里是什么 | 在链路上的角色 |
|---|---|---|
| `instruction` | `Can you enable the 'Do Not Track' feature in Chrome to enhance my online privacy?` | agent 看见的题面,也进 `_get_obs()["instruction"]` |
| `config` | `launch` google-chrome + socat 转发 9222 | **reset 之后**写入机器的任务工作区,不是空白桌面 |
| `evaluator.func` | `exact_match` | metric 名字,`_set_evaluator_info` 里 `getattr(metrics, func)` |
| `evaluator.result.type` | `enable_do_not_track` | getter 名字,拼成 `get_enable_do_not_track` |
| `evaluator.expected` | `{type: rule, rules: {expected: "true"}}` | `get_rule` 原样返回 `rules`,再交给 metric |
| `evaluator.postconfig` | `pkill chrome` → 再 launch → sleep 3 | **evaluate 前**把 Preferences 刷到磁盘 |

```diag
nest | Chrome DNT 一次 trial
DesktopEnv
  snapshot 回到可复位桌面
  config 启动 Chrome
  agent 用 GUI 改设置
  postconfig 重启 Chrome
  getter 读 Preferences.enable_do_not_track
  metric exact_match 对 "true"
```

别的 json 还可以带 `user_simulator`。那是**可选的任务 setup**(`desktop_env.py:476-482`),不是每道题的尺子。τ³ 的 User LLM 住在尺子里;这里模拟用户出现时,只是机器里多了一个会回话的人。

---

## 二、DesktopEnv:provider + snapshot reset

`DesktopEnv` 是 gym 环境(`desktop_env.py:30`)。构造时选虚拟化后端和复位点:

- `snapshot_name="init_state"`(`:39`,` :121`)
- `action_space`:`computer_13` / `pyautogui` / …(`:40`,` :135-136`)
- `require_a11y_tree=True`(`:44`,` :125`)——默认观察里带无障碍树

**看 `reset()` `:300`。** 真正贵的操作是 `_revert_to_snapshot()`(`:202-205` → `provider.revert_to_snapshot`)。它**不是每次 reset 都跑**:

```
is_environment_used == True   → revert 到 snapshot_name,再 _start_emulator,然后清 flag(`:329-336`)
is_environment_used == False  → 跳过 revert(`:337-338`)
```

flag 的初值按 provider 分(`:100-108`):

| provider | 启动时 `is_environment_used` | 第一次 reset |
|---|---|---|
| docker / aws / gcp / azure / … | `False` | 机器被认为是干净的,跳过 revert |
| vmware / virtualbox | `True` | 机器被认为是脏的,先 revert |

`step()` 和带 `config` 的 setup 会把 flag 打成 `True`(`:343`,` :549`)。下一道题才能保证回到 snapshot。

`config` 在 revert **之后**由 `_setup_task`(`:267-280`)交给 `SetupController.setup`(`controllers/setup.py:72-100`):`type: launch` → `_launch_setup`。OSWorld 2.0 §2.1.2 把这件事写成 **task-specific workspace**(文件、标签页、自托管站点、用户 profile),不是空白桌面。

然后 `reset` 返回 `_get_obs()`(`:411-412`)。

---

## 三、观察–动作环:screenshot → 键鼠 → 新 screenshot

`_get_obs()`(`:449-457`)一次给出四样:

```
screenshot            controller.get_screenshot()
accessibility_tree    可选,require_a11y_tree
terminal              可选,require_terminal
instruction           题面
```

2.0 §3.1:进模型的主观察是 **screenshot**。像素是 **agent 的输入**,不是分数。

`step(action)`(`:544-582`):

1. 记下 action,把 `is_environment_used = True`
2. `WAIT` / `FAIL` / `DONE` 是控制面:`FAIL`/`DONE` 把 `done=True`
3. `computer_13` → `controller.execute_action`(原语在 `actions.py` `ACTION_SPACE`:`MOVE_TO` / `CLICK` / …)
4. `pyautogui` → `controller.execute_python_command`
5. sleep,再 `_get_obs()`

**循环里的 `reward` 现在写死为 0**(`:551`,旁边还有 todo)。计入分数的不是逐步 reward,是循环结束后的 `evaluate()`。

整段 rollout 在 `lib_run_single.py` `run_single_example`(`:853`):

```
env.reset(task_config=example)          :880
obs = env._get_obs()                    :884
while not done and step_idx < max_steps :891
    agent.predict(instruction, obs)
    env.step(action)                    :928
env.evaluate()                          :982
_persist_evaluation_result(...)         :983
```

看这一段就够:agent 是 `step` 的调用方;环境与尺子都在 `DesktopEnv`。

---

## 四、尺子:getter 抽状态,metric 比期望

`evaluate()`(`:584-587`)默认走进 `_evaluate_with_evaluator()`(`:589`)。

Chrome DNT 这条路径:

```
postconfig          pkill + 再 launch Chrome,让 Preferences 落盘(`:598-602`)
result_getter       get_enable_do_not_track(env, {type: enable_do_not_track})
expected_getter     get_rule → {"expected": "true"}
metric              exact_match(result_state, expected_state) → 1.0 或 0.0
```

名字怎么接上:json 里 `result.type = "enable_do_not_track"`, `_set_evaluator_info`(`:513-516`)做 `getattr(getters, "get_{type}")`。`func: exact_match` 同样从 `metrics` 取函数(`:506-510`)。

`get_enable_do_not_track`(`evaluators/getters/chrome.py:1243-1270`)不看截图。它在 VM 里定位 Chrome `Preferences`,`json.loads` 之后读 `enable_do_not_track`,返回 `"true"` / `"false"`。

`exact_match`(`evaluators/metrics/general.py:41-48`)是字符串相等,命中 1.0,否则 0.0。

`expected.type = "rule"` 走 `get_rule`(`evaluators/getters/misc.py:87-91`):把 json 里的 `rules` 原样交给 metric。期望值写在题目里,不写在截图里。

`_persist_evaluation_result`(`lib_run_single.py:23-58`)把这个 float 写成 `result.txt`,dict 结果再写一份 `result.json`。

所以这道题的分数是:**Chrome 配置文件里 DNT 开了没有**,不是「最后一帧像不像标准截图」。2.0 §2.1.3 把同一设计说成对 concrete state / artifact 做 functional check。

多 metric 时 json 可以带 `conj`(`desktop_env.py:511`,` :616-672`):`and` / `or` / `avg` / `sum`。进阶点到为止。

---

## 五、对照:state 在哪、看见什么、怎么复位、怎么判

| | Terminal-Bench | SWE-bench | OSWorld | WebArena |
|---|---|---|---|---|
| **state** | 容器文件系统 / 进程 | 仓库 + 隐藏测试 | 整台桌面(应用 + OS + 文件) | 自托管网站栈 |
| **reset** | 新容器 | 新容器 + 指定 commit | VM snapshot,用过才 revert,再跑 `config` | 网站数据复位 |
| **obs** | shell 输出 | 代码 / 测试日志 | screenshot(+ a11y) | 页面(DOM / a11y / 截图) |
| **action** | shell | 产出 patch | 键鼠 / pyautogui | 浏览器动作 |
| **尺子** | `tests/` + parser | 官方测试是否过 | getter(状态)+metric(期望) | 功能检查(表单/DB/URL),不是像素 |
| **契约** | 世界被测到 | 一个 patch 文件 | 最终应用/OS 状态 | 最终网站状态 |

同一观察–动作环,state 粒度不同。WebArena 的环境是**浏览器里的世界**;OSWorld 的环境是**整台 OS**,Chrome 只是上面的一个应用。

---

## 进阶 30 · WebArena,以及 2.0 仍是同一台机器

### 看 `papers/webarena.pdf`

WebArena 把 environment 收成一组**可复现的自托管网站**(电商、论坛、GitLab 一类)。Agent 仍然 screenshot / 页面 → 浏览器动作 → 新页面;分数来自站点上的功能结果(买没买到、issue 建没建),不是截图像不像。

和 OSWorld 并排看:

```diag
compare | 世界有多大
WebArena | OSWorld
网站栈 = 全部环境 | 整台 OS 是环境
浏览器动作 | 键鼠,Chrome 只是其中一个应用
复位站点数据 | 复位 VM snapshot + 任务 config
```

OSWorld 2.0 把 31 个自托管站点**放进这台 VM**。那不是「改用 WebArena 当环境」,是整机里面多了一层 WebArena 式的网站。2.0 §2.2.3 把 WebArena 和 OSWorld 1.0 归在一起:真实可交互,但任务相对短、相对窄。长短程、难度、GDP-proxy —— **W5**。

### 2.0 改的是任务和尺子粒度,不是换机器

1.0 和 2.0 **共用同一套桌面 VM**。Agent 仍然看 screenshot(§3.1)。核心 60 追的 `reset / step / evaluate / getter+metric` 在这份 checkout 里仍然是主路径。

2.0 在同一台机器上把尺子磨细:1.0 终态二元;2.0 可以按 checkpoint 在**终态**上平均(`conj: avg`,`lib_run_single.py` 里可选的 checkpoint eval)。部分分、长程、leaderboard 数字留在 W5。本课只要记住:**机器没换,题和尺子的粒度换了。**

2.0 §2.1.3 还允许一小部分 model-based 分数作补充(全文约 11.53% 的分,且单题不超过一半)。主体仍是 getter+metric。本课用 Chrome DNT 就是那条主体路径。

---

## 本课自检

```
[ ] 1. 能用一句话说出 OSWorld 的 unique prop:整机 + 键鼠/截图 + getter+metric
[ ] 2. 能打开 Chrome DNT json,指出 instruction / config / postconfig / func / result.type / expected 各进哪一环
[ ] 3. 能说出 reset 何时 revert snapshot,以及 docker 与 vmware 的 is_environment_used 初值为什么不同
[ ] 4. 能指出 _get_obs 里哪些字段给 agent,以及 step() 里 reward=0 意味着什么
[ ] 5. 能从 result.type 拼出 getter 函数名,并说出 get_enable_do_not_track 读的是 Preferences 不是截图
[ ] 6. 能对比 TB / SWE / OSWorld / WebArena 的 state、reset、obs、尺子
[ ] 7. 能说出 WebArena 的环境是网站栈,OSWorld 2.0 把同类站点放进整机,而不是换成网站栈
```

---

## 本课一句话总结

> **OSWorld 让 agent 看屏幕、动手用键鼠,但分数问的是机器最后长什么样。**
> 截图是观察;getter+metric 才是尺子。

---

**上一课(Day 4)**:[τ³-bench](lesson04-tau3-bench.md)。
**下一课(Day 6)**:hello-bench —— 五个抽象亲手写一遍(`Task · Environment · Agent · Verifier · Result`)。讲义还在写;lab 已在 [`../labs/hello-bench/`](../labs/hello-bench/)。
