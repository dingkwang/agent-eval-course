# AI Coding Agent Benchmarks & Leaderboard | Artificial Analysis

source: https://artificialanalysis.ai/agents/coding-agents
fetched: 2026-08

---

Artificial Analysis
Models
Coding Agents
Speech, Image, Video
Inference
Leaderboards
About
AI Trends
Arenas
Premium
Log in
Artificial Analysis Coding Agent Benchmarks

We measure real-world performance of coding agents on software engineering tasks, including cost, token usage, and execution time. We compare how performance changes across agents, models, and execution settings.

To compare language models see our model benchmarks.

Benchmarks
Comparisons
Features
Artificial Analysis Coding Agent Index

Composite index of 3 benchmarks:

DeepSWE
Software engineering tasks, 113 tasks
By Datacurve
Terminal-Bench v2
Agentic terminal use, 84 tasks
By Laude Institute
SWE-Atlas-QnA
Technical Q&A, 124 tasks
By Scale AI

Each benchmark score averages pass@1 across three attempts per task. The Index gives equal weight to its 3 benchmark components. See methodology for scoring details and version history.

Coding Agents
General Work
Chatbots
Presentations
OCR
Data Analysis
Customer Support

Highlights

Coding Agent Index
Artificial Analysis Coding Agent Index v1.3 · Higher is better
Claude Code - Opus 5 (xhigh)
Codex - GPT-5.6 Sol (max)
Claude Code - Fable 5 (max) (with fallback)
Grok Build - Grok 4.5 (high)
Kimi Code CLI - Kimi K3
Opencode - Muse Spark 1.1 (xhigh)
Opencode - Gemini 3.6 Flash (high)
Claude Code - GLM-5.2
Cursor CLI - Composer 2.5 Fast
Claude Code - DeepSeek V4 Pro (high)
67
67
66
64
61
54
46
43
38
31
Time per Task
Average agent wall time per task · Lower is better
Cursor CLI - Composer 2.5 Fast (Cursor)
Codex - GPT-5.6 Sol (max) (OpenAI)
Opencode - Gemini 3.6 Flash (high) (Google)
Opencode - Muse Spark 1.1 (xhigh) (Meta)
Grok Build - Grok 4.5 (high) (SpaceXAI)
Claude Code - DeepSeek V4 Pro (high) (DeepSeek)
Claude Code - Fable 5 (max) (with fallback) (Anthropic)
Claude Code - Opus 5 (xhigh) (Anthropic)
Kimi Code CLI - Kimi K3 (Moonshot AI)
Claude Code - GLM-5.2 (Novita)
6.8m
10.2m
10.4m
12.6m
16.5m
17.9m
23.4m
23.6m
23.8m
25.1m
Cost per Task
Average API cost per task (USD) · Lower is better
Claude Code - DeepSeek V4 Pro (high) (DeepSeek)
Cursor CLI - Composer 2.5 Fast (Cursor)
Opencode - Muse Spark 1.1 (xhigh) (Meta)
Opencode - Gemini 3.6 Flash (high) (Google)
Grok Build - Grok 4.5 (high) (SpaceXAI)
Kimi Code CLI - Kimi K3 (Moonshot AI)
Claude Code - GLM-5.2 (Novita)
Codex - GPT-5.6 Sol (max) (OpenAI)
Claude Code - Opus 5 (xhigh) (Anthropic)
Claude Code - Fable 5 (max) (with fallback) (Anthropic)
$0.27
$0.55
$1.43
$2.08
$2.59
$3.18
$6.51
$7.08
$8.23
$11.7
Performance
Harness Comparison
Token Usage
Cost
Execution Time
Performance

Performance across the Artificial Analysis Coding Agent Index.

Index
Score by Benchmark
DeepSWE
Terminal-Bench v2
SWE-Atlas-QnA
Artificial Analysis Coding Agent Index
Artificial Analysis Coding Agent Index v1.3 incorporates 3 benchmarks: DeepSWE, Terminal-Bench v2, and SWE-Atlas-QnA · Higher is better
Color by
Model
Agent
15 of 53 models
NEW
Since benchmarking, we have observed a higher rate of content safety filtering on this endpoint.
What This Metric Means

The Artificial Analysis Coding Agent Index is a composite score built from DeepSWE, Terminal-Bench v2, and SWE-Atlas-QnA.

It is useful for quick comparison, but it should be read alongside the per-eval breakdowns. Two agents with similar index values can still have different strengths across repository tasks, terminal workflows, and rubric-based evaluations.

