# 新加入智能体的12问验收入口

仅阅读 PROJECT_HOME 与 registry 后，应能用下表定位明确答案；链接继续提供源码/指标证据，不要求重新通读全部历史。

| 问题 | 应掌握的答案 | 定位 |
| --- | --- | --- |
| 1 技术架构 | RGB/Mask→Ring CAD条件相机→官方HERO→原点/开放Mesh→评价；Body为候选 | [项目入口](../PROJECT_HOME.md)、[依赖图](DEPENDENCY_GRAPH.mmd) |
| 2 正式二维提取 | 独立DXY V9.1 measure_files/measure_frame；固定commit；不改DXY | [T01–T04](REUSABLE_MODULES.md) |
| 3 可复用选视角 | 015质量角度、016方向配额/权重、MAX可见proxy；目标/support分开 | [T10–T13](REUSABLE_MODULES.md) |
| 4 FIT/HOLDOUT | 先冻结本任务角色并保留上游身份；条件留出，重复RGB/共享父不独立 | [入口](../PROJECT_HOME.md)、[决策](DECISION_LOG.md)、[待解决接口](OPEN_INTERFACES.md) |
| 5 Ring-First边界 | CAD公制不消除yaw/深度耦合；单视频条件pose不等于跨视频统一 | [T14–T18](REUSABLE_MODULES.md) |
| 6 HERO与清理 | 官方loader/nativeZ/原ID/四状态可复用；018与MAX mesher不同；0删面非失败漏执行 | [T19–T23](REUSABLE_MODULES.md) |
| 7 P3D直接复用 | 014修复renderer、FreeVertices、MultiObjective、ContourDistance、Guard按原契约 | [T24–T34](REUSABLE_MODULES.md) |
| 8 九参数问题 | E1/E2各4/4数值0/4验收，多初值、留出轮廓、Ring穿透；隐藏背面先验 | [逐组失败](FAILURE_AND_DEPRECATED_ROUTES.md) |
| 9 跨视频未通过 | PhaseD D2 NOT_FUSED；019/020/021混合；重定位34/150条件候选非认证 | [失败记录](FAILURE_AND_DEPRECATED_ROUTES.md)、[索引](EXPERIMENT_INDEX.csv) |
| 10 不应重复什么 | 失败soft-zbuf、盲删Type2/PCA/SOR、将官方NF接线当新工作、把MonoSDF未跑当充分失败 | [失败记录](FAILURE_AND_DEPRECATED_ROUTES.md) |
| 11 下一步调用 | 先审阅E1/E2证据，复用T04–T09及T36/T37；不自动进入A2/HERO | [待解决接口](OPEN_INTERFACES.md) |
| 12 如何追代码版本 | 实验commit→报告/冻结→module commit+SHA→符号/输入；不用可移动分支代替 | [基线说明](BASELINE_AUDIT.md)、[机器表](MODULE_REGISTRY.json)、[资产规范](ASSET_MANAGEMENT_POLICY.md) |

上述链接提供导航，完整文件与源码不可变链接是正式追溯入口。总体数据规模未普查，11组/4组/75源不能相加或混称全项目。
