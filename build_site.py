"""Render the course homepage and markdown lessons into site/.

Lesson markdown may include ```diag blocks (pipe, flow, compare, nest, grid).
Those become figures before markdown runs.

Run from the course root:  python3 build_site.py
"""

import re
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
SRC = ROOT / "week01"
SRC_W2 = ROOT / "week02"
OUT = ROOT / "site"

# (slug, day, title, desc, tag, source .md — None = 尚未写)
LESSONS = [
    ("lesson01", "1", "Benchmark Anatomy", "六个 benchmark 的复杂度阶梯", "总览", "lesson01.md"),
    ("lesson02", "2", "Terminal-Bench 深读", "从 task 定义一路追到 score", "源码", "lesson02.md"),
    ("lesson03", "3", "SWE-bench", "Dataset / Runtime / Harness 为什么必须分开", "源码 + 实验", "lesson03-swe-bench.md"),
    ("lesson04", "4", "τ³-bench", "reward_basis 选出 verifier 再相乘;User LLM 在尺子里", "源码", "lesson04-tau3-bench.md"),
    ("lesson05", "5", "OSWorld · WebArena", "把整台机器当 environment", "源码", None),
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
     "4/6", True),
    ("2", "Eval Runtime & Trajectory Engineering",
     "不同 benchmark / Agent / backend 怎么经同一个 runtime 正确跑?Trajectory 是可重放事件日志,不是聊天记录",
     "2/5", False),
    ("3", "Metrics & Statistics",
     "一个 observation 是什么?误差棒怎么算?", None, False),
    ("4", "Scorers / Verifiers / LLM-as-Judge",
     "成功如何被判定?judge 准不准?", None, False),
    ("5", "Benchmark Design, Audit & Dataset Lifecycle",
     "成功/失败反映的是能力,还是题目和测试写坏了?", None, False),
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
.mast .wrap{display:flex;align-items:center;justify-content:space-between;gap:20px;
  padding-top:14px;padding-bottom:14px;flex-wrap:wrap}
.mast .id{font-family:"JetBrains Mono",monospace;font-size:11.5px;letter-spacing:.18em;
  text-transform:uppercase;color:var(--soft);white-space:nowrap}
.mast .id b{color:var(--signal);font-weight:500}
.mast nav{display:flex;gap:4px;flex-wrap:wrap}
.mast nav a{font-family:"JetBrains Mono",monospace;font-size:12px;text-decoration:none;
  color:var(--soft);padding:4px 9px;border:1px solid transparent;border-radius:4px}
.mast nav a:hover{border-color:var(--rule);color:var(--ink)}
.mast nav a.on{background:var(--ink);color:var(--paper);border-color:var(--ink)}

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
  .mast .id{letter-spacing:.08em;font-size:10.5px;max-width:100%;overflow:hidden;text-overflow:ellipsis}
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
"""

HEAD = """<!DOCTYPE html>
<html lang="zh"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{css}</style>
</head><body>
"""


def masthead(active: str) -> str:
    items = ['<a href="index.html"%s>课程</a>' % (' class="on"' if active == "index" else "")]
    for slug, n, _t, _d, _tag, src in LESSONS:
        if src is None:
            items.append(f'<span class="soonnav">{n}</span>')
            continue
        on = ' class="on"' if active == slug else ""
        items.append(f'<a href="{slug}.html"{on}>{n}</a>')
    for slug, n, _t, _d, _tag, src in W2_LESSONS:
        label = f"W2·{n}"
        if src is None:
            items.append(f'<span class="soonnav">{label}</span>')
            continue
        on = ' class="on"' if active == slug else ""
        items.append(f'<a href="{slug}.html"{on}>{label}</a>')
    if active == "index":
        badge = "12 WEEKS"
    elif active.startswith("w2-"):
        badge = "WEEK 02"
    else:
        badge = "WEEK 01"
    return f"""<header class="mast"><div class="wrap">
