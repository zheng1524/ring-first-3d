# TASK-E4-RING-RGB-J2-CORRECTION-012 — FINAL_REPORT

**STATUS: `J2 VERIFIED & RE-EVALUATED`（未重跑 BA；有证据表明无需重跑）**

## 0. 本轮最重要的事实

**修复后的模块与 011-REPAIR 的模块在全部 16 个 B0 位姿上输出完全相同（max|diff| = 0.0）。**
所以已有的 J2-v0 相机**就是**修正版 J2 的结果——不是用旧代码凑数，而是修复项确实不改变有效区域内的数值路径。

证据链：
1. `cad_margin()` 公式**本来就是对的**（见 §2.1，解析 vs 20 001 角度数值搜索，60 组随机位姿误差 <1e-3 mm）。
2. CAD_INVALID 从未触发：16 个视角 margin 最小值 **25.10 mm**（阈值是 0）。
3. 两版 `blocks()` 在同一组位姿上逐元素相同。

## 1. 修复清单

| 项 | 011-REPAIR | 012 修正 |
|---|---|---|
| 异常回退 | `np.full(n+2, 50.0)`（常数，无梯度） | 只捕获 `apparent-contour` 的 `ValueError`；回退值 **由 `cad_margin` 计算的位姿相关惩罚**（有梯度） |
| 遮障 | 无解析依据 | `margin = min_θ l(θ) − r`，连续 barrier，长度恒为 2 行 |
| 原始边界评价 | `min(mean→inner, mean→outer)`（错） | **逐观测点取 min 再求均值**（正确） |
| RGB Train | `NaN` | 用 `point_track_ids`（int 索引）正确对齐，B0 = **0.877 px** |
| B0/J2 评价分母 | 不同 | 同一函数重算两臂 |

## 2. 关键审计结果

### 2.1 CAD 合法性裕度（已证明原公式正确）

解析：`min_θ l(θ) = sqrt(max(0, R−d)² + Cz²)`，`d = hypot(Cx, Cy)`。
与 20 001 点角度搜索对比，60 组随机位姿（含 d<R、d=R、d>R、Cz≈0）误差 < 1e-3 mm。
**因此任务书 §3.1 所述"部分位置不正确"不成立**——但测试与 barrier 现在有了完整覆盖。

### 2.2 真实损失与梯度（B0 相机，16 视角平均）

| 块 | 数值 |
|---|---:|
| Inner MAE | 0.973 px |
| Outer MAE | 1.675 px |
| 原始边界（逐点 min，修复后） | **0.844 px** |
| Ring 能量 `E_ring = Σr²` | 6.66 |
| Barrier 能量 | 0（margin 25 mm，远离无效区） |
| RGB Train MAE | 0.877 px |
| Ring 梯度（每视角，SE(3) 统一尺度） | \|rot\| 0.6，\|trans\| 14.9 |
| 可信内/外弧 | 698/720、708/720 |

**回答"Ring 是否有能力推动相机"**：有——平移方向梯度量级 14.9，不是零。
但 RGB 训练能量（约 3×N_obs×σ²，N_obs≈90/视角 → 10³ 量级）压倒 Ring（6.7），
所以实际位移只有 0.11 mm。**不是 bug，是权重平衡。**

## 3. 修正后的比较（同一评价器重算两臂）

| 指标 | B0 | J2 |
|---|---:|---:|
| Inner MAE | **0.973** | 1.134 |
| Outer MAE | **1.675** | 2.018 |
| 原始边界（逐点 min） | **0.844** | 1.528 |
| Ring 能量 | 6.66 | 8.04 |
| RGB Held 中位 | **2.376** | 2.427 |
| 相机中心 Δ | — | 0.11 mm（max 0.22） |
| 旋转 Δ | — | 0.17°（max 0.39） |
| margin 最小值 | 25.10 mm | 25.10 mm |

## 4. 回答

- **Q1 原 J2 的具体错误？**
  *已确认*：① 原始边界评价公式错（min-of-means → 应为每点 min）；② RGB Train 因点-轨迹用字符串键而全 NaN；③ 异常回退是常数残差（无梯度）。
  *不成立*：`cad_margin` 公式错误（已验证正确）。
  *潜在*：无。CAD_INVALID 在本数据上从未触发。
- **Q2 修复后是否实现预期联合损失？** 是。Ring 块经 `sqrt(rglen/counts)` 抵消冻结缩放后权重 = 1，材料/背景块未被改动（`tail` 逐字节来自冻结 `ring_residual`）；barrier 恒占 2 行。
- **Q3 Inner/Outer 的实际贡献？** `E_inner=1.44`、`E_outer=5.23`（B0 处），梯度存在但被 RGB 压制两个数量级。
- **Q4 修复后的 J2 比旧 J2 更好吗？** **数值完全相同**（模块输出 max|diff|=0）。修正影响的是**评价与鲁棒性**，不是这次的相机数值。
- **Q5 J2 vs B0？** 各项略差：inner +0.16、outer +0.34、raw +0.68、held +0.05 px。**J2 不优于 B0。**
- **Q6 是否达到稳定状态？** **不能宣称严格收敛**：两臂均为 `nfev=60, success=False`（函数预算耗尽），本轮未做目标函数趋势/梯度范数检查。
- **Q7 是否具备进入下一轮矩阵的条件？** **NO**。理由：① 未证明收敛；② Ring 与 RGB 权重相差两个数量级，当前配置下 Ring 实际不起作用；③ 需要先把"共同收敛判据 + 一次预注册 λ_C 对照"做完，否则矩阵实验只会重复测同一件事。

## 5. 未完成

- 图 B（RGB 重投影，train/held 分开）；
- 收敛性检查（目标趋势、梯度范数）与同预算增额重跑；
- λ_C 对照（按要求本轮不做矩阵）。

## 6. 交付

`code/j2_obs_correct.py`、`code/audit_loss.py`、`tests/test_cad_margin.py`（4/4 通过）
`metrics/{LOSS_COMPONENTS,GRADIENT_DIAGNOSTICS,PER_VIEW_RESULTS,METHOD_COMPARISON,MODULE_EQUIVALENCE}.csv`
`visualization/A_ring/G03_005_A.png`、`visualization/C_camera/G03_005_C.png`
