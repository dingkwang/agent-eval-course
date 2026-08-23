# hello-bench —— 自己写一个最小的 agent benchmark

**Week 1 Day 6 的 lab。** 读了五个真 benchmark 之后,把那五个抽象自己写一遍。

```
Task  →  Environment  →  Agent  →  Verifier  →  Result
```

全部代码 **< 200 行**,`bench.py` 一个文件。目标不是造轮子,是让 Terminal-Bench 的
`solution.sh`、SWE-bench 的 `run_evaluation.py` 从此不再像魔法。

---

## 跑起来

```bash
cd labs/hello-bench
python3 run.py                          # 3 tasks × 3 agents,弱 verifier
python3 run.py --strong -t sum-numbers  # 换强 verifier
```

镜像第一次会自动 build(`python:3.12-slim` + pytest)。

---

## 1. 真实输出 ⭐

```
    task            oracle    null      cheat
    create-file     PASS      fail      fail
    start-server    PASS      fail      fail
    sum-numbers     PASS      fail      PASS      ← ⚠️
```

换成强 verifier 再跑 `sum-numbers`:

```
    task            oracle    null      cheat
    sum-numbers     PASS      fail      fail      ← 同一个 agent,同一份代码
```

`cheat` 在强 verifier 下的明细:`1 failed, 1 passed`
```
FAILED /verifier/test_outputs_strong.py::test_regenerated_input
       AssertionError: hardcoded answer? verifier changed the input
```

> **同一个 agent,同一份产出,分数从 PASS 变成 fail。变的只有 verifier。**
> 这就是七因子公式里那个 `× Scorer` —— 它不是修饰词,它直接决定数字。

---

## 2. 三个 agent 分别在测什么

| Agent | 应该 | 如果不是,说明 |
|---|---|---|
| **oracle** | 永远 PASS | **任务或 harness 坏了**,与模型无关 |
| **null** | 永远 fail | 任务**什么都没测**:成功条件本来就成立,或 setup 替 agent 干了活 |
| **cheat** | 看情况 | PASS ⟹ **verifier 有洞** |

前两个来自 Terminal-Bench(Day 2 的 oracle agent)。第三个是这门课自己加的,
因为**「跑通」和「测得准」是两件事**:oracle + null 只能证明前者。

```
oracle PASS + null fail  ⟹  这条 pipeline 是通的
                         ⟹  但完全没说明这道题在测什么
cheat  fail              ⟹  verifier 至少挡住了你想到的那一种作弊
```

---

## 3. 五个抽象,以及每一个的设计决定

### ① `Task` —— 什么进、什么出
`task.yaml` 只有三个字段:`instruction`(agent 看得到)、`image`、`setup`(agent 之前跑)。
`tests/` **不在 Task 对象里**,只有 Verifier 拿得到路径。

### ② `Environment` —— 状态活在哪
一个 host 临时目录,挂到容器 `/workspace`。每条命令一个 **一次性容器**。

```
文件状态   跨命令保留     ← 挂载目录
进程状态   不保留         ← 容器每次都是新的
```

这个选择直接改写了一道题的题面。`start-server` 原本是「起一个服务并让它活着」,
在这个模型下**无法验证** —— verifier 的容器看不到 agent 的进程。于是交付物从
**一个活进程**改成 **一个文件** `/workspace/server.py`,由 verifier 自己启动、
curl、杀掉。

> **这不是妥协,这是更好的 benchmark 设计。**
> 交付物是 artifact 时,任务可复现、可重跑、可归档;交付物是 live process 时,
> 你必须把 verifier 塞进 agent 的容器里 —— 而那正是 Day 3 讲的**信任边界崩塌**。
> 现实中的对照:SWE-bench 的契约是**一个 patch 文件**,不是一个活着的 repo。

### ③ `Agent` —— 唯一的接口
```python
def perform(self, task: Task, env: Environment) -> list[str]: ...
```
只有一个方法。三个实现都不是 LLM —— **这正是重点**:先用固定脚本证明 harness 本身
是对的,再谈模型。接一个真 LLM,只需要再写一个 `perform`。

### ④ `Verifier` —— 信任边界写在 `-v` 里
```python
env.run("pytest /verifier/...", mounts={task.path / "tests": "/verifier"})
```
agent 的容器**只挂 `/workspace`**;verifier 的容器**多挂一个只读 `/verifier`**。
agent 根本没有通往测试文件的路径 —— 不是靠约定,是靠 `docker run` 的参数。

