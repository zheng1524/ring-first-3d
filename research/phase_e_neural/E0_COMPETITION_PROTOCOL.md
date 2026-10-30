# E0｜Uncertainty-Aware Neural SDF vs MapAnything（竞赛预注册草案）

版本 `v0.2-PM-PROPOSED` · 2026-10-30 · **尚未获 RA 或研究者批准、尚未开始实验**。

## 1. 科学问题、假设与成功边界

**目标**：给定冻结的真实多视角 RGB、Ring CAD、候选/条件相机、HERO 深度和有来源身份的局部几何，比较两种方法能否形成**观测支持的统一可见表面**，改善真实未参与几何拟合目标视角的解释、降低局部层冲突和 Ring 实体穿插。模型仅根据先验生成的未知背面不属于观测认证面积。

- `H-S`：相机冻结、单物理场景逐场景优化的 Neural SDF，在显式不确定性/可见性下，可优于 Cleaned/F3 的至少一项预冻结外部观察指标，同时不出现不可接受的覆盖损伤或新增 CAD 穿插。
- `H-M`：MapAnything 预训练推理，合法的 K/pose/Z-depth 辅助输入应相对于 RGB-only 有可测几何收益，且其公制 Ring 尺度/实体合理性仍须独立审计。
- 允许 `BOTH_NOT_PROVEN`、`SINGLE_VIDEO_ONLY`、`NOT_EVALUABLE`。两臂计算范式不同，不用同等运行时间伪装公平；报告实际预算/输入和一张匹配输入条件的子比较表。

## 2. 资格、冻结与泄漏规则

|物理组|形态/Ring|E0 资格|正确的分母|
|---|---|---|---|
|G01|Ip/R10，video004、video005、photo001–003|两段视频各自 LOCAL_RING_MM，独立 SDF/Map；跨视频 `CANDIDATE_NOT_FUSED`；照片只作诊断|1 个物理组、2 个视频场景，不当作 2 病例|
|G06|IIa/R10|`NORMAL_CONDITIONAL`；有 2 张历史非自投影诊断帧，但旧 HERO 来源须核查|1 组、1 视频|
|G08|IIa/R10|`LIMITED_STRESS`；此前无预冻结独立留出|1 组、1 视频，仅有限条件结论|
|G07|Is/R5|`UNQUALIFIED_CAMERA_STRESS`，相机不合格|1 组、1 视频；不进正常科学成功率|

固定用历史来源 manifest 确认每个视角 `image_sha, mask_sha, original_frame_id, image_processing, K, distortion, c2w, pose_quality, depth_type, native_depth_sha, HERO_input_image_shas, confidence_proxy, train_or_infer, holdout, physical_scene_id`。若历史预测的源图或同一图像进入 HERO multi-view 输入，就不得称 E0 **全流程盲留出**。分为：`HOLDOUT_STRICT`、`HOLDOUT_RECON_ONLY`、`DIAGNOSTIC_ONLY`、`INELIGIBLE`，精确列 SHA 和去重理由；不得后验换帧。

执行任何竞赛模型之前固定方法代码版本/权重SHA、数据源SHA、样本名单、训练/推理视角、验证/最终检验划分、指标、参数和预算。`GT_ACCESS=DENY` 为训练、初始化、筛选、注册、调参与胜者选择的强约束；GT 仅可冻结后读取做独立后验，部署变换未知时绝对3D误差 `NOT_EVALUABLE`。

## 3. 统一相机/几何契约

**内部几何**公制 `mm`；如模型期望米，所有 XYZ、camera translation、HERO `depth_z` 和尺寸同步乘 0.001，返回内部再乘1000。`depth_z` 是相机光轴 Z，不是沿视线长度。位姿的 `c2w` 为 OpenCV 相机系（右 X、下 Y、前 Z）；输入前检查行列、旋转行列式、相机前方正 Z、深度与投影 Ring CAD 的次序。调整分辨率时对 K 的 `(fx,fy,cx,cy)` 和 Mask/深度采取各自正确采样，冻结转换矩阵、不能悄悄换内参。

统一 output adapter 记录 `world_xyz_mm`, `source_pixel_uv`, `source_frame_sha`, `method`, `confidence_raw`, `confidence_calibration`, `observed_supported`, `prior_only`, `occluded_or_unknown`, `scene_id`, `camera_source`。**MapAnything 的 `conf` 并不自动等于独立 3D 概率校准；SDF 闭合表面也不自动拥有真实观察支持。** 两臂最终在固定开放可见域上审计，可输出其他推测区，但不得混统计。

## 4. Arm S：单场景 Neural SDF

优先审计成熟实现的可改造性：

