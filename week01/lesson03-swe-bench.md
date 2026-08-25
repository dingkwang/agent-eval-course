# 第 3 课:SWE-bench
## Dataset、Agent Runtime 与 Evaluation Harness 为什么必须分开

**Week 1 Day 3** · 源码 + 实验课 · 建议 90 分钟

> ### 本课唯一命题
> # SWE-bench evaluator ≠ SWE-bench agent environment
>
> 这不是措辞讲究,是**信任边界**。搞混它,你会写出一个可以被作弊的 benchmark。

```diag
compare | 管判,不管做
SWE-bench 给 | SWE-bench 不给
dataset + evaluation harness | agent runtime
全新容器 · apply patch · 跑官方测试 | 探索 repo、改代码、跑局部测试
唯一契约:一个 patch 文件 |
```

```diag
grid | 同一 harness,四种结局
resolved | gold patch,测试过
unresolved | 修了,测试不过
empty | 没产出 patch
error | runtime 崩了
```

> 📎 **本课所有输出都是真跑出来的**(2026-08,`SWE-bench_Verified` / `astropy__astropy-13398`)。
> 💻 **先做 lab,再读讲义**:`../labs/swe-bench-teardown/`

---

## 一、SWE-bench 给你 **dataset** 和 **evaluation harness**,但**不给 agent runtime**

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
│ Agent Runtime    │  ← ❌ SWE-bench 不提供 │
│ repo checkout    │                      │
│ shell/editor     │                      │
│ network policy   │                      │
└────────┬─────────┘                      │
         │                                │
    model_patch                           │
         └───────────────┬────────────────┘
                         ▼
              ┌─────────────────────┐
              │ SWE-bench Harness   │  ← ✅ SWE-bench 提供
              │ Docker              │
              │ apply patch         │
              │ apply tests         │
              │ execute tests       │
              │ parse results       │
              └──────────┬──────────┘
                         ▼
                    resolved?
