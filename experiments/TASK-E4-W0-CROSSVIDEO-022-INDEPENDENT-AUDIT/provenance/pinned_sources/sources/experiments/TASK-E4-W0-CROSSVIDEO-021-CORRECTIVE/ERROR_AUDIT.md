# ERROR_AUDIT

| id | 严重度 | 位置 | 根因 | 修复 | 测试 |
|---|---|---|---|---|---|
| E1 | critical | `shared_se3.exp_se3` | `q[:3]` 同时当 v 和 ω，6 维只有 3 维生效 | `core/se3.py` 精确 exp map | Jacobian 秩 6、scipy、pytorch3d |
| E2 | critical | `shared_se3.sampson_px` | 分母为两范数之和 | 标准四项平方和 | `test_standard_formula_*` |
| E3 | high | `shared_se3.optimize` | 边界按单步检查 | 累计 `H·H_seed⁻¹` | `test_cumulative_*` |
| E4 | high | `shared_se3.optimize` | 拒绝后 Adam 动量未回滚 | 位姿+m/v 全回滚 | `test_adam_rejection_restores_state` |
| E5 | high | `w0_adapter` | `adm.get(i,'ACCEPT')` 与 G03 硬编码 | fail-closed + 参数化 | `test_w0_provenance` 4 项 |
| E6 | medium | `cross_video_matches` | SIFT 4000 vs 协议 6000/.01 | 对齐 | 匹配数 482→3749 |
| E7 | medium | `yaw_1dof` | 失败原因并成 DEGENERATE | 状态拆分 | G03 INIT=AMBIGUOUS_MULTIMODAL |
| E8 | high | `ring_term` | 用 `torus_contours` 顶替 `RingRenderer` | 未解决，标 NOT_VERIFIED | A6 对称性 PASS，但无 020 对照 |
| E9 | high | 019/020 模块 | legacy 逐视角缓存缺失 | 未执行，标 BLOCKED | — |
| E10 | medium | W0 `positive_depth` | 单点（Ring 原点）代替轨迹比例 | 只诊断，未改主线 | `POSITIVE_DEPTH_AUDIT.csv` |
