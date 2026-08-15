# 第 4 课:这个分数能不能信?
## Bernoulli · 标准误 · Wilson 置信区间

**Week 1 Day 4** · 编码日 · 建议 60 分钟

> 📎 **素材锚点**:⭐ `papers/error_bars_in_evals.pdf`(*Adding Error Bars to Evals*,arXiv 2411.00640)· `papers/codex_passk.pdf`(pass@k 出处,arXiv 2107.03374)
> 💻 **本课代码**:`labs/wilson.py`(**下文所有数字都是它真跑出来的**,不是估算)

---

## 一、为什么这一课必须在第一周

Day 1–3 你学会了「一个分数由七个因子决定」。但还差最关键的一问:

> **这个分数本身,有多大的不确定性?**

Error Bars 论文开篇一句话就把问题点破(原文):

> *"Fundamentally, **evaluations are experiments**; but the literature on evaluations has largely **ignored the literature from other sciences on experiment analysis and planning**."*

**evaluation 是实验。** 实验就要报误差棒。一个不带置信区间的 leaderboard 分数,在科学上是不完整的。

论文的章节结构本身就是本课程统计部分的路线图:
```
2 Analysis framework   ← 本课 + Week 4
3 Variance reduction   ← Week 4
4 Comparing models     ← Week 4(paired bootstrap / McNemar)
5 Power analysis       ← Week 4 进阶
A Clustered standard errors ← Week 4(同一任务多次 repeat 的正确处理)
```

---

## 二、Bernoulli:agent 成功率的底层模型

一个任务跑一次,结果非成即败:

```
y ~ Bernoulli(p)      y ∈ {0,1},P(y=1) = p
```

跑 n 次独立试验,成功 k 次:

```
k ~ Binomial(n, p)
p̂ = k / n                      ← 我们观测到的分数
SE(p̂) = sqrt( p(1-p) / n )     ← 标准误
```

**三条直觉**:
1. **SE ∝ 1/√n** —— 想让误差减半,样本要变 **4 倍**
2. **p 越接近 0.5,SE 越大** —— 中等难度的 benchmark 最"吵"
3. **SE 不是误差本身,是「p̂ 这个估计量的波动幅度」**

---

## 三、为什么不能用正态近似(Wald 区间)

最常见的写法:

```
p̂ ± 1.96 · sqrt( p̂(1-p̂)/n )        ← Wald / 正态近似
```

它在 p 靠近 0 或 1、或 n 小的时候**会给出荒谬结果**。以下是 `labs/wilson.py` 的**真实输出**:

### 病症 A:p = 0 或 1 时,宽度恰好为 0
```
20/20 (100%)   Wilson [ 83.9%, 100.0%]  w=16.1%  |  Normal [100.0%, 100.0%]  w= 0.0%
 0/20   (0%)   Wilson [ -0.0%,  16.1%]  w=16.1%  |  Normal [  0.0%,   0.0%]  w= 0.0%
```
> 20 次全成功,Wald 说「我 95% 确信真实成功率**恰好**是 100%」。
> 这显然错 —— 只跑 20 次,真实成功率是 90% 也完全可能。**Wilson 给出 [83.9%, 100%],这才对。**

### 病症 B:接近边界时越出 [0,1]
```
19/20 (95%)    Wilson [ 76.4%,  99.1%]  |  Normal [ 85.4%, 104.6%]   ← 上界 >100% ❌
 1/20  (5%)    Wilson [  0.9%,  23.6%]  |  Normal [ -4.6%,  14.6%]   ← 下界 <0%   ❌
```

> **结论:agent eval 的成功率经常落在极端区间(很难的任务接近 0,很简单的接近 1),所以正态近似在这个领域格外危险。默认用 Wilson。**

---

## 四、Wilson 区间

