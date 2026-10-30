# E0｜Uncertainty-Aware Neural SDF vs MapAnything 预注册竞争协议

版本：v0.1，`PROPOSED`；由 RA 与研究者审阅后冻结。

## 一、研究问题与独立假设

**H-SDF**：逐场景的统一SDF能够综合不一致的HERO深度与真实图像，在**相机不变、相同可用观测**时，相较历史点云生长改善留出视角轮廓解释、几何冲突与CAD穿插，而不会通过仅平滑/补背面伪造完整性。

**H-MAP**：MapAnything 的预训练空间先验与异构几何输入能在无需本项目训练的情况下得到更一致的公制空间；其几何辅助输入相较纯RGB应有可验证收益。

**竞争原则**：两者属于不同范式（逐场景优化 vs 预训练推理），**不要求完全相同算时**，但必须公开预算和使用条件；比较分为“同等可用输入”与“各自最优官方配置”两层，不混成一个虚假冠军榜。

## 二、数据冻结

- G01：先做video004与video005独立重建；跨视频候选只能作为诊断，未通过 Ring/背景/留出帧约束不能强制联合。photo001–003无认证K/位姿，初期仅作为外观或候选对应诊断。
- G06：IIa/R10正常条件、跨形态检验。
- G08：IIa/R10有限条件，作为敏感性测试。
- G07：Is/R5相机不合格压力测试，**不计入科学成功率**。如仓库有更合格Is/R5组，可额外加入，但不能悄悄替换失败组。
- 按**独立物理模型**计分；G01两视频是一组，不是两个病例。
- 从现有原始参考、真实相机合格列表和冻结深度中选有限训练视角；不同参考里若共享同一HERO输入，说明并非独立深度样本。
- 先将留出帧和其来源追溯冻结并记录 SHA，不允许后验根据输出质量改换。包含横跨不同观察方向的留出（条件允许），至少记录真实Mask/可见区域。
- 不使用GT/Oracle进行初始化、训练、位姿或超参选择；源CAD/Blender与真实部署姿态未知，严格绝对3D误差不具备时填NOT_EVALUABLE。

## 三、输入与相机/单位契约

统一索引记录：`group_id, physical_scene_id, video_id, source_frame_id, image_sha, mask_sha, K, distortion, c2w, camera_quality, hero_depth_sha, depth_type, xyz_units, confidence, training_flag, holdout_flag`。

- 所有几何内部统一 **mm**；外部实现要求 **m** 时显式 `mm→m`，包括相机平移与Z-depth；输出转换回mm后审计 Ring CAD 几何。
- `depth_z`是光轴方向Z-depth，不是射线长度；对于重采样必须同时正确更新K和Mask。
- MapAnything官方输出 `pts3d`、`depth_z`、`camera_poses`、`conf` 等；官方输入支持图像、内参、Z-depth、cam2world相机及is_metric_scale。必须验证真实版本，不可凭猜测调用接口。
- Neural SDF先冻结现有可信相机；绝不可将“自由位姿+自由几何+任意置信度”一起放开以获得低训练损失。
- Ring CAD固定，Polyp与Background分别处理Mask和支持域；不得把Ring当作神经表面要重新生成的训练目标，也不得直接以Ring平面作正常组织基底。

## 四、Arm S——统一不确定性 Neural SDF

1. 查已有成熟代码：NeuS2、MonoSDF、SparseRecon、LightNeuS。优先选择**能运行且可最小扩展**的单场景SDF，不要求重新实现体渲染和哈希编码。
2. **S0最小版**：冻结相机；使用Polyp Mask、可见性、冻结HERO深度的受限稳健损失和SDF正则；不加新训练数据、不做GT对齐。
3. **S1增量版**：在S0可复现基础上加入明确的深度置信度和可靠跨帧特征对应；必要时加入Ring-CAD非穿插软约束和内镜光照鲁棒损失。
4. 配置必须使每个新增损失可单独开启/关闭，做最小消融：没有HERO、HERO无置信度、HERO+置信度（在算力允许下）。
5. 不确定性权重不可无限下降使困难区域完全不参与；用固定清理/掠视/多视图支持代理和合理下界或正则。
6. SDF输出区分：有观测支持的开放可见零水平集、仅先验/正则推断的模型表面、未确定区域。不得将完整水密零水平集统称真实可见表面。
7. 不做一般息肉形态生成补全；形态先验属于未来E3独立任务。

