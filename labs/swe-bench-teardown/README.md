# Lab · SWE-bench Teardown

**从 JSON → Docker image → gold patch → test_patch → grading report 完整跑一遍,并记录每一步的源码入口。**

> 本 README 里的**所有输出都是真跑出来的**(2026-08,`SWE-bench_Verified` / `astropy__astropy-13398`),不是示意。

---

## 为什么是这个 lab

第 3 课的命题是:
> **SWE-bench evaluator ≠ SWE-bench agent environment。**

光读源码说服力不够。这个 lab 让你**亲手把四种 prediction 喂进真 harness**,看它输出四种**不同类别**的结果 —— 那张 failure taxonomy 表是跑出来的,不是背来的。

---

## 快速开始

```bash
# ① 拆实例:看 agent 能看到什么 / grader 独占什么,并生成四份 prediction
python3 labs/swe-bench-teardown/teardown.py

# ② 依次跑四个实验(每个约 2–4 分钟,首次会拉 ~2GB 镜像)
bash labs/swe-bench-teardown/run.sh gold
bash labs/swe-bench-teardown/run.sh empty
bash labs/swe-bench-teardown/run.sh partial
bash labs/swe-bench-teardown/run.sh malformed
```

**环境要求**:Docker · ~10 GB 磁盘 · 能访问 DockerHub(`swebench/` 命名空间)。
**harness 用的是 clone 版**(`../agent-sandbox-course/code/SWE-bench`),不是 pip 版 —— 见下文「踩到的坑 ①」。

---

## 实例:`astropy__astropy-13398`

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
environment_setup_commit  cdf311e0714e…   ← 装依赖用的 commit,与 base_commit 不同
```

> **判分契约**:`resolved = 4 个 FAIL_TO_PASS 全过 AND 68 个 PASS_TO_PASS 仍过` = **72 个断言全绿**。

---

## 四个实验 · 真实结果

| 实验 | prediction 内容 | harness 输出 | 说明 |
|---|---|---|---|
| **gold** | 官方参考解法 | `resolved: 1` | ✅ evaluator 本身工作正常 |
| **empty** | `""` | **`empty patches: 1`** | ⚠️ **不计入 unresolved** —— 单独一类 |
| **partial** | 只保留 gold 的第一个文件(加了个 import,但被 import 的模块不存在) | `unresolved: 1` | patch 应用成功,但测试挂 |
| **malformed** | 指向不存在文件的假 diff | **`errors: 1`** | ⚠️ 连 apply 都失败 —— 又是一类 |

### gold 的判分明细(真实 `report.json`)
```
resolved: True | patch applied: True
  FAIL_TO_PASS   success=  4  failure=0
  PASS_TO_PASS   success= 68  failure=0
  FAIL_TO_FAIL   success=  0  failure=0
  PASS_TO_FAIL   success=  0  failure=0
```
> 72 个断言全绿,与契约完全一致。

### 🔑 本 lab 最重要的收获:**四种结局,四个类别**

```
resolved        →  真的修好了
unresolved      →  patch 应用了,但测试没过        ← 模型能力问题
empty patch     →  agent 什么都没产出              ← 通常是 agent runtime 挂了
error           →  patch 无法 apply                ← infra / 格式问题
```

**只报 "resolved %" 的 leaderboard,把后三类混成了一个数字。**
一个 agent 得 0 分,可能是它不会修 bug(unresolved),也可能是它的 runtime 崩了(empty)——
**这两件事的改进方向完全相反。** 这就是 W6「Failure Taxonomy」要展开的东西。

---

## 踩到的两个坑(都值得记住)

### 坑 ① pip 版 harness ≠ repo 版
```
pip install swebench          → 5.0.2,不支持 --cache_level / --namespace / --force_rebuild
clone 的 SWE-bench repo       → 支持
```
症状:`run_evaluation.py: error: unrecognized arguments: --cache_level`
解法:`run.sh` 用 `PYTHONPATH=<repo> python3 -m swebench.harness.run_evaluation`。

> **教训**:讲义引用的是 repo 源码,lab 就必须跑同一份代码,否则你验证的不是你讲的东西。

### 坑 ② 「把 patch 改坏」比想象中难 ⭐
第一次造 broken patch 用的是:
```python
x["patch"].replace("+", "-", 1)
```
结果 **仍然 `resolved: True`**。

原因:整个 diff 里第一个 `+` 出现在 **`+++ b/...` 文件头**,不是代码行。`git apply` 容忍了这个畸形头。

> **教训**:**要让一个 patch 失败,必须改它「做什么」,而不是改它「怎么拼写」。**
> 改成两个真正的失败案例后才拿到 `unresolved` 和 `error` 两种不同结局。
> 这条也直接对应 Week 5「任务质量」:**你以为你造了个负例,其实没有。**

---

## 源码入口(边跑边对照)

harness 在 `../../../agent-sandbox-course/code/SWE-bench/swebench/harness/`:

| 你在跑什么 | 源码入口 |
|---|---|
| 整个评测 | `run_evaluation.py` — 参数是 `--predictions_path`,**吃已产出的 patch** |
| 建镜像 | `docker_build.py` · `dockerfiles/`(9 种语言的生成器)· `prepare_images.py` |
| 容器里执行什么 | `test_spec/python.py` — 生成 eval 脚本 |
| 判分 | `grading.py` — FAIL_TO_PASS / PASS_TO_PASS |
| 解析测试输出 | `log_parsers/` — 每个测试框架一个 parser |
| 汇总 | `reporting.py` |

### ⭐ 反作弊设计:eval 脚本会先抹掉 agent 对测试的改动
`test_spec/python.py:419-425`:
```python
reset_commands: git checkout {base_commit} {test_patch 改过的文件}
                rm -f {test_patch 新增的文件}
apply_test_patch_command: git apply -v - <<'EOF' {官方 test_patch} EOF
```
**先强制还原测试文件,再贴官方测试。** 这是「不信任 agent 碰过的东西」写进代码里 ——
也正是为什么 **agent 绝不能跑在 eval 容器里**。

---

## 产物

```
astropy__astropy-13398.json          缓存的实例
preds_{gold,empty,partial,malformed}.jsonl
logs/run_evaluation/<run_id>/…/report.json    每次运行的判分明细
logs/build_images/…                            镜像构建日志
<run_id>.<run_id>.json                          汇总报告
```

## 待做实验(留给读者)

```
[ ] 实验 3:同一个 run_id 换不同 prediction 再跑一次 → 观察 result caching 这个坑
[ ] 实验 4:docker exec 进容器,对比 agent-visible repo 与 grader-visible test_patch
[ ] 换一个多语言实例(java / js),看 dockerfiles/ 里对应的生成器
```
