# RA_REVIEW_REQUEST_E0_001｜Phase E E0 竞争实验首轮独立审查请求

**发起者**：PM（2026-10-30）　**状态**：`PROPOSED / RA_REVIEW_PENDING`　**Codex**：`NOT_DISPATCHED`。

## 0. 请 RA 优先评价的主张

E0 不是再扩大边界生长阈值，而是尝试一个统一几何表示最大程度解释具有相机/深度不确定性的真实多视角观察。竞争者为逐场景优化的 `Uncertainty-Aware Neural SDF`（Arm S）和官方预训练前馈 `MapAnything`（Arm M）。我们不假定神经模型一定优于历史 F3；当前仅请求**审查实验设计与 P0 静态审计任务**。P1 最小运行和 P2–P4 四组竞争尚未授权，GPU 未启动。

## 1. 已核对的真实研究事实与来源

|事实|仓库版本/量化结果|科学判读|
|---|---|---|
|边界生长新面|`fa50f68`：4物理组、5视频，300轮接纳、22/24新HERO成功；五视频新增完整原面暴露代理分别17.8053、16.0070、8.8305、5.2470、15.7549 mm²|真实工程上形成来源连通原面，**非唯一解剖新增面积，也未认证物理精度**|
|G01 共同 RGB 退化|同像素 S0→Joint：004_15 22.813→24.155；005_00860 19.634→22.809；005_00611 8.842→10.941（MAE/255）|Joint 不能因接缝更好/覆盖变化认定几何更好；反光/位姿有干扰但退化事实成立|
|固定 Ring CAD 穿插|同批旧点经 Joint 后额外入 Ring：004 19、005 21；最深0.1165/0.2561 mm（`CAD_penetration_diagnostic`）|违背无新增穿插强条件；G07 原有287点穿插是另一个压力反例|
|MASt3R分区已真实执行|`4adfe3aa`：18次官方MASt3R、5次冻结 HERO，80,419 Raw/75,273 Cleaned新 XYZ；005 独立非自投影覆盖73.921%→79.133%，共同 MAE16.981→17.025|覆盖改善有限且伴随共同误差略升，不把新点数当正确性|
|跨视频不融合|G01 双向轴向冲突65.90%/70.40%，面距离 p95 2.551/0.911 mm；边界生长追加005→004局部1.1331 mm²候选未带来目标覆盖|所有跨视频只 `REGISTRATION_CANDIDATE_NOT_FUSED`；不同视频 Ring-local mm 坐标未统一认证|
|可观测/GT限制|`43274773`：G01两视频独立局部轨迹；G06仅少量来源、G08有限、G07不合格相机；四组真实部署GT变换未知|不做 GT 对齐/绝对3D认证；高度/直径数学候选不能作为本轮优化监督|
|硬件阻塞|`fa50f68`：005末两次 CUDA 输入上传故障；新进程 CUDA 不可用而 `nvidia-smi` 可见 RTX3060 6GiB|这是运行环境故障不是算法效果证据；必须先审查可用性|

完整证据路径：

