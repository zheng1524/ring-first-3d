# TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT

> **任务类型：独立审计；不是效果优化/功能开发。** 任务日期：2026-11-22。  
> **代码基线：** `exp/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE` / `bfd9c622bb2660b4a2e4c2ffdbadbb72b19971fd`。  
> **历史参考：** commit `5636aaebd61a3d53b69f528692c4c7095df46508` 下 019/020 源码。  
> **仓库：** `zheng1524/ring-first-3d`。  
> **建议新工作分支：** `audit/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT`，基于上述固定审计对象创建。  
> **验收关键词：** 程序真实调用、数学真实性、实验有效性、W0 来源、源码复用、独立复现、fail-closed。

## 0. 给 Codex 的唯一任务定义

作为**不参与 021 开发的独立审计者**，请先查明 021-CORRECTIVE 在真实数据上到底调用了哪些源文件、读取了哪些输入、优化了哪个目标函数、哪些测试真的具有证明力；然后定位 019/020 中已经实现却未进入当前正式链路的算法组件，提出**保持单一 W0 主线的最小修复方案**。本轮**不以提升 G03 数值、让 G01/G05 通过或输出新的跨视频相机为目标**。不得先修改再审计；不得直接执行 023 完整恢复与重新优化。

**研究总目标**：给两段视频的 W0 相机网络建立可信的共享 `SE(3)` 变换，使真实 Ring CAD、RGB 多视角背景三维地标、二维极线对应在公制空间自洽，之后才允许 HERO/Body 跨视频融合。正式变换方向为 `H_(005<-004)`，固定 005 世界，现行 W0 中单段内部相对运动原则上不变。历史 020 的 `004<-005` 方向与当前相反，复用时必须检查求逆和坐标约定。

## 1. 已知事实：必须从证据重新核实，不能将报告当作通过证明

1. 021 名义上修复六维 SE(3) 指数、标准 Sampson、累计幅度约束及 Adam 回滚；但部分测试与实际调用函数不相同，测试断言亦有缺陷。
2. 实际已知入口：`run_cross_video.py -> core/run_corrective.py -> w0_adapter -> cross_video_matches -> yaw_1dof -> shared_se3.optimize -> evaluate`；没有证据表明正式链调用完整的 `features019 / features020 / RingRenderer / objective020 / optimize020`。因此 021 目前是 **Ring + EPI + Prior 诊断**，不是完整 020 R3。
3. G03：W0 004 有 6 个 ACCEPT、005 有 16 个 ACCEPT；FIT / HOLDOUT 的 Sampson 中位数从 9.669/7.476 px 下降到 4.637/4.538 px，但 HOLDOUT <3 px 从 30.4% 下降为 29.4%，HOLDOUT p95 仍为 177.92 px；yaw 仍多模态；无可靠的跨视频共同 3D 地标。**不得宣称三维配准 PASS**。
4. G01、G05 的两段视频均有 `0 ACCEPT`；按统一准入应 `BLOCKED`，不得使用旧冻结相机替代。W0 `positive_depth` 使用 Ring 原点布尔值而非 RGB 轨迹深度比例，属于待单独审计的评价语义问题，不能在本分支静默修改 W0。
5. 文档/代码中 `accepted=80/80` 是 Adam 接受更新步，不是 80 个相机准入。`OPTIMIZE=PASS` 也不是三维几何验收。
6. 019/020 已有成熟模块和历史研究资产，但它们使用过旧视角及旧数据；**只允许迁移代码实现和算法语义，不允许迁移旧相机与旧结果作为正式输入**。

任何与上述事实不同的发现，都以**当前固定源码、实际输入及原始输出**为准，并用具体路径、函数、行号、文件 SHA 和日志更新结论。

## 2. 本轮边界（P0，违反任一项则任务无效）

