# VISIBLE_EDGE_VALIDATION

| 项 | 做法 |
|---|---|
| 观测生成 | 可用 GT 相机（`ring_observations` 只用于生成 GT 观测） |
| 优化时边缘 | `levels.run` 调 `geometry_from(cams_init, …)`，**只用初始相机** |
| GT 隔离 | `cams_init[c][1]` 是 W0 c2w；GT 相机只出现在 `scene['C_gt']`，不进 `geometry_from` |
| 范围 | 边缘在一次求解内冻结（已记录为局部近似）；求解后用最终相机重算 Ring 作独立评价 |
| 测试 | L0（GT 残差为零）证明观测与 CAD 一致；L1 在 GT 相机初始化下不漂移 |

未执行"边缘集合随相机变化"的敏感性统计 → `NOT_DONE`。
