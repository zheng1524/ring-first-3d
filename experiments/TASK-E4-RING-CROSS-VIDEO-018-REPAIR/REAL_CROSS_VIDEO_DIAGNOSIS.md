# REAL_CROSS_VIDEO_DIAGNOSIS

## 三组对照（真实 SIFT，背景 mask 过滤，未使用 F-RANSAC 预筛）

| 组 | 对数 | 联合 θ | 每对 yaw 中位 | **MAD** | ±5° 内 | 匹配中位 | inlier3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 同视频（005 内部，已知 α） | 20 | — | 误差 **0.055°** | — | — | 0.70 px | 97% |
| **B：004 ACCEPT ↔ 005** | 38 | 47.67° | **47.24°** | **1.29°** | **81.6%** | 7.5 px | 21% |
| A：004 QUARANTINE ↔ 005 | 50 | 32.38° | 33.42° | 6.79° | 40% | 33.3 px | 8% |

## 解释

- **B 组**：38 个独立图像对的 yaw 高度一致（MAD 1.29°，31/38 在 ±5° 内），
  说明"004 ACCEPT 相机 ↔ 005"之间存在**真实的相对 yaw ≈47.2°**。
  但匹配级中位残差 7.5 px、inlier3 仅 21%，说明背景里有大量重复纹理错配，
  这个 yaw 的**精度**受限于匹配质量，而不是求解器。
- **A 组**：yaw 散乱（MAD 6.79°，仅 40%），并出现 155°/−144°/170° 的离群值。
  → 前段**不能**用单一 yaw 分支解释，存在额外位姿错误。

## 负对照

- 打乱一侧对应：θ=14.8°、DEGENERATE、inlier 3%、median 69 px。
- S7 法向分支错误：DEGENERATE。

## 误差来源分类（`metrics/ERROR_CLASSIFICATION.csv`）

| 来源 | 证据 | 适用组 |
|---|---|---|
| MATCHING_ERROR | B 组中位 7.5 px、inlier3 21%；A 组 33 px | B、A |
| CAMERA_POSE_ERROR | A 组 yaw 不一致（MAD 6.8°），且其 Gate 已判 QUARANTINE | A |
| YAW_MODEL_INSUFFICIENT | A 组在单一 yaw 下无一致解 | A |
| SOLVER_ERROR | 受控 + 同视频 + 负对照全部通过 | **排除** |
| GEOMETRIC_DEGENERACY | 未检出（B 组曲率充分） | — |
