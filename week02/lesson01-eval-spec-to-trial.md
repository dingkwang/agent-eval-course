# 第 1 课:从 Eval Spec 到可执行 Trial

## Runtime 如何把一份 evaluation 声明,确定地编译成一组可审计的 Trial

**Week 2 Day 1** · 源码课 · 建议 60 分钟 + 小 lab

> ### 本课唯一命题
> # Harbor 的执行单位是 **Trial**,不是 Task。
> # Runtime 的第一件事是把 Job 声明 **展开并写成 JobLock**,不是开跑。

> 📎 Harbor `b378332` · Inspect `499e615`
> 💻 lab:`../labs/eval-runtime/compile.py`

```diag
flow | Harbor:声明变成 Trial
JobConfig
resolve → validate → expand
JobPlan + JobLock 快照
TrialConfig[]
```

```diag
compare | 可跑单位不是同一个东西
Harbor | Inspect
Trial = Task × Agent × Attempt | Task = Dataset + Solver + Scorer
n_attempts 是乘积的一轴 | epochs 留在 Task 内部
JobLock 无序 Trial 集合 | EvalLog.eval_id 含 created 时间
```

```diag
nest | Trial 不是 SUT
一次 Trial
  SUT · Agent + model + prompt/tools
  实验条件 · task · environment · verifier
  重复观测 · attempt(无 attempt_index 字段)
```

---

## 零、十分钟前置:Agent ≠ Model

`AgentConfig` 里这两件事是分开的(`models/trial/config.py`):

```
name / import_path   跑哪一个 agent 程序(adapter)
model_name           这个程序连哪一个模型
```

`name` 和 `import_path` 都空时,默认不是「随便一个 LLM」,是 **oracle**:

```python
# config.py:166-169
def set_default_name(self):
    if self.name is None and self.import_path is None:
        self.name = AgentName.ORACLE.value
```

换模型、不换 agent,SUT 变了一半。换 agent、模型写成同一个名字,SUT 整份都变了。
**leaderboard 上写模型名、实际跑的是某个 CLI agent,测的就不是那个模型。**

本课剩下的时间不讨论 agent 怎么跑,只讨论:声明怎么变成一列 Trial。

---

## 一、Harbor 先编译,再执行

`JobPlan` 的 docstring 写得很直(`job_plan.py:23-26`):

> *"Resolved plan for a Harbor job **before trials are executed**."*

它是一个 dataclass,里面已经是展开完的列表:

```
config
id
task_configs[]     解析完的任务
trial_configs[]    笛卡尔积之后、准备开跑的 Trial
metrics
task_download_results
job_lock           这次实验输入的结构化快照(不是 overall checksum)
```

`from_config`(`job_plan.py:35-62`)在 **exec 之前**把声明物化完:

```
resolve_agent_skills          字符串技能源 → 本地路径(99-113)
resolve_task_configs          datasets ∪ tasks → TaskConfig[]
validate_resource_policies    环境能力,跑之前就问,不是跑炸了再问(52)
resolve_metrics
cache_tasks                   远程 task 落到 cache,带 content hash
from_resolved → build_trial_configs
```

空 dataset / 不可达的 package task 在这里就 `EmptyDatasetError` / `ValueError`(`job_plan.py:44-46,135`),进不了队列。
默认值也在编译期物化:agent 名叫空 → oracle(`config.py:166-169`);`job_name` 空 → 墙钟时间戳(下面 §三)。
`JobPlan` 是普通 dataclass,没有 `frozen=True`;`task_configs` / `trial_configs` 仍是可变 list。Harbor 做到的是 **resolved + recorded + comparable**,不是类型系统上的 immutable。生成 `JobLock` 只证明「输入被记录了」,不证明执行阶段没人改 `JobPlan`。

**编译失败发生在执行之前。**

---

## 二、展开公式(以源码为准,不要脑补第四轴)

`build_trial_configs`(`job_plan.py:140-168`)就是三重循环:

```python
return [
    TrialConfig(task=..., agent=agent_config, environment=config.environment, ...)
    for _ in range(config.n_attempts)
    for task_config in task_configs
    for agent_config in config.agents
]
```

```
|trials| = n_attempts × |tasks| × |agents|
```

模型**不是**第四重循环。`model_name` 住在 `AgentConfig` 里。
两个模型 = 配两个 `AgentConfig`(可以 `name` 相同、`model_name` 不同)。

Inspect 的配方不是这个乘积。`Task.__init__`(`task.py:76-88`)是:

```
Task(dataset, solver=generate(), scorer=None, model=None, ...)
```

Dataset + Solver + Scorer 绑在**一个** Task 上;model 也是 Task 的字段。
换 solver 往往是 `task_with(...)` 替换,不是 Harbor 那种 agents 列表的笛卡尔积。

> **Harbor:`Trial = Task × Agent × Attempt`(环境从 Job 拷下来)。**
> **Inspect:`Task = Dataset + Solver + Scorer`(sample 在 Task 内部跑)。**
> 这就是「执行模型」的差别。本课只要能说出这一句;对照的细账在第 2 课。

