"""Generate the exact SVG figures used by Week 3 Lesson 2.

Pure stdlib so the course figures can be rebuilt without a plotting runtime:

    python3 week03/plots/lesson02_curves.py
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"

INK = "#131A20"
SOFT = "#5A6672"
RULE = "#C9D2D8"
PANEL = "#F8FAFB"
ORANGE = "#C8501C"
BLUE = "#2B5F9E"
GREEN = "#34734A"


def points(values: list[float], x0: float, y0: float, w: float, h: float) -> str:
    n = len(values)
    return " ".join(
        f"{x0 + i * w / (n - 1):.1f},{y0 + (1 - value) * h:.1f}"
        for i, value in enumerate(values)
    )


def chart(
    *,
    title: str,
    subtitle: str,
    series: list[tuple[str, str, list[float], str]],
    filename: str,
    max_k: int,
    note: str,
) -> None:
    width, height = 920, 570
    x0, y0, plot_w, plot_h = 92, 104, 748, 316
    grid = []
    for pct in range(0, 101, 20):
        y = y0 + (100 - pct) / 100 * plot_h
        grid.append(
            f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + plot_w}" y2="{y:.1f}" '
            f'stroke="{RULE}" stroke-width="1"/>'
            f'<text x="{x0 - 14}" y="{y + 5:.1f}" text-anchor="end" class="tick">{pct}%</text>'
        )
    for k in range(1, max_k + 1):
        x = x0 + (k - 1) * plot_w / (max_k - 1)
        grid.append(
            f'<text x="{x:.1f}" y="{y0 + plot_h + 28}" text-anchor="middle" class="tick">{k}</text>'
        )

    lines = []
    legend = []
    for idx, (label, color, values, dash) in enumerate(series):
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        lines.append(
            f'<polyline points="{points(values, x0, y0, plot_w, plot_h)}" fill="none" '
            f'stroke="{color}" stroke-width="4" stroke-linecap="round" '
            f'stroke-linejoin="round"{dash_attr}/>'
        )
        for i, value in enumerate(values):
            x = x0 + i * plot_w / (max_k - 1)
            y = y0 + (1 - value) * plot_h
            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="{color}"/>')
        lx = 104 + (idx % 2) * 310
        ly = 510 + (idx // 2) * 24
        legend.append(
            f'<line x1="{lx}" y1="{ly - 5}" x2="{lx + 34}" y2="{ly - 5}" '
            f'stroke="{color}" stroke-width="4"{dash_attr}/>'
            f'<text x="{lx + 45}" y="{ly}" class="legend">{label}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{title}</title><desc id="desc">{subtitle}</desc>
<style>
  .title{{font:700 25px Arial,sans-serif;fill:{INK}}}
  .sub{{font:14px Arial,sans-serif;fill:{SOFT}}}
  .tick{{font:12px "JetBrains Mono",monospace;fill:{SOFT}}}
  .axis{{font:13px Arial,sans-serif;fill:{INK};font-weight:600}}
  .legend{{font:13px Arial,sans-serif;fill:{INK}}}
  .note{{font:12px Arial,sans-serif;fill:{SOFT}}}
</style>
<rect width="100%" height="100%" rx="12" fill="{PANEL}"/>
<text x="46" y="43" class="title">{title}</text>
<text x="46" y="68" class="sub">{subtitle}</text>
{''.join(grid)}
<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 + plot_h}" stroke="{INK}" stroke-width="1.5"/>
<line x1="{x0}" y1="{y0 + plot_h}" x2="{x0 + plot_w}" y2="{y0 + plot_h}" stroke="{INK}" stroke-width="1.5"/>
<text x="{x0 + plot_w / 2}" y="{y0 + plot_h + 52}" text-anchor="middle" class="axis">k attempts</text>
<text transform="translate(25 {y0 + plot_h / 2}) rotate(-90)" text-anchor="middle" class="axis">Task-macro probability</text>
{''.join(lines)}
{''.join(legend)}
<text x="870" y="553" text-anchor="end" class="note">{note}</text>
</svg>'''
    OUT.mkdir(exist_ok=True)
    (OUT / filename).write_text(svg)


def main() -> None:
    ks_single = list(range(1, 11))
    p = 0.6
    chart(
        title="One task, opposite questions",
        subtitle="At p = 0.60, more attempts raise capability coverage and lower all-success reliability.",
        series=[
            ("pass@k = 1-(1-p)^k", BLUE, [1 - (1 - p) ** k for k in ks_single], ""),
            ("pass^k = p^k", ORANGE, [p**k for k in ks_single], ""),
        ],
        filename="lesson02-single-task-curves.svg",
        max_k=10,
        note="Exact values from the formulas; no sampled data",
    )

    ks_compare = list(range(1, 9))
    chart(
        title="Same pass@1, different capability structure",
        subtitle="Agent A has pᵢ=0.5 on every task; Agent B has pᵢ∈{0,1} on equal halves of tasks.",
        series=[
            ("Agent A · pass@k", BLUE, [1 - 0.5**k for k in ks_compare], ""),
            ("Agent A · pass^k", ORANGE, [0.5**k for k in ks_compare], ""),
            ("Agent B · both metrics", GREEN, [0.5 for _ in ks_compare], "9 7"),
        ],
        filename="lesson02-same-pass1.svg",
        max_k=8,
        note="Both agents have pass@1 = 50%",
    )


if __name__ == "__main__":
    main()
