# 决策记录

本表继承已有明确边界，不替研究者新增科学验收。历史版本日期及争议保留；仅出现数值/工程成功不构成“接受新主线”。

| ID | 已确认边界或决定 | 证据 | 执行含义 / 不可自动改变 |
| --- | --- | --- | --- |
| D01 | Ring-First→官方 HERO→点云/开放 Mesh；Ring 始终 CAD | [AGENTS](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/AGENTS.md)、[架构](../architecture/SYSTEM_OVERVIEW.md) | 不用 Ring 点云重建替换 CAD，不更改 Ring 参数 |
| D02 | DXY 与三维独立，DXY 仓库只读，正式 V9.1 固定 | [当前报告](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/TECHNICAL_REPORT.md) | 只消费像素几何；不把毫米测量/历史结果回退到新路线 |
| D03 | E4 分阶段：粗 Body 后先人工审阅，再考虑 A2/B1 | [路线图](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/docs/PHASE_E4_RESEARCH_ROADMAP.md) | 本次初始化未过门槛，不自动启动位姿/重定位/融合 |
| D04 | 当前 E1/E2 主组各4/4数值、0/4完整科研验收，结论MIXED | [资格表](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/metrics/NEXT_STAGE_ELIGIBILITY.json) | 不宣布通用赢家；2未收敛结果保留并排除选择 |
| D05 | Body-U 为正式R3 B3历史融合/校正结果，不是GT | [R3报告](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-BODY-ANCHORED-MULTIHERO-001/TECHNICAL_REPORT.md) | 冻结后对照，不参与新预测；明确历史整合 |
| D06 | 源码/参数/预测先冻结，GT仅后续评价 | [协作规范](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/COLLAB_STANDARD_v1.3.md)、[数据流](../architecture/DATA_FLOW.md) | 预测不得依据组名、GT或组误差选算法 |
| D07 | 015、016、MAX 视角选择有不同目标 | [015](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/TECHNICAL_REPORT.md)、[016](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-UPDATE-CAUSALITY-016/TECHNICAL_REPORT.md)、[MAX](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/TECHNICAL_REPORT.md) | 不无依据融合三套选择器；目标和support分别冻结 |
| D08 | P3D已真实验证，可见性离散步骤须detach/recompute | [RingAware](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/TECHNICAL_REPORT.md)、[014](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-PYTORCH3D-014/TECHNICAL_REPORT.md) | 禁止推荐原始爆梯度soft-zbuf；renderer通过≠主体通过 |
| D09 | 017 最终保留全部原面；TRUSTED 非真值 | [017](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017/TECHNICAL_REPORT.md) | 不默认执行PCA/边缘/gap删除，Raw保留 |
| D10 | 021 G01共同地标全背景，不证明跨视频息肉绝对正确 | [021](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/TECHNICAL_REPORT.md) | 不外推G03/G05/G06；共享SE3不能修同视频相对深度 |
| D11 | TSDF/NeuralFusion/全局MonoSDF扩展暂停；训练完整性分别记录 | [路线图](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/docs/PHASE_E4_RESEARCH_ROADMAP.md)、[失败记录](FAILURE_AND_DEPRECATED_ROUTES.md) | 不重复“官方首次接线”，不把未训练完整的MonoSDF当充分失败 |
| D12 | 局部雅可比秩不能认证全局唯一性/绝对位姿 | [repair诊断](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/metrics/JACOBIAN_IDENTIFIABILITY.json) | 区分带CAD离散的观测J、conic-only J与先验 |
| D13 | 本轮只建立文档与索引，不迁移src、不删历史、不做LFS迁移 | [任务报告](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-PROJECT-TECHNOLOGY-REGISTRY-001/TECHNICAL_REPORT.md) | 后续共享模块晋升、历史删除另行人工审查 |

## 保留的争议

相机Z与深度bias耦合、对称环yaw、HERO错层与真实侧面的区分、隐藏背面、柄部sheet、未命中梯度及真正独立留出均未解决。旧“candidate/key technical version”记录不是当前科学验收决定。历史不同口径不能自动覆盖；以任务ID、freeze与原分母定位后分别比较。见[待解决接口](OPEN_INTERFACES.md)。
