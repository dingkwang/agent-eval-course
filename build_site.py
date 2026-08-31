"""Render intro (index.html), catalog (toc.html), and markdown lessons into site/.

Lesson markdown may include ```diag blocks (pipe, flow, compare, nest, grid)
and `$$ ... $$` (or ```math) display equations. Diagrams and math are expanded
before Markdown so `_` inside TeX is not eaten as emphasis.

Run from the course root:  python3 build_site.py
"""

import re
from shutil import copyfile
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
SRC = ROOT / "week01"
SRC_W2 = ROOT / "week02"
SRC_W3 = ROOT / "week03"
SRC_W4 = ROOT / "week04"
SRC_W5 = ROOT / "week05"
SRC_PROJECTS = ROOT / "projects"
OUT = ROOT / "site"

# (slug, day, title, desc, tag, source .md — None = 尚未写)
LESSONS = [
    ("lesson01", "1", "Benchmark Anatomy", "六个 benchmark 的复杂度阶梯", "总览", "lesson01.md"),
    ("lesson02", "2", "Terminal-Bench 深读", "从 task 定义一路追到 score", "源码", "lesson02.md"),
    ("lesson03", "3", "SWE-bench", "Dataset / Runtime / Harness 为什么必须分开", "源码 + 实验", "lesson03-swe-bench.md"),
    ("lesson04", "4", "τ³-bench", "reward_basis 选出 verifier 再相乘;User LLM 在尺子里", "源码", "lesson04-tau3-bench.md"),
    ("lesson05", "5", "OSWorld · WebArena", "把整台机器当 environment", "源码", "lesson05-osworld-webarena.md"),
    ("lesson06", "6", "造一个自己的 benchmark", "五个抽象亲手写一遍", "编码", None),
]

# Week 1 labs actually run. Shown under W1 on the course homepage.
LABS = [
    ("labs/swe-bench-teardown/", "SWE-bench Teardown",
     "同一个 harness,四种 prediction → resolved / unresolved / empty patch / error",
     "Day 3 · 已跑通"),
    ("labs/tau3-verifier/", "τ³ verifier teardown",
     "四条手写轨迹喂进官方 evaluator;cheat 在 airline id=3 上 reward=1.0",
     "Day 4 · 已跑通"),
    ("labs/hello-bench/", "hello-bench",
     "290 行写完 Task→Environment→Agent→Verifier→Result;cheat agent 在弱 verifier 下 PASS、强 verifier 下 fail",
     "Day 6 · 已跑通"),
]

# 12-week map (PLAN.md §三). href is None until that week has pages.
# status: None = not started; string shown on the row.
WEEKS = [
    ("1", "Popular Benchmark Anatomy",
     "拿到 repo,源码追通 task → environment → agent → rollout → verifier → result",
     "5/6", True),
    ("2", "Eval Runtime & Trajectory Engineering",
     "不同 benchmark / Agent / backend 怎么经同一个 runtime 正确跑?Trajectory 是可重放事件日志,不是聊天记录",
     "2/5", False),
    ("3", "Statistical Inference for Stochastic Agent Evals",
     "从 Trial observations 到可信结论:估计什么、不确定性多大、A 是否真的优于 B?",
     "4/4", True),
    ("4", "Scorer Validation for Agent Evals",
     "从 executable outcome 到开放式作品:scorer 真的测到了成功或质量吗?",
     "3/5", True),
    ("5", "Benchmark Design, Task QA & Dataset Lifecycle",
     "从 capability claim 到 task set:成功/失败为什么能代表目标能力?", "2/5", True),
    ("6", "Reproducibility, Failure Semantics & Experiment Operations",
     "同一 Agent、同一 benchmark,为什么改一点 infra 分数就变?哪些失败进分母?", None, False),
    ("7", "Evaluation Integrity & Adversarial Validation",
     "怎样防止 Agent、数据和基础设施破坏测量本身?(不讲 cgroups / seccomp)", None, False),
    ("8", "Leaderboard / Aggregation / Artificial Analysis",
     "成千上万个 task result 怎么压成一个数字?", "plan exists", False),
    ("9", "Production / Online Evaluation",
     "这个数字跟真实产品表现有什么关系?", None, False),
    ("10", "Evaluation ↔ On-policy RL",
     "同一套 environment 怎么同时服务 eval 与训练?", None, False),
    ("11", "Kimi K3 / AgentENV / Harbor RL Case Study",
     "前沿是怎么把这些拼在一起的?", None, False),
    ("12", "Capstone Benchmark",
     "自己从零做一个可运行、可复现、可评分的 benchmark", None, False),
]

# Week 2: 4 lectures + 1 lab. slug w2-0N so it does not collide with W1 lesson01.html.
W2_LESSONS = [
    ("w2-01", "1", "从 Eval Spec 到可执行 Trial", "JobPlan 编译,不是开跑", "源码",
     "lesson01-eval-spec-to-trial.md"),
    ("w2-02", "2", "Agent / Environment / Trial 协议", "换实现后仍是同一个实验", "源码",
     "lesson02-protocol-boundary.md"),
    ("w2-03", "3", "Trajectory / 因果 / 副作用", "没收到 response 时怎么记", "源码", None),
    ("w2-04", "4", "并发与 Runtime Correctness", "并发不改变实验语义", "源码", None),
    ("w2-05", "5", "EvalRT Core", "五个强不变量", "lab", None),
]

# Week 3: statistical inference for stochastic agent evals.
W3_LESSONS = [
    ("w3-01", "1", "Observation、Experimental Unit 与 Estimand",
     "一行数据是什么,这个数字要推广到哪里", "统计",
     "lesson01-observation-estimand.md"),
    ("w3-02", "2", "Repeated Trials", "Capability vs Reliability", "统计",
     "lesson02-capability-reliability.md"),
    ("w3-03", "3", "Uncertainty for Structured Eval Data",
     "CI 必须重采样 estimand 的随机单位", "统计 + lab",
     "lesson03-uncertainty-structured-data.md"),
    ("w3-04", "4", "Paired Comparison、Power 与 Statistical Eval Report",
     "A 是否真的优于 B,证据是否足以支持决策", "统计 + report lab",
     "lesson04-paired-comparison-report.md"),
]

# Week 4: treat the scorer itself as a system under evaluation.
W4_LESSONS = [
    ("w4-01", "1", "Scorer Is a Measurement Instrument",
     "score 不是 ground truth;先写 measurement contract", "方法",
     "lesson01-scorer-measurement-instrument.md"),
    ("w4-02", "2", "Deterministic Verifiers",
     "确定性不等于判得正确", "源码 + 审计",
     "lesson02-deterministic-verifiers.md"),
    ("w4-03", "3", "LLM-as-a-Judge for Open-Ended Artifacts",
     "文学写作没有 gold answer 时,judge 究竟代表谁", "judge + lab",
     "lesson03-open-ended-artifacts.md"),
    ("w4-04", "4", "Gold Set 与 Calibration",
     "用 reference labels 测量 scorer error", "统计", None),
    ("w4-05", "5", "Scorer Audit Report",
     "错误是否足以改变发布结论", "lab", None),
]

# Week 5: validate the benchmark's capability claim, task distribution, and tasks.
W5_LESSONS = [
    ("w5-01", "1", "From Capability Claim to Benchmark Blueprint",
     "先写 validity argument,再收集 task", "方法 + 源码",
     "lesson01-capability-to-benchmark-blueprint.md"),
    ("w5-02", "2", "Task Validity & Construct-Irrelevant Difficulty",
     "低通过率为什么能归因给目标能力", "方法 + 审计",
     "lesson02-task-validity-difficulty.md"),
    ("w5-03", "3", "Benchmark QA Is a Sampling Problem",
     "自动筛查漏掉的坏题怎样被看见", "审计 + 统计", None),
    ("w5-04", "4", "Release, Versioning & Retirement",
     "修题后还是不是同一个 benchmark", "生命周期", None),
    ("w5-05", "5", "Benchmark Release Candidate",
     "从 candidates 到 versioned release", "lab", None),
]

