# DXY_RING_OBSERVATION_CONTRACT

**性质：** 三维侧与 DXY 二维几何之间的接口契约。DXY 只读；本文件定义"取什么、怎么换算、怎么加权、失败怎么办"。

---

## 1. 调用方式（只读）

```
解释器：/usr/bin/python3（唯一同时具备 skimage 与 cv2 的环境；主 venv 无 skimage）
路径：  PYTHONPATH=/home/liu/new-polyp-dxy/src
调用：  from dxy_mid._engine import ring_component as RC
        base, payload = RC.recover(labels_360x640, BGR_image, inner_diameter_mm=10.0)
导出：  每视角一个 JSON -> metrics/DXY_OBSERVATIONS/<view>.json
```

- DXY 源码、配置、权重、39 组结果、评价指标**均未修改**。
- 三维侧不 import DXY，只读 JSON，避免把 skimage 依赖带进主线。
- `inner_diameter_mm = 10.0`：DXY V9.1 主线使用的 R10 内径（与冻结 CAD `R=5.6, r=0.6` 一致：内径 = 2(R−r) = 10.0）。

---

## 2. 每个视角必须取到的字段

| 字段 | 含义 | 用途 |
|---|---|---|
| `valid` | DXY 是否成功恢复环几何 | 失败时**不删除视角**，该视角回退到原始边界项并记录 |
| `branch` | `visible_inner_arc_RANSAC`（直接内弧）或 `centerline_symmetry*`（推断） | 推断分支权重 ×0.6 |
| `inner` | `{cx, cy, major_radius, minor_radius, angle_deg}` | **内 Conic**，主观测 |
| `outer` | 同上 | **外 Conic**，主观测 |
| `centerline` | 内外平均 | 仅用于初始化/一致性检查，**不与内外等权相加** |
| `diagnostics.inner_arc_coverage` | 可见弧覆盖 | 权重因子 |
| `diagnostics.inner_normalized_residual` | 归一化拟合残差 | 权重因子 |
| `diagnostics.inner_sector_instability` | 扇区稳定性 | 权重因子 |
| `diagnostics.center_gap_norm` / `wire_*` / `angle_gap_deg` | 内外一致性、线材厚度 | 诊断记录 |

---

## 3. 坐标契约

- DXY 输出为**原图 360×640 像素**；005 的 Ring 观测（`observe`）与 `torus_contours` 也使用同一坐标系。
- 本轮**不存在**缩放重采样，因此不需要 `C' = H^{-T} C H^{-1}` 的非等比换算。契约中保留该式作为将来换分辨率时的强制规则，禁止对各椭圆参数直接乘同一系数。
- Conic 在构造后按 Frobenius 范数归一化（`||C||=1`），使不同尺寸的椭圆残差可比。

---

## 4. 置信度权重（连续，非硬门控）

```
w = clip(coverage, 0.2, 1.0)
    * 1/(1 + 10*normalized_residual)
    * 1/(1 + 5*sector_instability)
    * (1.0 if branch == visible_inner_arc_RANSAC else 0.6)
w = clip(w, 0.05, 1.0)
```

- 不使用固定 `min_area`，不按病例设定阈值。
- DXY `valid=False`：该视角 `dxy_*_conic` 缺省，Ring 项回退为原始边界（与 A0 相同），并在 `CAMERA_PROVENANCE` 标 `DXY_FALLBACK`。

---

## 5. 残差接口

```
ring_residual(pose, ob, part='train', K) -> vector
```

- `ob['dxy_inner_conic'] (3×3)`、`ob['dxy_outer_conic'] (3×3)`、`ob['dxy_*_weight']` 由契约 §3/§4 预写入观测文件。
- CAD 轮廓：`torus_contours(pose, K)` 返回两条闭合曲线，按**围成面积**分为内/外（不假设顺序）。
- 每条曲线取 64 个等间隔点，计算到对应 Conic 的 Sampson 距离，乘以 `sqrt(w)`，拼成残差向量。
- A2 额外附加 `sqrt(0.2) × 原始边界残差`（轮廓级最近点距离，不是固定点对点）。
- BA 优化器、预算、`jac_sparsity` 结构不变。

---

## 6. 禁止事项（写入代码断言/审计）

1. 不修改 DXY 任何文件，不重跑 DXY 主线评价。
2. 不另行实现竞争性的二维椭圆拟合器。
3. 不把 `centerline` 当作第三个独立观测。
4. 不使用点对点固定对应替代轮廓残差。
5. 不用 DXY 的 `mm_per_rectified_px` 或直径输出参与位姿求解（那是 DXY 的测量主线，不是本任务的输入）。
6. 不因 DXY 失败而删除视角。

---

## 7. 来源指纹

- DXY 源码 SHA256 记录于 `metrics/INPUT_SHA256.json`（`ring_component.py` 等）。
- 每视角 JSON 记录 `cache` 路径与导出时间；`metrics/DXY_OBSERVATIONS/INDEX.json` 给出 80 个视角的 `valid/branch` 汇总。
