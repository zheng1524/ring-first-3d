# E2 失败与限制记录

本表保留实际失败、未执行和不可评价状态；验收条件未因组别/GT/结果而改变。工程通过不消除下列科学门槛。

| ID | 步骤/源/状态 | 原因及处理 | 证据 |
| --- | --- | --- | --- |
| F01 | 初始化E2文件/两次ENOSPC，已恢复 | 仅新E2工作树稀疏检出；缓存暂存内存后49+8文件SHA一致恢复持久目录；历史删除0 | [存储回执](provenance/STORAGE_RECOVERY.json)、[授权/事件](provenance/AUTHORIZATION.json) |
| F02 | 首次C2a背景断言FAIL | 测试按射线长度选择背景平面分组不可靠；改用真实primitive2/3，几何和0.002mm阈值不变。原失败数值未记录，保留null，原分组表达式未逐字归档 | [原始失败JSON](provenance/C2A_attempt001_FAILED.json)、[原冻结](provenance/C2A_attempt001_FREEZE.json)、本地runtime/C2A_attempt001.log |
| F03 | 后补复现脚本假设FAIL | 曾假设初版阈值35mm，但该阈值未错误选中前平面，故脚本断言失败；记录该错误。改为25mm的明确诊断反例：1242条错分，误差18.1546mm；primitive分组0mm。此为反例，不宣称精确复现初版源码 | [失败假设](provenance/NEGATIVE_REPLAY_ATTEMPT001.json)、[反例](metrics/REPLAY_FIRST_TEST_FAILURE.json)、[旧脚本](provenance/negative_replay_attempt001.py.txt) |
| F04 | RA晚到，初版合同不一致，已修正 | 初版只有五类可见性、沿用E1 Map命名、HERO冲突抹去Mask、未命中深度零值。按RA改为独立五类采样/保留正Mask/NaN/RA M0–M4，重跑受影响E2检查，归档旧代码和结果，不改E1 | [PRE_RA](provenance/PRE_RA_C2A_GATE.json)、[旧代码](provenance/pre_RA_code/opacity.py.txt)、[当前合同](config/RA_ALIGNED_CONTRACT.json) |
| F05 | 六源HERO与可见前缀冲突，RETAINED | 逐源878/439/324/452/354/316，共2763；正Mask保留，矛盾深度拒绝；非删除失败像素来改善误差 | [逐源分母](metrics/C2A_REAL_RAY_CLASSES.csv)、[图2](figures/Fig2_actual_ray_semantics.png) |
| F06 | G01_004/G01_005 HERO相关与源间冲突，OPEN | 每视频一个相关分量，源对冲突比例004约19.1–92.4%、005约11.5–66.1%；固定0.25权重和阈值，不代表真实误差 | [完整源对](metrics/C2B_DEPTH_CONFLICTS.csv)、[来源图3](figures/Fig3_C2b_shared_source_loss.png) |
| F07 | 六源解析前表面未命中，NaN | 观测572/命中408/未命中164；逐源14/26/32/37/23/32。无零深度回归，正Mask仍在；非神经结果 | [逐源响应](metrics/C2B_PER_VIEW_LOSS_RESPONSE.csv)、[图3](figures/Fig3_C2b_shared_source_loss.png) |
| F08 | 真实不透明BG网格，NOT_AVAILABLE | 只有源同像素高质量HERO点自由空间界；不能用插值/假表面补齐认证。正Polyp不被来源BG点裁掉 | [真实几何溯源](provenance/REAL_RAY_GEOMETRY.json)、[图2](figures/Fig2_actual_ray_semantics.png) |
| F09 | 官方初始化/物理beta，NOT_EXECUTED | 旧bias理想化在004有前交点、005无；候选规则非模型实测，不能按组选择。beta对应3.4061/2.8406mm，下轮配置未定 | [初始化表](metrics/INITIALIZATION_DOMAIN_GUARD.csv)、[beta表](metrics/SDF_BETA_UNIT_CONTRACT.csv) |
| F10 | 官方神经图/模型输出，NOT_RUN | callable有限积分与CPU解析梯度已测；官方raw SDF/sampler/RGB/Eikonal神经接线未实测。MASt3R锚点/CAD惩罚未实现；无正式预测 | [门槛](metrics/GPU_READINESS.json) |
| F11 | G01物理测量，NaN/NOT_RUN | 独立成功0/1，两视频均无新模型输出。GT封存且位姿未认证；不做旧预测回填 | [分母表](metrics/E2_MEASUREMENT_DENOMINATORS.csv)、[图3](figures/Fig3_C2b_shared_source_loss.png) |
| F12 | 严格留出0，NOT_EVALUABLE | 004诊断、005仅重建留出；历史身份暴露不能重新命名为严格盲测试。本轮目标像素未访问 | [身份](provenance/EVALUATION_IDENTITIES_FROZEN.json) |
| F13 | Map公平性与循环评价，OPEN | M1全HERO比SDF内部深度信息更广；F1/F2/F3有历史祖先优势；M3输入CAD后的Ring残差只为自洽 | [变量](metrics/FUTURE_EXPERIMENT_VARIABLES.csv)、[图4](figures/Fig4_Map_M0_M4_inputs.png) |