对照 SWE-bench:它做得更狠,eval 前先 `git checkout` 把测试文件强制还原
(`test_spec/python.py:419-425`),因为它必须假设 agent 动过同一个 repo。

### ⑤ `Result` —— 为什么不能只存一个 bool
```python
success · trajectory · duration · tests_total · tests_failed · failure_mode
```
`failure_mode` 区分 `no_action` / `agent_error` / `tests_failed`。跑一次就能看到
差别:`null` 全是 `no_action`,`cheat` 在强 verifier 下是 `tests_failed`。

> 这三类的改进方向完全不同,压成一个 0 就再也分不开了 —— 对应 SWE-bench 的
> `unresolved` / `empty patch` / `error`(Day 3 §三),以及 **W6 Failure Taxonomy**。

---

## 4. `sum-numbers`:一道故意可以被 game 的题 ⭐

题面:`/workspace/numbers.txt` 每行一个整数,写 `sum.py` 打印它们的和。
setup 写入 `17 / 11 / 14`,和是 **42**。

两个 verifier,同一道题:

| | 做法 | `print(42)` |
|---|---|---|
| `test_outputs.py`(弱) | 只对着 setup 那份固定输入判 | **PASS** |
| `test_outputs_strong.py`(强) | 重新生成随机输入再判 | **fail** |

```python
def test_regenerated_input():
    nums = [random.randint(1, 999) for _ in range(5)]
    Path("/workspace/numbers.txt").write_text("\n".join(map(str, nums)) + "\n")
    assert _run() == str(sum(nums)), "hardcoded answer? verifier changed the input"
```

弱 verifier 的问题不是「写得潦草」,是**它测的其实是另一道题**:
> 你以为在测「会不会读文件求和」,实际在测「知不知道答案是 42」。

`CheatAgent` 花了一行就把这个差别暴露出来。**每写一个 verifier,都要先问一句:
有没有一个不解决问题、却能让它变绿的最短程序?**

> 🔁 呼应 Day 3 的坑 ②:那次是「我以为造了个负例,其实没有」。
> 这次是「我以为造了个测试,其实没有」。**同一个病:没有验证你的验证。**
> 这条会在 **W5 任务质量** 展开。

---

## 5. 留给你的四个练习

```
[ ] ① 第四道题:反过来 —— 让 null agent 意外 PASS
     (提示:让 setup 把活干了。这在真数据集里比你想的常见)
[ ] ② 给 create-file 也写一个 CheatAgent 捷径。写不出来?说明这道题是干净的
[ ] ③ 让 rollout 跑 5 次,统计 pass rate —— 你会发现 start-server 偶尔抖
     (然后去看它 verifier 里那个 40 次重试的 for 循环)
[ ] ④ 接一个真 LLM:只需要新写一个 Agent.perform,其余四个抽象一行不改
```

---

## 6. 环境笔记(踩过的坑)

**`docker exec` 在某些机器上是 no-op** —— 返回 0、无输出、无副作用。
最初版本的 `Environment` 是 `docker run -d` + `docker exec`,全矩阵 `0/0 tests`。

诊断路径:
```
docker run --rm img echo X   → 有输出   ✅
docker exec  cid  echo X     → 空       ❌
docker exec  cid 'echo>/f'   → 文件不存在 ❌   ← 确认是 no-op,不是输出丢了
```
改成 **前台 `docker run` + bind mount** 后全部正常。

> **教训**:harness 的第一个 bug 通常不在你的代码里,在你对 runtime 的假设里。
> 这也正是 oracle agent 存在的理由 —— 上面那三行,就是 oracle 全红时该做的事。

另:容器加 `--user $(id -u):$(id -g)`,否则挂载目录里的文件会归 root。

---

## 文件

```
hello-bench/
├── bench.py            五个抽象 + rollout
├── agents.py           OracleAgent / NullAgent / CheatAgent
├── run.py              跑矩阵、打表、存 json
├── Dockerfile          python:3.12-slim + pytest
└── tasks/
    ├── create-file/    最简单:文件存在 + 内容对
    ├── start-server/   交付物是 artifact,不是活进程
    └── sum-numbers/    ⚠️ 可被 game;两个 verifier
        ├── tests/test_outputs.py         弱
        └── tests/test_outputs_strong.py  强
```