- **禁止改动主线：** 不得修改 DXY、HERO、Body、Ring CAD、W0 正式门限、Mask 物理含义；不得用 Body/HERO 拟合误差校正 W0。不得改变统一任务约定，只为了某组的数字好看。
- **审计期间只读原工程：** 不直接改动 019/020/021 正式源码、历史运行包、主工作空间数据；在隔离工作树/临时目录复制代码、运行测试或写验证夹具。新脚本、审计报告允许提交到独立 022 审计目录；不覆盖既有结果。
- **禁止重新发明完整算法：** 旧模块缺失或接口不匹配时，先查 `git log`、固定 commit、源码依赖、配置及运行包，列出**源码检索证据**；只有确实无法复用时才给出替代实现建议。本轮不实施新算法。
- **禁止静默回退输入：** 只使用真实 PREPARED + 当前 W0 `camera_result/admission`；缺失文件、view ID、K、Mask、Ring 观测、匹配身份，标记 `MISSING/BLOCKED`。绝对不将缺失 3D 地标项设为 0 后宣称完整 R3 可运行。
- **禁止空 PASS：** 对于每项测试必须指出 GT、变化输入、可辨识性、断言表达式、运行日志、测试对应的正式函数。测试文件名或 `19/19 passed` 不构成算法验证。
- **不能静默调整阈值：** 按现行冻结协议评价；如发现阈值/状态定义错误，提交独立 W0 修复建议和影响评估，不在跨视频分支悄悄修改。
- **完整上传证据：** 不只提交 markdown；上传用于审计的代码、来源索引、隔离验证用例、输出、失败日志、sha、config 等；不上传含敏感数据的完整原始视频或无关巨大中间文件。必须提供原始数据的路径与 hash/访问方式（权限允许时），不能假造。
- **安全执行：** 不执行 `git reset --hard`、覆盖工作树、清理历史资产、批量删除文件。不为审计请求覆盖原始数据。任何需要修改原始项目的动作先停下，另列授权请求。

## 3. 执行顺序与证据产出（严格按阶段）

### S0：冻结审计对象、找到全部真实源码（先做；不得跳过）

1. 读取本压缩包 `README_FIRST.md`、`manifest/PINNED_GITHUB_SOURCES.json` 及历史交接说明。先核对仓库身份、git worktree 状态和指定固定 commit；记录未提交改动。若无法获得固定 commit，只报告阻断，不能切换到相似分支冒充。
2. 在**隔离输出目录**运行：`python tools/collect_pinned_sources.py --repo /真实/仓库路径 --out /独立输出路径`。它读取固定 git commit，逐项以 **Git blob SHA1** 校验列出的实际源码。必须检查失败/缺失汇总，所有关键条目未通过时不能宣称“源码齐全”。该脚本默认不联网、不修改 git 历史。
3. 并行查找固定 021 commit 下其余 `tests/*`、运行配置和 W0 入口；若发现新文件，补充审计清单并用 hash/commit 固定，不能用不明来源的最新文件替代。
4. 产生 `BASELINE_LOCK.md`：仓库、分支、commit、HEAD、dirty state、27+ 文件的 git blob/sha256、环境依赖、不可获得项目、历史 020 与 021 的文件结构差异。

**S0 停止条件：** 关键审计对象无法确定或代码来源不明，直接 BLOCKED；提交缺失列表和修复来源建议，不进入 S1-S5。

### S1：建立真实执行调用图与输入谱系

必须双轨取证：① 入口到函数的静态调用图（含实际 import）；② 隔离副本的最小动态执行/日志或明确标注动态不可运行。逐函数追溯 `PREPARED -> W0 camera_result -> W0 admission -> image/mask/K -> SIFT matches -> FIT/HOLDOUT split -> yaw seed -> H -> losses -> evaluation`。

- 对每个依赖注明“实际调用 / 仅被 import / 历史存在但未调用 / 缺失 / 数据来自外部”五种身份。
- 对每一视频和每一 view 核对 group、video、raw_frame、view_id、RGB、mask、Ring CAD、K（**每视角真实 K，不能统一硬编码**）、T 的方向、相机来源状态及文件 SHA。缺失 PREPARED view 不得静默 continue。
- 核对 `core/run_corrective.py`、`core/reproduce_offline.py` 中的硬编码 `K=[[490,0,319.5],[0,490,179.5],[0,0,1]]` 是否覆盖了真实 per-view K。
- 审查 `source_sha` 是否真正是 SHA256 而非路径字符串；确认不同组 `RUN_STATE` 的 `code_sha/config_sha` 是否相同。原报告中 G03 与 G01/G05 `code_sha` 不一致、配置 SHA 为空，需要溯源解释。

