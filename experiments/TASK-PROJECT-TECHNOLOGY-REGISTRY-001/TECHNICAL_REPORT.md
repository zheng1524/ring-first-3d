# TASK-PROJECT-TECHNOLOGY-REGISTRY-001 技术资产注册报告

本任务为 DOCS-ONLY：对关键历史路线进行只读审计，建立项目入口、系统/坐标契约、43 个模块条目、33 项主题实验索引、决策/失败记录、技术依赖和三层资产规范。未提出新重建算法，未运行推理、拟合、训练、融合或测量。没有修改历史代码、指标、相机、CAD、HERO 或 DXY；没有迁移src、删除/移动/重命名历史资产或执行LFS迁移。

工作分支：exp/TASK-PROJECT-TECHNOLOGY-REGISTRY-001。parent：5636aaebd61a3d53b69f528692c4c7095df46508（DXY-REPAIR）。main 与历史清理审计分支的关系已检查，未发现应替代此科研基线的更新正式清理分支；history-audit 与 repair 分叉，不合并。详情：[基线审计](../../docs/registry/BASELINE_AUDIT.md)、[远程refs快照](../../docs/registry/REMOTE_REFS.json)。

## A 项目上下文与 B 技术路线

从[PROJECT_HOME](../../docs/PROJECT_HOME.md)进入。项目目标是CAD参考环锚定的息肉公制可见表面；DXY正式二维测量与三维独立。科学瓶颈是跨视频条件相机、HERO多层冲突、二维到三维不唯一和未观测区域。工程与科研双维状态明确分开；本任务没有授予任何候选新的科学验收。[技术路线表](../../docs/registry/TECHNICAL_ROUTE_MATRIX.md)逐项链接具体源码和指标证据。

当前E1/E2分别4/4主组数值、0/4完整验收；36次拟合中2次不收敛；75/75是DXY候选覆盖，不是真实轮廓正确率。E1/E2总体MIXED，未执行A2、HERO重定位/融合/新训练，未读真实三维GT；Body-U是历史正式R3 B3对照，椭球背面是先验。这些均直接继承冻结报告，没有重算历史统计。

## C 历史地图与源码证据

[主题实验索引](../../docs/registry/EXPERIMENT_INDEX.csv)含用户规定字段，另列THEME和历史分支tip。所有本地报告通过统一snapshot commit取回，日期定义为报告在该快照中的最后提交；不伪造运行日期。[54份顶层报告目录](../../docs/registry/REPORT_CATALOG.json)区分CURATED与仅发现未充分审阅，重要嵌套010–013另外索引。

[复用清单](../../docs/registry/REUSABLE_MODULES.md)有43条、41份不同Python文件，包含实际符号、分支、commit、完整SHA256、IO、调用、修改、限制与既有实验。AST静态核验符号，不执行原main。DIRECT/AST/ADAPTED/REIMPLEMENTED分别登记；旧Body-E重写不能冒充A1原样复用；PyTorch3D须用可见性修复版本。源码哈希与82份精选证据哈希分别在[机器模块表](../../docs/registry/MODULE_REGISTRY.json)、[证据清单](../../docs/registry/EVIDENCE_MANIFEST.json)。

[失败登记](../../docs/registry/FAILURE_AND_DEPRECATED_ROUTES.md)涵盖TSDF、NeuralFusion、未完成充分训练的MonoSDF、跨视频/重定位、Body/P3D、清理等，并逐组链接当前E1/E2实际投影与六方向图。没有把NOT_RUN算失败运行，没有把GT最佳刚体评价用于预测，也没有把S0/V2等历史测量用于回退。

## D 资产规范与 E 待解决接口

[资产政策](../../docs/registry/ASSET_MANAGEMENT_POLICY.md)定义Git、LOCAL_ONLY、评估后外部/LFS三层；列出大PNG/PLY/GLB/NPZ、SHA/来源、复现与删除审批规范，仅制定而未执行清理。[LOCAL_ARTIFACTS](../../docs/registry/LOCAL_ARTIFACTS.json)实际核验7个代表资产+1份旧清单指针；6个代表资产重算哈希，2.42GB checkpoint仅继承冻结回执哈希并核验存在/bytes，明确未重算。范围不是全盘普查。FINAL_CAMERA_POOL实际位于原始资产目录，不再复述“32源缺相机”的已纠正错误。

[待解决接口](../../docs/registry/OPEN_INTERFACES.md)与[12问验收入口](../../docs/registry/ONBOARDING_CHECKLIST.md)指引下一任务；本次不自动推进初始化失败后的研究。

## 固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 本任务无新测量组，N/A；继承当前主分析分母4物理组，另列历史11组/8组等范围，不相加 |
| 本算法独立成功 | N/A（未运行算法）；历史E1/E2各4/4数值、各0/4完整科研验收 |
| 本算法失败 | N/A；历史失败/NaN原样保留，当前36次拟合2未收敛及单源池null/NaN见原报告 |
| 历史测量值回退 | 0 |
| 失败组及具体原因 | 当前G01/G03/G05/G06逐组见[失败登记](../../docs/registry/FAILURE_AND_DEPRECATED_ROUTES.md)，有原帧投影/三维证据 |
| 最终统计样本 | 本次无新统计；历史仅相应路线独立成功组，并明确全体目标分母；不将23held帧当23物理组 |
| 是否使用GT选择算法 | 否；仅阅读冻结报告/指标/源码，不加载原始GT，不选择或生成预测；没有新参数需要冻结 |

中位绝对相对误差、真实尺寸MAE/p95/max：本DOCS-ONLY任务N/A；当前repair没有独立GT，为NOT_EVALUABLE。不得用px/IoU冒充这些指标。

## 验证与交付

最终只读校验回执：[AUDIT_VALIDATION.json](AUDIT_VALIDATION.json)。校验范围含规定文件、源码符号/哈希、报告/指标哈希、实验字段/枚举/路径、模块卡/机器表一致性、重要Markdown相对链接和GitHub不可变源码对象。不会访问HTTP验证全部外链；外链可用性明确限于本地git对象存在与内容哈希，不声称外部网页全量逐个联网验证。Git差异按docs-only路径允许清单核验；DXY与外层工作区保持不提交。

复核步骤：[REPRODUCE](REPRODUCE.md)。本分支单独提交/推送，最终commit和远程SHA由交付时git核验，避免将自身commit写入其内容产生自引用哈希。
