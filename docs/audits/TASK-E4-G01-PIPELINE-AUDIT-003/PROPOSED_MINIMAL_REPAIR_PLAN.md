# PROPOSED_MINIMAL_REPAIR_PLAN

**Task:** TASK-E4-G01-PIPELINE-AUDIT-003
**Status:** `AWAITING_RA_REVIEW` — **本轮不实施任何修改**
**前提：** 只允许"恢复 G01/V6 中已经存在、当前遗漏或连接错误"的环节。任何新算法都属于 C 类，本轮仅登记、不实施。
**硬约束（继承任务书 §八）：** 不放宽任何既有门控；不改 DXY；不改 Ring 物理尺寸/K/FOV/Ring-First 数值求解器/官方 HERO/PyTorch3D 优化器/3 px 门限/FIT-HOLDOUT 隔离/GT 事后评价；不改 G01 历史结果。

---

## 0. 排序逻辑

按"**证据强度 × 风险 × 是否可离线验证**"排序。所有 A 类修复都必须能**在已冻结的现有产物上离线复算**，不得以"重跑一次看看"作为验证手段。

```
第 1 步  A3 旋转离散度诊断        （零风险，纯观测，可当天完成）
第 2 步  A1 恢复每帧标定验证       （核心；离线复算即可判定）
第 3 步  C1/C2 一致性/停滞诊断     （只标注，不阻断）
第 4 步  A2 支持视角筛选           （依赖 A1 的判定结果）
第 5 步  B1 参考库-主体 gauge 检查 （需要 RA 决定是否允许 FIT-only 选支）
第 6 步  B2/B3 DXY 掩膜与椭圆诊断  （依赖 DXY_READONLY_METHOD_REVIEW 结论）
```

**不建议**在本轮之后立刻改动：Ring 五自由度、RGB yaw 栅格、PnP 参数、BA 目标函数、HERO 模型、Body 优化器、任何门限数值。

---

## A3. 补回"初始化旋转离散度"诊断

| 项 | 内容 |
|---|---|
| **具体问题** | 002 的 `CALIBRATION_RING_DIAGNOSTIC.json` 每视角只有 `Ring_MAE_px / Ring_P95_px / center_spread_mm`。而 Ring 是旋转对称体，绕环轴的翻转**几乎不改变相机中心**（实测 6/8 视角 1.3–2.3 mm），因此现有诊断与主要失效模式正交。V6 记录过 `initialization_rotation_spread_deg`，002 把它删掉了。 |
| **原始 G01/V6 对应实现** | `ring_first_v6_local_reconstruction/scripts/validate_select.py:15`：`rotspread=max(degrees(Rotation.from_matrix(po[i,:3,:3].T@xx['c2w'][i,:3,:3]).magnitude()) for xx in packs.values())` |
| **预计修改文件** | `experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/code/bootstrap_references.py`（第 88–90 行的 diagnostic 构造） |
| **修改内容** | 在 `diagnostic.append(...)` 中增加 `rotation_spread_deg` 与 `normal_branch_disagreement`（两版本 normal 点积符号），并把 V6 的 `config.json: validation_center_spread_mm=2.0` 作为**告警**阈值写进同一行记录。 |
| **是否影响科学算法** | **否**。只增加输出字段，不参与任何判定。 |
| **是否涉及 DXY** | 否 |
| **风险** | 极低；需重算一次 diagnostic 文件（只读重算，不重跑求解——两版本的相机 npz 已存在） |
| **验证方法** | 对 G03/005、G06/005 直接用已存在的 `NATIVE_CALIBRATION_0/1.npz` 复算，不调用求解器 |
| **成功判据** | G03/005 的 `raw00373`、`raw00402` 出现 `rotation_spread_deg ≈ 179°` 且 `center_spread_mm` 同步 > 2 mm；G01/004 等冻结实例不产生告警 |
| **失败判据** | 对全部 8 视角都报 ~177°，即该量无法区分"全局规范选择"与"单视角异常"——则说明还需要 A1 的 held-track 判据，A3 只作辅助 |

> 说明：实测 G03/005 的两版本对**全部**视角都有 174–179° 差异（全局分支差），因此 A3 单独**不足以**定位坏视角，必须与 A1 联合使用。这一步的价值是让"翻转"这件事第一次可见。

---