交付：`ACTUAL_CALL_GRAPH.md`、`SOURCE_INPUT_LINEAGE.csv`、`BASELINE_LOCK.md`。

### S2：数学与优化器审计（正式目标，而不是替身函数）

逐项审计并给可执行验证：

**M1—SE(3) / 约定：** `xi=(v,omega)` 顺序、左/右乘、world<-camera 及 camera<-world、004->005 方向、Ring 世界中心绕轴旋转、每视角 K 及二者不同时的 E/F 推导；与 SciPy/PyTorch3D 数值一致性。检查 `H_candidate @ inv(H_seed)` 的累计约束，而非逐步增量限制。

**M2—正式 loss：** 确认实际 021 中 Ring、Sampson、Prior（以及正式 R3 所需 SIFT 3D）的量纲、Huber、分母、归一和权重。对**同一个正式 objective、同一批观测和同一个 H** 比较总损失及逐项有限差分/自动微分梯度；不能拿 `torch_objective.py` 与其自身有限差分通过来宣称 `shared_se3.objective` 通过。零/无效 Ring 观测必须 fail-closed。

**M3—优化器：** 审查 Adam step、bias correction、累积 m/v、拒绝候选时 q/m/v/step rollback、暂停后保存并恢复 q/m/v/step 与随机性；真正验证 `resume==uninterrupted`（先运行 N 步、存盘、重载、再运行 M 步 vs 从头连续 N+M 步），不是两次从头运行。检查每个失败断言不会因 `if acc==0` 等分支未触发而绕过。

交付：`MATHEMATICAL_DEFECTS.csv`、`TEST_VALIDITY_REPORT.md`、隔离的最小可运行测试与日志。只修**测试夹具或审计副本**；正式源码的修复先写计划留到 023。

### S3：受控实验是否具有证明力

对 A2/A3/A6 逐个审计输入生成与 GT 的关系：

- **A2：** Ring/相机/观测生成必须确实施加非零 `H_true`。观察 `H_true` 换值，图像数据是否相应变化；未变化说明测试失效。
- **A3：** 构造具有平移与旋转同时非零的 GT，明确断言 `R_est R_true^T` 角误差和 `||t_est-t_true||`；不能只断言列表长度、代码执行结束、loss 降低。失败要区分优化器不收敛、实现错误和数据不可辨识。
- **A6：** 固定同一套合成观测，仅改变候选 Ring yaw；核实 Ring-only 的法向旋转歧义，以及加入可辨识 RGB 背景地标之后的约束是否真实出现。不能同时旋转观测和相机后得 0 误差冒充验证。
- **新增关键正对照：** 已知非共线、空间分布充分的 3D 背景同名点 + Ring CAD + 两组相机位姿 + 已知六自由度变换。要求联合方法在事先固定的几何阈值下恢复 GT，并给出噪声=0、可控噪声及错误匹配的对照；阈值在看结果前锁定、说明依据，不允许根据运行结果追调。
- **负对照：** Ring-only yaw 不可辨识、错误特征身份、极小基线、无 3D 地标等场景应呈现 `AMBIGUOUS/INVALID/BLOCKED`，不能无声 PASS。

交付：每个测试的 GT、观测生成代码、断言、误差、结论与反例。**S3 任务是审计/证伪：若需要重新实现完整 R3 才能做的正对照，应标明尚无法执行、列入 023，而不是发明一个替代目标函数做通过演示。**

### S4：真实数据 G03 匹配、W0 跨组和评估协议