Harness Comparison

Artificial Analysis Coding Agent Index by harness for Claude Opus 4.7.

Artificial Analysis Coding Agent Index
DeepSWE
Terminal-Bench v2
SWE-Atlas-QnA
Harness Comparison: Artificial Analysis Coding Agent Index
Composite average pass@1 across Claude Code, Cursor CLI, and Opencode for Claude Opus 4.7 · Higher is better
What This Chart Shows

This chart holds the underlying model constant at Claude Opus 4.7 and compares how it performs across different coding-agent harnesses, including Cursor, Claude Code, and OpenCode.

Token Usage

Token consumption across the Artificial Analysis Coding Agent Index, including total usage, token mix, efficiency, and per-benchmark breakdowns.

Token Usage
Token Distribution
Cache Hit Rate
Input vs. Output
Tokens by Benchmark
Token Usage per Task
Average input, cache, and output tokens per task
15 of 53 models
NEW
Output
Cached Input
Input
Prompt cache hit rates can vary significantly by provider routing, which can materially change effective cost.
Input Tokens

Non-cached input tokens sent to the model, including prompts, instructions, tool context, and task context that were not served from prompt cache.

3 more notes
Artificial Analysis Coding Agent Index vs. Total Tokens
Artificial Analysis Coding Agent Index vs. average total tokens per task
Color by
Model
Agent
15 of 53 models
NEW
Most attractive quadrant
Anthropic
OpenAI
SpaceXAI
Moonshot AI
Meta
Google
Z.ai
Cursor
DeepSeek
How to Read This Chart

Each point represents a coding-agent variant. Farther left means lower average total token usage per task, while higher on the chart means higher benchmark performance. Agents toward the upper-left achieve stronger results with fewer tokens.

Cost

Cost across the Artificial Analysis Coding Agent Index based on current per-token API pricing, including cache write pricing and cache discounts where available. Many users will access coding agent harnesses through subscription plan offerings rather than pay-per-token.

Cost to Run
Cost Distribution
Total Cost
Cost per Task
Average pay-per-token API cost per task (USD) · Lower is better
Color by
Model
Agent
15 of 53 models
NEW
What Cost Is Measuring

This chart shows the average pay-per-token API cost per task across the Artificial Analysis Coding Agent Index, spanning DeepSWE, Terminal-Bench v2, and SWE-Atlas-QnA.

Where applicable, that cost model includes standard input pricing, discounted cached-input pricing, separate cache-write charges, and output pricing rather than treating all prompt tokens as if they were billed at the same uncached input rate.

It is intended to show pay-per-token API cost, not consumer plan pricing or the full operational cost of deploying the system in production. Infrastructure, engineering, and supervision costs are not the focus of this metric.

Artificial Analysis Coding Agent Index vs. Cost per Task
Artificial Analysis Coding Agent Index vs. average pay-per-token API cost per task (USD)
Color by
Model
Agent
15 of 53 models
NEW
Most attractive quadrant
Pareto line
Anthropic
OpenAI
SpaceXAI
Moonshot AI
Meta
Google
Z.ai
Cursor
DeepSeek
How to Read This Chart

Each point represents a coding-agent variant. Farther left means lower average cost per task, while higher on the chart means higher benchmark performance. The most efficient agents sit toward the upper-left: stronger results at lower cost.

Execution Time

Active agent runtime across the Artificial Analysis Coding Agent Index.

Execution Time
Turns
Time per Task
Average agent wall time per task · Lower is better
Color by
Model
Agent
15 of 53 models
NEW
What Execution Time Is Measuring

This chart uses agent wall time: how long the agent process was actively running on each task.

It does not include environment startup, verifier or judge time, or other harness overhead, so it is a cleaner comparison of how long the agent itself was working.

Artificial Analysis Coding Agent Index vs. Execution Time
Artificial Analysis Coding Agent Index vs. average agent wall time per task
Color by
Model
Agent
15 of 53 models
NEW
Most attractive quadrant
Anthropic
OpenAI
SpaceXAI
Moonshot AI
Meta
Google
Z.ai
Cursor
DeepSeek
How to Read This Chart

Each point represents a coding-agent variant. Farther left means shorter average agent runtime per task, while higher on the chart means higher benchmark performance. Agents toward the upper-left deliver stronger results in less active agent time.

Run Specifications
Frequently Asked Questions
What is the Artificial Analysis Coding Agent Index?

