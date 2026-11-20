# TASK-E4-G01-PIPELINE-AUDIT-003

**STATUS: `AWAITING_RA_REVIEW`**
**性质：** 只读审计。**未修改任何运行代码、配置、门限、数据；未重跑任何优化/HERO 推理/Body 训练；未修改 DXY。**
**审计基线：** `/home/liu/ring_first_3d_workspace` @ `ff24295`（`exp/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002`）
**被审任务：** `experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002`（下称 **002**）
**对照：** `ring_first_v6_local_reconstruction`（**V6**）、`TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001`（**001**）

---

## 交付物

| 文件 | 内容 |
|---|---|
| [G01_REFERENCE_PIPELINE.md](G01_REFERENCE_PIPELINE.md) | G01 两条上游的真实执行链、核心源码、参数、004/005 关系、版本谱系、成熟与未验证分界 |
| [DXY_READONLY_METHOD_REVIEW.md](DXY_READONLY_METHOD_REVIEW.md) | DXY V9.1 实际调用链、Mask 清理、环形拟合、PQX、质量诊断、可移植/不可移植 |
| [PIPELINE_DIFFERENCE_MATRIX.md](PIPELINE_DIFFERENCE_MATRIX.md) | 21 个模块的逐项差异判定 + 五个疑点的定量核实 |
| [PROPOSED_MINIMAL_REPAIR_PLAN.md](PROPOSED_MINIMAL_REPAIR_PLAN.md) | A/B/C 三类最小修复，含修改文件、验证方法、成败判据、执行顺序 |

---

## 七问七答

### Q1. G01 成熟流程究竟是什么？

**不是一条，是两条。**

- **A 线（004 线，E4/native）**：`observe()` 直接取 Ring 边界 → 参考库 → `rgb.pnp` → `camera.recover` 五自由度 + RGB yaw 栅格 → 来源过滤 → 3 px 门限 → HERO → Body。Ring 求解配置 `seed_retain=2, max_nfev=35`。
- **B 线（005 线，V6）**：DXY 分割/补洞/连通域 → `diverse_four` 播种 → Ring 候选（`seed_retain=4, max_nfev=100`）→ `track005` → `local_ring_sfm`（初始化/三角化/BA）→ **`validate_select` 每帧验证** → **`select_supported_views` 筛选** → MVS → 曲面封装。

两条线的 Ring 求解**内核逐字节相同**（源 `ring_pose_contact_v1/scripts/recover.py`），但**观测来源、搜索预算、最终相机来源（per-view vs BA）、验证机制**都不同。

**002 的组合方式：B 线建库 + A 线出相机。这个组合历史上从未被验证过。**

### Q2. 当前统一流程与它相比，遗漏或改变了哪些步骤？

| 遗漏/改变 | 判定 | 后果 |
|---|---|---|
| `validate_select` 每帧验证整段缺失 | `STAGE_MISSING` | 坏相机无拦截 |
| `select_supported_views` 视角筛选缺失 | `STAGE_MISSING` | 坏相机直接进 HERO/Body |
| 旋转离散度诊断被删（只留 center_spread） | `STAGE_MISSING` | 保留的诊断与主要失效模式正交 |
| `prepare_ring` 的 DXY 环预处理缺失 | `ALGORITHM_CHANGED`（相对 B 线） | 无补洞/无连通域 |
| Ring 搜索预算 4/100 → 2/35 | `ALGORITHM_CHANGED`（配置） | 分支命中率可能不同 |
| 参考库三条来源并存 | `ALGORITHM_CHANGED`（按实例） | 10 个实例中仅 4 个走 B 线 |
| 最终相机统一用 A 线 `recover()` | `ALGORITHM_CHANGED`（相对 B 线） | 混合链 |
| BA 收敛不进门禁、`min(version)` 选版本 | `IDENTICAL`（**V6 就有，非新引入**） | 选中未收敛版本 |

### Q3. G03/005 与 G05/005 的失败，哪些可以被现有成熟方法解释？

**G03/005（FIT IoU 0.24）——已定量定位，且现有成熟方法本可发现：**

