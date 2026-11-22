# W0_GROUP_DIAGNOSTICS

数据：`results/W0_admission_views.csv`、`results/W0_admission_summary.csv`（逐视角，96 行）。

| 组/视频 | ACCEPT | 主要失败类别 | held_n 中位 | held_p95 中位 | ring 中位 |
|---|---:|---|---:|---:|---:|
| G03/004 | 6 | HELD_P95_FAILURE ×10 | 120.5 | 9.60 | 1.03 |
| G03/005 | 16 | — | 107.0 | 3.21 | 0.78 |
| G01/004 | 0 | HELD_P95_FAILURE ×14、RING_FAILURE ×2 | 43.0 | 33.75 | 1.21 |
| G01/005 | 0 | HELD_P95_FAILURE ×15、HELD_MEDIAN ×1 | 37.5 | 18.61 | 0.90 |
| G05/004 | 0 | INSUFFICIENT_TRACKS ×13、HELD_P95 ×3 | 16.0 | 22.47 | 0.52 |
| G05/005 | 0 | INSUFFICIENT_TRACKS ×16 | 13.0 | 113.22 | 0.54 |

## 解释（区分三类）

- **G01 = 尾部失败**：`held_n` 中位 37–43（≥20 门限），但 p95 18–34 px。属于 `HELD_P95_FAILURE`，
  不能简单归为"观测不足"。
- **G05 = 观测不足**：`held_n` 中位 13–16 < 20，门控先触发 `INSUFFICIENT_EVIDENCE`；这是 **证据不足**，
  **不等于相机错误**。但 G05/005 的 held_p95 中位 113 px 说明单视频几何本身也很差，需 023 单独诊断。
- **G03 = 部分可用**：004 的 10 个 QUARANTINE 全部是 p95 失败，005 全过。

## `positive_depth` 语义

`tools/run_w0_camera.py` 用 Ring 原点单点代替轨迹点比例（见 021 的 `W0_EVALUATOR_BUG_REPORT.md`）。
本轮复核：六段视频的门控值与真实轨迹点正深度比例**都为 1.0**（`results/POSITIVE_DEPTH_AUDIT.csv`），
因此对 021 的准入结论**无影响**；仍是需要单独修复的评价语义问题，022 不改 W0。

## 状态语义

`OPTIMIZE=PASS`（80/80 Adam 步）与 `W0_VIEW_ACCEPT` 是两件事；`BODY_CROSS_VIDEO_ADMISSION=NO`。