- [MonoSDF（NeurIPS 2022）](https://github.com/autonomousvision/monosdf) / [论文](https://arxiv.org/abs/2206.00665)：有单目几何 cue 与 SDF 思路，代码 MIT；旧 GPU/依赖和数据转换工作量需审计。
- [NeuS2（ICCV 2023）](https://github.com/19reborn/NeuS2) / [论文](https://arxiv.org/abs/2212.05231)：哈希编码和 CUDA/CMake 构建，速度潜力高，但本机 6GiB + CUDA 故障下不可事先认定易部署。
- [SparseRecon（ICCV 2025）](https://github.com/hanl2010/SparseRecon) / [论文](https://arxiv.org/abs/2508.00366)：特征/深度一致性可参考；官方环境 PyTorch2.0.1+cu118 和 VisMVSNet/Omnidata 依赖，首轮不额外训练这些模型。

由 RA 按可最小适配、许可、显存和官方脚本可运行性选 1 个 SDF 基座；不能将三套重写混合后称为官方基线。S0（条件 P1）先固定相机、单视频、一个有限场景，损失建议：

\[
L = \lambda_{rgb}L_{robust\,rgb}+\lambda_{sil}L_{silhouette}+\lambda_{d}\sum_{i,u}w_{i,u}\rho(z_{SDF}-z_{HERO})+\lambda_{eik}L_{eikonal}.
\]

其中 `w` 来自冻结的相机质量、Raw/Cleaned来源、局部多视角一致性/掠视/遮挡的可复算代理，设置正下界或权重惩罚，不能让困难像素权重自动归零。`S1`（后续单独授权）才考虑跨帧可靠对应、Ring CAD 非穿插软约束、鲁棒光照与极小位姿微调；不得同时自由优化相机、几何与权重。最小消融：无 HERO、HERO 恒权、HERO 不确定权；所有子试验同预算，记录每步 GPU/总时间，停止条件统一。

## 5. Arm M：MapAnything 预训练推理

官方：[代码](https://github.com/facebookresearch/map-anything) / [论文](https://arxiv.org/abs/2509.13414)。截至 2026-10-30 官方 README 宣称接收 `img`, `intrinsics`/`ray_directions`, `depth_z`, `camera_poses`（OpenCV cam2world），输出 `pts3d`, `depth_z`, `camera_poses`, `conf`, `mask`。代码 Apache 2.0；权重 `facebook/map-anything` CC-BY-NC-4.0（学术）及 `facebook/map-anything-apache` Apache 2.0 是**不同版本/许可**；官方 CHANGELOG 记录 2026-01-18 v1.1 及 V1 权重另存。应固定具体 commit、checkpoint revision、SHA 和许可证，不混权重结果。

|Arm M 配置|输入|资格与目的|
|---|---|---|
|M0|同组 RGB-only|所有图像身份合格组；不对 M0 作 GT/ICP 规模修正|
|M1|RGB+有效 K|`K` 来源/resize 通过静态审计时|
|M2|RGB+K+冻结同视频 c2w|仅合格的条件相机；若首视角无 pose，须按官方约束判不可调用|
|M3|RGB+K+冻结 c2w+HERO Z-depth|仅合法深度/单位/对应 RGB&K 同步；`is_metric_scale` 按真实输入选择|

官方 `model.infer` 要求 depth 提供 K/rays，不能同时 K 与 rays；若某视角带 pose，首视角也必须带。处理器 `preprocess_inputs` 会 resize/归一化，必须将转换后的 K/Mask/深度与输出复算一致。采用 `memory_efficient_inference`/小批推理，但先做一帧或很小合法视角组烟测；**6 GiB 不保证容纳模型**。绝不在实验中训练 MapAnything 或使用未经认证跨视频 H。

## 6. 匹配输入 vs 最优合法配置

比较 A：在单视频、同组样本/相机/holdout/目标像素的**实际共同输入**子表里报告 S0 与 M1/M2/M3（只比较两个臂均合法的输入），与 `Raw`, `Historical Cleaned F1`, `Historical F2`, `AllAvailable Cleaned F1`, `F3 PreJoint`, `F3 Joint` 共同分母评估。

比较 B：各自最优**合法官方路径**独立汇报，包括 M0 纯 RGB、S0 优化收敛预算、最终采用视角、显存/时间/硬件依赖；不把使用不同 K/pose/depth 的结果混成一张单冠军榜。不保留 GT 优化途径。

## 7. 指标与终止

指标（每组/每帧分子分母完整）：真实独立目标 Polyp Mask 投影覆盖与轮廓 IoU / boundary F-score、共同有效像素 RGB MAE（照明限制显式）、原三角面投影覆盖/未知、叠层冲突、可见支持比例、固定 Ring CAD 穿插数/最大深度、3D 未确定区、运行时间/峰显存与失败数。绝对 3D 误差没有部署姿态认证时一律 `NOT_EVALUABLE`。

**停止类别**：`RUNTIME_BLOCKED`（CUDA、驱动、依赖、权重/许可/容量）、`DATA_INELIGIBLE`（源 SHA、K/pose/Z、泄漏、GT 边界）、`ALGORITHM_NOT_PROVEN`（通过工程运行但留出没有实质性收益或新增 CAD 穿插/支持损伤）。不得以运行失败宣布模型科学失败；不得用数值较小的不同像素 MAE 宣布胜出。详见 `EVALUATION_PROTOCOL.md` / `ACCEPTANCE.md`。

## 8. 分阶段授权门禁

- **P0（本次拟交 Codex 的首个 Task，仍待授权）**：本机静态资产+源码+官方接口审计、独立留出资格、GPU 只读检测、adapter 设计；不下载、训练、推理或跑新优化。
- **P1（以后单独批准）**：有限权重获取或复用、最小 MapAnything 推理和一次 SDF 单场景烟测；严守 GPU/运行时预算，失败分类。
- **P2（以后单独批准）**：G01 004 与 005 两臂单视频、小预算及冻结 baseline 对照。
- **P3（以后单独批准）**：G06、G08 和 G07 压力，完整四物理组表。
- **P4（以后）**：消融、独立 RA 验收、是否为 `BOTH_NOT_PROVEN`。
- **P5（有条件后续）**：仅跨视频相机/几何通过独立认证才讨论统一，不提前合并；P6 形态补全另立科学任务。

每一阶段必须留 3–4 张核心复合图，其他完整图库 `LOCAL_ONLY` + 索引。G01 固定三列：`SINGLE-VIDEO RECONSTRUCTION — video004` / `SINGLE-VIDEO RECONSTRUCTION — video005` / `CROSS-VIDEO CANDIDATE — NOT FUSED`；通过真正跨视频认证门禁之前不得改标签。
