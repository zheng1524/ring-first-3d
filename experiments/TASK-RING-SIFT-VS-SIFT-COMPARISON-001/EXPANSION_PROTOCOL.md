# 扩组与相机位置姿态差值协议 v2

人工追加授权（2026-11-26）：“请继续扩大试验。这两张图片里面看上去hero都很相似，下次顺便报告对应的相机的位置姿态的差值在什么量级。”

沿用任务001独立工作树/分支，基于4bea8e94197635fa3bb5aff7e2c0a15046033185。原COMPARISON_PROTOCOL.md、原两段输入/相机/元组/深度均冻结，旧结果不重跑。范围扩至原协议的5物理组×004/005共10视频；新增8视频。HIST completed快照只读，不接任务A clean，不改两臂科学内核。

## 复用组成表

| 能力 | 入口 | 输入→输出 | 处置/验证 |
|---|---|---|---|
| 冻结输入、划分、元组 | sift_comparison.run.prepare | 已完成HIST快照→共同输入 | REUSE，新增8个允许case及v2协议SHA |
| 独立R/S求解 | run.solve_r / colmap_arm.solve | 同训练轨迹→独立相机 | REUSE；旧2视频按哈希复用，新8段CPU重跑 |
| 留出评价/单次整体归一 | run.evaluate / core.positive_similarity | 冻结相机→预测/正Sim(3) | REUSE；无可用相机保留NaN/NOT_EVALUABLE |
| 原生HERO/深度一致性 | surfaces.hero / evaluate_depth | 同四帧→原生输出 | ADAPT，仅预算从已完成8扩至总40，新32上限；A优先 |
| 两解位姿分歧 | 新pose_metrics边界评价 | 冻结R/S及同一个既有Sim(3)→逐帧/逐对小表 | 用户明确新增评价；不参与任何门控/调参/选Support |
| 扩组交付 | 新expanded_report，复用report.page | 全10视频含失败→汇总、位姿差值图/中文页面 | ADAPT报告，不改科研输出 |

## 固定条件与完整分母

5组：GP_IIa_14.0mm_closed_R10_single_refY、GP_Ip_12.0mm_closed_R10_single_refY、GP_Ip_20.0mm_closed_R10_single_refY、GP_Ip_8.8mm_closed_R5_single_refY、GP_Is_14.0mm_closed_R5_single_refY；各004/005，RAW SHA按快照核验。每视频全部选中帧、每类query、2个固定Target/3 Support保持v1规则。保留原两段作为扩组的组成部分，不将同组两个视频算两个独立物理组。每视频先报告，跨视频用等权视频摘要并同时提供5组摘要，不池化背景点主导结果。

R/S方法、软件/参数、训练轨迹、原held拆validation/test、正深度/RGB门槛不改。原held曾参与历史门控的局限仍成立。本次不新增配对扰动稳定性试验；两臂差值是算法间分歧，不是重复求解稳定性。

## 相机差值（运行前定义）

仅使用HERO前冻结的整视频、共同训练3D轨迹正尺度/无反射Sim(3)，将S转换到R坐标。不得另拟合相机中心来压低差值，不逐帧对齐，不把HIST/R当GT。

1. 逐帧位置差：`norm(C_R-C_S_aligned)`，单位R尺度归一单位（R中1单位=1mm，S不独立公制）；保存dx/dy/dz。旋转差：`acos(clip((trace(Q_R.T@Q_S_aligned)-1)/2,-1,1))`，度。报告median/P95/max、共同数/全部帧数；额外标注共同RGB通过集和实际HERO四帧集合。无有效对齐/缺任一臂位姿保留NOT_EVALUABLE与原因。
2. 每个冻结HERO Target–Support对（每视频6个有向角色，可重复同帧对但保留组合身份）：`T_target^-1 @ T_support`。比较两臂相对旋转角、相对平移向量差（相同归一单位）、相对平移差/R臂该baseline长度（百分比）。零baseline比例不可评价。不按这些差值换组合。
3. 分别呈现整段对齐后的逐帧分歧和HERO实际相对位姿分歧。总体世界坐标分歧较大而元组相对分歧较小，可能解释深度外观接近；只能作为解释线索，不声称因果。它们不是ATE/RPE精度指标，无GT，不能决定哪臂位置或姿态正确。

## 资源与交付

原8条HERO启动保留，全任务累计≤40；新8视频各两Target×两臂≤32，不对失败换Support/重试。GPU共用 /home/liu/ring_first_3d_workspace/runs/shared_gpu.lock，A优先；A全量调度器在运行时先完成CPU，再登记排队，绝不抢占。原始大输出在 runs/ring_sift_comparison_001；CPU及GPU分开启动并可恢复，不把排队算成功。

交付新增EXPANDED_RESULTS.csv、CAMERA_POSE_DIFFERENCES.csv、HERO_RELATIVE_POSE_DIFFERENCES.csv、POSE_DIFFERENCE_SUMMARY.csv、扩组中文可视化入口及各阶段状态。唯一TECHNICAL_REPORT.md更新为本轮总报告，原小试报告按此前Git提交可追溯。提交源码前运行边界测试，执行前冻结版本/输入哈希，增量push后核对远端SHA。