## A1. 恢复每帧标定验证（`validate_select` 语义）

| 项 | 内容 |
|---|---|
| **具体问题** | 002 完全没有 per-frame 校验：只要 `recover()` 返回 `originalRF5DoF_RGB_yaw` 且 Ring MAE < 3 px 就判 PASS。Ring 对称性使该门限对"绕环轴翻转"完全不敏感。V6 用 held 轨道（每 5 条取 1，从不进入初始化/BA）做独立重投影检验，能发现自相矛盾的相机。 |
| **原始 G01/V6 对应实现** | `validate_select.py:5-18`：`passed = len(errors)>=8 and ee['MAE']<=3 and ee['p95']<=6 and pos>=0.95 and rg['MAE']<=3 and rg['p95']<=6 and spread<=2.`；阈值来自 `config.json: validation_min_test=8, validation_MAE_px=3.0, validation_p95_px=6.0, validation_positive=0.95, validation_center_spread_mm=2.0`。**注意：002 的 `frozen_calibration/config.json` 与 V6 逐字节相同，这些阈值已经就位，只是没有消费者。** |
| **预计修改文件** | 新增 `code/validate.py`；在 `bootstrap_references.py` 求解循环之后调用；`cameras.py` 在写 ADMISSION 时读取该结果 |
| **修改内容** | 1) 复用已冻结的 `track005` 输出中的 `held` 掩码（002 已经生成 `tracks005.npz` 并保存了 `held`，但**没有任何消费者**）；2) 对每个 version、每个视角计算：held 轨道三角化重投影 MAE/p95、正深度比例、Ring 自轮廓（`q_held`）MAE/p95、中心离散、旋转离散；3) 写出 `metrics/CALIBRATION_VALIDATION.json`，逐视角 `VALIDATED / MODEL_PREDICTED`；4) **不改变** `primary=min(available)`（保持 V6 规则），只是把非 VALIDATED 视角标出来供下游使用 |
| **是否影响科学算法** | **不改变任何求解器、参数、目标函数**。但会改变"哪些视角可以进入下游"，属流程变更，需 RA 明确批准。 |
| **是否涉及 DXY** | 否 |
| **风险** | ① 004 的四个实例是冻结引用，重算验证可能与历史不一致 → 只对**新建实例**启用，004 保持冻结并标注"未验证/继承"；② `held` 轨道在 8 视角下可能不足 8 条（`validation_min_test=8`），导致整实例不可验证 → 需先做离线统计，再决定是否放宽为"按可用 held 数报告"（**放宽 min_test 属于改阈值，需 RA 单独批准**） |
| **验证方法** | 离线读 `tracks005.npz` + `NATIVE_CALIBRATION_{0,1}.npz`，不重跑 SfM/BA。先对 G03/005、G06/005、G01/005 三个已存在实例复算，再对 4 个 MATURE 实例全量复算 |
| **成功判据** | ① G03/005 的 `raw00373`、`raw00402` 被判 `MODEL_PREDICTED`；② 其余 6 个视角的判定与我的 Body 投影复算一致（IoU≈0.13 的 6 个视角应至少有一部分被标出）；③ G01/005、G06/005 的判定与它们 0.87 的 FIT IoU 不矛盾（即不出现大面积误伤） |
| **失败判据** | held 轨道重投影对"全局翻转"同样不敏感（因为翻转对 held 轨道是自洽的）——**这是很可能的结果**。若如此，A1 只能抓住 2 个不稳定视角，抓不住 6 个全局翻转视角，则必须进入 B1 |

> **必须提前说清**：A1 是对 V6 行为的忠实恢复，但**不能保证**解决 G03/005 的 6 个全局翻转视角。全局翻转是"自洽但整体错"的失效，任何基于内部一致性的检验都抓不到，只有引入外部锚（冻结 Body / 004 参考）才能判定。这正是 B1 存在的理由。

---

## C1. HERO 深度公制一致性诊断（只标注）

