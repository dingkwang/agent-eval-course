# 素材清单(已下载并**逐一核验** · 2026-08)

> 铁律沿用:每节结论**锚定原始素材**——📄 论文小节/图号 · 💻 代码 `file:line` · 🌐 抓取页(含来源 URL + 抓取日期)。
> 计划见 `PLAN.md`,第一周见 `week01/PLAN.md`。

## 📄 papers/(10 篇 · 标题已逐一核对,arXiv 号无误)

| 文件 | 论文(核验过的真实标题) | arXiv | 用在 |
|---|---|---|---|
| `survey_agent_eval_2025.pdf` | A Survey on Evaluation of LLM-based Agents | 2503.16416 | W1D2 · 全课地图 |
| ⭐ `error_bars_in_evals.pdf` | **Adding Error Bars to Evals**: A Statistical Approach to LM Evaluation | 2411.00640 | **W4 统计I** · W1D4 |
| `codex_passk.pdf` | Evaluating Large Language Models Trained on Code(pass@k 出处) | 2107.03374 | W4 |
| `llm_as_judge_mtbench.pdf` | Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | 2306.05685 | W5 judge |
| `chatbot_arena.pdf` | Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference | 2403.04132 | W5 Elo/BT 排名 |
| `gaia.pdf` | GAIA: A Benchmark for General AI Assistants | 2311.12983 | W8 |
| `swebench.pdf` | SWE-bench: Can Language Models Resolve Real-World GitHub Issues?(ICLR'24) | 2310.06770 | W8 · W1D5 |
| `tau_bench.pdf` | τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains | 2406.12045 | W8 · W1D5 |
| `webarena.pdf` | WebArena: A Realistic Web Environment for Building Autonomous Agents(ICLR'24) | 2307.13854 | W8 |
| ⭐ `kimi_k3.pdf` | **Kimi K3: Open Frontier Intelligence**(47 页,2026-07-27) | **2607.24653** | **W11 case study** |

### Kimi K3 内容核验(W11 要引,已确证在正文中)
| 机制 | 命中次数 |
|---|---|
| partial rollout | 5 |
| AgentENV | 7 |
| generative reward model | 2 |
| multi-teacher / on-policy distillation | 5 / 6 |
| resumable microVM · snapshot | 3 / 5 |
| independent verifier | 8 |
| reasoning effort | 14 |

> 原文摘录(§ 系统): *"For million-token agentic RL, our co-located system combines **partial rollouts, external KV-cache retention, adaptive throttling and resumable microVM sandboxes** to preserve long-lived model and environment state."*

## 🌐 docs/(Artificial Analysis 快照 · headless 渲染抓取)

| 文件 | 内容 | 用在 |
|---|---|---|
| ⭐ `aa-intelligence-benchmarking-methodology.md` (116k字) | Intelligence Index 完整口径 | W1D1 · W2 |
| `aa-evaluations.md` (6k字) | AA 的 agent evaluations 总览 | W1D5 · W2 |
| `aa-coding-agents-leaderboard.md` (13k字) | Coding Agent Index:等权组合、每任务 3 次、task-normalized pass@1、**同模型不同 harness 对比** | W1D3 · W2 |

**已核验的关键数字**(W2 整周建立其上):
```
Intelligence Index v4.1.1
Agents 34% · Coding 24% · Scientific Reasoning 24% · General 18%
提及次数:GDPval 17 · Terminal-Bench 16 · Harvey 14 · AutomationBench 10
         ITBench 8 · AA-Briefcase 8 · SciCode 7 · EnterpriseOps 7 · APEX 6
```

来源 URL:
```
https://artificialanalysis.ai/methodology/intelligence-benchmarking
https://artificialanalysis.ai/evaluations
https://artificialanalysis.ai/agents/coding-agents
```

## 🔗 跨课复用(不重复下载)
| 资源 | 位置 | 用在 |
|---|---|---|
| **Harbor**(Terminal-Bench 团队 eval infra;`--n-concurrent`、Daytona/Modal、rewardkit、RL rollouts) | `../llm-rl-course/code/harbor` | W6 · W7 · W10 |
| **Inspect AI**(task/solver/scorer + sandbox lifecycle) | `../agent-sandbox-course/code/inspect_ai` | W6 · W9 |
| **SWE-bench harness** | `../agent-sandbox-course/code/SWE-bench` | W7 · W8 |
| **Anthropic *Demystifying evals for AI agents*** | `../agent-sandbox-course/docs/agentic/anthropic-demystifying-evals.md` | W1 · W9 |
| **Anthropic *Quantifying infrastructure noise*** | `../agent-sandbox-course/docs/agentic/anthropic-infra-noise.md` | W9 · W12 |
| sandbox / microVM / cgroups 全套 | `../agent-sandbox-course/docs/` | W7 |

## 🌐 在线(未下载)
| 资源 | 原因 |
|---|---|
| DeepLearning.AI *Evaluating AI Agents* | 需注册的视频课(W1D2;可用 survey 论文替代) |
| HuggingFace Agents Course · LangChain Academy · W&B 课程 | 在线课程,按需 |
| AA 排行榜实时数据 | 持续更新,快照仅作教学口径参考 |

## ⚠️ 注意
- AA 页面是 **2026-08 快照**,分数会变;引用时标明抓取日期,**不要把快照数字当当前值**。
- `kimi_k3.pdf` 晚于我的训练截止 —— 课程里所有关于它的陈述都来自**这份 PDF 原文**,不是记忆。
