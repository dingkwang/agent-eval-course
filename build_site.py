"""Render week01 markdown lessons into a static site under site/.

Design: "specimen teardown" — the course dissects benchmarks, so the site reads
like a field manual: cool instrument paper, industrial grotesque display type,
and a depth cross-section as the signature figure (depth = how much of the real
world a benchmark actually instantiates).

Run from the course root:  python3 build_site.py
"""

import re
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
SRC = ROOT / "week01"
OUT = ROOT / "site"

LESSONS = [
    ("lesson01", "1", "Benchmark Anatomy", "主流 agent benchmark 是怎么实现的", "源码"),
    ("lesson02", "2", "组件级 Evaluation 与 Trace", "任务失败时,哪一环失败了", "概念"),
    ("lesson03", "3", "Agent 分数 ≠ Model 分数", "七因子里只有一个是模型", "写作"),
    ("lesson04", "4", "这个分数能不能信", "Bernoulli · 标准误 · Wilson CI", "编码"),
    ("lesson05", "5", "三个 Benchmark 横向解剖", "统一维度 + 怎么 game 它", "分析"),
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
  text-transform:uppercase;color:var(--soft)}
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
a.card{display:grid;grid-template-columns:64px 1fr auto;gap:18px;align-items:center;
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

/* ---- lesson page ---- */
.page{display:grid;grid-template-columns:236px 1fr;gap:44px;padding:34px 0 0;align-items:start}
.rail{position:sticky;top:22px;font-size:13.5px}
.rail .rt{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--faint);margin-bottom:10px}
.rail a{display:block;text-decoration:none;color:var(--soft);padding:4px 0 4px 11px;
  border-left:2px solid var(--rule);line-height:1.4}
.rail a:hover{color:var(--ink);border-left-color:var(--signal)}
.doc{min-width:0}
.doc h1{font-size:clamp(30px,4.6vw,46px);margin:0 0 6px}
.doc h2{font-family:"Archivo",sans-serif;font-weight:600;font-size:26px;letter-spacing:-.015em;
  margin:44px 0 12px;padding-top:16px;border-top:1.5px solid var(--ink)}
.doc h3{font-family:"Archivo",sans-serif;font-weight:600;font-size:19px;margin:28px 0 8px}
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

.pager{display:flex;justify-content:space-between;gap:14px;margin:52px 0 0;
  border-top:1.5px solid var(--ink);padding-top:18px;flex-wrap:wrap}
.pager a{font-family:"JetBrains Mono",monospace;font-size:13px;text-decoration:none;color:var(--probe)}
.pager a:hover{color:var(--signal)}

footer{margin-top:56px;border-top:1.5px solid var(--ink);background:var(--panel)}
footer .wrap{display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap;
  padding-top:18px;padding-bottom:44px;
  font-family:"JetBrains Mono",monospace;font-size:11.5px;color:var(--faint);letter-spacing:.04em}

