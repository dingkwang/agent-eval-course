# Week 1 讲义 — Evaluation 基本框架

> 6 天 × 1 小时。逐日安排见 `PLAN.md`,讲义正文在下面六个文件。
> **所有数字均已对本地素材快照逐条核验**;未能核验的显式标注为「待确认 / 推断」。

| Day | 讲义 | 类型 | 主命题 |
|---|---|---|---|
| **1** | [`lesson01.md`](lesson01.md) | 源码 | Benchmark Anatomy:六个 benchmark 的复杂度阶梯 |
| **2** | [`lesson02.md`](lesson02.md) | **源码** | **Terminal-Bench 深读**:从 task 定义一路追到 score |
| **3** | [`lesson03.md`](lesson03.md) | 概念 | 组件级 evaluation 与 trace:任务失败时,**哪一环**失败了? |
| **4** | [`lesson04.md`](lesson04.md) | 写作 | 为什么 agent 分数不是 model 分数 |
| **5** | [`lesson05.md`](lesson05.md) | 编码 | 这个分数能不能信?Bernoulli · 标准误 · Wilson CI |
| **6** | [`lesson06.md`](lesson06.md) | 分析 | 三个 agent benchmark 横向解剖 + 怎么 game 它 |

## 贯穿本周的两个公式

```
① 测得的性能 = Model × Agent Harness × Environment × Task Distribution × Budget × Scorer × Randomness
                        ↑ 七个因子里只有一个是 model

② 四种评价单位 = turn(单步对不对) · trajectory(过程好不好)
              · task(最终成没成) · session(跨轮/跨用户是否安全)
```

## 代码
```bash
python3 ../labs/wilson.py     # Day 5:Wilson vs 正态近似,四组真实输出
```

## 本周产出清单
```
[ ] notes/day1-aa-benchmark-catalog.md        Day 1  九项 evaluation 解剖表 + 3 个疑问
[ ] notes/day2-terminal-bench-source-map.md   Day 2  Terminal-Bench 源码地图
[ ] notes/day3-component-eval.md              Day 3  3 概念 / 2 疑问 / 1 案例
[ ] sec1-why-agent-score-is-not-model-score.md Day 3 800–1,200 字自写讲义
[ ] notes/day5-ci-findings.md                 Day 5  三个结论 + 扩展代码
[ ] sec2-benchmark-teardown.md                Day 6  另选三个 benchmark 的解剖表
[ ] notes/day6-next-week-questions.md         Day 6  5 个下周问题
[ ] figures/evaluation-stack.txt              本周交付:完整 evaluation stack 图
```

## 核心素材(全部本地)
```
docs/aa-intelligence-benchmarking-methodology.md   ⭐ Day 1·3·5(v4.1.1 官方口径)
docs/aa-coding-agents-leaderboard.md               Day 3(同模型不同 harness)
docs/aa-evaluations.md                             Day 5
papers/survey_agent_eval_2025.pdf                  Day 2(arXiv 2503.16416)
papers/error_bars_in_evals.pdf                     ⭐ Day 4(arXiv 2411.00640)
papers/codex_passk.pdf                             Day 4(pass@k 出处)
papers/tau_bench.pdf · papers/swebench.pdf         Day 5
```

## 本周一句话

> **不要把 benchmark 当作一套题;要把它看成一套由「任务分布 + 执行环境 + agent harness + 资源预算 + 随机过程 + 评分器 + 统计聚合」共同组成的测量系统。**