| 项 | 内容 |
|---|---|
| **具体问题** | HERO 门禁只检查 `valid_pixels / polyp_vertices / faces`。实测 40 个视角中有 2 个（G03/005 的 `raw00373`、`raw00402`）深度中位数为 1060.8 mm、246.6 mm，而相机距环心仅 41.7/40.3 mm（比值 25.4×、6.1×），仍被记为 PASS 并进入 Body。 |
| **原始 G01 对应实现** | 无（V6 也没有）。**故这属于"从未存在"的检查，不是恢复项。** |
| **预计修改文件** | `code/standard.py`（hero 阶段后）或新增 `code/consistency.py` |
| **修改内容** | 计算 `depth_median_mm / ||c2w.t||` 与 p10/p90 分布，写入 `HERO_METRIC_CONSISTENCY.json`；超过预先登记的倍数即标 `SUSPECT`。**不阻断、不修改深度**。 |
| **是否影响科学算法** | 否（仅诊断） |
| **是否涉及 DXY** | 否 |
| **风险** | 阈值需标定；若错误阻断会掩盖真实结果 → 因此本轮只做标注 |
| **验证方法** | 对现有 40 个视角离线复算（数据已存在），统计分布 |
| **成功判据** | 正常视角比值集中于 1.0–1.7（实测中位 1.03、p90 1.61），两个异常视角 >5 |
| **失败判据** | 若正常视角分布本身跨越 >5，则该指标不可用，需改用"Hartley 归一化后的重投影一致性"等其他量 |

---

## C2. Body 更新停滞诊断（只标注）

| 项 | 内容 |
|---|---|
| **具体问题** | G02/005 与 G06/005 的 B1/B2 相对 INITIAL 的最大顶点位移为 **1.6e-5 / 2.6e-5 mm**，`UPDATES.json` 中 `graph_translation_mm` 从迭代 0 起即为全零，但门控仍逐帧 accepted，B0/B1/B2 指标完全相同。这是"执行成功 ≠ 优化有效"。 |
| **原始 G01 对应实现** | 无 |
| **预计修改文件** | `code/run.py` 或 `body_stage` 适配层（只写报告文件） |
| **修改内容** | 训练结束计算 `||FINAL-INITIAL||` 的 max/mean，低于预登记阈值（建议 1e-3 mm）时在 `PREDICTION_FROZEN.json` 与汇总表中标 `STAGNATION_NO_EFFECTIVE_UPDATE`，并在报告里禁止把它写作"PASS"。 |
| **是否影响科学算法** | 否（仅标注） |
| **是否涉及 DXY** | 否 |
| **风险** | 阈值过低会把正常小步长误标；建议同时报告位移分布，而非只给二元标签 |
| **验证方法** | 对已存在的 10 个 body 目录离线统计（本轮已做过，见表 §5） |
| **成功判据** | 标出 G02/005、G06/005；G01/005（0.633 mm）、G03/005（0.462 mm）不误标 |

---

## A2. 支持视角筛选（依赖 A1）

| 项 | 内容 |
|---|---|
| **具体问题** | 002 把全部 8 个 FIT 视角送入 HERO 与 Body。V6 只让 `VALIDATED` 视角进入 MVS。当前 G03/005 的坏相机因此直接污染 HERO 与深度监督。 |
| **原始 G01/V6 对应实现** | `select_supported_views.py:2`：`ok=[i for i,x in enumerate(rec) if x['status']=='VALIDATED']` |
| **预计修改文件** | `code/standard.py`（hero/body 的视角枚举处） |
| **修改内容** | 仅当 A1 产出 VALIDATED 列表时，用其收窄 hero/body 的 FIT 集合；同时强制"至少 N 个视角 + 覆盖 004/005 两视频"的最小支持约束（见风险） |
| **是否影响科学算法** | 是（改变输入视角集合）。**必须 RA 批准** |
| **是否涉及 DXY** | 否 |
| **风险** | 视角数减少 → 覆盖下降、Body 欠约束、HOLDOUT 评价分母变化；与"保留全部 FIT、不筛视角"的既有协议冲突 |
| **验证方法** | 离线模拟：对现状 10 个实例，按 A1 结果重算"若只保留 VALIDATED 视角，FIT 覆盖与 Body 是否仍可解"——用已有对应与 Mesh，不重训 |
| **成功判据** | G03/005 被标为 `INSUFFICIENT_VALIDATED_SUPPORT` 而不是产出一个 IoU 0.24 的 Body |
| **失败判据** | 多数实例可用视角 < 3，导致整体不可运行 → 则应降级为"仅警告"，不阻断 |

---

## B1. 参考库/相机规范（gauge）与冻结 Body 的一致性检查

