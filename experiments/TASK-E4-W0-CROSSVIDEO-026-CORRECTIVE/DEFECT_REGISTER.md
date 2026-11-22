# DEFECT_REGISTER

| # | 出错文件/函数 | 出错代码 | 数学/数据原因 | 影响的实验 | 最小修复 | 修复前失败测试 | 修复后验收测试 |
|---|---|---|---|---|---|---|---|
| D1 | 026 `core/p1_ring_io.py` 适配脚本（`ring/<view>.json` 生成） | `json.dump(dict(inner=rec['inner'], outer=rec['outer'], centerline=rec['inner']))` | Centerline 语义错误：用 Inner 椭圆冒充三维中心线投影 | 全部 22 视角 E_C 与 E_Ring；H025 评价 | 用历史 019 相同例程 `dxy_mid._engine.ring_component.recover(labels,RGB,10.)` 重新生成 `ring_corrective/` | `TestCenterline.test_old_adapter_is_wrong_and_new_is_distinct`（断言 old C==I、new C≠I 且差 >0.5 px） | 22/22 视角 centerline 与 inner 不同；C 中位 **1.8339 → 0.1397** |
| D2 | 026 `core/p2_sensitivity.py::losses_for` 调用 | `Hc = H025 @ T; losses_for(Hc, cid)` | `RingRenderer.losses(H)` 内部已做 `C = canonical(H @ T)`，再传 `H@T` 等于 H 被应用两次 | H025 Ring 评价（178.7）与全部候选 H 检查 | 传**增量**：`H_increment = T_pert @ inv(T0)`；004 侧用 H，005 侧用 H⁻¹ | `test_inc_equals_direct_camera`：旧写法可检出 I 差 >0.05 | `SE3_COMPOSITION_TESTS.csv`：6 例最大矩阵差 **7.1e-15**；端到端损失等价 ≤ **1.2e-5** |
| D3 | 026 `p2_sensitivity.py` 扰动 | `C=dH@C0; losses_for(inv(C0)@C)` | 传 `inv(T0) dH T0`（共轭）而非世界系增量 `dH`；且把相机局部旋转标注为"Ring 法向 yaw" | `RING_POSE_SENSITIVITY`（曾报 yaw 45° → 54.2） | 直接传 `dH`（世界系）或 `T0 dH_local inv(T0)`（相机局部），并显式区分两帧 | `test_world_ring_axis_rotation_is_symmetric`：旧共轭 15° 时 I 变化 >0.5 | 世界 Ring 轴旋转 0–45° MIO 恒 **0.1632**；局部 yaw 从 0.163→**5.70**（45°） |
| D4 | 026 `p2_sensitivity.py::pert` 与 `p2_relative.py` | `n=min(len(Xp),len(Xb)); disp=norm(Xp[:n]-Xb[:n])` | 数组行号≠物理轨迹；扰动后质量门接受不同轨迹集合 | 全部三角化敏感性数值（曾报 10–38 mm） | 稳定键 `tuple(sorted((view,feature_id)))` 交集匹配 | `TestTrackIdentity`：行号法中位 3.62 mm vs 稳定键 0.99 mm | 共同模式 100% 存活；005 独立 0.5° 存活 41%，p50 **0.99 mm**、p90 7.52、max 45.8 |

## 附：两处测试方式错误（非算法，已在本轮替换）

- 026 无独立数值测试，仅有"跑通即通过"式检查 → 本轮 4 个非平凡断言测试（`tests/test_defects.py`）。
- 026 的 `p4_figures.py` 第 9 图把不同实验并列 → 本轮明确标注"非配对"，分两面板呈现。
