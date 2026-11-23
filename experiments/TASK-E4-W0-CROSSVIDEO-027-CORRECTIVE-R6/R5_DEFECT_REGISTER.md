# R5_DEFECT_REGISTER（R6 修复）
| # | R5 位置 | 错误 | 影响 | 修复 | 修复前 | 修复后 |
|---|---|---|---|---|---|---|
| D1 | `r5_core.ring_candidates` | 6-DoF 优化只接收**标量能量** | Ring 候选精化目标与 BA 不同 | `ring_vector_for_H`：正式 I/C/O 残差向量；`ring_energy_for_H` 由同一向量算 | 候选可能停在非最优/不可比 | `test_vector_matches_energy_and_length`：向量能量与 BA 块能量相对差 <1e-12 |
| D2 | 报告把 yaw=120° 当最终姿态 | 未保存最终 H 与精化增量 | 误把搜索起点当结果 | 候选保存 `H_initial/H/refine_rot/refine_trans/nfev` | 无法追踪 | `test_candidate_records_final_H`；CSV 含 refine_rot（6.7°–156°） |
| D3 | `r5_experiments` 流程 | 相机先乘 H，又把 H 作为 H0 传入 BA | **H 重复应用** | `make_problem` 只接收 W0 相机，H 只在 BA 内部 | 端到端 H 偏差/不收敛 | `test_H_applied_once`：`C == H@T0` 且 `!= H@H@T0` |
| D4 | `PIPELINES.csv` | `H_M2`/`H_M3` 同一值、M3b 的 X 未更新 | 端到端结论不可用 | 分阶段保存 `H_after_M2/H_after_M3b`、`X_init/X_tri/X_after`，`save()` 写 `RESULT.npz` | INVALID | 两阶段分别记录（本轮 `PIPELINES.csv`） |
| D5 | `epipolar_energy` | 读 `sc['C_gt']` | 005 扰动时仍用 GT | 改为读取传入的参考相机 `cams[c5]` | 扰动不可见 | `test_epipolar_uses_given_reference_cameras` |
