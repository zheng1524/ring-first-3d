# CONTROLLED_TEST_RESULTS

沿用 024 并通过（`tests/test_p0_math.py`，4/4）：

| 用例 | 结果 |
|---|---|
| A2 纯平移 | 0.0054 mm / 0.016° |
| A3 混合 6DoF | 0.0010 mm / 0.014° |
| A6 Ring 歧义 | Ring ±60° 仅 0.47 px；背景 3D 124 px、唯一极小在真值 |
| A7 身份一致性 | 0/20/50% 错误 → 精确；80% → 0.42 mm/2.47°（边界）；100% → INSUFFICIENT |
| resume / rollback / 双实现梯度 / 不同 K 极线 | 全部 PASS |

本轮新增 025 契约测试（`tests/test_025_contracts.py`，4/4）：身份索引映射、H/H⁻¹ 双向、HOLDOUT 隔离、可视化只读。
合计 **8/8 通过**。
