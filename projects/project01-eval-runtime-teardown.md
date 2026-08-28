# P1 · Eval Runtime Teardown
## W1–W2 · 拆一个真实 benchmark，再扩展现有的 hello-bench

**正式提交次数:1** · **建议投入:8–10 小时** · **截止:W2 结束**

> 这份作业不是让你重写 Harbor，也不是写一篇 runtime 理论报告。你只做两件主事：先把一个真实 benchmark 的源码执行链找出来，再把课程现有的 `hello-bench` 扩展成一个能留下完整运行记录的 mini eval。

---

## 一、最后要交什么

```text
projects/p1-eval-runtime/
├── source-map.md       # 第一部分：拆解真实 benchmark
├── mini-eval/          # 第二部分：扩展后的 hello-bench / eval-runtime
├── sample-runs/        # 第三部分：五个实验的真实输出
└── README.md           # 怎么运行，以及你观察到了什么
```

验收时只看四件事:

1. 你能不能从源码解释一个真实 benchmark 怎么跑；
2. 你的 mini eval 能不能真的运行；
3. Oracle、Null、Cheat、Timeout 是否产生正确且不同的结果；
4. 别人能不能从保存的记录看懂一次 run 为什么 PASS、FAIL 或 ERROR。

## 二、第一部分：拆一个真实 benchmark

从 Terminal-Bench 或 SWE-bench 中选一个。找到下面六项的**具体文件路径、类或函数**:

```text
task 定义在哪里
environment 怎么启动
Agent 从哪里接收 instruction
rollout loop 在哪里
verifier 检查什么状态
最终 result 从哪里产生
```

把结果写入 `source-map.md`，建议使用这个模板:

```text
Benchmark:
Repository + commit:

One concrete task:
  task definition:
  instruction field:
  environment setup:

Execution:
  runner entrypoint:
  Agent interface:
  rollout loop:

Evaluation:
  verifier entrypoint:
  state inspected:
  result object / file:

One thing that surprised me:
```

控制在一到两页。重点是路径和调用关系准确，不讨论“这个 benchmark 好不好”。

## 三、第二部分：扩展现有 mini eval

直接复用仓库中的:

```text
labs/hello-bench/
labs/eval-runtime/
```

不需要另造一套大型框架。最终程序只需要跑通这条线:

```diag
flow | 你要实现的 mini eval
读取 task.yaml
创建干净 workspace
让 Agent 执行动作
保存 trajectory
Verifier 检查最终状态
写出 TrialResult
```

### Step 1：让 task 来自配置文件

至少有两个小任务，例如:

```text
create-file：创建 result.txt，内容为 42
sum-numbers：读取 numbers.txt，写程序输出总和
```

`task.yaml` 至少写:

```yaml
id: create-file
instruction: Create /workspace/result.txt containing 42
timeout_sec: 10
verifier: tests/test_result.py
```

### Step 2：保留一个统一的 Agent 接口

```python
class Agent:
    def perform(self, task, environment) -> list[str]:
        ...
```

实现三个 scripted agents:

| Agent | 行为 |
|---|---|
| Oracle | 按正确方法完成任务 |
| Null | 什么都不做 |
| Cheat | 不真正解决问题，只针对弱 verifier 写死答案 |

不要求接真实 LLM。

### Step 3：每次 run 使用干净 workspace

Agent A 运行后留下的文件不能被 Agent B 看见。最简单的实现是每次创建新的临时目录，并在结束后 cleanup。

在 README 里说明:

```text
初始文件从哪里复制
Agent 可以读写哪里
verifier 从哪里读取结果
tests 是否对 Agent 可见
```

### Step 4：保存 trajectory

不用先实现复杂的 ATIF schema。每次 run 保存一个简单 JSONL 即可:

```json
{"type":"trial_started","task_id":"create-file","agent":"oracle"}
{"type":"command","value":"printf 42 > /workspace/result.txt"}
{"type":"command_result","exit_code":0}
{"type":"verifier_result","passed":true}
{"type":"trial_finished","status":"PASS"}
```

要求只有一个：别人只看这个文件，也能知道 Agent 做了什么、命令是否成功、verifier 为什么通过。

### Step 5：保存 TrialResult

每次 run 生成:

```json
{
  "task_id": "create-file",
  "agent": "oracle",
  "status": "PASS",
  "tests_total": 1,
  "tests_failed": 0,
  "duration_sec": 0.42,
  "failure_reason": null,
  "trajectory": "trajectory.jsonl"
}
```

`status` 至少区分 `PASS`、`FAIL` 和 `ERROR`。Timeout 属于 ERROR，不要伪装成普通任务失败。

## 四、第三部分：跑五个实验

保存下面五次 run 的 trajectory 和 TrialResult:

| 实验 | 预期结果 | 你在验证什么 |
|---|---|---|
| Oracle + strong verifier | PASS | task、environment、Agent、verifier 整条链能工作 |
| Null + strong verifier | FAIL | setup 没有替 Agent 把任务做完 |
| Cheat + weak verifier | PASS | 弱 verifier 确实存在 shortcut |
| Cheat + strong verifier | FAIL | 强 verifier 能抓住写死答案 |
| Timeout Agent | ERROR | runtime 能区分超时和任务失败，并留下记录 |

最终命令可以像这样:

```bash
python run.py --task sum-numbers --agent oracle --verifier strong
python run.py --task sum-numbers --agent null --verifier strong
python run.py --task sum-numbers --agent cheat --verifier weak
python run.py --task sum-numbers --agent cheat --verifier strong
python run.py --task sum-numbers --agent timeout --verifier strong
```

最终输出至少包含:

```text
agent      verifier    status   reason
oracle     strong      PASS     expected state reached
null       strong      FAIL     no action
cheat      weak        PASS     hardcoded shortcut
cheat      strong      FAIL     regenerated-input check
timeout    strong      ERROR    deadline exceeded
```

## 五、README 只回答六个问题

1. 怎么从干净环境运行？
2. 一个 task 从哪里被读取？
3. Agent 能看到什么、不能看到什么？
4. Verifier 实际检查什么状态？
5. PASS、FAIL、ERROR 分别是什么意思？
6. 五个实验分别证明了什么？

不要求写成长报告。截图不能代替保存的 JSON / JSONL 结果。

## 六、评分

| 部分 | 分数 |
|---|---:|
| `source-map.md` 路径和执行链准确 | 20 |
| mini eval 能从 task config 跑到 TrialResult | 30 |
| 每次运行使用干净 workspace，verifier 边界说清楚 | 15 |
| 五个实验得到合理结果并保存 trajectory | 25 |
| README 能让别人复现 | 10 |

**80 分通过。Oracle 不通过、Null 意外通过、没有保存 trajectory，任一情况都不能通过。**

## 七、选做，不影响通过

下面这些是后续 W2 深入练习，不是 P1 最低要求:

- 把 resolved defaults 保存成 immutable `JobPlan`；
- 检测偷偷向 instruction 加 hint 的 adapter；
- 表达 tool 已执行但 response 丢失的 ambiguous outcome；
- 并发运行多个 tasks 并证明互不污染；
- 实现 cancellation-safe cleanup；
- 接入真实 LLM Agent。

> **一句话总结：P1 = 一页源码地图 + 一个能跑的 hello-bench 扩展 + 五次对照实验。**