```

| 组件 | SWE-bench 提供? | 证据 |
|---|---|---|
| **Dataset** | ✅ | HuggingFace,每条含 9 个字段(见 §二) |
| **Agent Runtime**(怎么产出 patch) | ❌ **不提供** | README 指向外部:*"[Apr. 2, 2024]: We have released **SWE-agent**"*;`swebench/inference/` 只有 `run_api.py`/`run_llama.py`/`bm25_retrieval.py` = **单轮基线脚本**,不是 agent loop;grep 整个 `swebench/harness/*.py` **零处调用模型**,唯一命中是 `utils.py:59` 的注释 `# compatible with SWE-agent predictions` |
| **Evaluation Harness** | ✅ 且容器化 | `run_evaluation.py` 官方入口;`dockerfiles/` 有 **9 种语言**的镜像生成器;README:*"fully containerized evaluation harness using Docker for more reproducible evaluations"* |

> ### 一句话
> **SWE-bench 管「判」,不管「做」。** 两者之间的**唯一契约是一个 patch 文件**。

---

## 二、一条真实实例里,**哪些字段 agent 看得到、哪些只有判分器看得到**

`astropy__astropy-13398`,跑 `python3 ../labs/swe-bench-teardown/teardown.py` 可复现。

### agent 看得到的
```
instance_id   astropy__astropy-13398
repo          astropy/astropy
base_commit   6500928dc0e57be8f06d1162eacc3ba5e2eff692
version       5.0
problem_statement   5,323 chars
```

### 只有 grader 看得到的(**agent 绝不能看到**)
```
patch (gold)              13,884 B, 4 files
test_patch                 7,533 B, 1 file
FAIL_TO_PASS               4    改完必须由失败转通过
PASS_TO_PASS              68    本来就过,不许弄坏
environment_setup_commit  cdf311e0714e…
```

**两个字段值得单独说**:

**`environment_setup_commit`** —— 它和 `base_commit` **不是同一个 commit**。装依赖用前者,checkout 代码用后者。
> 为什么要分开?因为「这个 bug 存在于哪个 commit」和「用哪个版本的依赖能装起来」是两件事。这是可复现性的关键设计,也是很多自制 benchmark 会漏掉的。

**`PASS_TO_PASS` 有 68 个** —— 它防的是「把测试删了就通过」。
```
resolved = 4 个 FAIL_TO_PASS 全过  AND  68 个 PASS_TO_PASS 仍过
         = 72 个断言全绿
```

### ⭐ 但「agent 看不到测试」这句话要说准

上面那张表说的是**数据集字段**。仓库本身是另一回事 —— agent 拿到的是 `base_commit` 时刻的
完整 checkout,**里面的测试它全都读得到、也跑得动**。

全 500 条 SWE-bench Verified 里,`test_patch` 到底动了什么:

```
只新建测试文件 :   3
新建 + 改已有   :  12
只改已有文件    : 485      ← 97%
```

我们这条 `astropy__astropy-13398` 就属于那 485 条 —— `test_patch` 只改一个文件
`astropy/coordinates/tests/test_intermediate_transformations.py`,而这个文件在 `base_commit`
里**本来就存在**。逐个核对那 4 个 FAIL_TO_PASS 函数在 diff 里是新增行还是上下文行:

```
test_itrs_topo_to_altaz_with_refraction     新增=True  原有=False
test_itrs_topo_to_hadec_with_refraction     新增=True  原有=False
test_cirs_itrs_topo                         新增=True  原有=False
test_itrs_straight_overhead                 新增=True  原有=False
```

所以精确的边界是:

| | agent 能看到? | |
|---|---|---|
| 测试**文件**本身 | ✅ | 仓库里本来就有 |
| 68 个 **PASS_TO_PASS** | ✅ 能读能跑 | 就在同一个文件里,是已有测试 |
| 4 个 **FAIL_TO_PASS** 的代码 | ❌ | `test_patch` 才加进去 |
| F2P / P2P 的**名字列表** | ❌ | dataset 里的 grader-only 字段 |

> **一句话**:agent 看得到「不许弄坏什么」,看不到「必须修好什么」。
> 这个不对称是故意的 —— P2P 可见无所谓,它们本来就该过;F2P 不可见才是防作弊的核心。

**连带的推论**:agent 没法「跑测试跑到绿」,因为判分的那 4 个测试还不存在。
官方参考 scaffold(`mini-swe-agent`,`config/benchmarks/swebench.yaml:30-36`)的措辞也印证了这点:

```
2. Create a script to reproduce the issue        ← 自己写复现脚本
4. Verify your fix works by running your script again   ← 跑自己写的
```

```
agent 的「绿」  = 它自己写的复现脚本过了
harness 的「绿」= 官方那 4 + 68 个测试过了
```

**两套不同的测试。** SWE-bench 考的不是「跑到测试通过」,是「猜中出题人会怎么测」。

---

## 三、⭐ 四种 patch 喂进**同一个** harness,得到**四种不同的结局**

> 这是本课的核心。四种 prediction 喂进**同一个** harness,得到**四种不同类别**的结果。

| 实验 | prediction | harness 输出 |
|---|---|---|
| **gold** | 官方参考解法 | `Instances resolved: 1` |
| **empty** | `""` | **`Instances with empty patches: 1`** |
| **partial** | 只保留 gold 的第一个文件(加了 import,但被 import 的模块不存在) | `Instances unresolved: 1` |
| **malformed** | 指向不存在文件的假 diff | **`Instances with errors: 1`** |

### gold 的判分明细(真实 `report.json`)
```
resolved: True | patch applied: True
  FAIL_TO_PASS   success=  4  failure=0
  PASS_TO_PASS   success= 68  failure=0
  FAIL_TO_FAIL   success=  0  failure=0
  PASS_TO_FAIL   success=  0  failure=0
```
72 个断言全绿,与 §二 的契约**完全一致**。这同时证明了:**evaluator 本身是好的**。

### 🔑 四种结局 = 四个类别

```
resolved        →  真的修好了
unresolved      →  patch 应用了,但测试没过        ← 模型能力问题
empty patch     →  agent 什么都没产出              ← 通常是 agent runtime 挂了
error           →  patch 无法 apply                ← infra / 格式问题
```

> **只报 "resolved %" 的 leaderboard,把后三类混成了一个数字。**
> 一个 agent 得 0 分,可能是它不会修 bug(unresolved),也可能是它的 runtime 崩了(empty)——
> **这两件事的改进方向完全相反。**
> ⟹ 这就是 **W6 Failure Taxonomy** 的起点,也是为什么 SWE-bench 官方后来把 infra failure 与正常 unresolved 区分开。

**对照 Day 2 的 oracle 原则**:gold patch 之于 SWE-bench,就是 `solution.sh` 之于 Terminal-Bench ——
**先证明尺子是准的,再用它量东西。**

---

## 四、为什么 agent **绝不能**跑在 eval 容器里 —— 反作弊是写死在代码里的

为什么 agent **绝不能**跑在 eval 容器里?看 eval 脚本的生成顺序(`test_spec/python.py:419-425`):

```bash
git checkout {base_commit} {test_patch 改过的文件}   # ← 抹掉 agent 对测试的任何改动
rm -f {test_patch 新增的文件}                        # ← 删掉 agent 可能造的假测试
git apply -v - <<'EOF' {官方 test_patch} EOF         # ← 再贴上权威测试
# 然后才跑测试
```

**先强制还原测试文件,再贴官方测试。** 这是「**不信任 agent 碰过的任何东西**」写进代码里。

三条理由:
1. **反作弊** —— agent 改不了判分标准
2. **确定性** —— 每个 instance 起**全新**容器,agent 装过的包、改过的 env 不会污染判分
3. **verifier independence** —— verifier 必须在 agent 够不到的地方

> ⚠️ 但注意:**agent 自己也需要一个 sandbox**,只是不是这一个。
> ```
> Agent sandbox   ← SWE-bench 不管,SWE-agent 等自带  (探索 repo、改代码、跑局部测试)
> Eval sandbox    ← SWE-bench 提供                    (全新容器 → apply → 跑官方测试 → 判分)
> ```

---

## 五、跑 lab 时,**每一步该翻哪个源码文件**

`../agent-sandbox-course/code/SWE-bench/swebench/harness/`:

| 你在跑什么 | 源码入口 |
|---|---|
| 整个评测 | `run_evaluation.py` —— 参数是 `--predictions_path`,**吃已产出的 patch** |
| 建镜像 | `docker_build.py` · `dockerfiles/`(python/java/js/go/rust/c/php/ruby)· `prepare_images.py` |
| 容器里执行什么 | `test_spec/python.py` —— 生成 eval 脚本 |
| 判分 | `grading.py` |
| 解析测试输出 | `log_parsers/` —— **每个测试框架一个 parser** |
| 汇总 | `reporting.py` |
| 云端执行 | `modal_eval/` |

> **镜像分层**(W2 会展开):`base → env → instance`。`--cache_level` 控制保留哪一层。

---

## 六、两个真踩过的坑:**装错版本**,和**「以为造了个负例,其实没有」**

### 坑 ① pip 版 harness ≠ repo 版
```
pip install swebench   → 5.0.2,不支持 --cache_level / --namespace / --force_rebuild
clone 的 repo          → 支持
```
症状:`run_evaluation.py: error: unrecognized arguments: --cache_level`

> **教训**:讲义引用的是 repo 源码,lab 就必须跑同一份代码,**否则你验证的不是你讲的东西**。

### 坑 ② 「把 patch 改坏」比想象中难 ⭐
第一次造 broken patch 用的是:
```python
x["patch"].replace("+", "-", 1)
```
结果 **仍然 `resolved: True`**。

原因:整个 diff 里第一个 `+` 出现在 **`+++ b/...` 文件头**,不是代码行。`git apply` 容忍了这个畸形头。

> **教训**:**要让一个 patch 失败,必须改它「做什么」,而不是改它「怎么拼写」。**
> 更普适的版本 —— **你以为你造了个负例,其实没有。** 这条会在 **W5 任务质量** 再遇到:
> 一个没有真正区分能力的任务,和一个坏掉的负例,在数据里长得一模一样。

---

## 七、Hands-on:**四条命令,复现上面那四种结局**

```bash
python3 ../labs/swe-bench-teardown/teardown.py          # 拆实例 + 生成四份 prediction
bash    ../labs/swe-bench-teardown/run.sh gold          # 应 resolved
bash    ../labs/swe-bench-teardown/run.sh empty         # empty patch(不是 unresolved!)
bash    ../labs/swe-bench-teardown/run.sh partial       # unresolved
bash    ../labs/swe-bench-teardown/run.sh malformed     # error
```

**留给你的两个实验**:
```
[ ] 实验 3:同一个 run_id 换不同 prediction 再跑一次 → 观察 result caching 这个坑
[ ] 实验 4:docker exec 进容器,对比 agent-visible repo 与 grader-visible test_patch
```

---

## 八、本课自检:**这七件事你能不能说清**

```
[ ] 1. 能说清 dataset / agent runtime / evaluation harness 为什么是三件事
[ ] 2. 能说出 SWE-bench 提供哪两件、不提供哪一件,并给出源码证据
[ ] 3. 能解释 base_commit 与 environment_setup_commit 为什么分开
[ ] 4. 能解释 PASS_TO_PASS 防的是什么
[ ] 5. 能说出四种 harness 结局及各自意味着什么
[ ] 6. 能指出 eval 脚本里的反作弊那三行,并说明为什么 agent 不能在 eval 容器里
[ ] 7. 能说出「你以为你造了个负例,其实没有」是怎么发生的
```

---

## 本课一句话总结

> **SWE-bench 的精髓不在数据集,在那条 patch 契约:agent 在外面做,harness 在里面判,中间只传一个 diff。**
> 这条边界让它可复现、可防作弊 —— 也让「agent 环境」成了你自己的责任。

---

**上一课(Day 2)**:[Terminal-Bench 深读](lesson02.md)。
**下一课(Day 4)**:[τ³-bench](lesson04-tau3-bench.md) —— 从 repo state 走向 **application state + user state + conversational trajectory**,以及 verifier 为什么会裂成四个。
