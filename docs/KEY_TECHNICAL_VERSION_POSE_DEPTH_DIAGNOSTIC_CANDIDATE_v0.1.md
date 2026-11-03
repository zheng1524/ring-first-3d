# 位姿—深度诊断候选 v0.1

2026-11-04。候选分析记录，WAIT_REVIEW；不升级正式相机、清理或重建主线，也不覆盖SDF v0.3历史状态。

任务 TASK-RING-FIRST-POSE-DEPTH-IDENTIFIABILITY-001，父50239b5。本轮明确暂停训练/融合，全部新计算在本地CPU。采用v1.0及后续输入对应关系：冻结Ring-First、HERO、Mask/K/c2w/CAD，G01人工V6与N0固定A2、G06 N0、G08最近多息肉任务已冻结同规则输入；没有重新运行旧Type-2密度清理。来源资格仍为当前Camera Gate v0.1条件身份，不冒充GT。

A：历史ref08→004_14首对Raw三角面预测六字段逐位复现；另三历史帧对均保留。SIFT只用RGB估计R与平移方向，公制对照仅借RF平移长度，明确称SIFT + RF-scale。4/4恢复数值，RF覆盖/轮廓4/4较好，但RGB存在反例，不能声称绝对位姿更准确。

B：右/body SE(3)，A固定，统一轴向HERO偏差；冻结行身份及可见性、小步中心差分。G01为2/4/8视角，G06实际仅5源，使用2/4/5。18个雅可比/SVD与不同阈值、单位和数量归一结果保留。Ring改善弱方向，最大相机Z/深度列余弦仍约0.95–0.97；增视角并非单调改善。双视角可靠HERO-backed RGB对应均为0，轮廓是代理；补充去轮廓分析，不能因代理满秩认证真实误差可分离。

完整结果、来源SHA、固定分母、失败和四张图见[技术报告](../experiments/TASK-RING-FIRST-POSE-DEPTH-IDENTIFIABILITY-001/TECHNICAL_REPORT.md)。任何扰动相机/HERO仅为诊断副本，未采纳为修正结果；GT/Oracle、训练、新融合均未执行。等待研究者和PM审阅，不自动恢复下一阶段。
