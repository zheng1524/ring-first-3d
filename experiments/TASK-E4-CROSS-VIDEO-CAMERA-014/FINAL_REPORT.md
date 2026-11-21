# TASK-E4-CROSS-VIDEO-CAMERA-014 — FINAL_REPORT

```
CROSS_VIDEO_CAMERA_STATUS: BLOCKED
BODY_RECONSTRUCTION_ADMISSION: NO (for cross-video fusion; per-video 005 remains possible)
```

## 0. 一句话

**005 的 16 个相机在统一 Ring CAD 帧下全部 ACCEPT；但 004 的 8 个相机用修正后的评价器全部不合格（held 中位 70 px），且 004↔005 的 RGB 匹配极弱（688 对中仅 1 对 ≥20 内点，最高 20）。因此跨视频共视配准不成立。**

## 1. 逐视频准入（统一 Gate + 统一 Policy，未放宽任何阈值）

| 臂 | 视角 | ACCEPT | QUARANTINE | INSUFFICIENT | Ring raw | held 中位 | p95 | 相邻旋转 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| G03/005（冻结 W0） | 16 | **16** | 0 | 0 | 0.96 | **0.98** | 3.21 | 0.13° |
| G03/004（旧 005 主线相机） | 8 | **0** | 5 | 3 | 0.88 | **70.04** | 112.28 | 0.57° |

004 的 Ring 投影本身不差（0.88 px），**坏的是 RGB 多视角一致性（70 px）**——这是相机错误，不是 Ring 观测问题。由于本轮禁止重新开 J2/J3，也不允许为单视频放宽门限，004 必须保持不合格状态。

## 2. 跨视频 RGB 对应（核心否决证据）

对 004 的 43 个候选帧 × 005 的 16 个视图，共 **688 对**做 SIFT + ratio 0.75 + RANSAC-F：

| 指标 | 值 |
|---|---:|
| 可用对（≥20 内点） | **1 / 688** |
| 单对最大内点 | **20** |
| 最大 ratio-match 数 | 33 |

几何上 20 内点是勉强可三角化的下限，1 对无法支撑跨视频 BA，更无法解决 Ring 绕轴旋转歧义。

## 3. 参考照片

本轮**未取得 G03 专用的三张参考照片身份**：仓库中只有 `surface_fusion_v1/inputs/real_rgb_XXX.png` 这一组共享参考图（G01 曾使用 `real_rgb_008`），与 G03/004 的 `keyXX_rawYYYYY` 视图没有可验证的绑定关系。

按任务书"必须使用已有 Manifest、不猜测来源"的要求，**不把它们强行分配给 G03**；状态记为 `INSUFFICIENT_EVIDENCE（身份未绑定）`。这是本轮的第二项阻塞。

## 4. 统一世界坐标的现状（Q1 的准确回答）

- **公制尺度是共享的**：两段视频都以 R=5.6 mm / r=0.6 mm 的 Ring CAD 原点为世界原点，尺度来自 CAD。
- **相对位姿没有建立**：Ring 的绕轴 yaw 不可观测，004 与 005 之间没有可信 RGB 对应来消除该歧义；且 004 相机本身不合格。
- 因此：**"共享公制坐标系"在形式上成立，"共视配准"不成立。**

## 5. 回答

- **Q1 能否建立可信共同世界坐标？** **否**（相对位姿未验证；004 相机不合格）。
- **Q2 跨视频 RGB 是否有一致性？** **否**：688 对中仅 1 对达 20 内点，不构成可验证的共视几何。
- **Q3 三张参考照片的有效约束？** **无**：身份未绑定到 G03，未强行使用。
- **Q4 门控拒绝哪些视角、原因？** 004 全部 8 个：5 个 QUARANTINE（held 中位/大残差超标）、3 个 INSUFFICIENT_EVIDENCE（几何有效轨迹不足 20 条）。005 无拒绝。
- **Q5 剩余视角方向覆盖是否足够？** **仅 005 自身**：16 个 ACCEPT 视角覆盖约 90° 方位（见 013 统计），单视频可用；跨视频方向覆盖不存在。
- **Q6 能否支持主体恢复？** **跨视频融合：否。** 单视频 005：可以（16 个 ACCEPT，held 0.98 px），但只能得到**单视频局部**主体，无法与 004 或参考照片统一。

## 6. 阻塞项与可在 015 继续验证的问题

**阻止 014 完成的问题**
1. 004 的相机需用与 005 相同的 B0 流程重新恢复（本轮禁止重新优化，未做）。
2. 004↔005 RGB 对应不足：需要跨视频候选帧选择（更多帧、更长基线）或更强的匹配策略（如 LightGlue），仍属"成熟模块复用"。

**可在 015 中验证、不阻塞**
3. 三张参考照片的身份绑定（需人工指定或从 Manifest 中确认）。
4. 004 重新恢复后能否达到 ACCEPT（有 005 的成功先例）。

## 7. 交付

- `metrics/PER_VIEW_METRICS.csv`（24 行：16×005 + 8×004）
- `metrics/CAMERA_ADMISSION_RESULTS.csv`
- `metrics/CROSS_VIDEO_MATCHES.csv`（688 对）
- `UNIFIED_CAMERA_MANIFEST.json`（含 005 相机资产 SHA、004 来源、跨视频统计）
- `visualization/A_camera_network.png`、`B_cross_video_matches.png`、`C_ring_projection.png`
- `code/{camera_admission, camera_rotation_metrics, evaluate_held_geometry}.py`（与 013-PATCH 同源）

未覆盖或修改 013、011、005 的任何历史结果。
