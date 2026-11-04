# Phase E4 / A1 关键技术候选 v0.1

2026-11-04。研究者授权路线调整；正式路线状态见 [PHASE_E4_RESEARCH_ROADMAP.md](PHASE_E4_RESEARCH_ROADMAP.md)。保留此前所有版本和报告，未改 Ring-First、K/c2w、HERO、P0、Mask、CAD、清理结果或 DXY。

实验：`TASK-E4-A1-COARSE-BODY-001`，冻结提交 `7cd3c47`，父提交 `6550275d518020f50ae7a02dd9b8c6907ca6189b`。A1仅使用自己的参数模型产生预测；TSDF/NeuralFusion/MonoSDF/历史DXY测量均不参与生成。

当前 Gate 复用 E3-N0 八视角任务的 CAMERA_GATE_RESULTS/RULES，视角分区复用已冻结 View Partition，输入清理仅复用已存在原生有效性缓存。G07 部分单相机已是 CONDITIONAL_USABLE，但历史 HERO 上游链仍未合格；不得回退称“全部当前相机不合格”，也不得升级正式Is实证。G01_005缺当前入组链，保持独立视频空间审计身份。

新增：9参数椭球、16参数Ip有界三阶星凸、10参数Is开放球冠、11参数IIa有限非负高度场；原生射线首次轴向深度、固定相对D、原面身份软支持；A-only三初值有界TRF；固定B像素评价；不含先验的白化观测J/物理尺度归一及有限扰动。

完成4个物理组条件/压力诊断、20模型/60初值、40固定扰动和4核心图；G04/G05的Is资格不足保留NaN。所有B仅独立于当前参数拟合，历史依赖未排除。G1=NOT_PASSED，未提升为正式三维测量主线。A2只预备设计，B1/B2未执行。

发现：G06高度场有条件性收益；Ip星凸没有统一优势，且真实ref08有1条33点根扫描漏检，首交点合同FAIL；G08可出现轮廓更好但深度更差；5个模型J数值不稳定，1个纯二维厚度方向局部不可辨识。详见 [技术报告](../experiments/TASK-E4-A1-COARSE-BODY-001/TECHNICAL_REPORT.md)。等待人工/PM审查后决定是否修复数值合同、补齐资格或授权A2。