- [边界生长报告](https://github.com/zheng1524/ring-first-3d/blob/exp/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001/TECHNICAL_REPORT.md)、[结果](https://github.com/zheng1524/ring-first-3d/blob/exp/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001/RESULT_INDEX.md)、[复现](https://github.com/zheng1524/ring-first-3d/blob/exp/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001/REPRODUCE.md)。
- [分区MASt3R报告](https://github.com/zheng1524/ring-first-3d/blob/exp/TASK-VIEW-PARTITION-MAST3R-FUSION-001/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001/TECHNICAL_REPORT.md)、[代码复用](https://github.com/zheng1524/ring-first-3d/blob/exp/TASK-VIEW-PARTITION-MAST3R-FUSION-001/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001/CODE_REUSE_AUDIT.md)。
- [可观测/GT资格报告](https://github.com/zheng1524/ring-first-3d/blob/exp/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/TECHNICAL_REPORT.md)。

## 2. 实现复用与外部方法（实测和预计严格区分）

历史现成：`camera_frame_inventory`、`Ring-First source/target_source`、`load_official` HERO、`unproject/depth_mesh`、Cleaned/Raw/source UV、`projection/common_metric` 真 A→B、`cad_audit`、`real_p0_renderer.py`（固定mm轴、RGB源色）和 GLB/NPZ 输出。**已静态核对仓库内的 CODE_REUSE_AUDIT，但未在旧实验机运行这些代码，原视频/完整XYZ/权重不在 GitHub 主分支。** 参见 `CODE_REUSE_AUDIT.md`。

SDF 方法：

1. [MonoSDF 官方实现](https://github.com/autonomousvision/monosdf)，[arXiv 2206.00665](https://arxiv.org/abs/2206.00665)；深度监督思路直接相关，但几何 cue/相机/环境适配待审。
2. [NeuS2 官方实现](https://github.com/19reborn/NeuS2)，[arXiv 2212.05231](https://arxiv.org/abs/2212.05231)；较快但有 Instant-NGP/CUDA 构建和6GiB风险。
3. [SparseRecon 官方实现](https://github.com/hanl2010/SparseRecon)，[arXiv 2508.00366](https://arxiv.org/abs/2508.00366)；相关特征/深度一致性，但额外旧版Torch/特征模型依赖很重，可作方法参考不默认首选。

正式竞赛 M 臂：[MapAnything 官方实现](https://github.com/facebookresearch/map-anything)、[arXiv 2509.13414](https://arxiv.org/abs/2509.13414)。官方 README 支持 `img, intrinsics, depth_z, camera_poses, is_metric_scale`；pose 是 OpenCV cam2world；depth_z 要配 K/ray，不可同时 K 和 rays。其代码 Apache 2.0，研究权重 CC-BY-NC 4.0，另有 Apache 权重；v1.1 版本/权重必须固定。尚未验证本机 6GiB 可用性/模型缓存，不许称模型已经可运行。

## 3. 统一输入、四组资格与真留出

E0 Adapter: RGB/Mask SHA、原像素/resize K、distortion、c2w(wrt 视频本地 Ring)、native HERO optical-Z/depthSHA、XYZ/UV/sourceID、Ring R5/R10 CAD、相机资格与观测可靠性代理；内部 mm，送模型可转 m，位姿平移与所有几何**同变换**。Map 输出 `pts3d/depth_z/pose/conf/mask` 还原 mm；SDF 提取开放可见零水平集并记录 `observed_support` / `prior_only` / `unknown`。Ring CAD 独立固定，不作为神经网络重新雕刻的 Ring 表面。

|组/视频|相机与数据|现有评价身份|E0 审查状态|
|---|---|---|---|
|G01_004 Ip/R10|NORMAL_CONDITIONAL，旧 P0 3 参考；004原视频 raw 编号未独立核准|分区旧HOLDOUT污染；生长有一张 `004_15` 非已知 HERO 来源但 `whole_pipeline_blind=false`|单视频可静态审计；**未获得严格盲留出认证**|
|G01_005 Ip/R10|NORMAL_CONDITIONAL，旧 P0 3 参考|分区旧非自投影5帧；生长 `00860`、`00611` 目标，均非全流程盲|首选 P1 单视频候选，先做所有 HERO 输入 SHA 排除|
|G06_004 IIa/R10|NORMAL_CONDITIONAL，旧P0 1参考、新参考1；条件邻接 PnP|分区非自投影2帧；旧HERO输入集合部分不全|跨形态第二候选；先查依赖|
|G08_005 IIa/R10|LIMITED，旧P0 1参考/新参考1|分区无预冻独立留出；生长两张有限诊断帧|只能敏感性/诊断，不能后验称盲测|
|G07_004 Is/R5|UNQUALIFIED_CAMERA_STRESS，旧P0 1参考/新参考1|分区非自投影1帧；姿态不合格|只作压力测试、另列，不进入正常成功率|

`HOLDOUT_STRICT` 的定义为从未进入旧/新 HERO multi-view 输入、P0 源、E0 拟合/调参的源图 SHA；历史 `HOLDOUT_RECON_ONLY` 仍可用于受限一致性验证。新任务应在任何模型推理前保存完整 `SOURCE_LEAKAGE_LEDGER`，若缺乏完整旧 HERO 输入列表，就如实标 `UNKNOWN/NOT_EVALUABLE`。不得把五视频当五独立病例。

## 4. S0 最小方法与公平性安排

建议 S0 相机冻结，单视频单场景优化；Mask silhouettes + 鲁棒 RGB + 冻结 HERO 光轴 Z 深度一致性 + Eikonal 约束，权重来自预冻结的来源/深度/相机/可见性代理且不能自发变零。可用损失：`L_rgb + L_sil + w_depth*rho(z_sdf-z_hero) + L_eikonal`；`CAD collision`/跨帧 feature 应列 S1 单独消融，不能不说明地只加给 SDF，然后与 Map M0 宣称公平。

Map M0 RGB、M1 RGB+K、M2 RGB+K+冻结 pose、M3 RGB+K+pose+Z-depth（仅官方接口和相机资格同时通过时）。对照分为①**输入条件匹配**的 SDF 与 Map 子实验，②**各自最优合法条件**，均对照 Raw/Cleaned/F2/F3，同目标帧、同原 Mask、同可见共同像素/同 Ring CAD；同时报告显存/时长/人工干预、支持区域和不可评价。Map M0 RGB 自称公制也要独立 Ring 尺度审计；不允许 GT ICP 调整。

当前可用物理分组太少，不能设定“四组统计显著证明冠军”。停止状态需要区分：`RUNTIME_BLOCKED` / `DATA_INELIGIBLE` / `ALGORITHM_NOT_PROVEN`；两臂均失败就是 `BOTH_NOT_PROVEN`。量化阈值尚请 RA 冻结，不能结果出来后补门槛。

## 5. Codex 第一轮任务与代码变动

拟派发 `experiments/TASK-NEURAL-E0-COMPARE-001/TASK.md` **仅 P0 静态审计**：完整来源/图像/深度/模型依赖SHA，核验数据与真留出分层，GPU 只读检查，接口/单位静态样例，官方版本/许可证/权重大小可执行性，SDF 候选两选一建议，出 P1 最小有界烟测预算提案。P0 不安装、不下载、不推理、不训练、不重配准，不改相机/深度/渲染核心。可变代码范围仅未来 adapter 设计与新 Task 文档；禁止触碰冻结 P0/HERO/Ring-First/CAD/Dxy，拒绝 GT Loader 进入训练路径。

如果获授权执行 P0，Codex 在独立分支增量 push 3–4 张输入/资格核心图、4组/5视频清单、源码+数据 SHA、中文单份报告与失败 ledger。随后由 PM 验收、RA 审阅，再请研究者单独批准 P1 最小实际运行。**本请求目前既未发给 Codex，也没有 GPU 权限**。

## 6. 请求 RA 裁决的三个实质问题（最多三项）

1. **SDF 基座与最低可验证损失**：优先哪一个官方实现（MonoSDF/NeuS2；SparseRecon作为补充），能在 RTX3060 6GiB 的现实环境下做最小单场景 S0 且最少改原有代码？在纯几何支持受限时哪些 loss 应禁用/延后，何时宣布基座不可行？
2. **留出严格性与结论范围**：若 G01_004/G08 无法补证真正严格独立帧，是否将科学 E0 主要比较限制在可确认的 G01_005/G06，其他三视频（含004、G08、G07）保留诊断/压力并列，禁止报告四组泛化成功？是否认可 `HOLDOUT_RECON_ONLY` 仅称“给定冻结 HERO 条件的一致性证据”？
3. **公平成功门槛**：如何预注册覆盖、共同像素误差、CAD 新穿插、source-support、运行成本的最低必要改善与否决规则，以避免“只因SDF更平滑”或“只因Map更快”就宣布赢家？SDF/Map 输入匹配和各自最优配置双表是否足够？

期待 RA 回传：`RA_DECISION_E0_001.md`，明确 `ACCEPT / REVISE / REJECT`、逐项意见、是否允许 PM 将 P0 任务提交研究者审批。RA 不向 Codex 直接下命令。

## 7. GitHub 交接阻塞（不能忽略）

当前 PM 可读所有上述实验分支和资料，但创建 `pm/phase-e-e0-review-001` 被 GitHub 返回 `403 Resource not accessible by integration`。因此此份内容暂为**待上传包内草案，不是已经在共享仓库的 RA 请求**。请由具仓库写权限的 Codex 在用户许可下**仅上传文档**，或修复连接后由 PM 创建审核 PR；报告 commit/PR URL 后再请 RA 从同一仓库读取。不同对话不会自动触发审查。