## 五、Arm M——MapAnything

使用官方 `facebookresearch/map-anything` 代码和明确的正式权重，不自行训练。记录代码SHA、模型版本、许可证与显存要求。

至少完成适用的输入组：
- M0：RGB-only（与场景几何基础模型固有先验竞争）。
- M1：RGB + 官方支持的K（已认证的K时）。
- M2：RGB + K + 经核实的冻结相机（合法时）。
- M3：RGB + K + HERO Z-depth + frozen pose（官方接口允许、K/单位/相机资格一致时）。

不满足输入前提的组合标NOT_EVALUABLE，不允许默默补造相机/深度。`is_metric_scale`只在输入确实为公制且单位匹配时使用；MapAnything公制输出仍需Ring实体独立验证。MapAnything输出的局部曲面/低置信度也需要观测支持标记，不因其模型置信度高就认证物理准确性。

## 六、基线、指标与失败机制

对照：冻结HERO单参考、Cleaned F1 全来源、历史F2、最新F3 边界生长。统一验证帧与物理尺度，比较：

- 留出图像：Polyp Mask 轮廓IoU/Boundary F-score、共同支持的重投影误差，预测/真实RGB误差需报告有效支持分母和相机/光照限制。
- 几何：Ring CAD穿插计数/最大深度、局部重叠层分布、连续性、可见方向覆盖、投影原面覆盖和未知支持。
- 准确度：有**独立真实部署姿态GT**的组才测绝对距离/深度误差；若没有就NOT_EVALUABLE，不执行GT ICP后称重建正确。
- 研究质量：新增表面来源、观测支持、推断区比例，不能用“完整水密Mesh”、“更平滑”、“三角面数”单独决定胜负。
- 工程：GPU时长、峰值显存、模型下载/权限问题、复现成功率、推理/优化成本、手动修正次数。

必须先列成功门槛与失败证据，不以平均RGB最低直接判获胜。若两臂都未改善留出可见性或Ring穿插，结论为`BOTH_NOT_PROVEN`，不能硬选胜者。若仅同视频有效，允许`SINGLE_VIDEO_ONLY`，跨视频不认证。

## 七、流程与决策

P0：仓库/官方方法复用审计 + 数据资格、预冻结留出；
P1：硬件/模型权重/最小样本smoke test，CUDA故障与算法失败分开；
P2：G01-004、G01-005 两臂基线，视角/样本一致；
P3：G06、G08与G07压力，至少四组记录；
P4：两臂公平对照、失败消融、独立RA审阅；
P5（**条件后续**）：只有一臂证明跨同视频有收益且跨视频相机通过认证时，才开展跨视频联合优化；
P6（**后续独立**）：形态先验或不可见补全，不混入E0成功率。

每阶段核心3—4图：真实图/Mask、深度/不确定性输入、固定尺度6-view真实XYZ、留出视角A→B、Mask/遮挡/未知、CAD穿插与每组状态。G01始终显示004/005独立场景及未认证跨视频状态，不能用漂亮的共同渲染冒充FUSED。

## 八、最少明确交付

`research/phase_e_neural/PM_STATUS.md`
`research/phase_e_neural/E0_COMPETITION_PROTOCOL.md`
`research/phase_e_neural/RA_REVIEW_REQUEST_E0_001.md`
`experiments/TASK-NEURAL-E0-COMPARE-001/TASK.md`
`experiments/TASK-NEURAL-E0-COMPARE-001/TECHNICAL_REPORT.md`（**仅执行获批准任务后**）
`experiments/TASK-NEURAL-E0-COMPARE-001/metrics/` 与 `figures/`、`REPRODUCE.md`、`RESULT_INDEX.md`、`provenance/`。

所有状态使用`PROPOSED/APPROVED_TASK/RUNNING/REPORTED/ACCEPTED/REJECTED/NOT_EVALUABLE`，报出物理组分母、视频分母和样本依赖。不得因为失败回填历史值，实验分支隔离，不修改原P0、Ring-First、HERO、Dxy。
