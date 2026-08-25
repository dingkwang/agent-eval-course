# 第 2 课:Agent / Environment / Trial 协议

## 换实现之后,还是同一个实验吗?

**Week 2 Day 2** · 源码课 · 建议 75 分钟 + lab

> ### 本课唯一命题
> # Adapter 和 backend 不是「接得上就算正确」。
> # 只有当它们不增加、不删除、不扭曲 task information,并且对相同 action 给出相同的可观察环境语义时,换实现才不会改 evaluation experiment。

```diag
nest | SUT 不是整个 Trial
一次 Trial
  SUT · Agent 实现 + model + prompt/tools/config
  实验条件 · instruction · 初始环境 · user simulator · limits · verifier
  一次观测 · attempt
```

> 📎 Harbor `b378332` · Inspect `499e615`
> 💻 lab:`../labs/eval-runtime/`(`protocol.py` · `trial.py` · `adapters/` · `environments/`)

---

## 零、从第 1 课接过来

第 1 课把声明展开成 resolved Trial。本课问的不是「怎么调用 `agent.run()`」,而是:

**把 Claude Code 换成 Codex,或把 Docker 换成另一个 sandbox,怎么证明变的只是实现,不是题目?**

```diag
flow | 现在要执行的是已经展开的 Trial
JobConfig
resolve / validate / expand / record
TrialConfig(task, agent, environment, verifier)
本课:换 Agent 或 backend,实验还是不是同一个
```

Task、environment、attempt **都不是 SUT**。SUT 是被测 Agent 系统。其余是实验条件。

---

## 一、两个 backend 都返回 1,实验就等价吗?

任务:`Create /workspace/answer.txt containing exactly: 42`。同一个 scripted agent 写 `"42\n"`。Local 和 Docker 的 verifier 都返回 1。这仍然不够。

```diag
grid | final score 相同没有证明的东西
task information | 有没有被 adapter 加料
initial state | 有没有上次 Trial 的残留
action semantics | user / cwd / mkdir / timeout 是否一致
state transition | 相同动作是否落到相同可见状态
verifier input | 尺子读到的是不是同一份最终态
termination | stop 失败是否仍被记成成功
```

本课的 conformance 查的是这六项,不是 `score_A == score_B`。

```diag
compare | 接得上 ≠ 实验还在
API shape 对上 | 实验语义还在
setup / run 都实现了 | instruction 一字不改
start / exec / stop 都有 | 相同 action → 相同可见状态
分数是 1 | 终态 digest + 终止原因相同
```

---

## 二、四个边界,不是两个 Python class

```diag
compare | 谁拥有什么
组件 | 不准做什么
Task | 不决定某个 Agent 的私有 prompt 格式
Agent Adapter | 不补充答案、不删限制、不重写任务语义
Environment Backend | 不因 provider 不同而静默改变任务语义
Trial Runtime | 不替 Agent 做题,不替 verifier 猜结果
```

```diag
flow | Trial 里四件事的顺序
create / start Environment
Agent.setup(environment)
Agent.run(instruction, environment, context)
Verifier.verify(final state) → stop Environment
```

允许的转换:canonical instruction → CLI argv / stdin / ACP message。
不允许:在 instruction 后面偷偷接上 oracle hint。后者即使分数提高,实验已经坏了。

---

## 三、Harbor 的 Agent 协议

### 3.1 `BaseAgent` 不是 `act(obs) → action`

`agents/base.py` 的核心是两个粗粒度方法:

```python
async def setup(self, environment: BaseEnvironment) -> None: ...
async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None: ...
```

`run()` 自己返回 `None`。Agent 有两路输出:

```diag
compare | Agent.run 的两路输出
环境副作用 | AgentContext
写文件 · 起服务 · 改状态 | token · cost · metadata · trajectory 相关
没有副作用 → 任务失败 | 没有 context → 审计和成本残缺
```

`SUPPORTS_WINDOWS` / `SUPPORTS_ATIF` / `SUPPORTS_RESUME` 是能力声明。不支持就必须拒绝,不能装成支持。`resume()` 存在,本课不展开(→ W6)。

Trial 在 `setup()` **之前**把 `environment.default_user` 设好(`trial/trial.py` `_prepare`)。

### 3.2 Null 和 Oracle 是实验对照,不是 SUT

`NopAgent.setup/run` 都是 `pass`(`nop.py`)。负控:非平凡题若 Nop 也能过,初态或 verifier 漏了答案。

