# LANDMARK_IDENTITY_REPORT

## 单视频三维地标（历史 `features019.landmarks`，仅 FIT 视角）

| 视频 | FIT 视角 | 合格地标 | 说明 |
|---|---:|---:|---|
| 004 | 3 | **317** | 3 视角要求使轨迹数下降（023 全视角为 738） |
| 005 | 8 | **806** | 023 全视角为 1213 |

质量门沿用历史：≥3 视角、MAGSAC 内点、Sampson<4 px、正深度、max reproj<2 px、parallax>0.5°、|X|<300。

## 跨视频候选身份（历史 `match_desc`，ratio 0.72 + mutual）

**15 个候选**（023 用全部地标时为 24 个）。每个候选都记录：
`landmark_004/005`、两侧支持视角数与视角名、两侧三维坐标、三维残差、RANSAC 内点、最终状态。

| 状态 | 数量 | 含义 |
|---|---:|---|
| `GEOMETRY_CONFLICT` | **4** | 三维 RANSAC 内点（≤1 mm），但**与 Ring 冲突**（见下） |
| `REJECTED_3D` | 11 | 三维残差 >1 mm（中位 8.9 mm，最大 42.7 mm） |

**没有 `SUPPORTED`**：因为 Ring 检查不通过（RANSAC H 使 004 FIT 视角的 Ring MAE 从 1.04 px 恶化到 7.70 px）。