The Artificial Analysis Coding Agent Index is our composite score for coding-agent performance across the public benchmark suite on this page. It combines DeepSWE, Terminal-Bench v2, and SWE-Atlas-QnA to capture implementation, terminal workflow, repository-understanding, and broader software-engineering performance in a single headline metric.

Which benchmarks are included in the index right now?

The current public index includes DeepSWE, Terminal-Bench v2, and SWE-Atlas-QnA. These benchmarks are combined because they stress different parts of the coding-agent workflow rather than repeating the same task format.

What kinds of tasks are these benchmarks actually testing?

The public benchmark suite mixes several software engineering task styles. Some tasks are Q&A and repository-understanding tasks that focus on reading a codebase, understanding architecture or behavior, and producing a correct technical answer. Some are implementation and bug-fix tasks that require code changes and are closer to the classic make-a-patch-that-works framing. Some are terminal workflow tasks that test whether the agent can navigate a shell-driven environment, execute tools correctly, and complete a multi-step command-line workflow. All three current benchmarks use binary task outcomes.

How do Q&A-style tasks differ from implementation-style tasks?

Q&A-style tasks emphasize repository understanding, code reading, tracing behavior, and producing a correct technical explanation. Implementation-style tasks are closer to shipping a working change: the agent has to understand the task, navigate the repository, edit files correctly, and satisfy an evaluator or test-based outcome under execution constraints. Those are related capabilities, but they are not identical. An agent can be strong at repository reasoning and still be weaker at reliable patch execution, or vice versa, which is one reason the composite index should be interpreted alongside the per-benchmark chart.

How are agents scored on each benchmark?

The benchmark page reports task-normalized average pass@1. For each benchmark, we first average the three evaluated attempts for each task, then average those task-level scores so every task has equal weight. All current component outcomes are binary. An attempt can complete cleanly and still score zero when it does not satisfy its verifier. SWE-Atlas-QnA binary pass/fail scoring is aligned with Scale AI's Task Resolve Rate methodology.

How is the overall index weighted?

The index is computed from DeepSWE, Terminal-Bench v2, and SWE-Atlas-QnA. For the current Artificial Analysis Coding Agent Index, the public methodology is a simple average across those benchmark scores. Benchmark methodology can evolve as coverage improves, so comparability is best interpreted within the published benchmark suite and its current component set rather than as a timeless absolute score.

What does execution time mean?

Execution time on this page refers to average wall-clock task runtime per task, not just raw model latency. It is meant to reflect the user-facing time cost of running the whole agent workflow. That includes time spent reasoning, issuing tool calls, reading and writing files, executing shell steps, and waiting on model responses. So an agent can have a fast underlying model and still be slower overall if its workflow is longer or more tool-heavy.

What does token usage mean, and why does it matter?

Token usage is the average observed token consumption per task across the benchmark suite. On this page we break it out into input, cache, and output tokens. Input tokens are the tokens sent into the model, including prompts, instructions, tool context, and task context. Cache tokens are prompt tokens reused through prompt caching when the provider exposes that telemetry. Output tokens are tokens generated by the model in its response. Token usage matters because it often drives cost and can also indicate how much context an agent consumes to get work done, but token efficiency and cost are not identical because providers price token categories differently and caching can materially change the bill.

Why can a higher-index agent still be worse for my use case?

A higher index score means stronger performance across the included benchmark mix, but it does not mean the agent is best for every workflow. The index is a balance across benchmark quality, not a direct measure of your specific latency, cost, tooling, or task-type priorities. Real-world choice still depends on whether your workflow looks more like repository Q&A, patching, or terminal execution, and on practical constraints such as IDE integration, model availability, and reliability.

How realistic are these tasks, and what setup was used for each agent?

These benchmarks measure coding-agent performance across repositories, tools, multi-step workflows, and evaluator-based outcomes. Results on this page reflect specific evaluated agent variants, not just generic product names: model choice, settings, and execution configuration can materially change outcomes, which is why a single agent family may appear in multiple variants in the results. For more background on benchmark runs, task-level scoring, and methodology, see the coding-agents benchmarking methodology page. View the coding-agents benchmarking methodology

Get notified about new articles

Email address
Subscribe

Artificial Analysis

Explore

LLM Leaderboard
Image Arena
Video Arena
AI Agents
Evaluations

Company

Methodology
Services
Contact
Articles
FAQ
X
LinkedIn
YouTube
Rednote
Discord

© 2026 Artificial Analysis

Terms of Use
Privacy Policy
English