| 项 | 内容 |
|---|---|
| **具体问题** | 004 的相机与 `EXACT013` Body 在同一环坐标系下共同建立；005 的环坐标系是**重新求解**的，其绕环轴的 yaw 与法向符号相对 Body 是任意的。实测：G03/005 两版本互差 ~177°，选中的版本使 Body 投影均值 IoU 仅 0.31，未选中的版本为 0.84。当前流程没有任何环节检查"相机规范是否与冻结 Body 一致"。 |
| **原始 G01 对应实现** | 没有直接对应。V6 试图用 `align_local_scenes_disjoint.py` 建立 004↔005 对齐，但结果 `accepted=false`（alpha=-88.9°，held MAE 9.17/41.9 mm），说明该路不可用。001 通过"只引用 004 库 + 拒绝跨视频库"回避了这个问题。 |
| **预计修改文件** | 新增 `code/gauge.py`；在 `cameras.py` 写 ADMISSION 前调用 |
| **修改内容** | **两种子方案，风险不同：**<br>**(a) 只诊断**：枚举离散候选（绕环轴 0/90/180/270° × 法向翻转 ±），对每个候选计算"冻结 Body 在 FIT 视角的投影 IoU"（只用 FIT mask，绝不读 HOLDOUT/GT），把最优候选与当前候选的 IoU 差值写入 `GAUGE_DIAGNOSTIC.json`，超阈值标 `RING_AXIS_GAUGE_SUSPECT`。<br>**(b) 选择性修正**：用最优候选替换当前相机。**不建议本轮采用**，因为它改变预测。 |
| **是否影响科学算法** | (a) 否；(b) 是 |
| **是否涉及 DXY** | 否 |
| **风险** | 用 FIT mask 选择模型属于"用训练数据选支"，不是 GT 泄漏，但会引入选择偏差，且 4 个离散候选可能都不对（环轴连续旋转）。**必须 RA 明确这是否可接受。** |
| **验证方法** | 离线复算（本轮已做过 G03/005 的两版本对比）：对 10 个实例，比较当前相机与候选相机的 FIT 投影 IoU 分布 |
| **成功判据** | G03/005 的当前 IoU 0.24 与候选 0.84 的差距被稳定检出；G01/004（0.85）、G05/004（0.97）、G06/004（0.92）等不产生告警 |
| **失败判据** | 候选间 IoU 差异不显著（<0.05）或最优候选在不同实例间不一致 → 说明该诊断不可靠，回退到 A1+A2 的"标记不可用"策略 |

> **这是本方案中唯一"超出恢复成熟实现"的项。** 如果 RA 认为不可接受，则 G03/005 这类实例在现有边界内无法被正确重建，只能如实报 `NOT_EVALUABLE`。

---

## B2/B3. DXY 可复用方法（已按 `DXY_READONLY_METHOD_REVIEW.md` 定稿）

**先纠正一个容易做错的预期：** DXY 的 `select_components`（`polypseg_ring_fitting.py:23-35`，`min_area=300`，取最大组件）**只影响拟合选用哪个组件**；孤立环斑块仍留在掩膜里，仍参与 `band` 抑制与 P 的 3×3 邻接判定（`v2_candidates.py:34`；`observable_boundary.py:47-49`）。因此"照搬 DXY 就能修好 G05/005"**不成立**。

| 候选 | 针对问题 | DXY 证据 | 三维侧缺口 | 级别 | 备注 |
|---|---|---|---|---|---|
| **B2** Ring 小孔填充 | 环内小洞造成的边界伪影；`observe()` 直接用原始 labels | `ring_holes.py:6,22-36`（只加不减、5 条拒绝、不变式 assert） | 无任何环清理 | **B（推荐先做诊断版）** | 该步骤**已在 V6 的 `prepare_ring.py:67` 链上**，所以对 B 线而言更接近 A 类"恢复"；对 A 线是新增 |
| **B3** 椭圆拟合质量三件套（覆盖/稳定性/归一化残差） | 为 A1 提供**第二个独立几何判据**，避免只看 3 px | `ring_component.py:51-53,71-74,106-120` | 只有 Ring MAE/P95 | B | 可作为 A1 的辅助诊断，不单独否决 |
| **B4** 观测层连通域选择 | G05/005 `raw00404`：63 px 孤立块把 MAE 从 0.724 拉到 9.451 | DXY 只做拟合层选择；**观测层选择是三维侧的新语义** | `observe()` 无组件概念 | **C（需 RA 明确批准）** | 不属于"照搬"，必须声明为语义变更；且需同时报告含/不含两种 MAE |
| **B5** 原始 Mask 与处理后 Mask 分离 | 使任何形态学处理可审计 | DXY 只保留哈希、不返回数组（`pipeline.py:80-81`） | 三维已有输入冻结哈希 | A（工程规范） | 无算法影响 |
| **B6** 显式失败原因枚举 + "降级但标注" | 替代当前 PASS/FAIL 二元 | `ring_component.py:61-95`；`q_distance_selection.py:22` | 只有 `NO_RESOLVED_RING_FIRST_RGB_YAW` | A | 纯字段扩展 |