- G03：追踪 FIT 2003 / HOLDOUT 1746 匹配的每一来源，按 Raw keypoint -> ratio -> mutual -> 背景 Mask -> robust geometry -> track ID -> 3D landmark ID -> FIT/HOLDOUT 分组统计。不应假定这些历史阶段已全部发生；没有发生的标注 `NOT_IMPLEMENTED`。检查 `n_raw=len(ka) and len(kb)` 统计错误。
- 对随机抽样+最大残差样本绘制可检查的原始两图匹配、坐标、类别 Mask、视角分布、时间簇和误差分布（必要时只输出受限图，不公开完整原始视频）。回答为何 p95 ~178 px、3 px 内点率不足；区分匹配噪声、视角几何错误和统计方法问题。不能通过删除高残差匹配来制造成绩。
- FIT/HOLDOUT：核对 005 偶/奇划分的实际数据泄漏；004 视角是否全部被训练观测用到；匹配身份筛选、初始化、权重调参是否接触留出数据。提出**两侧视角/地标/时间簇留出**的可实施协议。冻结评估定义，不能看结果后改划分。
- G01/G05：检查各 004/005 的 W0 0 ACCEPT 证据，区分 Held p95 尾部、轨迹不足、实质几何失配。审计 `positive_depth` 指标语义与六段视频的结果影响，形成单独 W0 bug 建议；**不在 022 修改 W0 或放宽门限**。
- 报告 `OPTIMIZER_ACCEPTED_STEP`、`W0_VIEW_ACCEPT`、`DIAGNOSTIC_OPT_COMPLETED`、`CROSS_VIDEO_GEOMETRY_ACCEPT`、`BODY_CROSS_VIDEO_ADMISSION` 五类不同的指标/状态；当前正式 `BODY_CROSS_VIDEO_ADMISSION=NO`。

交付：`W0_GROUP_DIAGNOSTICS.md`、真实数据分项统计与必要的可视化索引、`LEAKAGE_AUDIT.md`。

### S5：最小修复和正式 023 实验设计（**先审计，后提方案**）

- 对比历史 `features019.py`、`features020.py`、`ring020.py`、`objective020.py`、`optimize020.py`、`gate020.py`、`feature_gate020.py` 与当前真实链路，以**函数级**制作复用矩阵：旧功能/依赖、现行 W0 适配点、必须修复的缺陷、数学差异、新旧状态、跨组回归需求。
- 正式 023 应恢复的目标语义：`L = L_Ring + 0.2*L_SIFT3D + 0.02*L_EPI + 0.01*L_Prior`（参考历史 R3，**本轮不得调整权重**）。其中 `L_SIFT3D` 必须来自多视角身份可追踪的背景三维地标，并做双向 3D->2D 投影。只有 EPI、没有真实 3D 地标时明确标 `INCOMPLETE`。
- 对 W0 所需新接口列出精确输入字段、前后约定、转换公式；禁止把历史 G01 的 view/相机/landmark/初始 yaw 拿来当 G03 正式输入。
- 写一个 023 的 staged plan：先 P0 数学修复+干净环境 Level-1 复算 -> 再最小 019/020 接口适配 -> 可辨识受控 GT -> G03 两侧留出真实验证 -> G01/G05 不绕门控的跨组回归。只在共享 SE(3) 严格失败并证据充分时另行讨论 BA。

交付：`SOURCE_REUSE_PLAN.md`、`MINIMAL_FIX_PLAN.md`、`TASK_023_PROPOSAL.md`，每一修复条目有 owner file/function、最小 diff 方向、测试、回归范围与未通过时退出机制。

## 4. 最终提交与验收

应在**新的独立审计目录**中提交并上传：

```
experiments/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT/
  INDEPENDENT_AUDIT.md
  BASELINE_LOCK.md
  ACTUAL_CALL_GRAPH.md
  SOURCE_INPUT_LINEAGE.csv
  MATHEMATICAL_DEFECTS.csv
  TEST_VALIDITY_REPORT.md
  W0_GROUP_DIAGNOSTICS.md
  LEAKAGE_AUDIT.md
  SOURCE_REUSE_PLAN.md
  MINIMAL_FIX_PLAN.md
  TASK_023_PROPOSAL.md
  audit_tests/                  # 可运行的最小夹具，标注审计副本
  results/                      # 数值、分项报告、可视化与失败数据
  provenance/                   # 输入/代码/配置 sha，运行命令、环境及日志
  evidence/                     # 原始报告与核心输入副本或不可获取说明
  FINAL_SUMMARY.md
```

最终交付标准：

