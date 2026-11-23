# GT_LEAKAGE_AUDIT

| 环节 | GT 进入？ | 说明/测试 |
|---|---|---|
| 观测生成 | 是（允许） | `r2_synth` |
| Ring 候选 | 否 | 仅 Ring CAD/观测 + 初始相机；`geom_from(..., H)` 不读 GT |
| 极线评分 | 否 | 仅 FIT 二维观测 + 传入的参考相机（`test_epipolar_uses_given_reference_cameras`） |
| 权重/归一化 | 否 | λ_R=λ_E=1，先冻结；Ring 为无单位能量、Sampson 为像素，两者量级相近（0.0003–0.0007 vs 0.53–0.73），未做 GT 驱动的缩放 |
| X0 | 否（005 相机=参考定义） | 未用 GT 三维点 |
| HOLDOUT | 否 | `test_holdout_does_not_change_selection`（替换 HOLDOUT 观测不影响候选） |
| 最终评价 | 是（允许） | `gt_metrics` |

## 已知弱点

`X0` 来自准确的 005 相机（近 GT），对两条流程都是同一先验 → 公平，但**不代表真实数据条件**；
E1 中已改为"扰动 005 相机三角化"，部分缓解。