$$
\text{center} = \frac{\hat p + \frac{z^2}{2n}}{1 + \frac{z^2}{n}}, \qquad
\text{half} = \frac{z\sqrt{\frac{\hat p(1-\hat p)}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}
$$

代码(`labs/wilson.py`):
```python
def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    denom  = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half   = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return center - half, center + half
```

**为什么它更好**:它不是「以 p̂ 为中心加减」,而是**反解**「哪些真实 p 值能以 95% 概率产生我观测到的 k/n」。所以它天然把中心往 0.5 拉一点,并且**永远落在 [0,1] 内**。

---

## 五、三个必须做出来的结论

### 结论 1 · 同样是 60%,n 不同,可信度天差地别(真实输出)
```
 30/50    p=60%   Wilson [46.2%, 72.4%]   宽度 26.2%
300/500   p=60%   Wilson [55.6%, 64.2%]   宽度  8.6%
                                          宽度比 = 3.06×
```
> 两个都写作「60%」。但第一个的真实值可能低到 46%,第二个被锁在 56–64%。
> **在排行榜上并列的两个 60%,可能一个是噪声、一个是事实。**

### 结论 2 · 宽度 ∝ 1/√n,减半要 4 倍样本(真实输出)
```
n= 50  宽度 26.21%
n=100  宽度 18.86%
n=200  宽度 13.46%      ← 相比 n=50 减半(26.21 → 13.46),n 变 4 倍
n=400  宽度  9.56%
n=800  宽度  6.77%
```

### 结论 3 · 真实 benchmark 规模下,误差棒有多大(真实输出)
```
n= 89 (Terminal-Bench)  p=50%  Wilson [39.3%, 59.6%]  半宽 ±10.2%
n= 97 (τ³-Banking)      p=50%  Wilson [39.7%, 59.3%]  半宽 ± 9.8%
n=220 (GDPval-AA)       p=50%  Wilson [43.4%, 56.6%]  半宽 ± 6.6%
```

> ### 🔥 本课最重要的一句
> **Terminal-Bench 只有 89 个任务。在 p≈50% 处,单次评测的 95% 区间半宽约 ±10 个百分点。**
> **⟹ 排行榜上相差两三个点的模型,在统计上很可能无法区分。**
>
> (注:实际 AA 每任务跑 3 次,有效样本更大、区间更窄;但同一任务的多次 repeat **不是独立样本**,不能简单当作 n=267 —— 正确处理见 Error Bars 论文附录 A "Clustered standard errors",Week 4 展开。)

---

## 六、repeated pass@1 ≠ pass@k(接 Day 1)

pass@k 的原始定义来自 Codex 论文(`papers/codex_passk.pdf`)。无偏估计式:

$$
\text{pass@}k = \mathbb{E}_{\text{tasks}}\left[\, 1 - \frac{\binom{n-c}{k}}{\binom{n}{k}} \,\right]
$$

其中每任务采 n 个样本、其中 c 个正确。

| | 公式 | 回答 |
|---|---|---|
| **repeated pass@1** | 所有 (任务, repeat) 的成功率平均 | 随机跑一次的成功概率 |
| **pass@k** | 每任务「k 次里至少一次成功」的概率,再对任务平均 | 允许 k 次尝试的成功概率 |

**数值关系**:`pass@k ≥ pass@1`,且**方差越大的模型,从 pass@k 中获益越多**。
> ⟹ 一个不稳定但偶尔灵光的模型,在 pass@8 上可能反超一个稳定的模型。**报哪个指标,就是在选择奖励哪种行为。**

---

## 七、动手任务

### 任务 1(必做):跑通并读懂
```bash
python3 labs/wilson.py
```
逐段对照本文的四组输出,确认你能解释**每一行为什么长这样**。

### 任务 2:扩展代码
在 `labs/wilson.py` 里加两个函数:
```python
def n_for_width(target_width: float, p: float = 0.5, z: float = 1.96) -> int:
    """要达到给定 CI 宽度,至少需要多少任务?"""

def pass_at_k(n: int, c: int, k: int) -> float:
    """Codex 论文的无偏 pass@k 估计(用 1 - C(n-c,k)/C(n,k))"""
```
用它们回答:
1. 想把 p≈50% 处的 95% 区间半宽压到 **±3%**,需要多少个任务?
2. 某任务采 n=5、成功 c=2:pass@1、pass@2、pass@5 分别是多少?

### 任务 3:回到真实排行榜
从 AA 快照里挑两个分数接近的模型(差距 < 3 个点),用 Wilson 估算各自的区间,回答:
> **仅凭公开分数,你能断言谁更强吗?还需要什么信息才能断言?**
> (提示:你需要的是 **paired** 比较 —— 是否跑了相同任务集。Week 4 学 paired bootstrap 和 McNemar。)

📁 产出 → `notes/day4-ci-findings.md`

---

## 八、报告规范(从今天起遵守)

写任何 eval 结果时:

```
[ ] 报 n(任务数)和 R(每任务 repeat 数),不只报百分比
[ ] 报置信区间(默认 Wilson),不只报点估计
[ ] 说明是 repeated pass@1 还是 pass@k
[ ] 比较两个系统时,说明是否跑了相同任务集(paired 与否)
[ ] 说明 grader / harness / 预算版本
[ ] 不写「A 比 B 强」,除非区间不重叠或做过 paired 检验
```

---

## 本课一句话总结

> **evaluation 是实验,实验必须报误差棒。** 在 89 个任务上 50% 的成绩,真实值可能在 39% 到 60% 之间 —— 排行榜上两三个点的差距,常常什么都不说明。

---

**下一课(Day 5)**:把 GDPval-AA、τ³-Banking、Terminal-Bench 放在同一张表里横向解剖,并练习「怎么 game 它」。