<span class="id">Agent Evaluation &amp; Benchmark Engineering · <b>{badge}</b></span>
<nav>{''.join(items)}</nav></div></header>"""


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


def build_index() -> str:
    week_html = []
    for n, title, q, status, expand in WEEKS:
        soon = "" if expand or status else " soon"
        st = status or "未写"
        if n == "1":
            body = w1_body()
        elif n == "2":
            body = w2_body()
        else:
            body = ""
        inner = f'<div class="wbody">{body}</div>' if body else ""
        week_html.append(
            f'<div class="week{soon}" id="w{n}"><div class="wh">'
            f'<div class="wn">{n}</div>'
            f'<div><div class="wt">{title}</div><div class="wq">{q}</div></div>'
            f'<div class="st">{st}</div></div>{inner}</div>'
        )
    return f"""{HEAD.format(title="Agent Evaluation & Benchmark Engineering", css=CSS)}
{masthead("index")}
<section class="hero"><div class="wrap">
<span class="eyebrow">12 周 · 每周 5 天 · 每天约 1 小时</span>
<h1>Agent Evaluation<br>&amp; Benchmark Engineering</h1>
<p class="subhead">从排行榜、统计推断到 RL Environment</p>
<p class="thesis">不是教「怎么跑一个 benchmark」。<b>leaderboard 分数 ≠ 模型能力。</b>
七个因子里只有一个是 model。</p>
<div class="formula">
<div class="eq">performance = <b>Model</b> × Harness × Environment × Task × Budget × Scorer × Randomness</div>
测得的性能是这七项的乘积。换 harness、换资源上限、换 user simulator,数字会动 —— 模型可以没变。
</div>
</div></section>

<section class="sec"><div class="wrap">
<h2>这门课训练的四件事</h2>
<p class="lede">现有课程能覆盖工具使用,但没有一门同时覆盖统计学 + benchmark 设计 + environment + evaluation integrity + on-policy RL。</p>
<div class="skills">
<div class="skill"><i>1</i><span>能<strong>读懂并质疑</strong>排行榜</span></div>
<div class="skill"><i>2</i><span>能设计<strong>有统计可信度</strong>的 agent benchmark</span></div>
<div class="skill"><i>3</i><span>能搭建<strong>可复现、隔离、可验证</strong>的 agent environment</span></div>
<div class="skill"><i>4</i><span>能让同一套 infra <strong>同时服务 evaluation 与 on-policy RL</strong></span></div>
</div>
</div></section>

<section class="sec"><div class="wrap">
<h2>三段</h2>
<p class="lede">v1 一上来讲统计,是在给一个你还没见过的东西算误差棒。先看见系统,再测量它。</p>
<div class="arcs">
<div class="arc"><div class="k">W1–W2 · 工程</div><b>怎么工作</b><span>benchmark 与 runtime 是怎么跑出一条 observation 的</span></div>
<div class="arc"><div class="k">W3–W7 · 方法论</div><b>怎么测量</b><span>分数能不能信:统计、题目、噪声、对抗</span></div>
<div class="arc"><div class="k">W8–W12 · 系统</div><b>怎么变成结论</b><span>排行榜、线上 eval、喂给训练、自己造一个</span></div>
</div>
<div class="fails"><b>W2 / W5 / W6 / W7 是四种失败,不是四个近义词。</b>
W2 产生 observation · W5 是否测到目标能力 · W6 是否被运行噪声污染 · W7 测量本身是否被泄漏、攻击或 game。
素材约 30% 论文,70% RFC / 官方文档 / 源码。</div>
</div></section>

<section class="sec"><div class="wrap">
<h2>12 周</h2>
<p class="lede">点 W1 / W2 已写的课直接进讲义。其余周先占位 —— 名字已经是真问题,不是待填的标签。</p>
{''.join(week_html)}
</div></section>
{FOOT_INDEX}"""


def build_lesson(idx: int) -> str:
    slug, _n, _t, _d, _tag, src = LESSONS[idx]
    md_text = expand_diagrams((SRC / src).read_text())
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    html = md.convert(md_text)

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
              else '<a href="index.html">← 课程</a>')
    next_l = (f'<a href="{nx[0]}.html">第 {nx[1]} 课 · {nx[2]} →</a>' if nx
              else '<a href="index.html">回课程 →</a>')

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
    md_text = expand_diagrams((SRC_W2 / src).read_text())
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    html, rail_html = _anchor_h2(md.convert(md_text))
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
              else '<a href="index.html#w2">← Week 2</a>')
    next_l = (f'<a href="{nx[0]}.html">W2 第 {nx[1]} 课 · {nx[2]} →</a>' if nx
              else '<a href="index.html#w2">Week 2 →</a>')
    return f"""{HEAD.format(title=f"W2 第 {n} 课 · {title}", css=CSS)}
{masthead(slug)}
<div class="wrap"><div class="page">
<aside class="rail"><div class="rt">本课目录</div>{rail_html}</aside>
<article class="doc">{html}
<div class="pager">{prev_l}{next_l}</div>
</article></div></div>
{foot}"""


def main() -> None:
    OUT.mkdir(exist_ok=True)
    idx = build_index()
    (OUT / "index.html").write_text(idx)
    print(f"  index.html      {len(idx):>8,} B")
    live = {"index.html"}
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
    for stale in sorted(p for p in OUT.glob("*.html") if p.name not in live):
        stale.unlink()
        print(f"  removed stale   {stale.name}")
    print(f"\n→ {OUT}")


if __name__ == "__main__":
    main()
