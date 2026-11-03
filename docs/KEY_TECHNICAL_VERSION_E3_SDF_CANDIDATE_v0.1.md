# 关键技术候选记录：E3-SDF v0.1

2026-11-03，`EXPERIMENTAL / NOT_ACCEPTED_AS_MAINLINE`。原 `KEY_TECHNICAL_VERSION_v1.0.md` 保持不变。本记录绑定 `TASK-E3-SDF-MONOSDF-FULL-TRAINING-REVALIDATION-001`，并非新正式主线。

继承：当前 N0 G01_004 ref08/ref13/ref03 身份/DAG、Camera Gate v0.1资格、View Partition B3/B5/B2、V6及N0固定A2派生深度、原生ID、既有320×240等比crop、冻结K/c2w和实际黑色Ring CAD。三个相机均INSUFFICIENT_EVIDENCE，仅条件研究入组。没有新清理/相机优化/深度预测，未混G01_005。

公制域沿当前N0的20.106mm立方体，MonoSDF改中心化坐标 `(X-C)/10.053`，深度Z/10.053、SDF_mm=10.053*f，旋转/K不变。域、尺度与所有模型对照统一。

官方 MonoSDF `12513009cd20a08b35ddc2c55a7e42da2c7baf43` plain8×256网络、自适应采样、渲染、官方runner更新块和官方iso0提取，必要有限ROI/CAD/数据/单位/无效法向适配公开。M0基础适配与M1项目几何保护分别命名，不能将M1称原始官方方法。

每模型200k更新、1024射线、lr5e-4/官方指数衰减，额外1000步warmup。先单ref08 M0/M1各200k；资源审查后研究者选择分阶段，三CORE不自动启动。完整预注册和正式冻结见任务config/provenance。

E2.7仅G01_005两次首步更新，不足否定MonoSDF；本轮短资源测试也不是收敛证据。只有已保存实际学习SDF驱动的完整Mesh才可作结果；不删面、不几何平滑、不把显示法线当改善。

当前阶段：输入/官方接线/资源与初始化提取核查完成，充分训练执行中，科学有效性尚NOT_EVALUABLE。最终还需单参考及三CORE充分训练、固定分母/首层/主面/多层/未知评价和研究者/PM验收。任何GT指标保持NOT_EVALUABLE。详见 [执行报告](../experiments/TASK-E3-SDF-MONOSDF-FULL-TRAINING-REVALIDATION-001/TECHNICAL_REPORT.md)。