`OracleAgent.__init__` 拿 `task_dir`(`oracle.py`)。`run()` 把 solution dir **upload** 进环境,再 `exec` 那份脚本。正控:Oracle 不过,先查题/环境/尺子,再查模型。它**不是** leaderboard 上的 SUT,是 harness diagnostic。

`task_dir` 在 sandbox 外面。普通 Agent 协议只有 `instruction` + `environment` + `context`;Oracle 多握一份宿主机题目目录,这是特权。Lab 里的 `OracleAgent(solution=hidden["expected"])` 是同一件事的缩写:答案从构造函数进,不从 `/workspace` 读。

```diag
grid | 最小 sanity matrix
Nop | 期望 FAIL · 若 PASS → 初态污染或尺子过弱
Oracle | 期望 PASS · 若 FAIL → task/env/verifier 闭环坏了
被测 Agent | 只有两个 control 正常,分数才可解释
```

---

## 四、Harbor 的 Environment 协议

### 4.1 task 环境定义 ≠ runtime backend

task 自带 environment definition(`task.toml`、Dockerfile)。`TrialConfig` 里的 EnvironmentConfig 选**怎样实现**它。换 backend 不是换题。

```diag
pipe | 两层环境
task 定义「应该得到什么环境」 → runtime backend「由谁实现」 → 本 Trial 的实例
```

### 4.2 `BaseEnvironment` 的门

`environments/base.py`(只抽 API,不读 `docker.py`):

```
type / start / stop
exec(command, cwd, env, timeout_sec, user) → ExecResult
upload_file / upload_dir / download_file / download_dir
capabilities  gpus · windows · mounted · docker_compose · disable_internet · …
```

Agent 只能走这些门。`user=None` 回落到 `default_user`。不支持的 requirement 必须 **fail fast**,不能静默降级。network allowlist 的细则 → W7。

### 4.3 不要把 Harbor 写成 Gymnasium

Harbor **没有** `step(action)`。外部 CLI Agent 一次 `run()` 里可能 `exec` 几十次,runtime 只看见粗边界。这就是第 3 课要单独讲 trajectory 的原因。

```diag
pipe | Harbor 看见的粒度
start → Agent.setup → Agent.run(多次 exec) → collect → verify → stop
```

---

## 五、Trial 才拥有生命周期

`trial/trial.py` `run()` 可以收成:

```diag
flow | Trial.run(b378332)
emit START
prepare: start env → healthcheck → setup agent
run workload(除非 install_only)
except CancelledError: CANCEL + recover_outputs + raise
except Exception: record + recover_outputs
finally: finalize → stop env → write result → END
```

Cancellation 是一条退出路径,不是跳过 `finally` 的许可。Agent 不拥有 sandbox 的寿命;Trial 拥有。shared vs separate verifier → W7。并发池 → 第 4 课。

教学用状态机(Harbor **没有**这个 enum,是从控制流抽的):

```diag
pipe | 非法转换必须有答案
CREATED → PREPARING → AGENT_RUNNING → VERIFYING → FINALIZING → SUCCEEDED/FAILED/CANCELLED
```

CREATED → VERIFYING、SUCCEEDED → AGENT_RUNNING、CANCELLED → VERIFYING 都非法。setup 失败后 verifier 跑不跑、timeout 后是否收 partial logs,必须有确定答案。

---

## 六、怎样证明换实现后仍是同一道题

真实 LLM 有随机性,不能用「最终 patch 逐字相同」证明等价。用可控 probe:

```diag
compare | 两种等价,不要混
Input equivalence | Execution equivalence
Agent 看见的任务语义相同 | 相同 scripted actions → 等价状态
instruction / 可见文件 / limits | 初态 · 动作序列 · 终态 · 终止原因 · verifier 输入
```

```diag
grid | conformance 最小阵
Nop | 两 backend 都 FAIL
Oracle | 两 backend 都 PASS(特权:构造函数带 hidden payload)
Scripted valid · 走 exec | 终态 digest 相同
Hint-injecting adapter | reward 可以是 1,status 必须是 ADAPTER_VIOLATION
```

```diag
compare | 两种 Agent 看见的信息
协议内 Agent | 特权 Oracle
instruction + /workspace 可见文件 | 另外拿到 task_dir / hidden solution
只能走 exec / read / write | Harbor:upload solution 再 exec
换 backend 必须仍能跑同一组 probe | 正控失败先查题,不查模型
```

Local backend 是教学实现,不是 Harbor 官方 backend:每 Trial 新临时目录,不准把宿主机任意路径暴露给 Agent。Docker lab 是 **host workspace bind-mount + `docker run --rm`**,因为这台机器上 `docker exec` 会丢 stdout;不要把它读成 Harbor 的 docker backend。