所有G01源/帧在主报告列出分母；G06/G08/G07不纳入E2，未假装运行失败。GPU授权始终NOT_GRANTED。磁盘清理授权未被用于删除历史产物。

## 本轮CPU继续执行补充

| ID | 状态 | 原因及处理 | 证据 |
| --- | --- | --- | --- |
| C01 | 工作树创建行政错误，已修复 | 新worktree已注册但Git继承稀疏检出缺少自身info目录；仅补建新worktree管理目录，未reset旧库。首次日志重定向前runtime目录未创建，补目录后执行；非数值PASS或科学失败 | [冻结事件](continuation_cpu/provenance/AUTHORIZATION_AND_FREEZE.json) |
| C02 | 官方神经/sampler NOT_RUN | raw/radiance调用协议和解析四损失图已实现；sampler含CUDA分配和夹持SDF访问，官方模块执行仍被拒绝，不用解析替身冒称官方网络已测 | [API绑定](continuation_cpu/provenance/OFFICIAL_API_BINDING.json)、[72项接线](continuation_cpu/metrics/JOINT_WIRING_GATE.json) |
| C03 | 三参考全miss的单源，EXPECTED_REJECT | 负控制明确移除一源全部命中，新联合入口抛出IncompleteReferenceError并保留逐源观测/缺失分母，不重归一其余两源来制造通过 | [测试表](continuation_cpu/metrics/JOINT_WIRING_TESTS.csv) |
| C04 | HERO可见性冲突未消除 | 2759在Ring后，4在0.05mm安全裕量，全部保留正Mask/拒绝深度；没有调整阈值、相机或CAD | [逐源分类](continuation_cpu/metrics/HERO_CONFLICT_CATEGORIES.csv)、[图6](continuation_cpu/figures/Fig6_source_conflicts_common_HERO.png) |
| C05 | 解析深度miss164，NaN | 572观测/408命中，未作优化；不代表正式MonoSDF结果 | [梯度和分母表](continuation_cpu/metrics/JOINT_LOSS_GRADIENTS.csv)、[图5](continuation_cpu/figures/Fig5_joint_loss_CPU.png) |
| C06 | 信息匹配只到几何载荷，OPEN | 两路线合格HERO像素相同，但RGB编码/分辨率/置信使用不同；公共资格本身已用Mask/CAD，不得称S0无任何CAD信息 | [共同数据Manifest](continuation_cpu/provenance/COMMON_HERO_GEOMETRY_MANIFEST.json) |
| C07 | G01新测量0/1，NOT_RUN | 正式网络/初始化/科学预算未执行；严格留出0和真实BG网格认证缺口仍在，GT与历史测量均未读取 | [最新报告第9节](TECHNICAL_REPORT.md#9-本轮继续执行联合损失接线与共同几何输入2026-10-31) |
| C08 | 本地日志清单回读失败，已修复 | 首次validator清单记录了自身仍在写入的日志，结束后该日志SHA变化；保留预期/实际SHA，改为排除活动日志、结束后由Git交付回执单独核验，不改科学阈值或输入 | [失败SHA回执](continuation_cpu/provenance/LOCAL_LOG_RECEIPT_FAILURE.json) |

新数值合同检查72+70项均通过；没有通过改容差或删源像素制造PASS。行政错误、预期拒绝、解析未命中、未执行的神经模型分别记录。
