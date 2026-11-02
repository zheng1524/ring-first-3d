# Codex Gate A 正式任务书草案｜官方NeuralFusion兼容与几何输入合同

**Task ID：`TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001`**  
**状态：`DRAFT_NOT_APPROVED`；研究者明确批准后才能人工交给EX。**  
预备分支：`exp/TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001`，从D0分支审查时HEAD `d69ade170352d1b5a1e46239f9516ab38c575648`切出；禁止改D0本身或把它变成成功冻结。任务只允许CPU、隔离环境、官方checkpoint静态/CPU载入、图像几何适配和玩具/真实输入**反投影**验证。不允许任何NeuralFusion `FusionPipeline.forward`真融合/官方测试集推理、GPU、训练、HERO重推或TSDF融合实验。

**已获研究者明确方法决策（2026-11-02）：各视角独立等比例裁剪。** 允许不同来源采用不同的`a_i`，但所有来源使用冻结相机与同一毫米世界/统一latent物理域；裁剪规则参数和质量门槛在看到任何融合输出前固定。该方法决策**不代表Gate A计算任务本身已经获准执行**。

## A. 单一主问题

**是否可以在不更改官方权重/主网络、不使用GT和不破坏公制几何的条件下，将G01_004原生HERO有效深度送入一个严格兼容的240×320 NeuralFusion输入与固定空latent坐标系？**

结果必须返回四类之一：`GATE_A_PASS`、`GATE_A_FAIL_GEOMETRY`、`GATE_A_FAIL_MODEL_COMPAT`、`GATE_A_NOT_EVALUABLE_ENV`。PASS仅授权PM提交Gate B审批，不代表预训练网络有效或任何Mesh可信。

## B. 输入白名单、复用矩阵与只读保护

| 模块 | 路径/来源 | 操作 |
|---|---|---|
| 官方模型 | `weders/NeuralFusion`固定main tree `4f0c14f67ad9d2368b68cbeb78c237a6328971e5`；`pipeline/pipeline.py`、`model.py`、`extractor.py`、`integrator.py`、`translator.py`、`utils.py` | 只读核对/隔离vendor镜像；不得改模型层数、重训、随机初始化权重冒充 |
| 官方权重 | `pretrained_models/shapenet_noise_005/version_0/{config.json,checkpoints/best.ckpt,hparams.yaml}`；`tanks_and_temples`同型文件 | 主ShapeNet严格CPU载入，Tanks仅备用静态结构对照；记录Git SHA和下载SHA256。若无合法可用权重/网络受限，停机而不造权重 |
| 现有数据 | D0 `HERO_TSDF_INPUT_MANIFEST.json`、`TSDF_CONFIG.json`、`code/hero_tsdf_adapter.py`、`code/common.py` | 6来源原生352×640深度、旧Mask/RGB、K/c2w、Ring CAD、源SHA。仅原始可用层，不以Raw Mesh伪造深度 |
| 验证与可视化 | D0 `code/diagnose_single.py`、`code/evaluate.py`、`code/figures.py`；批准的`visualization/real_p0_renderer.py` | 复用pixel/XYZ/CAD raycast、Face ID与真实深度可视化，不自行重写相机优化器 |
| 来源资格 | E3-A DAG/方向分区、E3-B native/Raw区别、E3-C条件证据、Camera Gate `TECHNICAL_REPORT.md` | 只读取证据；不把`INSUFFICIENT_EVIDENCE`升格为已认证 |

固定6源顺序（仅为几何输入审计）：`ref08,ref13,ref03,growth_r04,new_r00,growth_r14`。Gate A不得执行F0→F5前向。Git写入只限新分支与任务目录；旧数据路径、本地DXY、相机、HERO、D0/C/E3历史提交只读；禁`git add .`、`git clean`、force push及大权重上传。

## C. 按序执行的最小工作包

### A0 官方适配与环境清单（只读）

1. 记录官方Git commit、许可证、权重存在/完整性/约17MB与18MB大小，检验文件SHA256、CPU下checkpoint加载格式、两config/hparams、strict state_dict加载的missing/unexpected/mismatched shapes；仅主ShapeNet允许**模型构造和strict加载**，不调用forward。若需要Lightning训练类来初始化，必须检查是否偷偷创建GT数据库；禁止走该路径，改为单纯模块实例化和显式安全载入。不能`strict=False`。
2. 审计Python、Torch、CUDA driver、Lightning、NumPy、Open3D、第三方`graphics.voxelgrid`/RoutedFusion来源与API。**只检查并记录**可执行环境；如需新安装/网络/系统修改，先单独请求用户许可，绝不静默改主环境。
3. 生成`CHECKPOINT_COMPATIBILITY_MATRIX.csv`：模型结构/网络参数/n_features/n_samples/count/Renderer heads/128³或64³/依赖/weights hash/device/形状兼容/加载时间+RAM；Tanks如无法严格CPU加载只记NOT_TESTED，不切换主权重。