1. 两个标定版本互为 ~177° 翻转分支（8 视角旋转差 174.1°–179.4°）；
2. 被选中的版本 0 BA 未收敛（`success=False`，nfev 打满 60）；
3. **Body 投影复算：版本 0 均值 IoU 0.308，版本 1 均值 0.840**（同一 Mesh、同一 mask，仅换相机）；
4. Ring 门限对此完全失明（Ring 旋转对称，翻转几乎不改变 Ring 残差）。

→ **V6 的 `validate_select` 会记录 `initialization_rotation_spread_deg`；002 删掉了它，只留 `center_spread_mm`，而后者对绕视线轴翻转几乎不敏感（6/8 视角仅 1.3–2.3 mm）。**

**补充证据（复核 v6 冻结产物）：** `ring_first_v6.../metrics/camera005_status.csv` 的 `rotation_spread_deg` = **177.2–178.1°**——**v6 当年就已经把这个翻转记录下来了**。所以这不是"成熟链没有诊断"，而是"002 删掉了成熟链已有的诊断"。

**同一份复核还给出一个反向警告：** 在 v6 自己的 005 上，v0（`BA.success=False`）反而是更好的版本（15/22 VALIDATED），v1（`BA.success=True`，nfev 仅 12）是 **0/22**。因此**不能**把修复简化为"过滤 `success=False`"或"按目标函数取最优"——必须用验证通过数 / 旋转离散 / Body 投影一致性作为判据。

**G05/005（PARTIAL）——两类独立原因：**

1. `G05_v005_raw00404`：63 px 孤立 Ring 分量，MAE 75.19 px，对总 MAE 贡献 8.81 px；主环单独为 0.724 px。**现有诊断（`RING_COMPONENT_DIAGNOSTICS.csv`）已经把原因算出来了，只是没有据此行动。**
2. `raw00251`/`raw00285`：RGB 内点 0（7/9 匹配），属参考库覆盖不足，与掩膜无关。

### Q4. DXY 中哪些 Mask 清理、轮廓和椭圆拟合方法值得复用？

| 优先 | 方法 | 可复用理由 |
|---|---|---|
| 高 | 小孔填充规则集（只加不减 + 5 条拒绝 + 不变式 assert，`ring_holes.py:22-36`） | 单侧、可审计、不改息肉；且**已在 V6 链上** |
| 高 | 椭圆拟合质量三件套（覆盖/稳定性/归一化残差，`ring_component.py:51-53,71-74,106-120`） | 给 A1 提供第二独立判据 |
| 中 | 显式失败原因枚举（`ring_component.py:61-95`） | 替代二元 PASS/FAIL |
| 中 | "降级但标注"（`q_distance_selection.py:22`） | 与三维需要的 `SUSPECT` 语义一致 |

### Q5. 哪些地方不能直接复用 DXY，为什么？

1. **中心线 `(inner+outer)/2`**（`ring_component.py:100`）——透视下内外边界不相似，丢掉了唯一化所需的内外双约束。
2. **尺度 `(D+1.2)/(2a_mid)`、`M=I`**（`scale.py:17-19`）——弱透视同深度假设，与任何 3D 整流冲突。
3. **暗环专用 ±5 灰度阶跃**（`ring_component.py:28-29`）——换材质即失效。
4. **无相机模型**：`FrameInput` 无 K/畸变/位姿（`components.py:8-16`），全仓无 `solvePnP`。椭圆 5 参数对 6 自由度位姿欠定；单视图圆环还有法向二重解；`R` 与 `d` 不可分离。
5. **`observable_P` 的 3×3 邻接**——纯 2D 拓扑，3D 可见性应由深度/遮挡定义。
6. **孤立环斑块**：DXY 只让**拟合**忽略它，**不删除**它；它仍影响 band 与 P 判定。所以"照搬连通域就能修 G05/005"**不成立**。

### Q6. 如果只允许最小修改，应该改哪几个具体文件和函数？

按风险从低到高（详见修复方案）：

