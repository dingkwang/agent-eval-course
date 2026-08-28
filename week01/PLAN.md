# Week 1 — Benchmark Archaeology
## 拿到任何 agent benchmark repo,能从源码追通整条链

> **Assessment policy**:本周的 Source Code Map、SWE-bench teardown、τ³ verifier 与 hello-bench 都是 [P1 Eval Runtime Teardown](../ASSESSMENTS.md) 的 checkpoints，不是四份独立作业。P1 在 W2 结束时只提交一次。

> **v2**(2026-08 重构)。v1「Evaluation 基本框架 → 统计 → 横向分析」已废止;
> 那一版里仍然有效的四篇讲义移到 `../_deferred/`,会在 W2/W3/W7/W8 重新启用。

## 本周唯一目标

> **拿到任何 agent benchmark repo,我可以从源码追通:**
> ```
> task → environment → agent → rollout → verifier → result
> ```

## 本周不学什么(重要)

```
❌ 统计学(pass@k / CI / 显著性)     → Week 3
❌ 组件级 evaluation 与 trace        → Week 2
❌ 权重、聚合、leaderboard           → Week 8
❌ 「这个 benchmark 好不好」         → Week 5 / Week 7
```

> **理由**:先知道「一个 observation 到底是什么」,统计和聚合才有上下文。
> 一上来讲 Wilson 区间,是在给一个你还没见过的东西算误差棒。

---

## 六天

| Day | 内容 | 最终必须能回答 | 讲义 |
|---|---|---|---|
| **1** | Benchmark anatomy overview | GAIA / BFCL / SWE / τ³ / TBench / OSWorld 有什么**结构差异**? | [`lesson01.md`](lesson01.md) ✅ |
| **2** | ⭐ Terminal-Bench + Harbor | task / environment / agent / verifier 到底**怎么接起来**? | [`lesson02.md`](lesson02.md) ✅ |
| **3** | ⭐ SWE-bench | dataset、agent runner、evaluation harness **为什么是三件事**? | `lesson03-swe-bench.md` ⏳ |
| **4** | ⭐ τ³-bench | user simulator、mutable state、tools、grader **如何工作**? | `lesson04-tau3-bench.md` ⏳ |
| **5** | OSWorld / WebArena | GUI/browser environment 如何 **reset 和验证**? | `lesson05-osworld-webarena.md` ⏳ |
| **6** | **Build a tiny benchmark** | 自己做一个**能真正运行**的 benchmark | `lesson06-build-your-own.md` ⏳ |

---

## 复杂度递进(本周的知识地图)

```
GAIA            question → answer
BFCL            request → structured action
SWE-bench       issue → repo mutation → executable verifier
τ³-bench        conversation → tool calls → application state
Terminal-Bench  instruction → arbitrary computer state
OSWorld         visual observation → computer actions → application state
```

每个 benchmark 的**核心状态**不同,这才是要学的东西:

| Benchmark | 核心是什么 state |
|---|---|
| SWE-bench | **repo state + executable tests** |
| τ³-bench | **application state + user state + conversational trajectory** |
| Terminal-Bench | **arbitrary computer state** |
| OSWorld | **GUI / whole-machine state** |

---

## Day 3 · SWE-bench —— 三件事为什么必须分开

**核心命题**:
> **SWE-bench evaluator ≠ SWE-bench agent environment。**

```
                 SWE-bench dataset
                        │
        ┌───────────────┼───────────────┐
        │                               │
 problem_statement                 hidden eval info
 repo / base_commit                test_patch
        │                           FAIL_TO_PASS
        ▼                           PASS_TO_PASS
┌──────────────────┐                      │
│ Agent Runtime    │                      │
│ repo checkout    │                      │
│ shell/editor     │                      │
│ network policy   │                      │
└────────┬─────────┘                      │
         │                                │
    model_patch                           │
         └───────────────┬────────────────┘
                         ▼
              ┌─────────────────────┐
              │ SWE-bench Harness   │
              │ Docker              │
              │ apply patch         │
              │ apply tests         │
              │ execute tests       │
              │ parse results       │
              └──────────┬──────────┘
                         ▼
                    resolved?
```

**四个亲手实验**(P1 checkpoint；先做 lab,再写讲义):
```
1. 跑 gold patch          → 确认 evaluator 本身能工作
2. 跑 empty / 错误 patch  → 看 unresolved
3. 改 prediction 但保持同一 run_id → 观察 result caching 这个坑
4. 打开 container         → 看 agent-visible repo 与 grader-visible test_patch 的差别
```
📁 lab:`../labs/swe-bench-teardown/`

---

## Day 4 · τ³-bench —— 要学的是 **State**

```
Task
 ├── initial_state
 ├── user_scenario
 └── expected behavior
        ↓
User Simulator ←→ Agent
                   ↓  Tools
                   ↓  mutable DB state
                   ↓  Evaluator
```

**专门追一次这条链**(不要泛读论文):
```
agent tool call → Python function → domain state mutation → final evaluator
```
τ³ 现在有 `banking_knowledge`,含可配置 RAG、document search、embedding、agentic shell search,
并提供 **Gym-compatible interface** 用于 train/eval。
> 这为后面的 `evaluation ↔ RL` 埋伏笔 —— **但本周不展开 RL**。

---

## Day 5 · OSWorld / WebArena —— Observation–Action Loop

第一次从
```
tool_call(...)
```
转向
```
screenshot → model → mouse / keyboard action → new screenshot
```

**重点不是分数,是读这六样**:
```
environment initialization · snapshot/reset · observation
action space · app/browser state · evaluator 怎么定位最终 UI/application state
```

---

## Day 6 · 自己造一个 benchmark(P1 checkpoint)

> **repo 现在 lesson 很多、lab 太少。这一天不写讲义,写代码。**

```
labs/hello-bench/
├── tasks/
│   ├── create-file/
│   │   ├── task.yaml
│   │   ├── Dockerfile
│   │   ├── solution.sh
│   │   └── tests/
│   └── start-server/
├── agent.py
├── runner.py
└── README.md
```

**两道题**:
```
① Create /workspace/result.txt containing 42
② Start an HTTP server on port 8080 that returns "hello"
```

**要实现的五个抽象**:
```python
@dataclass
class Task:
    instruction: str
    image: str
    verifier: str

@dataclass
class Result:
    success: bool
    trajectory: list
    duration: float
```
`Task · Environment · Agent · Verifier · Result`

**跑通这条链**:
```
load task → start Docker → give instruction to agent
→ agent executes shell commands → run hidden pytest → Result(success=True)
```

> 允许非常简陋。**跑通比漂亮重要。**

---

## 本周验收

```
[ ] 1. 能画出 task → environment → agent → rollout → verifier → result,并对六个 benchmark 各填一遍
[ ] 2. 能说出每个 benchmark 的「核心 state」是什么
[ ] 3. 能解释 SWE-bench 为什么 dataset / agent runtime / evaluation harness 是三件事
[ ] 4. 能追通 τ³ 的 tool call → state mutation → evaluator
[ ] 5. 能说出 GUI benchmark 怎么 reset 和验证
[ ] 6. ⭐ 自己的 hello-bench 能跑通,且 oracle 满分、空 patch 零分
```

---

## 素材(全部本地)
```
code/terminal-bench      · code/tau2-bench   · code/OSWorld-V2 · code/gorilla(BFCL)
../agent-sandbox-course/code/SWE-bench       · ../llm-rl-course/code/harbor
papers/{gaia,swebench,tau_bench,webarena}.pdf
```