**约束（不可协商）：**
1. 全部在三维仓库内独立实现，**不 import、不调用、不修改、不运行 DXY 主线**。
2. 引用 DXY 时必须注明其"是否在 V9.1 正式链"（见审阅文档 §7）。
3. B2 若实施，必须同时验证"不改动息肉标签"（DXY 用 `assert` 保证，三维侧需同等断言）。
4. B4 若实施，**不得**删除掩膜中的孤立分量；只能选择并记录。

---

## 4. 不可做清单（本轮与下一轮都必须遵守）

1. 不放宽 3 px Ring 门限、不放宽 `validation_*` 阈值、不放宽 Body/几何门控。
2. 不删除 Ring 连通域以"通过"门限；只能选择并记录。
3. 不改 DXY 任何文件。
4. 不用 GT/HOLDOUT 做任何选择、分支或阈值。
5. 不把"重新跑一次得到更好数字"当作修复验证。
6. 不修改 Ring-First 五自由度、RGB yaw、PnP、BA、HERO、PyTorch3D 优化器。
7. 不把 004 的冻结结果与新实例混合统计。

---

## 5. 修复后的"一致性证明"要求（对应 Q7）

修复不得以"产生 PASS"为验收。必须同时给出：

| 证明对象 | 证明方法 |
|---|---|
| 算法执行成功 | 阶段表全 PASS + 无异常日志 |
| **与 G01 成熟实现一致** | 逐文件 SHA 与 V6/001 对照表（`frozen_calibration` 已具备）；**离线复算**：用 V6 冻结的 `tracks005.npz`/`local005_camera_*.npz` 重放 A1 验证，验证结果必须与 V6 `local_validation.json` 的 VALIDATED/MODEL_PREDICTED 分布一致 |
| 参考库可靠 | 每个地标的来源 view、视频归属、HOLDOUT 像素排除清单、构建方法（三选一）显式写出 |
| 相机恢复可靠 | 每视角 `VALIDATED/MODEL_PREDICTED` + held 重投影 MAE/p95 + 旋转/中心离散 |
| 多视角几何一致 | 同一 Body 在 8 个 FIT 视角的投影 IoU 分布（当前只有汇总值） |
| 主体优化有效 | `||FINAL-INITIAL||` 分布 + accepted/rejected 计数 + 是否 `STAGNATION` |
| 最终形态准确 | 独立 SE(3) 与固定 INITIAL→GT 两种结果并列，绝对三维位置仍 `NOT_EVALUABLE` |

---

## 6. 需要 RA 立即裁决的三个问题

1. **A1 是否允许改变"哪些视角进入下游"？** 若不允许，A1 只能作为诊断，G03/005 的坏相机仍会进入 HERO/Body。
2. **A1 的 `validation_min_test=8` 在 8 视角场景下是否可达？** 若不可达，是否允许按"可用 held 数"报告而不改阈值？（改阈值需单独批准。）
3. **B1 的 (a) 诊断是否可接受为"用 FIT mask 选支"？** 若不接受，请明确 G03/005 这类实例的最终状态应写为 `NOT_EVALUABLE` 还是 `INVALID_CALIBRATION`。

---

## 7. 附：本轮**未**做的事

- 未修改任何源码、配置、门限、数据。
- 未重跑任何优化、HERO 推理或 Body 训练。
- 未修改 DXY。
- 未把任何复算结果写回冻结产物；§2.3/§5 的复算全部在内存中完成，仅生成本文档引用。
