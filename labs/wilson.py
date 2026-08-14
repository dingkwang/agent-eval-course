"""Wilson vs normal-approximation confidence intervals for eval success rates.

Week 1 Day 4. Run: python3 labs/wilson.py
"""

import math


def normal_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wald / normal-approximation interval. Included to show how it breaks."""
    p = k / n
    half = z * math.sqrt(p * (1 - p) / n)
    return p - half, p + half


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval — stays inside [0,1] and works at extreme p."""
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return center - half, center + half


def width(ci: tuple[float, float]) -> float:
    return ci[1] - ci[0]


def _row(label: str, k: int, n: int) -> None:
    w, nm = wilson_ci(k, n), normal_ci(k, n)
    print(
        f"{label:16s} {k:5d}/{n:<5d} p={k/n:6.1%} | "
        f"Wilson [{w[0]:6.1%},{w[1]:6.1%}] w={width(w):5.1%} | "
        f"Normal [{nm[0]:6.1%},{nm[1]:6.1%}] w={width(nm):5.1%}"
    )


if __name__ == "__main__":
    print("① 同样是 60%,n 不同 → 可信度天差地别")
    _row("30/50", 30, 50)
    _row("300/500", 300, 500)
    r = width(wilson_ci(30, 50)) / width(wilson_ci(300, 500))
    print(f"   → Wilson 宽度比 = {r:.2f}×  (n 扩大 10 倍,宽度约缩小 √10 ≈ 3.16 倍)\n")

    print("② 极端比例:正态近似彻底失效(两种不同的病)")
    _row("20/20 (100%)", 20, 20)
    _row("0/20 (0%)", 0, 20)
    print("   → 病症 A:p=0 或 1 时 Normal 宽度恰为 0,声称『绝对确定』——显然荒谬")
    _row("19/20 (95%)", 19, 20)
    _row("1/20 (5%)", 1, 20)
    print("   → 病症 B:接近边界时 Normal 区间越出 [0,1](上界 >100% / 下界 <0%)")
    print("   → Wilson 两种情况都给出合理且落在 [0,1] 内的区间\n")

    print("③ 要把 CI 宽度减半,n 要几倍?")
    for n in (50, 100, 200, 400, 800):
        print(f"   n={n:4d}  p=60%  Wilson 宽度 = {width(wilson_ci(int(0.6*n), n)):.2%}")
    print("   → 宽度 ∝ 1/√n:宽度减半需要 n 变 4 倍\n")

    print("④ benchmark 常见规模下,一个点的差距意味着什么")
    for n in (89, 97, 220):
        w = wilson_ci(int(0.5 * n), n)
        print(f"   n={n:4d}  p=50%  Wilson [{w[0]:.1%}, {w[1]:.1%}]  半宽 ±{width(w)/2:.1%}")
