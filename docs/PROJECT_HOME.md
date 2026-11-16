# Ring-First 3D 项目入口

工程入口更新（TASK-RESEARCH-HARNESS-STORAGE-001）：[Research Execution Harness](RESEARCH_EXECUTION_HARNESS.md) 已提供 DXY 像素几何、独立视角选择和公制 Renderer 的共享接口；真实测试及 11 项契约通过。T31/T34 仅兼容性测试。先查注册表，再 Preflight/Smoke，随后执行已授权的大实验；本轮不提升科研验收状态。范围见[晋升政策](registry/MODULE_PROMOTION_POLICY.md)。

审计日期：2026-11-16。文档任务：TASK-PROJECT-TECHNOLOGY-REGISTRY-001。
科研快照：`exp/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001@5636aaebd61a3d53b69f528692c4c7095df46508`。
[基线与审计边界](registry/BASELINE_AUDIT.md) · [技术路线总表](registry/TECHNICAL_ROUTE_MATRIX.md) · [具体代码接口](registry/REUSABLE_MODULES.md)。

## 研究目标与当前问题

Reference-Ring Anchored Visible-Surface Reconstruction of Polyps：利用已知尺寸的参考环 CAD，恢复公制相机与息肉可见开放表面，保留真实来源、遮挡、不确定性，最终为物理测量提供可评价的三维证据。完整隐藏背面不是当前可观测事实，漂亮的封闭体或 GLB 不能替代精度与覆盖评价。

当前瓶颈是：条件相机与跨视频坐标关系尚未全面认证；多 HERO 来源存在深度层冲突；二维轮廓可被不同三维体解释；未命中区域缺少有效形状梯度；细柄/环下未知连接不能凭先验当作观测补齐。见[失败路线](registry/FAILURE_AND_DEPRECATED_ROUTES.md)与[待解决接口](registry/OPEN_INTERFACES.md)。

## 数据规模必须按实验解释

| 范围 | 实际分母与身份 |
| --- | --- |
| 015/016 的多组体型实验 | 11 物理组：Ip 5、Is 3、IIa 3；不是全项目数据总量 |
| 历史资产审计 002 | 8 物理组、9 视频；过滤条件 54，数值输出 40、NOT_EVALUABLE 14 |
| MAX-COVERAGE | G01/G03/G05/G06 共 4 物理组、8 视频、12 照片；7,650 解码帧→884 候选；47 次实际 HERO 含 1 控制 |
| 当前 DXY-REPAIR | 同 4 主物理组，75 来源、74 独立 RGB；主分析仅各组 004；另有独立 005/照片池，不直接合并 |
| 整个项目数据总量 | 本轮未做全盘数据普查，UNKNOWN；不能将上述重叠分母相加 |

具体证据按主题查[实验索引](registry/EXPERIMENT_INDEX.csv)。物理组、视频、帧、来源、拟合次数、提案次数是不同统计单位。

## 技术主线与进度

正式技术边界为：真实 RGB → 冻结分割/Mask → Ring CAD 与条件相机 → 官方 HERO 原生深度 → 可追溯点云/开放 Mesh → 独立评价。DXY V9.1 正式二维测量独立运行，三维端只消费像素几何或 Mask；不得修改 DXY、用历史直径或 GT 补三维预测。

E4 路线图提出粗 Body→人工审阅→A2 背景位姿→人工审阅→B1 保形 HERO；这是分阶段研究入口，不是已经全部通过的执行结果。当前 DXY-REPAIR 到主体初始化即停止：官方 DXY 75/75 产生候选（38 正常、37 Q-conflict 恢复），E1 几何与 E2 全 Mask 各 4/4 主组数值输出，36 次拟合中 2 次未收敛；完整科研验收各 **0/4**。E1/E2 结论 **MIXED**。本轮结果没有授权自动接入 A2、HERO 重定位或融合。[原报告](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/TECHNICAL_REPORT.md)

稳定的是有范围的工程接口：官方 DXY API、九参数解码与解析投影、修复后的 PyTorch3D/Ring-Aware renderer、来源身份与冻结核验、真实 P0 可视化。它们的工程验证不等于具体主体重建算法通过科研验收。015、016、MAX 三种选视角目标不同，不能自动合并。

候选研究包括主体优化、Sobolev 提案、GeometryGuard、完整原生 HERO 损失、跨视频 BA。TSDF/NeuralFusion 当前目标失败；MonoSDF 未完成充分训练，不能归为充分训练后的失败。历史融合与 HERO 重定位均未成为已认证三维 baseline。

## 新任务从这里开始

1. 读[系统架构](architecture/SYSTEM_OVERVIEW.md)、[坐标契约](architecture/COORDINATE_AND_DATA_CONTRACTS.md)和[决策记录](registry/DECISION_LOG.md)。
2. 在[路线表](registry/TECHNICAL_ROUTE_MATRIX.md)选技术 ID，再按[模块清单](registry/REUSABLE_MODULES.md)核对文件、函数、分支、commit、完整 SHA256 与实际调用。
3. 使用独立任务目录，先冻结来源、参数、FIT/HOLDOUT、预测与源码哈希；GT 只在独立评价阶段读取。
4. 核查失败证据与[资产规范](registry/ASSET_MANAGEMENT_POLICY.md)。缺输入保留 NaN/NOT_EVALUABLE；历史测量回退为 0；登记全体目标分母及共同成功组。
5. 先完成[Harness 预检查与真实 Smoke](RESEARCH_EXECUTION_HARNESS.md)，再执行明确授权的科研任务。四组 E1/E2 多初值、留出轮廓与 Ring 穿透证据仍待人工审阅；本轮用户授权的有限接口工程化不改变科研主线或授予算法科学验收。

可用[12 问入口](registry/ONBOARDING_CHECKLIST.md)检查理解。历史路线图/技术版本保留原文；当前范围与证据优先于旧版本“候选”称谓。
