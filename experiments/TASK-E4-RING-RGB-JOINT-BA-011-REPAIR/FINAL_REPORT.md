# TASK-E4-RING-RGB-JOINT-BA-011-REPAIR-CONTINUE — FINAL_REPORT

**STATUS: `J2-v0 COMPLETE` / `AWAITING_RA_REVIEW`**

## 0. 一句话

**J2-v0 已在 G03/005 的 16 个真实视角上完整跑通（16/16 有效相机、无 CAD_INVALID、无崩溃）。它不再像 011 那样崩坏，但也没有优于 B0：held 2.427 vs 2.376 px，Ring 略差。**

## 1. 配对结果（同一进程、同一 ini/X/tids/support/ref，v0）

| 指标 | B0-v0 | J2-v0 | 差异 |
|---|---:|---:|---:|
| Inner MAE (px) | **1.018** | 1.208 | +0.19 |
| Outer MAE (px) | **1.660** | 2.004 | +0.34 |
| Ring 原始边界 MAE（两曲线取最小） | **0.977** | 1.631 | +0.65 |
| RGB Held 中位 (px) | **2.376** | 2.427 | +0.05 |
| RGB Held p95 (px) | 4.387 | **4.325** | −0.06 |
| 正深度比例 | 0.986 | 0.987 | — |
| 有效视角 | 16/16 | 16/16 | — |
| 相机中心变化 | — | 均值 **0.11 mm**，最大 0.22 mm | |
| 相对旋转变化 | — | 均值 **0.17°**，最大 0.39° | |
| BA 状态 | nfev=60, success=False | nfev=60, success=False | 均达到函数预算 |

`success=False` 只表示 `least_squares` 用尽 `max_nfev=60`，不是失败；两臂同样记录。

## 2. 三个确定原因

### 原因 A：011 的 52.19 px 来自版本选择 + 崩溃（已证实）

011 中 B0 选 v0、J2 选 v1。本轮强制 v0 后，J2 的 held 从 52.19 回到 **2.427**。**这说明 011 的灾难性退化主要是执行偏差。**

### 原因 B：CAD_INVALID 会让 BA 直接崩溃（已修复）

优化会把相机推入 `invalid torus apparent-contour regime`（相机离环过近）。旧代码未捕获 → 崩溃；只加常数惩罚又会导致残差长度不一致（27637 vs 27635）→ 广播错误。

**修复**：几何合法性裕度
```
min_θ l(θ) > r,  l(θ)=sqrt((Cx cosθ + Cy sinθ − R)² + Cz²)
margin = min_θ l(θ) − r
barrier = sqrt(3)·max(0, 0.30 − margin)/0.10   （连续、有方向）
```
barrier 固定 2 行，任何分支（含异常回退）都返回相同长度 → 稀疏 Jacobian 稳定。

### 原因 C：Ring 项现在被 RGB 压制 → 相机几乎不动

相机只移动 0.11 mm / 0.17°，所以 Ring 误差基本保持 B0 水平，只被轻微扰动变差一点。
**即：在当前权重下，Ring 与 RGB 相容，但 Ring 没有获得足以改进几何的杠杆。**

## 3. 回答

- **Q1 完成 16 视角联合 BA？** ✅ 完成，16/16 有效，无崩溃。
- **Q2 Inner/Outer MAE？** J2：**1.208 / 2.004 px**（B0：1.018 / 1.660）。
- **Q3 RGB Held？** **2.427 px**（B0：2.376；p95 4.325 vs 4.387）。
- **Q4 相机变化？** 中心 0.11 mm（max 0.22）、旋转 0.17°（max 0.39°）——**没有异常漂移**。
- **Q5 双轮廓与 RGB 能否一致解释？** **能共存**（held 只差 0.05 px），但 Ring 也没有因此改善；当前是"互不干扰"而非"互相增强"。
- **Q6 冲突来源？** 不是 CAD 有效域（barrier 已消除），不是权重装配错误；是**权重平衡**：Ring 项相对 RGB 太弱，无法改变相机。
- **Q7 可否推广？** **暂不**。先做一次预注册的 `λ_C ∈ {0.5, 1, 2}` 单机制扫描，看是否存在"Ring 改善且 held 不退化"的窗口。

## 4. 交付

- `runs/G03_005/{B0,J2}/cameras.npz`（c2w、K、points、track_ids、ref、version）+ `ba_info.json`
- `metrics/{PAIRED_BA_RESULTS,PER_VIEW_RESULTS,CAMERA_CHANGES}.csv`
- `metrics/PRE_RUN_FAIRNESS_CHECK.json`（版本、ref、ini/X/tids SHA、tracks SHA）
- `visualization/A_ring_projection/G03_005_B0_vs_J2.png`（DXY vs B0/J2 的 CAD 投影）
- `visualization/C_camera_network/G03_005_network.png`（两臂相机中心与光轴 + Ring CAD）

## 5. 未完成

- 权重扫描（λ_C）——下一步唯一实验；
- 图 B（RGB 重投影，train/held 分开）——`train_mae` 本轮为 NaN（点-轨迹索引未对上），未伪造；
- 相机中心/旋转的逐视角图（CSV 已有，图未画）。