---

## 七、Inspect 对照:相同名词,不同协议中心

Inspect `@499e615`:

- 原生 Agent:`async def __call__(self, state: AgentState) -> AgentState`(核心是 `messages` / `output`)
- `SandboxEnvironment` docstring:*Environment for executing arbitrary code from tools*(`util/_sandbox/environment.py:127`)。Solver/Agent 的 Python **默认在 eval 主进程**;进机器走 `exec` / `write_file` / `read_file`
- `sandbox="docker"` **不等于** Agent 进程在容器里
- `sandbox_agent_bridge`(`agent/_bridge/sandbox/bridge.py:45`)才把外部 Agent 放进 sandbox,并代理模型 API —— 这是重叠区的源码位置,不是功能清单

```diag
compare | 协议中心
Harbor | Inspect
instruction + Environment + Context | AgentState → AgentState
Agent 通常在环境里跑 | 控制逻辑默认在 host
环境副作用 + AgentContext | messages / output
外部 CLI = 原生 BaseAgent 方向 | 外部 CLI 常走 Agent Bridge
```

课程目标不是做一个同时长得像两边的万能 API,而是定义**换实现仍必须保持的 canonical semantics**。

Gymnasium / BrowserGym:`reset` / `step` vs Harbor `start` / `exec` / `stop`。本课不展开。

---

## 八、Lab:conformance harness

```bash
python3 -m pytest labs/eval-runtime/tests/test_agent_contract.py \
  labs/eval-runtime/tests/test_environment_contract.py \
  labs/eval-runtime/tests/test_lifecycle.py \
  labs/eval-runtime/tests/test_differential.py
```

四个 Agent:

```
Null              负控,终态不变,reward=0
Oracle            正控,构造函数带 hidden payload(不是从 /workspace 算出来)
ScriptedValid     用 exec 写 42 —— 这才走 backend 的命令通道
ScriptedInvalid   用 exec 写 41
HintInjecting     改 instruction 再跑 ScriptedValid:reward 仍是 1,status 必须 ADAPTER_VIOLATION
```

hidden verifier 字节不准出现在 workspace。不支持的 OS capability 必须 `UNSUPPORTED`,不能装成能跑。`CancelledError` 仍走 `finally` 停环境。

Local 必测;Docker 在 `docker run --rm python:3.12-slim-bookworm` 能打印 `ok` 时测,否则 skip。

这是第 5 天不变量 2 的种子,不是 EvalRT Core 全文。

---

## 源码阅读(只答问题,不通读 backend)

Harbor:`BaseAgent.run` 为什么同时拿 environment 和 context?Nop 与 Oracle 各是哪种 control?`exec` 的 cwd/env/timeout/user 为什么都是实验语义?不支持的 capability 为什么必须 reject?`Trial.run` 在普通异常与 cancellation 下有何不同?`_finalize` 为什么还要 stop environment?

Inspect:只看 `AgentState → AgentState` 和 `SandboxEnvironment.exec/read_file/write_file`。外部 CLI 自己维护 session 时,怎样才能看到它真实的模型调用?

---

## 本课自检

```
[ ] 能区分 SUT、evaluation condition 与 Trial
[ ] 能解释 Adapter 为什么可能在不改 API shape 的情况下改变 benchmark
[ ] 能写出 Harbor BaseAgent 的 setup/run contract
[ ] 能说出环境副作用与 AgentContext 是两条输出通道
[ ] 能说出 Null 与 Oracle 分别检查什么
[ ] 能写出 BaseEnvironment 的 start/stop/exec/file contract
[ ] 能解释 capability 必须 fail fast
[ ] 能从 Trial.run() 画出成功 / 异常 / 取消 / cleanup
[ ] 能定义 input equivalence 与 execution equivalence
[ ] 能解释为什么相同 final score 不能证明两个 backend 等价
[ ] 能说出 HintInjecting 即使 reward=1 也必须是 ADAPTER_VIOLATION
[ ] 能说出 Oracle 的特权从哪来(Harbor:task_dir;lab:构造函数 payload)
```

---

## 本课一句话

> **Runtime 正确不是所有 Adapter 都实现了同名方法,而是换 Agent 或 backend 之后,任务语义、动作语义、verifier 读到的终态、Trial 的退出语义都没有被悄悄改掉。**

下一课:Harbor 的 `run()` 边界太粗。tool 已经改了环境、Agent 没收到 response 时,trajectory 怎么记因果?