---

## 三、身份字段进 lock,不进相等

`TrialConfig.__eq__`(`config.py:497-504`)故意丢掉身份:

```python
exclude = {"trial_name", "job_id"}
return self.model_dump(exclude=exclude) == other.model_dump(exclude=exclude)
```

`trial_name` 是 `task名__` + 7 位 ShortUUID(`config.py:537-540`)。两次编译,内容相同,名字不同。
**相等比的是「跑什么」,不是「这次叫什么」。**

`job_name` 默认是墙钟时间戳(`JobConfig`,`config.py:357-359`):

```python
job_name: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d__%H-%M-%S"))
```

所以 Job 声明本身也带一次「现在几点」。审计不能靠这个字符串。

真正锁输入的是 `JobLock` / `TrialLock`(`models/job/lock.py`):
- `TaskLock.digest`(64 hex)。`TaskLock.__eq__` **只比 digest**(`lock.py:87-89`),`name` / `path` 是给人看的
- agent / environment / verifier 的 frozen dump
- extra instructions 的 digest
- `JobConfig.__eq__` 丢掉 `job_name` 和 `debug`(`job/config.py:541-546`)
- `JobLock.__eq__` 不看 `created_at`、不看 trial 名字,看 schema、并发上限、retry、**无序的** trial 集合

注释写着(`TrialConfig` 440-441 行附近):

> *If replay-affecting fields are added or changed here, update TrialLock
> so lock.json records the same resolved run input.*

`lock.json` 是实验输入的**结构化锁定记录**,本身没有 overall checksum 字段。内容型资源(task / skill / extra instruction)带 digest;`JobLock.__eq__` 比较 `schema_version`、`n_concurrent_trials`、`retry`、以及 **无序的** `TrialLock` 集合(`lock.py:277-292`)。墙钟 `job_name` / `created_at` 不进相等。

---

## 四、SUT 是被测 Agent 系统,Trial 是一次实验实例

一份 `TrialConfig` 里同时有:

```
task          题目(实验条件)
agent         SUT:被测程序(+可选 model_name / prompt / tools)
user_agent    测量系统里的模拟用户(W1 的 τ³ 在这里入座)
environment   实验条件;从 Job 拷下来,本课不展开
verifier      测量系统;install_only 时会被 copy 成 disable=True
```

**SUT 是被测的 Agent 系统**(implementation + model + prompt/tools/config)。
Task、environment、user simulator、verifier 是实验条件或测量系统。
Attempt 是重复观测,不属于 SUT。Harbor 的 `TrialConfig` **没有** `attempt_index` 字段:它只是把同一份内容再构造一遍,靠不同的 `trial_name` 区分。

编译之后,**Trial 的实验条件被确定**:这个 SUT,在这个 task / environment / verifier 条件下,进行一次 attempt。
`user_agent` 不是 SUT;`verifier` 也不是;`install_only` 时 verifier 会被 copy 成 `disable=True`(`config.py:520-530`),避免共用一个 verifier 实例串改别的 Trial。
**模型名字只是 SUT(AgentConfig)上的一个字段。**

---

## 五、Hands-on:`compile_eval(spec) → JobPlan`

```bash
python3 ../labs/eval-runtime/compile.py
```

实现一个**教学用**编译器,四段对齐 Harbor 的 resolve → validate → expand → record,不是 Harbor 的绑定:

```
EvalSpec
    → resolve   默认 agent 名 → oracle;instruction / prompt 做成 digest
    → validate  空 tasks / agents / n_attempts<1 拒绝
    → expand    n_attempts × tasks × agents(循环顺序对齐 Harbor)
    → freeze    无序 Trial 多重集的 snapshot(对齐 JobLock.__eq__,不是有序 checksum)
```

展开列表保留 Harbor 的循环顺序,方便对照源码。**语义 snapshot 对 agents 顺序不敏感**,和 `JobLock` 的无序 `TrialLock` 集合一致。
Lab 里的 `attempt` 次数只表示多重性;Harbor 真实 `TrialConfig` 没有 `attempt_index`。
同一份 spec 编译两次,snapshot 必须相同。这就是不变量 1 的种子,Day 5 会再验。

```bash
python3 -m pytest labs/eval-runtime/tests/test_compile.py
```

---

## 本课自检

```
[ ] 能说出 AgentConfig.name 和 model_name 各管什么,以及默认 agent 为什么是 oracle
[ ] 能画出 from_config 在开跑之前做了哪几步
[ ] 能写出 |trials| = n_attempts × |tasks| × |agents|,并说明模型为什么不是第四轴
[ ] 能说出 Harbor Trial 乘积和 Inspect Task 配方的差别(一句话)
[ ] 能说出 trial_name / job_name 为什么不能当实验输入;`lock.json` 是结构化快照,不是 overall checksum
```

---

## 本课一句话

> **Runtime 的第一件事是编译:把声明展开成 Trial,把输入记进 JobLock。
> 还没 exec,这次 Trial 的实验条件已经定了。SUT 是 Agent 系统,不是整个 Trial。**