### A1 G01_004 六源Mask ROI映射

1. 锁定六份原生深度、RGB/Mask、K、c2w、Ring SHA与source family，确认native352×640和archived360×640的**实际中心约定**。非Polyp/Ring/背景/无值排除，保证`valid_polyp_depth`仅正、有限、Polyp标签1。
2. **六源各自独立**取`Polyp ∪ 真实可见Ring` bbox，初步20%或16px扩边，扩展为4:3内容区、等比缩放至320×240、letterbox pad。对每源分别输出完整仿射`A_i`与逆`A_i`、`u0_i/v0_i/a_i/px_i/py_i`、bbox、padding、`K'_i=A_iK_i`、深度/Mask同采样与原始来源索引。不得强制六源采用相同`a`，不得伪造深度、对无效0做双线性平均，不能使用最终Mesh调整ROI。
3. 导出每来源：原始Polyp可用深度数、裁剪前后合法样本对应/被丢失数量及比例、mask边界损失、Ring/CAD次序变化、可能细柄/小结构宽度代理（小于3像素记`THIN_STRUCTURE_UNRESOLVED_BY_CROP`），bbox碰图边和Mask缺失。关键误差必须标原source pixel/Face ID，而非只写比例。

### A2 统一物理模型域

1. 从有源原生深度、固定相机及CAD建立全6源统一公制bbox，列原生离群远端候选与主体尺度。**如果单个极端像素令共同网格无法合理覆盖主体，不得偷偷删该点：报告两类候选域与OUT_OF_GRID数量，停止等待研究者确定ROI策略。**
2. 对主ShapeNet设统一`O_mm`,`L_mm`，`N=128`，`X_model=(X_mm-O_mm)/L_mm`、`resolution_model=1/128`，故`voxel_mm=L_mm/128`。逐源深度、c2w平移、Ring CAD和bbox均同一个相似变换；`extrinsics`为c2w，不得当w2c。任何尺度/原点都要在看模型结果前固定，不许每帧不同。
3. 验证原图→裁剪→K逆→相机→世界→模型网格→世界的**解析**往返：每源至少1000个固定可追踪合法像素，含边界/细小结构/近Ring/深度跳变；统计median/p95/max（mm）。另独立给出实际nearest重采样导致的离散误差及像素身份变化，不混进解析往返PASS。Ring CAD外径约12.4mm应数值闭环，不能用于GT拟合。
4. 验证空`latent [N,N,N,17]`和`count [N,N,N]`，形状、轴顺序、有效观测域、合法射线格坐标；pad/无效深度不应写入有效计数。此步可用不调用FusionNet的几何核算和mock updates；**禁止调用真正网络forward或Translator生成融合面**。

### A2b 强制多视角几何不变性验证（优先级最高）

这是本次研究者要求新增的正式硬门禁，不得以A1单帧闭环代替。

1. 对固定CORE全部六个有向对`08→13,13→08,08→03,03→08,13→03,03→13`，用原来源有效HERO深度先获得世界点`X_w`，计算目标**未裁剪连续**投影`π_j(X_w)`；另计算目标**裁后连续**投影`π'_j(X_w)`，核对`π'_j(X_w)=A_j π_j(X_w)`。每一有向对保留固定有效射线完整分母及投影在/出图、Ring遮挡和Mask边缘的资格状态。
2. 三个新增条件性来源也做与CORE能合法投影的有向对，留存`INSUFFICIENT_EVIDENCE`/未单独Gate资格，**只检验变换不变性，不利用该检验认证原位姿正确**。
3. 在来源`i`自身核对`Unproject(D_i,K_i,c2w_i)`与使用`A_i,K'_i`的**解析裁后同点**世界坐标一致。每源≥1000固定有效像素及边界/细结构/Ring异常案例。分离：`analytic_xyz_error_mm`、`analytic_target_projection_error_px`、`nearest_resampling_quantization_mm`、`CROP_LOST`；不可只用“两个点云最近邻很好”替代同源身份闭环。
4. 不同`a_i`导致的有效采样密度单独输出`median/p95(Z/f'_{x,y})`、与ref08的比值、保留的有效Polyp深度对应覆盖、原/裁后Mask有效计数和最窄细结构宽度。这里的采样密度差是后续Gate B的**记录变量**，不是相机错误，也不能通过每视角不同3D缩放“纠正”。
5. 额外提供原始与裁后ref08/ref13/ref03点云的**同相机、同毫米范围、同黑色CAD**双面板图；展示原面/保留/丢失采样的三类身份，禁止自适应缩放观察相机让两者显得相同。

### A3 GT隔离、预注册与失败报告

