# E4 PMGR-R1候选v0.4：多数拒绝后停止，未验收

2026-11-05；继承PMGR父提交b8c41565d467c922fdf2f45d3a4adf92f332813d。执行冻结eea53d74e645f58fc67e6b4d01ce4db96e716524，独立分支exp/TASK-E4-PMGR-R1。

只执行G01_004/E2保守P0与部分P1：真实Ring实体交集从3.8960mm³降为0，整三角面正间隙0.08240mm，体积保留97.52%。九参数+12谱参数均开放，但10个更新9拒绝，仅接受0.007735mm微动，按用户指令GLOBAL_STOP。P2和G06/E1未运行。

直接拒绝原因均为逐源轮廓保护，非Ring碰撞或QP失败。只读诊断确认少视角方向/全视角保护不一致、轮廓样本切换以及预测/观测Ring邻接带剔除不对称。未改阈值、未修补后重跑。P0中间可行性日志因同名覆盖丢失，端点门槛重算并显式标注，未补造轨迹。

相机、尺度、HERO、Mask、Type-2、DXY及CAD保持原冻结；G01全部INSUFFICIENT_EVIDENCE，仅条件研究，旧B已为训练，本轮无独立留出。127项资产SHA不变，未读GT。安全初始化是局部工程成果，明显渐进更新机制尚未通过，不能升级正式主线。

[完整技术报告](../experiments/TASK-E4-PMGR-R1/TECHNICAL_REPORT.md)、[失败台账](../experiments/TASK-E4-PMGR-R1/FAILURE_LEDGER.md)。等待人工/PM审阅，不自动推广，不进入B1/B2。
