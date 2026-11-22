# DEFECT_REGISTER

| # | 位置 | 原代码 | 错误 | 影响 | 修复 | 修复前测试 | 修复后测试 |
|---|---|---|---|---|---|---|---|
| D1 | 027 `core/ba_core.py` | `anchor=('005',0)`；`self.order=[c for c in sorted(cams) if c != anchor]` | 锚点是元组，相机 ID 是字符串 → **没有任何相机被排除**，005 全被优化 | 027 B/C 的全部相机修正与 Ring 数值；报告"005 固定"为**假** | `core/camvar.py::CameraVariables`（FROZEN/ANCHOR/RELEASED 显式集合 + 断言 + 参数索引） | `test_old_anchor_never_matches_any_camera`：`len(order)==11` | `test_new_variable_sets`：released=2、frozen=9、dim=54；`test_frozen_cameras_never_change` 5 次随机扰动后 delta 恒 0 |
| D2 | 027 `core/p4_real.py::evaluate` | `rr.losses(inv(T0) @ C)` | 里层已做 `canonical(H_in @ T0)`，正确增量是 `C @ inv(T0)` | 027 的 `Ring004 53.162 / 54.156` 全错 | `core/ring_adapter.py::ring_increment_from_camera` + `evaluate_ring_at_camera` | `test_increment_recovers_the_actual_camera`：旧顺序与真实相机差 >1e-3 | 新顺序 `canonical(inc@T0)==canonical(C)` 到 **1e-12**；`test_evaluation_matches_historical_renderer` M/I/C/O 到 1e-12 |
| D3 | 027 `core/ba_core.py::residuals` | 只累加 `inner/outer` | BA 的 Ring 目标缺 M 与 C，与验收目标不同 | 优化目标≠评价目标 | `core/ba_core2.py` I/C/O 三块（M 作为约束见 §）；`core/ring_energy.py` 精确能量映射 | 无（027 无测试） | `test_lambda_is_an_energy_weight`：Σr²/2 精确等于历史加权均值（1e-12） |
| D4 | 027 | `W_RING=10` 乘在残差上 | 平方目标里权重变成 100 | 权重语义不可比 | `ring_energy.ring_residuals(d, lam, block)`，λ 为**能量**权重 | 无 | λ 1→4 时 Ring 能量严格 4.000×（不是 16×） |
| D5 | 027 `core/p3_controlled.py` | `scene['X'].copy()` 作初值；`X+0.5` | 真值三维点泄漏进优化 | 0.03° 的精度不可代表真实初始化 | `core/controlled2.py::tri_init`：仅用初始相机 + 二维观测跑历史 019 逐轨迹三角化；GT 写入独立 `GROUND_TRUTH.json` | 027 用 GT 初值时 0.03° | 改用三角化初值后 **3.0–10.6°**（见 `CONTROLLED_BA_RESULTS.csv`） |
| D6 | 027 `core/p4_real.py` | `max_nfev=20`，`success=false` 未报 | 未收敛却按结果报告 | B/C 结论无效 | `core/controlled2.py` 记录 `success/status/nfev/njev/cost0/cost1`；真实 BA 阻断 | `B_success=false, nfev=20` | 400 次迭代仍 `success=False` → Gate 3 FAIL |
