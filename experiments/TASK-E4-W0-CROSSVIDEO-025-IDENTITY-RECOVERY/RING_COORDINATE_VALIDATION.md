# RING_COORDINATE_VALIDATION

## 方向与坐标

- `H = H_(005←004)`：`X_005 = H X_004`，`T_common = H @ T_004`（与 W0 c2w 列向量一致）。
- 历史 020 的 `H` 是 `H_(004←005)`；本轮 `features020.make` 只生成身份，不产生 H，
  一致性模块输出的 H 直接按 025 定义（004→005），**未与历史 H 混用**。
- Ring CAD 在两段视频的世界原点；若 H 正确，`H·C4` 在 005 帧仍应把 CAD 投到真实 Ring 上。

## 实测（FIT 视角）

| 变换 | Ring MAE |
|---|---:|
| W0 相机（基准） | **1.04 px** |
| `H·C4`（seed 2 假设） | **6.84 px** |
| `H⁻¹·C5` | **5.77 px** |
| seed 1 假设 | **110.3 / 97.2 px** |

→ **`HYPOTHESIS_STATUS = RING_CONFLICT`**。这是**候选 H 的状态**，不是身份真值判定；
4 个 RANSAC 内点仍保留 `RIGID_CONSENSUS_SUPPORTED` + `RING_MODEL_CONFLICT` 双标记。

## 受控验证

`tests/test_p0_math.py` 用已知 `H_true` 生成的合成数据覆盖 SE(3) 6DoF、Sampson、不同 K、
以及双向投影（024 已完成，本轮沿用并通过）。Ring 在已知正确变换下的投影一致性由
`core/controlled_gt.A6` 覆盖：Ring 对 yaw 仅 0.47 px 伪信号，背景 3D 124 px。

## 与历史 Ring 的关系

`ring020.py` 的 M/I/C/O 加权与可见弧**未运行**（依赖历史 Ring 渲染资产）。
因此本轮 Ring 检查是 `torus_contours` 近似，**不等于** 020 的 Ring 目标，已在报告中标注。
