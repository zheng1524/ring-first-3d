# SYNTHETIC_SCENE_CONSISTENCY

## 场景

固定 CAD（G03 `RING.npz`）+ 12 个固定背景点；6 台 GT 相机（3×004，3×005），
`C_gt(004) = H_gt @ T0(004)`，`C_gt(005) = T0(005)`，`H_gt` = 旋转 (0.7,-0.4,12)°、平移 (0.4,-0.3,0.2) mm。

**同一场景生成两类观测**：
- RGB：`π(K_i, C_gt,i⁻¹ X_j)`（feature_id = landmark_id）
- Ring：用同一 `C_gt` 投影固定 CAD 的可见 I/O 边与中心线 `curves.mid`

## Level 0：GT 代入残差

| 项 | 能量 |
|---|---:|
| RGB | **0.0** |
| Inner | **1.2e-13** |
| Centerline | **1.7e-14** |
| Outer | **1.2e-13** |
| 总 | 2.5e-13 |
| 残差向量最大分量（10970 个） | 8.9e-09 |

⇒ **同一 GT 场景同时解释 RGB 与 Ring**（Q2 = 是）。027-CORRECTIVE 的失败源于场景不一致，不是 BA 数学。
