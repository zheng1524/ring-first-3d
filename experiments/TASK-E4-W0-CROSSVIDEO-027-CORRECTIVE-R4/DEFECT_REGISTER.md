# DEFECT_REGISTER（R4）

| # | 位置（R3） | 原代码 | 错误 | 修复 | 修复前测试 | 修复后测试 |
|---|---|---|---|---|---|---|
| D1 | `r3_run.solve` | `if mode=='h_only': ... else: return P.residuals(t,H0)` | 联合优化忽略 `rgb_mode`，Huber/平方不生效 | `ba_core_r4.residual_vector(H,dx,X,rgb_mode)` 单一路径，H-only/M1/M2/M3 共用 | 旧 `P.residuals` 无 `rgb_mode` 形参 | `test_joint_path_honours_rgb_mode`：大残差下 Huber≠平方（相对差 >1e-3），小残差下相对差 <1e-6 |
| D2 | `r3_run.energies` | `res_vector(...)[0]` | 只取第一个 RGB 残差分量，总能量错误 | `energy_table()` 由**同一残差向量**算各块能量，并核对 `E_terms == 0.5‖r‖²` | 旧式 rgb 能量与实际残差不等 | `test_energy_identity`：`|E_terms − 0.5‖r‖²| < 1e-9`（huber/squared/dir2d 三种） |
| D3 | `r3_run` `n_ring` | `sum(... for k,v in ring_obs.items())` 把相机 ID 当类别 | Ring 计数错误 | `n_ring_I/C/O` 由实际残差数组长度统计 | 旧计数与真实数组不符 | `test_energy_identity` 断言 I/C/O 计数 >0 且来自实际数组 |
| D4 | `r3_run --what h_only_sweep` | `build_scene(H_rot_deg=(...,yaw))` | 扫描改变的是 **GT 场景**，不是初始化 | `r4_run` 固定 GT（yaw=12°），仅改 `H_init`/相机/地标初值（实验 I） | 旧扫描混淆两件事 | `r4_run.make_fixed()` 场景固定；组间只改被指定变量 |
| D5 | `r3_run` | `max_nfev` 因调用而异 | 预算不可比 | R4 统一：M2=200，M1/M3=60（M3 为 30+30），逐次记录 `nfev` 与 `success` | — | `SUMMARY_*.csv` 记录每 run 预算与实际 nfev |
| D6 | R4 M4 | 参数偏移 `12+6nr` | M4 运行 `IndexError`（X 行数错） | 改为 `6+6+6nr`；本轮 M4 仍 **NOT_EXECUTED**（时间预算） | M4 5 次运行全部异常 | 修复后未重跑（如实记录） |