1. **每个 P0/P1 结论至少有路径+行号或函数+可复现测试+定量/日志证据**；没有证据标 `SUSPECTED/UNVERIFIED`。
2. **对 021 是什么以及不是什么有明确结论**：正式目标，未调用历史算法，哪些所谓 PASS 不可用，哪些修复真正有效。
3. **能指出 023 最少需要改哪些文件**，而不是给出一套全新的“更好算法”。
4. **不制造新的官方相机结果**：若进行隔离验证，仅报告 `AUDIT_DIAGNOSTIC`；G01/G05 没有 W0 ACCEPT 时保持 BLOCKED。
5. **版本一致且可溯源**：固定 commit + 每个文件 SHA + config SHA + 按组真实输入 SHA；多组不得因为运行代码版本不同却声称统一复现。
6. **可复现边界明示**：Level-1=用已归档相机/匹配/观测重新算优化与评价，在无 `/home/liu` 的干净目录执行；Level-2=从 RGB/Mask/当前 W0 完整重放。未真正成功运行不得写“已实现”。本次至少要审计现有 Level-1 的真实可行性并提出阻断清单；不要求在 022 重做全部 Level-2。
7. **上传实际资产**：审计脚本、输入夹具、输出、完整 stdout/stderr、版本清单和失败证据；对过大/无权分发的原始资产记录引用路径与 hash，不凭空添加到包内。

**判定权限：** 022 只能给 `AUDIT_PASS / AUDIT_FAIL / INCONCLUSIVE`，不得宣布跨视频三维配准已通过。`INCONCLUSIVE` 和 `BLOCKED` 是合法且有价值的结论。正式 023 实施必须等待 022 的最小修复方案和独立验收。

## 5. 应立即重点检查的十个问题（审计优先级）

| ID | 优先级 | 核心问题 | 预期证据 |
|---|---|---|---|
| P0-A | P0 | `torch_objective` 与实际 `shared_se3.objective` 不同 | 同批输入分项目标/FD 梯度对照 |
| P0-B | P0 | A2/A3/A6 缺少有效 GT 测试/断言 | 固定观测 GT 及明确阈值断言 |
| P0-C | P0 | Adam 回滚、step 和断点续算测试不足 | q/m/v/step 保存恢复对照 |
| P0-D | P0 | 单向成对 SIFT 未恢复多视角 3D 地标 | 实际调用链、019/020 源码对比 |
| P0-E | P0 | Ring 正式监督/遮挡语义不完整 | RingRenderer 与 ring_term 数学对照 |
| P0-F | P0 | 硬编码 K、跳过 PREPARED、伪 `source_sha` | per-view K 和源谱系追踪 |
| P0-G | P0 | G03 与 G01/G05 `code_sha` 不一致 | 三组冻结源码+配置 hash 回溯 |
| P1-H | P1 | 004 未独立 HOLDOUT，可能泄漏 | 双侧视角/地标/时间簇留出分析 |
| P1-I | P1 | 离线复现仍依赖 `/home/liu/...` | 无工作站目录的真实复算证据 |
| P1-J | P1 | `INIT=AMBIGUOUS` 却呈现 `OPTIMIZE=PASS` | 状态/准入语义一一对应 |

## 6. 请用下面的最终报告结构回复人工研究者

1. **一句话总结：** 当前 021 可信到什么程度？
2. **已验证的成果：** 仅保留独立复核能支撑的修复。
3. **阻断列表：** P0/P1 问题按严重性和依赖排序，每一条给证据。
4. **原代码复用清单：** 019/020 哪些模块下轮必须重新接入，哪些可以不动。
5. **现有真实结果的正确解释：** G03 数字能证明什么、不能证明什么；G01/G05 为何被阻断。
6. **下一轮最小修复：** 023 需要改什么，预计验证什么，遇到阻断如何停止。
7. **审计产物索引：** 提交 SHA、实际文件路径、压缩包路径、命令、测试日志以及尚未获得的数据清单。

**最终再次强调：022 不是让你把跨视频配准做成功，而是让我们第一次能够确信：当前程序到底做了什么、哪里错了、下一步只需要修什么。**
