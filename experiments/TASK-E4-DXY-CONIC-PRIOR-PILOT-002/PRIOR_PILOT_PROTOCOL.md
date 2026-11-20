# PRIOR_PILOT_PROTOCOL

**任务：** TASK-E4-DXY-CONIC-PRIOR-PILOT-002
**性质：** **可删除的验证态**（removable verification state）。全部先验**默认关闭**；空配置必须与冻结 A0/005 **逐位一致**（已实测 `max|camera−camera_005| = 0`）。
**基线：** `exp/TASK-E4-DXY-CONIC-RING-OBSERVATION-REUSE-001` @ `a87eac0`；A0 = `TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005` @ `ba6c4dc`。

---

## 1. 设计原则（保护现状）

| 原则 | 实现 |
|---|---|
| 不改动任何既有程序 | 005 的 `unified_camera.py`、DXY、001 任务目录均未修改；本任务只新增 `code/priors.py` 与 `code/pilot_runner.py` |
| 默认零影响 | `--priors ""`（或 `priors.ENABLED={}`）时 `compose()` **原样返回**基础残差；实测相机与 005 差 0 |
| 随时可删 | 删除本任务目录（或其 `code/`）不影响任何主线；没有 import 反向依赖 |
| 不写死 | 每个先验是 `PRIOR_FUNCS` 里的一个纯函数 + 一个权重；没有任何 `if group ==`、没有按病例分支 |
| 只用 FIT | 无 Body/GT/HERO；DXY 椭圆只读；held 只用于评价 |

---

## 2. 五个先验（全部 opt-in）

| 名 | 作用 | 依赖的 DXY 信息 | 形态 |
|---|---|---|---|
| **P1** support | 用 DXY 内外椭圆的 Sampson 距离给原始边界点做**软内点权重** `exp(-(d/2px)²)`，只缩放已有 q 项，不改几何目标 | 内/外椭圆 | 乘性权重 |
| **P2** shape | 以投影环心为极点，比较归一化径向形状 `r(θ)`；**减去每视角径向均值、除以均值半径**（偏置与尺度投影掉） | 内/外椭圆 | 追加正则项 |
| **P3** width | 管径剖面 `w(θ)=r_out−r_in`，去均值后比较 | 内外成对 | 追加正则项 |
| **P4** harmonic | 低阶谐波描述子（k=1..3）替代椭圆，比较复数系数 | 内/外椭圆 | 追加正则项 |
| **P5** offset-free conic | "修好的 A1"：极坐标下比较 CAD 轮廓与 DXY 椭圆，**减去每视角径向偏移** | 内/外椭圆 | **替换** q 项 |

组合规则（`priors.compose`）：
- 空 → 基础残差；
- 有 `P5` → q 项被替换；否则 q 项保留（P1 时乘 `sqrt(w)`）；
- `P2/P3/P4` 以 `sqrt(weight)` 追加，长度 72 或 24，BA 的稀疏结构自适应。

---

## 3. 运行

```bash
cd <task>/code
export PYTHONPATH=<ws>/src:.
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
$PY pilot_runner.py --tag P0                                  # 安全回归：应与 005 逐位一致
$PY pilot_runner.py --tag P1 --priors P1:1.0 --groups G01/004,G03/004,G03/005
$PY pilot_runner.py --tag P2 --priors P1:1.0,P2:0.1 --groups ...
$PY -m unittest discover -s tests -v                          # 8/8
```

产物：`runs/<TAG>/<G>/<V>/{camera,VALIDATION.json}`、`PILOT_<TAG>_VIEW_METRICS.csv`、`PILOT_SUMMARY.csv`、`PILOT_COMPARISON.csv`、`visualization/figures/*.png`。

---

## 4. 判据（先写死）

| 结论 | 条件 |
|---|---|
| 采纳 | 目标病例（G03/004、G02/005）held 中位下降 ≥20%，且成熟病例 G01/004 held 上升 ≤5%，且门禁通过数不降 |
| 仅诊断 | 形状改善但 held 不变 |
| 放弃 | held 上升、门限通过数下降，或初始化失败（NO_BA_VERSION） |

**禁止**：用 held 选先验/权重；按病例设权重；改门限；删困难视角。

---

## 5. 安全验证记录

| 检查 | 结果 |
|---|---|
| 空配置 == 005 相机 | G03/005，`max abs diff = 0` |
| 单元测试 | 8/8（空配置逐位一致、五先验有限性、扰动检测、P5 偏移不变性、权重边界、谐波长度、组合有限性） |
| 005/DXY/001 是否被修改 | 否（`git show --name-only` 仅本任务目录） |