1. 以静态依赖图和运行守卫证明新入口不import/call `training/database.py`的GT数据构造、`training/pipeline.py`的`_evaluate_database`、GT/Oracle/Dxy。无需构造任何假的GT文件。
2. 为Gate B准备**仅接口**的`inference_only`数据schema与reset清单：`input`、`original_mask`、`intrinsics`、`extrinsics`、`origin`、`resolution`、`volume`、`count`，及官方config需要的条件字段；验证类型、尺寸、设备和单位，不执行forward。写明Renderer在count=0或Unknown的处理必须在Gate B验证，不凭假设填面。
3. 测试：无效输入0和NaN、错误w2c、错误1000倍、Padding、Ring覆盖、Mask边界细柄、bbox外点、原生/归档1像素偏差、错误checkpoint/config混载均须触发错误或显式标状态；不能通过允许错误的silent fallback。

## D. 预先冻结的Gate A门槛

- 原输入SHA、六源身份、K/c2w/CAD未变；两套checkpoint配置与结构不得混载。主checkpoint必须strict CPU加载；若因环境无法评估，状态`NOT_EVALUABLE_ENV`，不伪造PASS。
- ROI内合法原Polyp深度不得被无声剔除；每一条裁剪损失计入固定原分母。ROI的细结构小于3输出有效像素时 **FAIL / REQUEST_REDESIGN**，而不是自动放宽。
- 每源≥1000可追踪采样，解析XYZ往返建议`max ≤1e-5mm`（在批准Task时冻结，不可结果后改）；另外报告实际nearest采样的离散误差，不要求其为0。Ring CAD公制尺寸与合法遮挡次序数值校验。
- **新增硬门槛**：CORE六有向对完整输出连续像素投影不变性；建议`max ≤1e-4 px`的`π'_j(X)-A_jπ_j(X)`解析残差（若使用FP64，执行前冻结）；条件性新增来源可评价对亦全部记录。所有`OUT_OF_CROP_FIELD/CROP_LOST_SUPPORT/CAD_OCCLUDED`明示，不以删分母提高准确性。
- **新增采样合同**：每来源允许不同的裁剪放大倍数，但必须汇报实际物理毫米/像素足迹、重采样量化误差及细结构保留。不同放大倍数不得改变其R/t或改变统一模型三维尺度。
- `valid_polyp_depth`中Ring/Background/Pad计数为0；未知区域不造远深度。空latents位于统一模型网格，六源的相机相对关系与物理Ring不变。
- 禁止GT访问、HERO再预测、CUDA融合调用、NeuralFusion模型forward、TSDF新融合、训练、面删除。所有专项检查必须有PASS/FAIL/N/A与原因，无法完成必须停止。

Gate A失败不自动许可Gate B；通过也只是`ENGINEERING_READY_FOR_B_REVIEW`，不是认可科学质量。

## E. 交付与可视化

- `TECHNICAL_REPORT.md`（200–350字摘要 + 事实/解释/决策/下一步）、`FAILURE_LEDGER.md`、`REPRODUCE.md`、`CODE_REUSE_MATRIX.md`；`SOURCE_AND_CROP_MANIFEST.json`、`CHECKPOINT_COMPATIBILITY_MATRIX.csv`、`METRIC_TRANSFORM.json`、`CROP_GEOMETRY_TESTS.csv`、`GT_ISOLATION_AUDIT.md`、测试输出及历史源SHA。
- 4张核心图，不提供虚构融合结果：`Fig1_RGB_Mask_Crop`（六源真实RGB/Mask/Ring + 320×240独立ROI与各自a）、`Fig2_Raw_vs_Cropped_CORE3_XYZ`（ref08/ref13/ref03原/裁后世界点云同毫米尺度同CAD并列，标丢失点）、`Fig3_CrossView_Invariance`（CORE六有向对的原→裁后目标投影叠合、解析误差及采样残差）和`Fig4_Metric_And_Failure`（模型体素/Ring、细柄/边界/远端异常及统一尺度案例）。同时在Fig2/3注明native/crop深度和K变化。无实际NeuralFusion Mesh/GLB，禁止把HERO Raw称NeuralFusion重建。
- 每张图带真实来源、单位mm、位姿资格、构建规则与negative case。只上传小PNG、metrics与必要源码，模型权重/全深度大数据LOCAL_ONLY+SHA。
- 完成时报告分支/commit、实际代码入口、所有门槛、手工未审核项、是否建议Gate B；EX停机等待PM与RA/用户。不得自动跑任何F0/F1/F2。

## F. RA与研究者须先批准的决策

1. 是否接受主权重ShapeNet noise0.005、Tanks仅静态备用？
2. 是否接受单一全6源物理ROI经Gate A无输出审计后冻结，遇异常远端点先停机而非裁掉？
3. 是否接受20%/16px起始ROI、细结构<3像素停机及解析XYZ `1e-5mm`建议门槛？
4. Gate A只有CPU strict load/几何，**不包含F0预训练前向**，是否批准这一明确界限？

**DRAFT_NOT_APPROVED。**