# Formal submissions. Lesson labs and exercises are checkpoints inside these
# projects; they are not separate assignments.
PROJECTS = [
    ("project-p1", "P1", "Eval Runtime Teardown", "W1–W2",
     "一个可运行的 mini benchmark + 可审计 runtime", "project01-eval-runtime-teardown.md"),
    ("project-p2", "P2", "Measurement Audit", "W3–W4",
     "统计推断与 scorer validity 合成一份 release audit", "project02-measurement-audit.md"),
    ("project-p3", "P3", "Benchmark Release Candidate", "W5–W7",
     "从 capability claim 到 versioned、adversarially-tested RC", "project03-benchmark-release-candidate.md"),
    ("project-p4", "P4", "Evaluation Decision Report", "W8–W11",
     "把 leaderboard evidence 转成采用、发布或训练决策", "project04-evaluation-decision-report.md"),
    ("project-c1", "C1", "Permission-Aware Multi-User Agent Benchmark", "W12",
     "课程 Capstone:权限正确、可运行、可评分的多用户 agent benchmark", "capstone-permission-aware-benchmark.md"),
]

# depth cross-section: the signature figure. depth = how much real environment.
STRATA = [
    ("GAIA", "task → answer", "无环境:只给题和答案", 0),
    ("BFCL", "task → structured tool call", "无环境:只判 call 结构", 1),
    ("SWE-bench", "task → patch → executable test", "容器化 evaluation;agent 自带", 2),
    ("τ³-bench", "task → interaction → mutable state", "领域数据库 + 模拟用户", 3),
    ("Terminal-Bench", "task → container → any command", "完整容器 + rollout 循环", 4),
    ("OSWorld", "task → whole computer", "整台机器:VM 生命周期", 5),
]

# In-lesson figure for §二. Each rung ADDS one layer of real environment —
# the chips accumulate, the newest one is highlighted. That accumulation is the
# whole point of the section, so it gets drawn rather than described.
LADDER = [
    ("GAIA", "task → answer", ["题目", "标准答案"]),
    ("BFCL", "task → structured tool call", ["工具 schema", "结构化 call"]),
    ("SWE-bench", "task → code change → executable test", ["代码仓库", "容器", "测试套件"]),
    ("τ³-bench", "task → interaction → tools → mutable state → verifier", ["可变状态库", "模拟用户", "多轮交互"]),
    ("Terminal-Bench", "task → agent → container → arbitrary commands → verifier", ["任意 shell", "rollout 循环"]),
    ("OSWorld", "task → agent → complete computer environment → verifier", ["整台机器", "GUI / 键鼠", "VM 生命周期"]),
]


_CJK = "零一二三四五六七八九"


def cjk_section_number(text: str) -> int | None:
    """`三、…` → 3, `十一、…` → 11. None if the heading isn't numbered."""
    head = text.split("、", 1)[0].strip() if "、" in text else ""
    if not head or any(c not in _CJK + "十" for c in head):
        return None
    if "十" not in head:
        return sum(_CJK.index(c) for c in head) if len(head) == 1 else None
    tens, _, ones = head.partition("十")
    return (_CJK.index(tens) if tens else 1) * 10 + (_CJK.index(ones) if ones else 0)


def _esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _figure(caption: str, inner: str) -> str:
    cap = (
        f'<figcaption><span>{_esc(caption)}</span></figcaption>'
        if caption else ""
    )
    return f'<figure class="diag">{cap}{inner}</figure>'