| 序 | 文件 | 函数/位置 | 改动 | 级别 |
|---|---|---|---|---|
| 1 | `code/bootstrap_references.py` | `build_one()` 的 `diagnostic.append`（:88-90） | 增加 `rotation_spread_deg`、`normal_branch_disagreement` | **A3**（零风险，纯诊断） |
| 2 | 新增 `code/validate.py` | 移植 `validate_select.py:5-18` 的 held 轨道验证 | 产出逐视角 `VALIDATED/MODEL_PREDICTED` | **A1**（核心） |
| 3 | `code/standard.py` / 新增 `code/consistency.py` | hero 阶段后 | 记录 `depth_median/||t||` 尺度一致性 | **C1**（只标注） |
| 4 | `code/run.py` / body 适配层 | 训练结束 | 记录 `||FINAL-INITIAL||`，低于阈值标 `STAGNATION` | **C2**（只标注） |
| 5 | `code/standard.py` | hero/body 视角枚举 | 仅用 VALIDATED 视角 + 最小支持约束 | **A2**（需 RA 批准） |
| 6 | 新增 `code/gauge.py` | 相机 ADMISSION 前 | 枚举环轴离散候选，用 **FIT** 投影 IoU 诊断规范一致性 | **B1**（需 RA 批准是否允许 FIT-only 选支） |
| 7 | 新增 Ring 预处理 | `observe()` 之前 | 小孔填充（DXY 规则，独立实现） | **B2** |

**明确不建议改**：Ring 五自由度、RGB yaw 栅格、PnP 参数、BA 目标、HERO 模型、Body 优化器、3 px 门限。

### Q7. 如何证明修复后的流程与 G01 成熟实现一致，而不是仅仅生成了 PASS？

必须同时给出六层证据，且**互不替代**：

| 层 | 证明方法 |
|---|---|
| 算法执行成功 | 阶段表 + 无异常日志 |
| **与成熟实现一致** | 逐文件 SHA 对照 + **用 V6 冻结的 `tracks005.npz`/`local005_camera_*.npz` 重放 A1，验证结果须与 V6 `local_validation.json` 的 VALIDATED/MODEL_PREDICTED 分布一致** |
| 参考库可靠 | 每地标的来源视角、视频归属、HOLDOUT 像素排除清单、构建方法（三选一）显式写出 |
| 相机恢复可靠 | 逐视角 VALIDATED + held 重投影 MAE/p95 + 旋转/中心离散 |
| 多视角几何一致 | 同一 Body 在 8 个 FIT 视角的**投影 IoU 分布**（当前只有汇总值） |
| 主体优化有效 | `||FINAL-INITIAL||` 分布 + accepted/rejected + `STAGNATION` 标记 |
| 最终形态准确 | 独立 SE(3) 与固定 INITIAL→GT 两种结果并列；世界坐标精度仍 `NOT_EVALUABLE` |

---

## 必须同时呈现的负面证据

1. G03/004 HOLDOUT 重放仍 3.065 px > 3 px。
2. **2/40 视角 HERO 深度尺度异常**（1060.8 mm / 246.6 mm，比值 25.4× / 6.1×）且被 PASS 接受；其目标相机在版本 0 下距支持相机 58–61 mm，版本 1 下 2.8–13.5 mm。**成因未证**（需重跑官方推理，本轮禁止）。
3. **G02/005、G06/005 的 Body 更新位移仅 1.6e-5 / 2.6e-5 mm**，`graph_translation_mm` 从迭代 0 起全零，却仍记 PASS。
4. 10 个实例中只有 4 个走 V6 同源构库，其余为混合来源。
5. 004/005 **从未共享坐标**（V6 对齐 `accepted=false`，held MAE 9.17/41.9 mm）。

---

## 本轮未做的事

- 未修改任何源码/配置/门限/数据；未重跑优化、HERO 推理或 Body 训练。
- 未修改 DXY。
- 未把复算结果写回任何冻结产物（§2.3 / §5 的复算均在内存中完成）。
- 未把审计阶段升级为修复阶段。

---

## 待 RA 裁决的三个问题

1. **A1 是否允许改变"哪些视角进入下游"？** 若不允许，A1 只能作为诊断，G03/005 的坏相机仍会进入 HERO/Body。
2. **`validation_min_test=8` 在 8 视角场景是否可达？** 若不可达，是否允许按可用 held 数报告（改阈值需单独批准）？
3. **B1 的"用 FIT mask 选规范分支"是否可接受？** 若不接受，请明确 G03/005 这类实例的终态应写 `NOT_EVALUABLE` 还是 `INVALID_CALIBRATION`。
