# CONTROLLED_GT_RESULTS（P0，真值真的在观测里）

观测生成：`X_005 = H_true X_004`，`C5_i = H_true C4_i`，两侧像素由真实投影 + 0.3 px 噪声生成。
因此 `H_true` **确实出现在数据里**（与 021/023 的失效 A2/A6 不同）。

| 用例 | 真值 | 估计误差 | 断言（事前锁定） | 结果 |
|---|---|---|---|---|
| **A2 纯平移** | t=(0.8,−0.3,0.2) mm, R=I | **0.0054 mm / 0.016°** | mm<0.05, deg<0.1 | **PASS** |
| **A3 混合 6DoF** | Rz 6°, t=(0.5,0.2,−0.1) mm | **0.0010 mm / 0.014°** | mm<0.10, deg<0.5 | **PASS** |
| **A6 Ring 歧义** | 只变候选 yaw，观测固定 | Ring 曲线误差在 ±60° 内只变 **0.47 px**（离散化伪信号）；加入背景 3D 后同一 yaw 扫描变化 **124.4 px**，唯一极小在真值 15° | Ring spread<1 px 且 3D spread>10 px | **PASS** |
| **A7 身份一致性** | 0/20/50/80/100% 错误身份 | 0–50%：精确恢复（err≈0）；80%：仍 SUPPORTED 但 **0.42 mm / 2.47°**（记录为已知边界）；100%：`INSUFFICIENT`(2 inliers) | — | **PASS（含已记录边界）** |
| A7 退化 | 共线 8 点 | `DEGENERATE`（奇异值比 0.0） | — | **PASS** |
| A7 样本不足 | 3 点 | `INSUFFICIENT` | — | **PASS** |

环境：open3d 0.19.0（本轮安装到项目 venv，见 RUN_MANIFEST），`TransformationEstimationPointToPoint(with_scaling=False)`。