def render_diag(kind: str, caption: str, body: str) -> str:
    """Render a ```diag block. Kinds: pipe, flow, compare, nest, grid."""
    lines = [ln.rstrip() for ln in body.splitlines() if ln.strip()]
    if not lines:
        return ""
    if kind == "pipe":
        nodes = []
        for raw in re.split(r"\s*→\s*", " ".join(lines)):
            raw = raw.strip()
            if raw:
                nodes.append(f'<span class="dnode">{_esc(raw)}</span>')
        inner = '<span class="darr">→</span>'.join(nodes)
        return _figure(caption, f'<div class="dpipe">{inner}</div>')
    if kind == "flow":
        parts = []
        for i, ln in enumerate(lines):
            if i:
                parts.append('<div class="darr">↓</div>')
            if " → " in ln:
                bits = [p.strip() for p in ln.split(" → ")]
                inner = '<span class="darr">→</span>'.join(
                    f'<span class="dnode">{_esc(p)}</span>' for p in bits
                )
                parts.append(f'<div class="dpipe">{inner}</div>')
            else:
                parts.append(f'<div class="dstep">{_esc(ln)}</div>')
        return _figure(caption, f'<div class="dflow">{"".join(parts)}</div>')
    if kind == "compare":
        rows = [ln.split("|", 1) for ln in lines if "|" in ln]
        if not rows:
            return ""
        head, rest = rows[0], rows[1:]
        cols = []
        for i, title in enumerate(head):
            cells = "".join(
                f'<div class="dcell">{_esc(r[i].strip() if i < len(r) else "")}</div>'
                for r in rest
            )
            cols.append(
                f'<div class="dcol"><div class="dh">{_esc(title.strip())}</div>{cells}</div>'
            )
        return _figure(caption, f'<div class="dcmp">{"".join(cols)}</div>')
    if kind == "nest":
        def tree(items: list[tuple[int, str]]) -> str:
            if not items:
                return ""
            depth = items[0][0]
            chunks = []
            i = 0
            while i < len(items):
                d, label = items[i]
                if d != depth:
                    break
                j = i + 1
                while j < len(items) and items[j][0] > depth:
                    j += 1
                kids = tree(items[i + 1:j])
                chunks.append(
                    f'<div class="dbox"><div class="dlab">{_esc(label)}</div>{kids}</div>'
                )
                i = j
            return "".join(chunks)

        parsed = []
        for ln in body.splitlines():
            if not ln.strip():
                continue
            indent = len(ln) - len(ln.lstrip(" "))
            parsed.append((indent // 2, ln.strip()))
        return _figure(caption, f'<div class="dnest">{tree(parsed)}</div>')
    if kind == "grid":
        cells = []
        for ln in lines:
            if "|" in ln:
                k, v = ln.split("|", 1)
                cells.append(
                    f'<div class="gcell"><b>{_esc(k.strip())}</b>'
                    f'<span>{_esc(v.strip())}</span></div>'
                )
            else:
                cells.append(f'<div class="gcell"><b>{_esc(ln)}</b></div>')
        return _figure(caption, f'<div class="dgrid">{"".join(cells)}</div>')
    return _figure(caption, f'<pre class="draw">{_esc(body)}</pre>')


_DIAG = re.compile(r"```diag[ \t]*\n(.*?)```", re.S)
_MATH_HTML = re.compile(
    r'<pre><code class="language-math">(.*?)</code></pre>', re.S
)


_MATH_FENCE = re.compile(r"```math[ \t]*\n(.*?)```", re.S)
_MATH_DOLLARS = re.compile(r"(?<!\$)\$\$(.+?)\$\$(?!\$)", re.S)


def expand_math(md_text: str) -> str:
    """Turn ```math / $$ fences into MathJax display HTML before Markdown runs."""

    def to_html(tex: str) -> str:
        return (
            '\n\n<div class="math-display">\\[\n'
            + tex.strip()
            + '\n\\]</div>\n\n'
        )

    md_text = _MATH_FENCE.sub(lambda m: to_html(m.group(1)), md_text)
    return _MATH_DOLLARS.sub(lambda m: to_html(m.group(1)), md_text)


def expand_diagrams(md_text: str) -> str:
    """Turn ```diag blocks into figures before markdown runs."""

    def one(m: re.Match) -> str:
        raw = m.group(1)
        first, _, rest = raw.strip("\n").partition("\n")
        kind, _, cap = first.partition("|")
        kind = kind.strip() or "flow"
        caption = cap.strip()
        return render_diag(kind, caption, rest)

    return _DIAG.sub(one, md_text)


def render_math_blocks(html: str) -> str:
    """Turn fenced `math` code blocks into MathJax display equations.

    Python-Markdown intentionally treats unknown fenced languages as code. A
    post-processing step keeps the Markdown source portable while ensuring the
    generated site exposes the formula as math rather than a code sample.
    HTML entities stay escaped here; the browser decodes them before MathJax
    reads the text node.
    """

    return _MATH_HTML.sub(
        lambda match: (
            '<div class="math-display">\\['
            f'{match.group(1).strip()}'
            '\\]</div>'
        ),
        html,
    )


def ladder_figure() -> str:
    rows, carried = [], []
    for i, (name, flow, added) in enumerate(LADDER):
        old = "".join(f'<span class="chip old">{c}</span>' for c in carried)
        new = "".join(f'<span class="chip new">+ {c}</span>' for c in added)
        rows.append(
            f'<div class="rung"><div class="rn">{i}</div>'
            f'<div class="rbody"><div class="rhead"><b>{name}</b>'
            f'<code>{flow}</code></div>'
            f'<div class="chips">{old}{new}</div></div></div>'
        )
        carried += added
        if i == 2:
            rows.append(
                '<div class="wline"><span>▼ 现实水线</span>'
                "<span>以下:benchmark 自己启动并管理有状态环境</span></div>"
            )
    return (
        '<figure class="ladder"><figcaption><span>Benchmark Complexity ↓</span>'
        "<span>每下一级 = 多实例化一层现实</span></figcaption>"
        + "".join(rows)
        + '<div class="lfoot">灰色 = 上一级已有 · <b>橙色 = 这一级新增的现实</b> —— '
        "environment 越来越真,verifier 能查的状态越来越接近真实结果。</div></figure>"
    )


CSS = """
*{box-sizing:border-box}
:root{
  --paper:#EDEFF2; --panel:#F8FAFB; --panel-2:#E4E9ED; --rule:#C9D2D8;
  --ink:#131A20; --soft:#5A6672; --faint:#8A95A0;
  --deep:#0E1A22; --signal:#C8501C; --probe:#2B5F9E; --pass:#34734A;
  --shadow:0 1px 0 rgba(19,26,32,.04), 0 16px 40px -24px rgba(19,26,32,.45);
}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:"Instrument Sans",system-ui,sans-serif;font-size:16.5px;line-height:1.65;
  -webkit-font-smoothing:antialiased}
a{color:var(--probe)}
code,kbd{font-family:"JetBrains Mono",monospace;font-size:.88em;
  background:var(--panel-2);padding:.08em .38em;border-radius:3px}
pre{background:var(--deep);color:#DCE3E8;border-radius:8px;padding:16px 18px;overflow-x:auto;
  font-family:"JetBrains Mono",monospace;font-size:13px;line-height:1.72;box-shadow:var(--shadow)}
pre code{background:none;padding:0;color:inherit;font-size:inherit}
.wrap{max-width:1120px;margin:0 auto;padding:0 28px}

/* ---- masthead ---- */
.mast{border-bottom:1.5px solid var(--ink);background:var(--panel)}
.mast .wrap{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;
  padding-top:14px;padding-bottom:14px;flex-wrap:wrap}
.mast .id{font-family:"JetBrains Mono",monospace;font-size:11.5px;letter-spacing:.18em;
  text-transform:uppercase;color:var(--soft);white-space:nowrap;padding-top:6px}
.mast .id b{color:var(--signal);font-weight:500}
.mast .id-dot{color:var(--soft)}
.mast-nav{display:flex;flex-direction:column;align-items:flex-end;gap:6px}
.mast nav{display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end}
.mast nav a{font-family:"JetBrains Mono",monospace;font-size:12px;text-decoration:none;
  color:var(--soft);padding:4px 9px;border:1px solid transparent;border-radius:4px}
.mast nav a:hover{border-color:var(--rule);color:var(--ink)}
.mast nav a.on{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.mast-lessons a,.mast-lessons .soonnav{font-size:11.5px}

/* ---- hero ---- */
.hero{padding:62px 0 8px}
.eyebrow{font-family:"JetBrains Mono",monospace;font-size:12px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--signal);display:inline-flex;align-items:center;gap:11px}
.eyebrow::before{content:"";width:30px;height:2px;background:var(--signal)}
h1{font-family:"Archivo",sans-serif;font-weight:700;font-size:clamp(38px,6.4vw,74px);
  letter-spacing:-.025em;line-height:.97;margin:18px 0 12px}
.thesis{font-size:18px;color:var(--ink);max-width:38em;margin:0}
.thesis b{color:var(--signal)}
.subhead{font-family:"Archivo",sans-serif;font-weight:600;font-size:clamp(15px,2vw,19px);
  color:var(--soft);margin:0 0 18px}

/* ---- signature: depth cross-section ---- */
.strata{margin:34px 0 6px;border:1.5px solid var(--ink);border-radius:10px;overflow:hidden;
  box-shadow:var(--shadow)}
.strata .cap{background:var(--ink);color:var(--paper);padding:9px 16px;
  font-family:"JetBrains Mono",monospace;font-size:11.5px;letter-spacing:.15em;text-transform:uppercase;
  display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap}
.strata .cap span:last-child{color:#93A2AE}
.layer{display:grid;grid-template-columns:132px 1fr 300px;gap:0;align-items:center;
  border-top:1px solid var(--rule);background:var(--panel);
  transition:background .18s}
.layer:first-of-type{border-top:none}
.layer:hover{background:#fff}
.layer .nm{font-family:"Archivo",sans-serif;font-weight:600;font-size:15px;padding:13px 16px;
  border-right:1px solid var(--rule)}
.layer .flow{font-family:"JetBrains Mono",monospace;font-size:12.5px;color:var(--soft);padding:13px 16px}
.layer .note{font-size:13px;color:var(--soft);padding:13px 16px;border-left:1px solid var(--rule)}
.layer .bar{display:block;height:3px;background:var(--probe);border-radius:2px;margin-top:7px;
  transform-origin:left;animation:grow .7s cubic-bezier(.2,.7,.3,1) both}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.waterline{display:grid;grid-template-columns:132px 1fr;background:var(--deep);color:#9FB3C0;
  font-family:"JetBrains Mono",monospace;font-size:11.5px;letter-spacing:.1em}
.waterline span{padding:7px 16px}
.waterline span:first-child{color:var(--signal);border-right:1px solid #24333D}
.stratanote{font-size:13.5px;color:var(--soft);margin:11px 2px 0}

/* ---- lesson cards ---- */
.sec{padding:50px 0 0}
.sec h2{font-family:"Archivo",sans-serif;font-weight:600;font-size:clamp(21px,3.2vw,29px);
  letter-spacing:-.015em;margin:0 0 4px}
.sec .lede{color:var(--soft);font-size:15.5px;margin:0 0 20px}
.cards{display:grid;gap:12px}
.card{display:grid;grid-template-columns:64px 1fr auto;gap:18px;align-items:center;
  text-decoration:none;color:var(--ink);background:var(--panel);
  border:1.5px solid var(--ink);border-radius:9px;padding:17px 20px;
  transition:transform .16s,box-shadow .16s,background .16s}
a.card:hover{transform:translateX(4px);box-shadow:var(--shadow);background:#fff}
.card .num{font-family:"Archivo",sans-serif;font-weight:700;font-size:30px;color:var(--signal);
  line-height:1;letter-spacing:-.03em}
.card .t{display:block;font-family:"Archivo",sans-serif;font-weight:600;font-size:19px;margin-bottom:3px}
.card .d{display:block;font-size:14px;color:var(--soft)}
.card .tag{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--soft);border:1px solid var(--rule);border-radius:20px;padding:3px 10px}
.card.off{border-style:dashed;border-color:var(--rule);background:transparent;cursor:default}
.card.off .num,.card.off .t{color:var(--faint)}
.card.off .d,.card.off .tag{color:var(--faint);opacity:.8}
.soonnav{font-family:"JetBrains Mono",monospace;font-size:12px;color:var(--faint);
  padding:4px 9px;border:1px dashed var(--rule);border-radius:4px}

/* ---- lab cards ---- */
.labs{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(330px,1fr))}
.lab{border:1.5px solid var(--ink);border-radius:9px;background:var(--panel);padding:16px 18px}
.lab .lh{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap}
.lab .lh b{font-family:"Archivo",sans-serif;font-weight:600;font-size:18px}
.lab .lh span{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:.08em;
  color:var(--pass);white-space:nowrap}
.lab p{margin:8px 0 11px;font-size:14px;color:var(--soft)}
.lab code{font-size:11.5px;color:var(--probe)}

/* ---- course intro ---- */
.formula{margin:28px 0 0;background:var(--deep);color:#DCE3E8;border-radius:10px;
  padding:18px 22px;font-family:"JetBrains Mono",monospace;font-size:13.5px;line-height:1.7;
  box-shadow:var(--shadow)}
.formula .eq{color:#fff;font-size:14.5px;margin-bottom:8px;overflow-wrap:anywhere}
.formula b{color:var(--signal);font-weight:500}
.skills{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:8px 0 0}
.skill{background:var(--panel);border:1.5px solid var(--ink);border-radius:9px;padding:14px 16px}
.skill i{font-family:"Archivo",sans-serif;font-style:normal;font-weight:700;font-size:22px;
  color:var(--signal);display:block;line-height:1;margin-bottom:6px}
.skill span{font-size:14.5px}
.arcs{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:8px}
.arc{border:1.5px solid var(--ink);border-radius:9px;padding:14px 16px;background:var(--panel)}
.arc .k{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:.12em;
  text-transform:uppercase;color:var(--signal)}
.arc b{display:block;font-family:"Archivo",sans-serif;margin:6px 0 4px;font-size:16px}
.arc span{font-size:13.5px;color:var(--soft)}
.fails{margin:10px 0 0;font-family:"JetBrains Mono",monospace;font-size:12.5px;color:var(--soft);
  background:var(--panel);border:1.5px solid var(--ink);border-radius:9px;padding:12px 16px;
  line-height:1.85}
.fails b{color:var(--ink);font-weight:500}
.week{border:1.5px solid var(--ink);border-radius:9px;background:var(--panel);margin:0 0 12px;
  overflow:hidden}
.week.soon{border-style:dashed;border-color:var(--rule);background:transparent}
.week .wh{display:grid;grid-template-columns:52px 1fr auto;gap:14px;align-items:start;
  padding:16px 18px}
.week .wn{font-family:"Archivo",sans-serif;font-weight:700;font-size:26px;color:var(--signal);
  line-height:1}
.week.soon .wn,.week.soon .wt{color:var(--faint)}
.week .wt{font-family:"Archivo",sans-serif;font-weight:600;font-size:17px}
.week .wq{font-size:13.5px;color:var(--soft);margin-top:3px}
.week .st{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:.08em;
  text-transform:uppercase;color:var(--pass);white-space:nowrap}
.week.soon .st{color:var(--faint)}
.week .wbody{border-top:1px solid var(--rule);padding:16px 18px 18px}

/* ---- lesson page ---- */
.page{display:grid;grid-template-columns:236px 1fr;gap:44px;padding:34px 0 0;align-items:start}
.rail{position:sticky;top:22px;font-size:13.5px}
.rail .rt{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--faint);margin-bottom:10px}
.rail a{display:block;text-decoration:none;color:var(--soft);padding:4px 0 4px 11px;
  border-left:2px solid var(--rule);line-height:1.4}
.rail a:hover{color:var(--ink);border-left-color:var(--signal)}
.rail a i{font-family:"JetBrains Mono",monospace;font-style:normal;font-size:10.5px;
  color:var(--faint);margin-right:7px}
.rail a:hover i{color:var(--signal)}
.doc{min-width:0}
.doc h1{font-size:clamp(30px,4.6vw,46px);margin:0 0 6px}
.doc h2{font-family:"Archivo",sans-serif;font-weight:700;font-size:31px;letter-spacing:-.02em;
  line-height:1.22;margin:62px 0 14px;padding-top:22px;border-top:2.5px solid var(--ink)}
.doc h2 .hn{display:block;font-family:"JetBrains Mono",monospace;font-weight:500;font-size:11.5px;
  letter-spacing:.24em;color:var(--signal);margin-bottom:10px}
.doc h2.sub{font-weight:600;font-size:23px;color:var(--soft);border-top:none;
  margin:0 0 18px;padding-top:0}
.doc h3{font-family:"Archivo",sans-serif;font-weight:600;font-size:19.5px;margin:30px 0 8px;
  padding-left:12px;border-left:3px solid var(--rule)}
.doc h4{font-family:"Archivo",sans-serif;font-weight:600;font-size:16px;margin:20px 0 6px;color:var(--soft)}
.doc p{margin:12px 0}
.doc ul,.doc ol{padding-left:22px}
.doc li{margin:5px 0}
.doc blockquote{margin:16px 0;padding:13px 18px;background:var(--panel);
  border-left:4px solid var(--signal);border-radius:0 8px 8px 0;color:var(--ink)}
.doc blockquote p{margin:6px 0}
.doc blockquote h3{margin-top:2px}
.doc blockquote h1{font-family:"Archivo",sans-serif;font-weight:700;
  font-size:clamp(18px,2.4vw,24px);line-height:1.35;letter-spacing:-.012em;
  margin:8px 0 6px;color:var(--ink)}
.doc blockquote h1 + h1{color:var(--signal);font-size:clamp(15px,2vw,18px);font-weight:600}
.doc table{width:100%;border-collapse:collapse;margin:18px 0;font-size:14.5px;
  background:var(--panel);border:1.5px solid var(--ink);border-radius:8px;overflow:hidden}
.doc th,.doc td{padding:9px 13px;text-align:left;border-bottom:1px solid var(--rule);vertical-align:top}
.doc thead th{background:var(--ink);color:var(--paper);font-family:"JetBrains Mono",monospace;
  font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;font-weight:500}
.doc tbody tr:last-child td{border-bottom:none}
.doc tbody tr:nth-child(even){background:#fff}
.doc hr{border:none;border-top:1px solid var(--rule);margin:30px 0}
.doc details{background:var(--panel);border:1px solid var(--rule);border-radius:8px;
  padding:11px 15px;margin:14px 0}
.doc summary{cursor:pointer;font-family:"Archivo",sans-serif;font-weight:600;font-size:14.5px;color:var(--probe)}
.doc img{max-width:100%}

/* ---- in-lesson figure: accumulating complexity ladder ---- */
.ladder{margin:22px 0 8px;border:1.5px solid var(--ink);border-radius:10px;overflow:hidden;
  box-shadow:var(--shadow);background:var(--panel)}
.ladder figcaption{background:var(--ink);color:var(--paper);padding:9px 16px;
  font-family:"JetBrains Mono",monospace;font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;
  display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap}
.ladder figcaption span:last-child{color:#93A2AE;text-transform:none;letter-spacing:.02em}
.rung{display:grid;grid-template-columns:46px 1fr;border-top:1px solid var(--rule)}
.rung:first-of-type{border-top:none}
.rn{font-family:"Archivo",sans-serif;font-weight:700;font-size:15px;color:var(--faint);
  padding:14px 0 0;text-align:center;border-right:1px solid var(--rule)}
.rbody{padding:12px 16px 14px}
.rhead{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:9px}
.rhead b{font-family:"Archivo",sans-serif;font-weight:600;font-size:16px}
.rhead code{background:none;padding:0;color:var(--soft);font-size:12.5px}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-family:"JetBrains Mono",monospace;font-size:11.5px;padding:3px 9px;border-radius:20px;
  border:1px solid var(--rule);color:var(--faint);background:var(--panel-2)}
.chip.new{border-color:var(--signal);color:#fff;background:var(--signal);font-weight:500}
.wline{display:flex;align-items:center;gap:14px;flex-wrap:wrap;background:var(--deep);color:#9FB3C0;
  font-family:"JetBrains Mono",monospace;font-size:11.5px;letter-spacing:.08em;padding:8px 16px}
.wline span:first-child{color:var(--signal);white-space:nowrap;font-weight:500}
.lfoot{border-top:1px solid var(--rule);padding:11px 16px;font-size:13px;color:var(--soft)}
.lfoot b{color:var(--signal)}
@media(max-width:640px){.rhead code{display:none}}

/* ---- in-lesson diagrams (```diag) ---- */
.diag{margin:22px 0 12px;border:1.5px solid var(--ink);border-radius:10px;overflow:hidden;
  background:var(--panel);box-shadow:var(--shadow)}
.diag figcaption{background:var(--ink);color:var(--paper);padding:9px 16px;
  font-family:"JetBrains Mono",monospace;font-size:11.5px;letter-spacing:.14em;text-transform:uppercase}
.dpipe{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:16px 18px}
.dnode{border:1.5px solid var(--ink);border-radius:8px;padding:8px 12px;background:#fff;
  font-family:"Archivo",sans-serif;font-weight:600;font-size:14px}
.darr{color:var(--signal);font-weight:700;font-family:"JetBrains Mono",monospace}
.dflow{padding:16px 18px;display:flex;flex-direction:column;align-items:stretch;gap:2px}
.dflow .darr{text-align:center;padding:2px 0}
.dstep{border:1.5px solid var(--ink);border-radius:8px;padding:10px 14px;background:#fff;
  font-family:"Archivo",sans-serif;font-weight:600;font-size:15px}
.dcmp{display:grid;grid-template-columns:1fr 1fr}
.dcol{padding:14px 16px}
.dcol + .dcol{border-left:1.5px solid var(--rule)}
.dh{font-family:"Archivo",sans-serif;font-weight:700;font-size:15px;margin-bottom:8px;color:var(--signal)}
.dcell{font-size:14px;padding:6px 0;border-top:1px solid var(--rule)}
.dcol .dcell:first-of-type{border-top:none}
.dnest{padding:16px}
.dbox{border:1.5px solid var(--ink);border-radius:8px;padding:10px 12px;background:#fff}
.dbox .dbox{margin-top:8px;background:var(--panel);border-color:var(--rule)}
.dbox .dbox .dbox{background:var(--panel-2)}
.dlab{font-family:"Archivo",sans-serif;font-weight:600;font-size:14.5px}
.dgrid{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:16px}
.gcell{border:1.5px solid var(--ink);border-radius:8px;padding:12px 14px;background:#fff}
.gcell b{display:block;font-family:"Archivo",sans-serif;font-size:15px;margin-bottom:4px;color:var(--signal)}
.gcell span{font-size:13.5px;color:var(--soft)}
@media(max-width:640px){
  .dcmp,.dgrid{grid-template-columns:1fr}
  .dcol + .dcol{border-left:none;border-top:1.5px solid var(--rule)}
}

.pager{display:flex;justify-content:space-between;gap:14px;margin:52px 0 0;
  border-top:1.5px solid var(--ink);padding-top:18px;flex-wrap:wrap}
.pager a{font-family:"JetBrains Mono",monospace;font-size:13px;text-decoration:none;color:var(--probe)}
.pager a:hover{color:var(--signal)}

footer{margin-top:56px;border-top:1.5px solid var(--ink);background:var(--panel)}
footer .wrap{display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap;
  padding-top:18px;padding-bottom:44px;
  font-family:"JetBrains Mono",monospace;font-size:11.5px;color:var(--faint);letter-spacing:.04em}

@media(max-width:900px){
  .mast .id{letter-spacing:.08em;font-size:10.5px;overflow:visible;text-overflow:unset;max-width:none}
  .mast .id-name,.mast .id-dot{display:none}
  .page{grid-template-columns:1fr;gap:20px}
  .rail{position:static;border-bottom:1px solid var(--rule);padding-bottom:12px}
  .rail a{display:inline-block;border-left:none;border-bottom:2px solid var(--rule);margin-right:10px}
  .layer{grid-template-columns:1fr}
  .layer .nm,.layer .note{border:none}
  .layer .note{padding-top:0}
  .waterline{grid-template-columns:1fr}
  .card{grid-template-columns:46px 1fr}
  .card .tag{display:none}
  .skills,.arcs{grid-template-columns:1fr}
  .week .wh{grid-template-columns:46px 1fr}
  .week .st{display:none}
  .dcmp,.dgrid{grid-template-columns:1fr}
  .dcol + .dcol{border-left:none;border-top:1.5px solid var(--rule)}
}
@media(prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  .layer .bar{animation:none}
  a.card:hover{transform:none}
}
.math-display{margin:24px 0;overflow-x:auto;text-align:center}
.math-display mjx-container[display="true"]{margin:.65em 0!important}
"""

HEAD = """<!DOCTYPE html>
<html lang="zh"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{css}</style>
<script>
window.MathJax = {{
  tex: {{inlineMath: [['$', '$']], processEscapes: true}},
  options: {{skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']}}
}};
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</head><body>
"""


def _first_lesson_href(lessons: list, toc_hash: str) -> str:
    for slug, _n, _t, _d, _tag, src in lessons:
        if src:
            return f"{slug}.html"
    return f"toc.html{toc_hash}"


def _week_nav() -> list[tuple[str, str, list, str]]:
    return [
        ("1", "W1", LESSONS, "#w1"),
        ("2", "W2", W2_LESSONS, "#w2"),
        ("3", "W3", W3_LESSONS, "#w3"),
        ("4", "W4", W4_LESSONS, "#w4"),
        ("5", "W5", W5_LESSONS, "#w5"),
    ]


def _active_week(active: str) -> str | None:
    if active.startswith("w2-"):
        return "2"
    if active.startswith("w3-"):
        return "3"
    if active.startswith("w4-"):
        return "4"
    if active.startswith("w5-"):
        return "5"
    if active.startswith("lesson"):
        return "1"
    return None


def masthead(active: str) -> str:
    top = [
        '<a href="index.html"%s>介绍</a>' % (' class="on"' if active == "index" else ""),
        '<a href="toc.html"%s>目录</a>' % (' class="on"' if active == "toc" else ""),
        '<a href="projects.html"%s>项目</a>' % (
            ' class="on"' if active == "projects" or active.startswith("project-") else ""
        ),
    ]
    current = _active_week(active)
    current_lessons = None
    for num, label, lessons, toc_hash in _week_nav():
        href = (
            f"toc.html{toc_hash}" if current is None
            else _first_lesson_href(lessons, toc_hash)
        )
        on = ' class="on"' if current == num else ""
        top.append(f'<a href="{href}"{on}>{label}</a>')
        if current == num:
            current_lessons = lessons
    lesson_row = ""
    if current_lessons is not None:
        chips = []
        for slug, n, _t, _d, _tag, src in current_lessons:
            if src is None:
                chips.append(f'<span class="soonnav">{n}</span>')
                continue
            on = ' class="on"' if active == slug else ""
            chips.append(f'<a href="{slug}.html"{on}>{n}</a>')
        lesson_row = f'<nav class="mast-lessons">{"".join(chips)}</nav>'
    if active == "index":
        badge = "12 WEEKS"
    elif active == "toc":
        badge = "CONTENTS"
    elif active == "projects" or active.startswith("project-"):
        badge = "PROJECTS"
    elif current == "2":
        badge = "WEEK 02"
    elif current == "3":
        badge = "WEEK 03"
    elif current == "4":
        badge = "WEEK 04"
    elif current == "5":
        badge = "WEEK 05"
    else:
        badge = "WEEK 01"
    return f"""<header class="mast"><div class="wrap">
<span class="id"><span class="id-name">Agent Evaluation &amp; Benchmark Engineering</span><span class="id-dot"> · </span><b>{badge}</b></span>
<div class="mast-nav"><nav>{''.join(top)}</nav>{lesson_row}</div>
</div></header>"""


def footer(left: str, mid: str, right: str) -> str:
    return f"""<footer><div class="wrap">
<span>{left}</span>
<span>{mid}</span>
<span>{right}</span>
</div></footer></body></html>"""


FOOT = footer(
    "Week 01 · Benchmark Archaeology",
    "源:Terminal-Bench · SWE-bench · τ³-bench · OSWorld · WebArena · GAIA · BFCL",
    "由 week01/*.md 生成 · build_site.py",
)
FOOT_INDEX = footer(
    "Agent Evaluation &amp; Benchmark Engineering",
    "12 weeks · source-first · 30% papers / 70% RFC · docs · source",
    "PLAN.md",
)


def w1_body() -> str:
    layers = []
    for name, flow, note, depth in STRATA:
        w = 12 + depth * 17
        layers.append(
            f'<div class="layer"><div class="nm">{name}</div>'
            f'<div class="flow">{flow}<span class="bar" style="width:{w}%;'
            f'animation-delay:{depth * .07:.2f}s"></span></div>'
            f'<div class="note">{note}</div></div>'
        )
        if depth == 2:
            layers.append(
                '<div class="waterline"><span>▼ 现实水线</span>'
                "<span>以下:benchmark 自己启动并管理有状态环境 —— agent 真的在里面跑</span></div>"
            )
    cards = []
    for slug, n, title, desc, tag, src in LESSONS:
        body = (f'<span class="num">{n}</span>'
                f'<span><span class="t">{title}</span><span class="d">{desc}</span></span>'
                f'<span class="tag">{tag}</span>')
        cards.append(f'<a class="card" href="{slug}.html">{body}</a>' if src
                     else f'<div class="card off">{body}</div>')
    labs = "".join(
        f'<div class="lab"><div class="lh"><b>{name}</b><span>{state}</span></div>'
        f'<p>{desc}</p><code>{path}</code></div>'
        for path, name, desc, state in LABS
    )
    done = sum(1 for *_x, src in LESSONS if src)
    return f"""<p class="lede" style="margin-top:16px">Day 1 总览,Day 2–5 一天一个真 benchmark 读源码,Day 6 自己造一个。
已完成 <b>{done}/6</b>。本周不讲统计(→ W3)、runtime 抽象(→ W2)、排行榜(→ W8)。</p>
<div class="strata">
<div class="cap"><span>Complexity ladder</span><span>Lesson 1 · 六个代表性 benchmark</span></div>
{''.join(layers)}
</div>
<p class="stratanote">水线以上是 <b>dataset benchmark</b>(只给题和答案,agent 与环境自带);
以下是 <b>environment benchmark</b>。SWE-bench 卡在中间:它给容器化的 <i>evaluation</i> harness,但不给 agent harness。</p>
<div class="cards" style="margin-top:18px">{''.join(cards)}</div>
<p class="lede" style="margin:22px 0 12px">讲义里的结论来自这些 lab 的真实输出,不是复述文档。</p>
<div class="labs">{labs}</div>"""


def w2_body() -> str:
    cards = []
    for slug, n, title, desc, tag, src in W2_LESSONS:
        body = (f'<span class="num">{n}</span>'
                f'<span><span class="t">{title}</span><span class="d">{desc}</span></span>'
                f'<span class="tag">{tag}</span>')
        cards.append(f'<a class="card" href="{slug}.html">{body}</a>' if src
                     else f'<div class="card off">{body}</div>')
    done = sum(1 for *_x, src in W2_LESSONS if src)
    return f"""<p class="lede" style="margin-top:16px">4 节深课 + Day 5 EvalRT Core。Harbor 贯穿;Inspect 对照。
已完成 <b>{done}/5</b>。Agent ≠ Model 是第 1 课开头 10 分钟,不是单独一课。</p>
<div class="cards">{''.join(cards)}</div>"""


def w3_body() -> str:
    cards = []
    for slug, n, title, desc, tag, src in W3_LESSONS:
        body = (f'<span class="num">{n}</span>'
                f'<span><span class="t">{title}</span><span class="d">{desc}</span></span>'
                f'<span class="tag">{tag}</span>')
        cards.append(f'<a class="card" href="{slug}.html">{body}</a>' if src
                     else f'<div class="card off">{body}</div>')
    done = sum(1 for *_x, src in W3_LESSONS if src)
    return f"""<p class="lede" style="margin-top:16px">3 节课 + Day 4 Statistical Eval Report lab。
已完成 <b>{done}/4</b>。W3 假定 verifier 已给出 score,只研究估计、不确定性、比较与决策。</p>
<div class="cards">{''.join(cards)}</div>"""


def w4_body() -> str:
    cards = []
    for slug, n, title, desc, tag, src in W4_LESSONS:
        body = (f'<span class="num">{n}</span>'
                f'<span><span class="t">{title}</span><span class="d">{desc}</span></span>'
                f'<span class="tag">{tag}</span>')
        cards.append(f'<a class="card" href="{slug}.html">{body}</a>' if src
                     else f'<div class="card off">{body}</div>')
    done = sum(1 for *_x, src in W4_LESSONS if src)
    return f"""<p class="lede" style="margin-top:16px">4 节课 + Day 5 Scorer Audit Report lab。
已完成 <b>{done}/5</b>。W4 固定 task 与 trial evidence,把 scorer 自己当作需要验证的测量系统。</p>
<div class="cards">{''.join(cards)}</div>"""


def w5_body() -> str:
    cards = []
    for slug, n, title, desc, tag, src in W5_LESSONS:
        body = (f'<span class="num">{n}</span>'
                f'<span><span class="t">{title}</span><span class="d">{desc}</span></span>'
                f'<span class="tag">{tag}</span>')
        cards.append(f'<a class="card" href="{slug}.html">{body}</a>' if src
                     else f'<div class="card off">{body}</div>')
    done = sum(1 for *_x, src in W5_LESSONS if src)
    return f"""<p class="lede" style="margin-top:16px">4 节课 + Day 5 Benchmark Release Candidate lab。
已完成 <b>{done}/5</b>。W5 固定通过审计的 scorer,改查 capability claim、task distribution 与 task admission。</p>
<div class="cards">{''.join(cards)}</div>"""


def build_intro() -> str:
    return f"""{HEAD.format(title="Agent Evaluation & Benchmark Engineering", css=CSS)}
{masthead("index")}
<section class="hero"><div class="wrap">
<span class="eyebrow">12 周 · 每周 5 天 · 每天约 1 小时</span>
<h1>Agent Evaluation<br>&amp; Benchmark Engineering</h1>
<p class="subhead">从排行榜解构、统计推断到 RL Environment</p>
<p class="thesis">行业普遍信任的 <b>Artificial Analysis 等综合排行榜</b>，本质上大多是若干个<b>已显陈旧、甚至易被过拟合的 Benchmark 的加权平均</b>。
把充满环境泄漏、弱裁判漏洞与数据污染的单项分揉在一起，算不出真实的智能跃迁。
评测工程的终极目标，不是去刷一个过时的加权榜单，而是构建严谨、抗对抗、可复现的<b>精密测量仪器与 RL 训练环境</b>。</p>
<div class="formula">
<div class="eq">performance = <b>Model</b> × Harness × Environment × Task × Budget × Scorer × Randomness</div>
测得的性能是这七项的乘积。当加权平均把陈旧题库与弱 Verifier 混在一起时，榜单总分往往掩盖了真实的系统方差与模型缺陷。
</div>
</div></section>

<section class="sec"><div class="wrap">
<h2>加权排行榜背后的三大盲区</h2>
<p class="lede">把多个单项 benchmark 简单加权平均，往往会在工业落地中引发灾难性的误判：</p>
<div class="cards" style="margin-top:16px">
<div class="card"><span class="num">01</span><span><span class="t">基准老化与数据污染</span><span class="d">依赖早期固定测试集（如过拟合严重的题库），模型刷到 90%+ 却在线上复杂业务中一触即溃。</span></span><span class="tag">W5 · W7</span></div>
<div class="card"><span class="num">02</span><span><span class="t">弱 Verifier 导致的作弊加权</span><span class="d">单项评测中存在的 Hardcoded 捷径与脆弱的 LLM 裁判偏见，被直接加权计入综合总分。</span></span><span class="tag">W4 · P2</span></div>
<div class="card"><span class="num">03</span><span><span class="t">平均分掩盖系统崩溃与安全红线</span><span class="d">9 个任务成功 + 1 个越权删库，平均分依然是 90%；加权平均抹平了成对检验与长尾可靠性。</span></span><span class="tag">W1–W3 · P1/P4</span></div>
</div>
</div></section>

<section class="sec"><div class="wrap">
<h2>五大工业级实战项目 (Assessments)</h2>
<p class="lede">全课只设 4 个阶段性工程项目 + 1 个 Capstone，所有 Lab 作为中间 Checkpoint 最终汇入项目交付：</p>
<div class="cards" style="margin-top:16px">{project_cards()}</div>
</div></section>

<section class="sec"><div class="wrap">
<h2>三段技术进阶体系</h2>
<p class="lede">从解构现有基准、科学测量到工程闭环，全链路构建端到端评测能力。</p>
<div class="arcs">
<div class="arc"><div class="k">W1–W2 · 工程底座</div><b>怎么工作</b><span>解构 Terminal-Bench / SWE-bench / Harbor / Inspect，跑通真正隔离的 Runtime</span></div>
<div class="arc"><div class="k">W3–W7 · 科学测量</div><b>怎么测量</b><span>统计推断、题目有效性审计、LLM 裁判鲁棒性攻击与抗刷榜防御</span></div>
<div class="arc"><div class="k">W8–W12 · 系统闭环</div><b>怎么落地</b><span>线上 Shadow Eval、生产决策报告、冷启动基准与 On-policy RL 训练环境</span></div>
</div>
<div class="fails"><b>W2 / W5 / W6 / W7 是四种系统性失败，不是四个近义词。</b>
W2 运行与观测失败 · W5 目标能力错位 · W6 随机与执行噪声 · W7 测量被泄漏、作弊或对抗污染。
素材约 30% 前沿论文，70% 工业级 RFC / 官方规范 / 源码实现。</div>
</div></section>

<section class="sec"><div class="wrap">
<a class="card" href="toc.html"><span class="num">12</span>
<span><span class="t">查看 12 周完整大纲与讲义</span><span class="d">深入每一节课的真实源码剖析与理论推导。</span></span>
<span class="tag">目录</span></a>
</div></section>
{FOOT_INDEX}"""


def project_cards() -> str:
    cards = []
    for slug, pid, title, weeks, desc, _src in PROJECTS:
        cards.append(
            f'<a class="card" href="{slug}.html"><span class="num">{pid}</span>'
            f'<span><span class="t">{title}</span><span class="d">{weeks} · {desc}</span></span>'
            '<span class="tag">正式交付</span></a>'
        )
    return ''.join(cards)


def build_projects_index() -> str:
    foot = footer(
        "Assessment Contract · 4 staged projects + 1 capstone",
        "lesson labs / exercises = checkpoints",
        "ASSESSMENTS.md",
    )
    return f"""{HEAD.format(title="正式项目 · Agent Evaluation & Benchmark Engineering", css=CSS)}
{masthead("projects")}
<section class="hero"><div class="wrap">
<span class="eyebrow">ASSESSMENT CONTRACT · 4 + 1</span>
<h1>正式项目</h1>
<p class="subhead">课程只收五次。每个 lesson lab 都进入相邻项目，不再产生新的 submission。</p>
</div></section>
<section class="sec" style="padding-top:8px"><div class="wrap">
<div class="cards">{project_cards()}</div>
</div></section>
{foot}"""


def build_toc() -> str:
    week_html = []
    for n, title, q, status, expand in WEEKS:
        soon = "" if expand or status else " soon"
        st = status or "未写"
        if n == "1":
            body = w1_body()
        elif n == "2":
            body = w2_body()
        elif n == "3":
            body = w3_body()
        elif n == "4":
            body = w4_body()
        elif n == "5":
            body = w5_body()
        else:
            body = ""
        inner = f'<div class="wbody">{body}</div>' if body else ""
        week_html.append(
            f'<div class="week{soon}" id="w{n}"><div class="wh">'
            f'<div class="wn">{n}</div>'
            f'<div><div class="wt">{title}</div><div class="wq">{q}</div></div>'
            f'<div class="st">{st}</div></div>{inner}</div>'
        )
    return f"""{HEAD.format(title="目录 · Agent Evaluation & Benchmark Engineering", css=CSS)}
{masthead("toc")}
<section class="hero"><div class="wrap">
<span class="eyebrow">12 周</span>
<h1>目录</h1>
<p class="subhead">点已写的课直接进讲义。其余周先占位 —— 名字已经是真问题,不是待填的标签。</p>
</div></section>
<section class="sec" style="padding-top:8px"><div class="wrap">
{''.join(week_html)}
</div></section>
<section class="sec" style="padding:20px 0 20px"><div class="wrap">
<h2>正式交付 · 4 + 1</h2>
<p class="lede">以下五页是唯一正式作业。各周 lab、exercise 与 checklist 只是项目 checkpoint。</p>
<div class="cards">{project_cards()}</div>
</div></section>
{FOOT_INDEX}"""


def build_project(idx: int) -> str:
    slug, pid, title, weeks, _desc, src = PROJECTS[idx]
    md_text = expand_diagrams(expand_math((SRC_PROJECTS / src).read_text()))
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    html, rail_html = _anchor_h2(render_math_blocks(md.convert(md_text)))
    p = PROJECTS[idx - 1] if idx > 0 else None
    nx = PROJECTS[idx + 1] if idx + 1 < len(PROJECTS) else None
    prev_l = (f'<a href="{p[0]}.html">← {p[1]} · {p[2]}</a>' if p
              else '<a href="projects.html">← 项目目录</a>')
    next_l = (f'<a href="{nx[0]}.html">{nx[1]} · {nx[2]} →</a>' if nx
              else '<a href="projects.html">项目目录 →</a>')
    foot = footer(
        f"{pid} · {title}",
        f"{weeks} · formal submission",
        f"由 projects/{src} 生成 · build_site.py",
    )
    return f"""{HEAD.format(title=f"{pid} · {title}", css=CSS)}
{masthead(slug)}
<div class="wrap"><div class="page">
<aside class="rail"><div class="rt">项目要求</div>{rail_html}</aside>
<article class="doc">{html}
<div class="pager">{prev_l}{next_l}</div>
</article></div></div>
{foot}"""


def build_lesson(idx: int) -> str:
    slug, _n, _t, _d, _tag, src = LESSONS[idx]
    md_text = expand_diagrams(expand_math((SRC / src).read_text()))
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    html = render_math_blocks(md.convert(md_text))

    # anchor every h2 and collect the rail. Headings numbered 一、二、… get a
    # loud "§ NN" eyebrow so sections read as sections; anything else (the
    # subtitle under h1, the closing 总结) stays quiet.
    rail = []

    def anchor(m):
        inner = m.group(1)
        plain = re.sub(r"<[^>]+>", "", inner).strip()
        aid = f"s{len(rail)}"
        n = cjk_section_number(plain)
        if n is None:
            cls = ' class="sub"' if not rail else ""
            rail.append((aid, plain, None))
            return f'<h2 id="{aid}"{cls}>{inner}</h2>'
        body = inner.split("、", 1)[1] if "、" in inner else inner
        rail.append((aid, plain.split("、", 1)[-1], n))
        return f'<h2 id="{aid}"><span class="hn">§ {n:02d}</span>{body}</h2>'

    html = re.sub(r"<h2>(.*?)</h2>", anchor, html, flags=re.S)

    # swap the ASCII complexity ladder for the drawn figure (lesson 1 only)
    if slug == "lesson01":
        html, n = re.subn(
            r"<pre><code>[^<]*Benchmark Complexity.*?</code></pre>",
            lambda _m: ladder_figure(), html, count=1, flags=re.S,
        )
        if not n:
            print("  ! warn: ladder code block not found in lesson01")
    rail_html = "".join(
        f'<a href="#{a}">{f"<i>{n:02d}</i>" if n is not None else ""}{t}</a>'
        for a, t, n in rail
    )

    def neighbor(step: int):
        j = idx + step
        while 0 <= j < len(LESSONS):
            if LESSONS[j][5]:
                return LESSONS[j]
            j += step
        return None

    p, nx = neighbor(-1), neighbor(1)
    prev_l = (f'<a href="{p[0]}.html">← 第 {p[1]} 课 · {p[2]}</a>' if p
              else '<a href="toc.html#w1">← 目录</a>')
    next_l = (f'<a href="{nx[0]}.html">第 {nx[1]} 课 · {nx[2]} →</a>' if nx
              else '<a href="toc.html#w1">目录 →</a>')

    return f"""{HEAD.format(title=f"第 {LESSONS[idx][1]} 课 · {LESSONS[idx][2]}", css=CSS)}
{masthead(slug)}
<div class="wrap"><div class="page">
<aside class="rail"><div class="rt">本课目录</div>{rail_html}</aside>
<article class="doc">{html}
<div class="pager">{prev_l}{next_l}</div>
</article></div></div>
{FOOT}"""


def _anchor_h2(html: str) -> tuple[str, str]:
    rail = []

    def anchor(m):
        inner = m.group(1)
        plain = re.sub(r"<[^>]+>", "", inner).strip()
        aid = f"s{len(rail)}"
        n = cjk_section_number(plain)
        if n is None:
            cls = ' class="sub"' if not rail else ""
            rail.append((aid, plain, None))
            return f'<h2 id="{aid}"{cls}>{inner}</h2>'
        body = inner.split("、", 1)[1] if "、" in inner else inner
        rail.append((aid, plain.split("、", 1)[-1], n))
        return f'<h2 id="{aid}"><span class="hn">§ {n:02d}</span>{body}</h2>'

    html = re.sub(r"<h2>(.*?)</h2>", anchor, html, flags=re.S)
    rail_html = "".join(
        f'<a href="#{a}">{f"<i>{n:02d}</i>" if n is not None else ""}{t}</a>'
        for a, t, n in rail
    )
    return html, rail_html


def build_w2_lesson(idx: int) -> str:
    slug, n, title, _d, _tag, src = W2_LESSONS[idx]
    md_text = expand_diagrams(expand_math((SRC_W2 / src).read_text()))
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    html, rail_html = _anchor_h2(render_math_blocks(md.convert(md_text)))
    foot = footer(
        "Week 02 · Eval Runtime & Trajectory Engineering",
        "Harbor b378332 · Inspect 499e615",
        "由 week02/*.md 生成 · build_site.py",
    )
    def neighbor(step: int):
        j = idx + step
        while 0 <= j < len(W2_LESSONS):
            if W2_LESSONS[j][5]:
                return W2_LESSONS[j]
            j += step
        return None

    p, nx = neighbor(-1), neighbor(1)
    prev_l = (f'<a href="{p[0]}.html">← W2 第 {p[1]} 课 · {p[2]}</a>' if p
              else '<a href="toc.html#w2">← Week 2</a>')
    next_l = (f'<a href="{nx[0]}.html">W2 第 {nx[1]} 课 · {nx[2]} →</a>' if nx
              else '<a href="toc.html#w2">Week 2 →</a>')
    return f"""{HEAD.format(title=f"W2 第 {n} 课 · {title}", css=CSS)}
{masthead(slug)}
<div class="wrap"><div class="page">
<aside class="rail"><div class="rt">本课目录</div>{rail_html}</aside>
<article class="doc">{html}
<div class="pager">{prev_l}{next_l}</div>
</article></div></div>
{foot}"""


def build_w3_lesson(idx: int) -> str:
    slug, n, title, _d, _tag, src = W3_LESSONS[idx]
    md_text = expand_diagrams(expand_math((SRC_W3 / src).read_text()))
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    html, rail_html = _anchor_h2(render_math_blocks(md.convert(md_text)))
    foot = footer(
        "Week 03 · Statistical Inference for Stochastic Agent Evals",
        "Adding Error Bars to Evals · On Randomness · Don't Use the CLT · Measuring all the noises",
        "由 week03/*.md 生成 · build_site.py",
    )

    def neighbor(step: int):
        j = idx + step
        while 0 <= j < len(W3_LESSONS):
            if W3_LESSONS[j][5]:
                return W3_LESSONS[j]
            j += step
        return None

    p, nx = neighbor(-1), neighbor(1)
    prev_l = (f'<a href="{p[0]}.html">← W3 第 {p[1]} 课 · {p[2]}</a>' if p
              else '<a href="toc.html#w3">← Week 3</a>')
    next_l = (f'<a href="{nx[0]}.html">W3 第 {nx[1]} 课 · {nx[2]} →</a>' if nx
              else '<a href="toc.html#w3">Week 3 →</a>')
    return f"""{HEAD.format(title=f"W3 第 {n} 课 · {title}", css=CSS)}
{masthead(slug)}
<div class="wrap"><div class="page">
<aside class="rail"><div class="rt">本课目录</div>{rail_html}</aside>
<article class="doc">{html}
<div class="pager">{prev_l}{next_l}</div>
</article></div></div>
{foot}"""


def build_w4_lesson(idx: int) -> str:
    slug, n, title, _d, _tag, src = W4_LESSONS[idx]
    md_text = expand_diagrams(expand_math((SRC_W4 / src).read_text()))
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    html, rail_html = _anchor_h2(render_math_blocks(md.convert(md_text)))
    foot = footer(
        "Week 04 · Scorer Validation for Agent Evals",
        "CUAVerifierBench · tool-calling audits · Inspect scorers",
        "由 week04/*.md 生成 · build_site.py",
    )

    def neighbor(step: int):
        j = idx + step
        while 0 <= j < len(W4_LESSONS):
            if W4_LESSONS[j][5]:
                return W4_LESSONS[j]
            j += step
        return None

    p, nx = neighbor(-1), neighbor(1)
    prev_l = (f'<a href="{p[0]}.html">← W4 第 {p[1]} 课 · {p[2]}</a>' if p
              else '<a href="toc.html#w4">← Week 4</a>')
    next_l = (f'<a href="{nx[0]}.html">W4 第 {nx[1]} 课 · {nx[2]} →</a>' if nx
              else '<a href="toc.html#w4">Week 4 →</a>')
    return f"""{HEAD.format(title=f"W4 第 {n} 课 · {title}", css=CSS)}
{masthead(slug)}
<div class="wrap"><div class="page">
<aside class="rail"><div class="rt">本课目录</div>{rail_html}</aside>
<article class="doc">{html}
<div class="pager">{prev_l}{next_l}</div>
</article></div></div>
{foot}"""


def build_w5_lesson(idx: int) -> str:
    slug, n, title, _d, _tag, src = W5_LESSONS[idx]
    md_text = expand_diagrams(expand_math((SRC_W5 / src).read_text()))
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    html, rail_html = _anchor_h2(render_math_blocks(md.convert(md_text)))
    foot = footer(
        "Week 05 · Benchmark Design, Task QA & Dataset Lifecycle",
        "ECBD · construct validity · METR · LifeSciBench",
        "由 week05/*.md 生成 · build_site.py",
    )

    def neighbor(step: int):
        j = idx + step
        while 0 <= j < len(W5_LESSONS):
            if W5_LESSONS[j][5]:
                return W5_LESSONS[j]
            j += step
        return None

    p, nx = neighbor(-1), neighbor(1)
    prev_l = (f'<a href="{p[0]}.html">← W5 第 {p[1]} 课 · {p[2]}</a>' if p
              else '<a href="toc.html#w5">← Week 5</a>')
    next_l = (f'<a href="{nx[0]}.html">W5 第 {nx[1]} 课 · {nx[2]} →</a>' if nx
              else '<a href="toc.html#w5">Week 5 →</a>')
    return f"""{HEAD.format(title=f"W5 第 {n} 课 · {title}", css=CSS)}
{masthead(slug)}
<div class="wrap"><div class="page">
<aside class="rail"><div class="rt">本课目录</div>{rail_html}</aside>
<article class="doc">{html}
<div class="pager">{prev_l}{next_l}</div>
</article></div></div>
{foot}"""


def main() -> None:
    OUT.mkdir(exist_ok=True)
    idx = build_intro()
    (OUT / "index.html").write_text(idx)
    print(f"  index.html      {len(idx):>8,} B   ← 介绍")
    toc = build_toc()
    (OUT / "toc.html").write_text(toc)
    print(f"  toc.html        {len(toc):>8,} B   ← 目录")
    projects = build_projects_index()
    (OUT / "projects.html").write_text(projects)
    print(f"  projects.html   {len(projects):>8,} B   ← 正式项目")
    live = {"index.html", "toc.html", "projects.html"}
    for i, (slug, *_rest, src) in enumerate(PROJECTS):
        page = build_project(i)
        (OUT / f"{slug}.html").write_text(page)
        live.add(f"{slug}.html")
        print(f"  {slug}.html   {len(page):>8,} B   ← projects/{src}")
    for i, (slug, *_rest, src) in enumerate(LESSONS):
        if src is None:
            print(f"  {slug}.html    {'—':>8}   (未写)")
            continue
        page = build_lesson(i)
        (OUT / f"{slug}.html").write_text(page)
        live.add(f"{slug}.html")
        print(f"  {slug}.html   {len(page):>8,} B   ← {src}")
    for i, (slug, *_rest, src) in enumerate(W2_LESSONS):
        if src is None:
            print(f"  {slug}.html    {'—':>8}   (未写)")
            continue
        page = build_w2_lesson(i)
        (OUT / f"{slug}.html").write_text(page)
        live.add(f"{slug}.html")
        print(f"  {slug}.html   {len(page):>8,} B   ← {src}")
    for i, (slug, *_rest, src) in enumerate(W3_LESSONS):
        if src is None:
            print(f"  {slug}.html    {'—':>8}   (未写)")
            continue
        page = build_w3_lesson(i)
        (OUT / f"{slug}.html").write_text(page)
        live.add(f"{slug}.html")
        print(f"  {slug}.html   {len(page):>8,} B   ← {src}")
    for i, (slug, *_rest, src) in enumerate(W4_LESSONS):
        if src is None:
            print(f"  {slug}.html    {'—':>8}   (未写)")
            continue
        page = build_w4_lesson(i)
        (OUT / f"{slug}.html").write_text(page)
        live.add(f"{slug}.html")
        print(f"  {slug}.html   {len(page):>8,} B   ← {src}")
    for i, (slug, *_rest, src) in enumerate(W5_LESSONS):
        if src is None:
            print(f"  {slug}.html    {'—':>8}   (未写)")
            continue
        page = build_w5_lesson(i)
        (OUT / f"{slug}.html").write_text(page)
        live.add(f"{slug}.html")
        print(f"  {slug}.html   {len(page):>8,} B   ← {src}")
    w3_assets = SRC_W3 / "assets"
    if w3_assets.exists():
        out_assets = OUT / "assets"
        out_assets.mkdir(exist_ok=True)
        for asset in sorted(p for p in w3_assets.iterdir() if p.is_file()):
            copyfile(asset, out_assets / asset.name)
            print(f"  assets/{asset.name}   ← week03/assets/{asset.name}")
    for stale in sorted(p for p in OUT.glob("*.html") if p.name not in live):
        stale.unlink()
        print(f"  removed stale   {stale.name}")
    print(f"\n→ {OUT}")


if __name__ == "__main__":
    main()