@media(max-width:900px){
  .page{grid-template-columns:1fr;gap:20px}
  .rail{position:static;border-bottom:1px solid var(--rule);padding-bottom:12px}
  .rail a{display:inline-block;border-left:none;border-bottom:2px solid var(--rule);margin-right:10px}
  .layer{grid-template-columns:1fr}
  .layer .nm,.layer .note{border:none}
  .layer .note{padding-top:0}
  .waterline{grid-template-columns:1fr}
  a.card{grid-template-columns:46px 1fr}
  .card .tag{display:none}
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
    items = ['<a href="index.html"%s>目录</a>' % (' class="on"' if active == "index" else "")]
    for slug, n, *_ in LESSONS:
        on = ' class="on"' if active == slug else ""
        items.append(f'<a href="{slug}.html"{on}>{n}</a>')
    return f"""<header class="mast"><div class="wrap">
<span class="id">Agent Evaluation &amp; Benchmark Engineering · <b>WEEK 01</b></span>
<nav>{''.join(items)}</nav></div></header>"""


FOOT = """<footer><div class="wrap">
<span>Week 01 · Evaluation 基本框架</span>
<span>源:AA v4.1.1 快照 · SWE-bench · Terminal-Bench · tau2-bench · OSWorld-V2 · BFCL</span>
<span>由 week01/*.md 生成 · build_site.py</span>
</div></footer></body></html>"""


def build_index() -> str:
    layers = []
    for name, flow, note, depth in STRATA:
        w = 12 + depth * 17
        layers.append(
            f'<div class="layer"><div class="nm">{name}</div>'
            f'<div class="flow">{flow}<span class="bar" style="width:{w}%;'
            f'animation-delay:{depth * .07:.2f}s"></span></div>'
            f'<div class="note">{note}</div></div>'
        )
        if depth == 2:  # reality waterline sits just below SWE-bench
            layers.append(
                '<div class="waterline"><span>▼ 现实水线</span>'
                "<span>以下:benchmark 自己启动并管理有状态环境 —— agent 真的在里面跑</span></div>"
            )
    cards = []
    for slug, n, title, desc, tag in LESSONS:
        cards.append(
            f'<a class="card" href="{slug}.html"><span class="num">{n}</span>'
            f'<span><span class="t">{title}</span><span class="d">{desc}</span></span>'
            f'<span class="tag">{tag}</span></a>'
        )
    return f"""{HEAD.format(title="Week 01 · Agent Evaluation 讲义", css=CSS)}
{masthead("index")}
<section class="hero"><div class="wrap">
<span class="eyebrow">Week 01 · 五节课</span>
<h1>Evaluation<br>基本框架</h1>
<p class="thesis">测得的性能 = Model × Harness × Environment × Task Distribution × Budget × Scorer × Randomness。
<b>七个因子里只有一个是模型</b> —— 所以 leaderboard 分数不是模型的属性,是一次测量的属性。</p>
</div></section>

<section class="sec"><div class="wrap">
<h2>Benchmark 深度剖面</h2>
<p class="lede">纵深 = 这个 benchmark 真正实例化了多少现实世界。越往下,环境越真,verifier 查的状态越接近真实结果。</p>
<div class="strata">
<div class="cap"><span>Complexity ladder</span><span>Lesson 1 · 六个代表性 benchmark</span></div>
{''.join(layers)}
</div>
<p class="stratanote">水线以上是 <b>dataset benchmark</b>(只给题和答案,agent 与环境自带);
以下是 <b>environment benchmark</b>。SWE-bench 卡在中间:它给容器化的 <i>evaluation</i> harness,但不给 agent harness。</p>
</div></section>

<section class="sec"><div class="wrap">
<h2>五节课</h2>
<p class="lede">2 天概念 · 1 天编码 · 1 天分析 · 1 天写作。每节 60 分钟。</p>
<div class="cards">{''.join(cards)}</div>
</div></section>

<section class="sec"><div class="wrap">
<h2>本周交付</h2>
<pre><code>notes/day1-aa-benchmark-catalog.md          九项 evaluation 解剖表 + 3 个疑问
sec1-why-agent-score-is-not-model-score.md 800–1,200 字自写讲义
notes/day4-ci-findings.md                  Wilson CI 三个结论 + 扩展代码
sec2-benchmark-teardown.md                 另选三个 benchmark 的解剖表
figures/evaluation-stack.txt               完整 evaluation stack 图</code></pre>
</div></section>
{FOOT}"""


def build_lesson(slug: str, idx: int) -> str:
    md_text = (SRC / f"{slug}.md").read_text()
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    html = md.convert(md_text)

    # anchor every h2 and collect the rail
    rail = []

    def anchor(m):
        inner = m.group(1)
        plain = re.sub(r"<[^>]+>", "", inner).strip()
        aid = f"s{len(rail)}"
        rail.append((aid, plain))
        return f'<h2 id="{aid}">{inner}</h2>'

    html = re.sub(r"<h2>(.*?)</h2>", anchor, html, flags=re.S)

    # swap the ASCII complexity ladder for the drawn figure (lesson 1 only)
    if slug == "lesson01":
        html, n = re.subn(
            r"<pre><code>[^<]*Benchmark Complexity.*?</code></pre>",
            lambda _m: ladder_figure(), html, count=1, flags=re.S,
        )
        if not n:
            print("  ! warn: ladder code block not found in lesson01")
    rail_html = "".join(f'<a href="#{a}">{t}</a>' for a, t in rail)

    title = LESSONS[idx][2]
    prev_l = f'<a href="{LESSONS[idx-1][0]}.html">← 第 {LESSONS[idx-1][1]} 课 · {LESSONS[idx-1][2]}</a>' if idx else '<a href="index.html">← 目录</a>'
    next_l = f'<a href="{LESSONS[idx+1][0]}.html">第 {LESSONS[idx+1][1]} 课 · {LESSONS[idx+1][2]} →</a>' if idx + 1 < len(LESSONS) else '<a href="index.html">回目录 →</a>'

    return f"""{HEAD.format(title=f"第 {LESSONS[idx][1]} 课 · {title}", css=CSS)}
{masthead(slug)}
<div class="wrap"><div class="page">
<aside class="rail"><div class="rt">本课目录</div>{rail_html}</aside>
<article class="doc">{html}
<div class="pager">{prev_l}{next_l}</div>
</article></div></div>
{FOOT}"""


def main() -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(build_index())
    print(f"  index.html         {len(build_index()):>7,} B")
    for i, (slug, *_rest) in enumerate(LESSONS):
        page = build_lesson(slug, i)
        (OUT / f"{slug}.html").write_text(page)
        print(f"  {slug}.html      {len(page):>7,} B")
    print(f"\n→ {OUT}")


if __name__ == "__main__":
    main()
