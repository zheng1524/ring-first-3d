# DEFECT_REGISTER（R2）

| # | 位置 | 原代码 | 错误 | 修复 | 修复前 | 修复后 |
|---|---|---|---|---|---|---|
| R1 | `027-CORRECTIVE/core/controlled2.py::tri_init` | `i = sum(1 for n in range(k) if tr[n][0] == m[0])` | 特征号由轨迹内顺序重新推导；同相机只有 1 个观测时**所有地标都读第 0 个特征** | `r2_synth.triangulate`：feature_id ≡ landmark_id，`xy[view][landmark_id]` 直接索引 | 旧法会造成地标串号（027 的 3–10° 失败不可解释） | T1–T5 全通过；12 地标三角化误差 **1e-6 mm** 以内 |
| R2 | 027-CORRECTIVE | Ring 观测取自真实 G03，RGB 观测来自合成相机 | 两份观测**不属于同一几何场景**，GT 本身无法同时解释 | `r2_synth.ring_observations`：从**同一 GT 相机**投影固定 CAD 生成 I/O/C 观测 | Level 0 无法定义 | **Level 0：RGB 0.0，I 1.2e-13，C 1.7e-14，O 1.2e-13**（num. zero） |
| R3 | 027-CORRECTIVE `controlled2.py` | `edges={k:v for k,v in edges.items() if k[1]!='mid'}` | Centerline 被过滤，BA 实际是 **IO** 而不是 ICO | `ba_core_r2.BAProblemR2`：`V_mid/E_mid` 独立通道，`L0 C=1.7e-14`、L2 中 `ring_C` 非零 | C 未进入 | C 进入残差（`use_centerline=True`），关闭 C 时总目标按定义变化 |
| R4 | 027-CORRECTIVE `controlled2.py` | `geometry_from(..., scene['H'] @ C)` | 可见边缘用 **GT H** 选择 | `levels.run`：边缘只从**初始相机**计算；GT 仅用于生成观测与最终评价 | GT 泄漏 | L0 残差验证 + 代码路径审计（`geometry_from(cams_init, …)`） |
| R5 | 027-CORRECTIVE | 名称与实验不符（S5 只扰动单相机等） | 命名误导 | 本轮只执行 L0/L1/L2 并如实命名；L3–L5 标 `NOT_EXECUTED` | — | 见 `CONTROLLED_LEVEL_RESULTS.md` |
