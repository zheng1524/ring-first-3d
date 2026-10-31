# TASK-NEURAL-E1-PIPELINE-RECOVERY-001

**Role**：新初始化 Codex；Ring-First Phase E 科研执行智能体（单实例）。  
**任务版本**：E1-C0C1-v2 / 已根据 `RA_DECISION_E1_001` D1–D3 修订。  
**状态**：`RA_APPROVE_WITH_CHANGES / RESEARCHER_TRANSFER_REQUIRED`。只有研究者明确批准并将本文件交给你，才可以开始执行。  
**授权范围**：仅 **C0+C1（C0 数据流资格恢复 + C1 无训练几何/接口合同验证）**，C2–C4均`NOT_AUTHORIZED`。**严禁GPU模型前向、SDF训练、MapAnything新推理、大权重下载、新HERO推理、清理旧数据、执行C2/C3/C4**。

## 0. 不可改变的科学任务

最终研究问题：在已知物理Ring、冻结Ring-First相机及多个互相可能冲突的HERO深度/真实RGB/Mask下，能否联合优化能够解释多视角观测的统一**可见**三维表面。两个**独立**竞争臂保留：
- Arm S：MonoSDF优先，未来同视频至少3份真实不同参考共同优化一个有支持的SDF；
- Arm M：独立MapAnything，包括原生M0–M3和利用合法派生条件接入历史HERO、Raw/Cleaned、F1/F2/F3等多源局部几何；**不是SDF初始化器**。

本任务**只证明数据来源可追溯、坐标/射线/官方输入接口正确，绝不以新模型生成三维结果结束任务**。历史E0 `TECHNICAL_REPORT`及所有失败记录只读，不能删改。输入范围由真实来源关系决定，不机械只选两图，也不把36份派生参考称为36个独立病例。

## 1. Git、输入和冻结边界

1. 在新独立 worktree / 分支 `exp/TASK-NEURAL-E1-PIPELINE-RECOVERY-001` 工作；初始记录`git status`、base SHA、E0/F3/View-Partition各准确SHA和相关文件哈希。读取仓库`AGENTS.md`、现行协同规范、E0 `TECHNICAL_REPORT.md`、`REPRODUCE.md`、`FAILURE_LEDGER.md`、E0 `code/audit.py`、`sdf_run.py`、`map_run.py`、`config/sdf_minimal.json`、`map_minimal.json`、`CODE_REUSE_EXECUTED.json`及F3、MASt3R分区报告。
2. 首先校验本机是否存在旧工作树/真实文件；不存在写`MISSING`、`LOCAL_ONLY`、`UNRESOLVED`，不得从报告凭空复制数据、重造相机或伪造HERO。
3. **相机强冻结**：全部已归档`K_i`和Ring-First `c2w_i`只读、值及哈希不变；神经/Map预测pose不能覆盖；两视频`004/005`坐标未认证，不得合并。Ring CAD实际物理尺寸与坐标固定；photo001/002/003未认证K/pose不进入公制模型数据。
4. DXY-MID V9.1、原始P0/深度、Ring-First/HERO权重、旧GT/Blender、历史任务报告/预测全只读；禁GT/Oracle、尺度拟合、ICP、位姿优化、重训练/模型forward、重新下载Map权重、旧目录清理。禁`git add .`、`git clean`、`reset --hard`、`push --force`。
5. 所有修改仅新任务目录下的CPU适配器、几何测试、配置、清单、PNG和报告；原视频、大型NPZ/GLB、权重和原始全量图像不得上传GitHub。分批显式`git add`、记录commit SHA/推送结果。

## 2. C0：恢复整个项目的来源数据流（无模型运行）

### C0.1 资产与依赖DAG

在真实本地文件基础上核实E0报告的预期池：9旧P0+5分区新增+22生长新增=36份参考；G01_004 11、G01_005 9、G06_004 5、G07_004 5、G08_005 6；47种HERO原始输入帧身份、154条依赖边作为**待复核预期数**，非自动通过数。

复用E0 `audit.py` 与 `provenance/{INPUT_ELIGIBILITY.json,HERO_DEPENDENCY_EDGES.csv,SOURCE_SHA_LEDGER.csv,SOURCE_LEAKAGE_LEDGER.csv,FRAME_CONVENTION_TESTS.json}`，形成 `metrics/E1_SOURCE_MANIFEST.csv` 与 `provenance/E1_SOURCE_DAG.json`。每条含：物理组/视频/来源ID、RGB/Mask/Depth/native及SHA、HERO source帧SHA、Raw XYZ/source UV/mesh、Cleaned版本、F1/F2/F3来源和父系、K/pose文件SHA/质量标签、Ring CAD、MASt3R边、场景坐标标签、训练/过渡/评价资格。

**衍生点云不能产生额外独立观测数**：多份F3补片可来自同一HERO或同一源RGB，必须画父子DAG。native不可读则标MISSING，不以display pack冒充native。

### C0.2 G01两视频多参考资格和共视

- **分别**检查G01 video004及video005，列出每段至少3份预期真实不同参考候选；比较来源相机观察方向、前景共视、Mask覆盖、重复帧/共享HERO源、重投影深度冲突、Ring附近遮挡和几何条件。尽量用互补观察方向，不以源数量机械判断独立性。
- 保留每组 `CORE/TRANSITION/HOLDOUT_RECON_ONLY/DIAGNOSTIC_ONLY/UNQUALIFIED` 及其证据；本轮只**提出**下一任务输入组合，绝不运行神经模型。
- G06 NORMAL、G08 LIMITED、G07 UNQUALIFIED_STRESS分别列出，多组资产必须真实检查。photo001/002/003登记真实图像、MASt3R匹配、K/pose候选与未认证限制，不能变成假公制相机。
- 检查旧G06 raw00351、G07 raw00293已知HERO输入依赖污染；E0严格全流程holdout=0，不得声称本次凭事后重新分组就获得严格盲测。

### C0.3 既有代码复用审计

交付 `CODE_REUSE_E1.csv`：真实文件路径、准确SHA、函数签名、是否可执行、何处最小适配。优先复用：

| 链路 | 既有入口/源 | 本轮新写上限 |
|---|---|---|
| 相机/来源 | E0 `audit.py`；F3 `common.py:source,target_source` | 标签/文件格式桥接 |
| HERO/XYZ/mesh | `ring_first_v1/scripts/common.py:unproject,depth_mesh`、原推理package/缓存 | 无深度模型或反投影重写 |
| Raw/Cleaned/F1/F2/F3 | Phase C + F3 point provenance & surfaces | 来源索引、源视图投影适配器 |
| MASt3R | View Partition `matching.py`, `registration.py` | 只读邻接/资格聚合 |
| CAD/A→B/render | `cad_audit.py`、真实重投影、`visualization/real_p0_renderer.py`、`SameCameraScene` | 可视化布局 |
| MonoSDF/Map | 官方固定revision，E0 `sdf_run.py`, `map_run.py` | **仅CPU域/接口测试**；无训练或forward |

## 3. C1：无训练硬门禁

### C1.1 OpenCV/公制/遮挡单元测试

对每个G01单视频选真实来源，辅以人工合成控制例，验证`c2w↔w2c`、旋转正交/行列式、轴向`z_depth`与欧氏`ray_length`非等价、mm↔m、K resize半像素主点规则、`XYZ→UV→XYZ`、深度与源UV/Mask对齐。输出原值、误差、分母和预设容差；保留冻结CAD Ring（R10中心线半径5.6mm/截面半径0.6mm，其他组用其实际R5/R10 CAD）的Z-buffer遮挡检查。CAD是独立刚体，不与Polyp标签混合。

**相机不变量断言**：本任务所有派生相机K/T字节或数值与源保持一致，不得在任何CPU adapter里暗中使用Map输出pose或拟合新pose。

### C1.2 MonoSDF真实射线/几何域（D1，最关键）

**不得只判断“相机中心是否在吸收球内”。** 必须读取MonoSDF固定revision真实`ErrorBoundSampler`、`LaplaceDensity`、`MonoSDFNetwork`等实现及当前E0包装，建立**不做网络训练/前向**的CPU几何单测：

1. 对真实source前景、邻近背景、Ring遮挡及不同图像角落采样像素，按冻结K/c2w生成世界射线，验证源轴向Z对应的正确ray参数，列出深度像素与真实点相交误差。
2. 确认scene origin/scale、Polyp与近端Background可信ROI、采样near/far、bounding/absorbing规则、几何表面可能的zero-crossing区间。对每类ray写`entry_t,exit_t,foreground_target_t,near,far,valid_sampling_fraction`及物理mm图。背景ray不必穿过息肉ROI，但必须能提供真实的自由空间/轮廓判别；不应全部因边界误设饱和。
3. 使用可解析的人工SDF几何（例如已知球/平面）验证SDF符号、表面0-crossing、沿有效ray的吸收/透明状态与基本数值变化；如需官方组件不可脱离GPU运行，只用CPU等价几何/静态源码行为测试，并明确`BLOCKED_STATIC_ANALYSIS_ONLY`，**不可伪造神经模型前向结果**。
4. **回归负例**：E0旧配置的10mm/unit、radius2.5、camera norm3.2714/3.8705，结合官方真实采样/吸收规则说明导致失效的具体机制，旧配置应`EXPECTED_FAIL`；若旧配置在某项子测试通过，必须解释而不是为得到FAIL修改断言。
5. 至多设计/静态测试**两个具有物理理由**的scene/domain修复方案（例如改变场景中心/规范尺度并保持公制相机一致性，或合理采样ROI/near-far），不是简单盲目放大sphere；记录ray正确进入表面支持域、可见/背景合法采样、零交叉和尺度闭环的量化结果。

输出`metrics/SDF_RAY_DOMAIN_TESTS.csv`、`config/SDF_DOMAIN_CANDIDATES.json`和旧失败/新候选可对照图。无有效方案则`ADAPTER_INVALID / STOP_SDF_BRANCH`并提交原因；**不得启动400步或任何GPU训练**。

### C1.3 MapAnything全量局部几何适配合同（D3）

1. **官方接口核验**：从锁定MapAnything官方代码/实际预处理查看`infer`可合法消费字段及组合，候选含`img`、`intrinsics`/`ray_directions`、`depth_z`、`camera_poses`、`is_metric_scale`；检查结构、维度、单位m、valid/NaN/0、resize K、深度对应相机Z、返回`pts3d/depth_z/camera_poses/K/conf/mask`契约。只读源码或E0冻结输出，**本轮不得任何新官方模型forward**。不支持的原生输入必须标`UNSUPPORTED_NATIVE_INPUT`，不可声称官方原生吃PLY/GLB/任意confidence。
2. **新增的强制测试——来源几何转合法深度条件**：选G01_004/005的真实Raw与Cleaned，至少各选一种来源明确的F1、F2、F3局部点/开放面；必要时为G06/G08/G07做单源压力检查。用**既有投影/Z-buffer/CAD**的CPU工具把真实XYZ/开放面转回其可认证来源相机视图，输出`axial_Z_mm`、转m后的`depth_z`、`validity`、`source_pixel/triangle_id`、`surface_origin`、`ring_occluded`与`conflict/unknown`，保留原始来源索引。
3. **不能乱补面**：稀疏点不能凭邻近像素填洞；只有真实已有三角面可以光栅化。无效值的NaN/0/valid mask处理必须证实官方接口真正消费的规则；若官方预处理没有对应valid channel且不能合法表达缺失深度，就标`ADAPTER_INVALID`或`UNSUPPORTED_NATIVE_INPUT`，**不可将无效像素当零深度真值**。
4. **跨来源冲突与信息相关性**：同一个target/source view由多个不同历史重建投影时，保留各自z-buffer层、支持点数、原始父系；标识同源重复、不同参考几何冲突、被Ring遮挡、真正未知。不能把F1/F2/F3在同一个RGB视图的三个先验深度算作三个独立相机观察；官方若不支持同图多深度条件，可定义**互斥配置消融候选**，不强塞接口。
5. **坐标绝对冻结**：所有适配输入K与c2w等于冻结Ring-First，几何来自同视频同局部系；禁止用Map输出pose当输入真实相机、绕CAD优化或ICP/scale fit。若要读E0 M3旧输出以示失败，展示原始pose与条件pose残差、Ring源像素距CAD约22mm及有效样本分母，不重新推理。
6. **新增对照资格矩阵**：`M-native`保留M0–M3；`M-geometry-conditioned`提出Raw/ Cleaned / F1 / F2 / F3 / 多HERO不同参考的正式合法配置；**M4/M5名称仅在接口被证实且后续预注册冻结之后才生效**。逐项标 `LEGAL_NATIVE / LEGAL_DERIVED_DEPTH / UNSUPPORTED_NATIVE_INPUT / NOT_VERIFIED / BLOCKED`，指出哪些历史三维信息是先验且来自同一个输入。

输出`metrics/MAP_GEOMETRY_ADAPTER_CONTRACT.csv`、`MAP_LEGAL_INPUT_MATRIX.csv`、`MAP_PRIOR_DEPENDENCY.csv`、`provenance/MAP_SOURCE_VIEW_DEPTH_EXAMPLES.json`和真实点云→深度/遮挡图。**本轮的PASS是适配转换与接口证据成立，不是Map模型科学有效。**

### C1.4 支持域/可见性规范

冻结未来标注层：`MULTI_VIEW_OBSERVED_SUPPORTED / SINGLE_VIEW_OBSERVED_SUPPORTED / CONFLICT / RING_OCCLUDED / PRIOR_ONLY / UNKNOWN`。现有可追溯来源点不因F3已接受就获得GT身份；Ring遮挡后未知与先验补全不得算观测面积。无模型预测时只允许画已有源XYZ和E0失败缓存的**已知支持证据**；不得声称训练模型生成新的supported mesh。

## 4. 必须交付及四幅可视化

输出目录：`experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/`。必须包含`TASK.md`、`TECHNICAL_REPORT.md`（一份中文摘要+完整分母/代码/错误）、`REPRODUCE.md`、`RESULT_INDEX.md`、`FAILURE_LEDGER.md`、`CODE_REUSE_E1.csv`、`metrics/*.csv`、`provenance/INPUTS_AND_SHAS.json`、源码/配置和本地`visualizations/index.html`。每项失败有原因与可重放测试，不许只留截图。

核心PNG（真实来源XYZ、mm轴和黑色实体Ring；默认复用`visualization/real_p0_renderer.py`）：

1. **Scene & Source DAG**：G01 004/005分开展示、photo001/002/003及G06/G08/G07分层，相机观察、HERO来源、F1/F2/F3父系/泄漏标识。
2. **MonoSDF domain gate**：E0旧配置负例与至多两种候选，真实相机射线穿ROI、foreground/background、采样/absorbing边界、Ray/Z几何数值。
3. **HERO geometry & conflicts**：至少3参考深度对应、Raw/Cleaned差异、局部深度冲突/遮挡/UNKNOWN及支持域；不以视觉漂亮表示科学成功。
4. **Map legal geometry adapter**：Raw/Cleaned/F1/F2/F3真实XYZ/来源开放面→source view的axial-Z/valid/source-index图、Ring遮挡/冲突；并列E0旧M3的CAD偏移和输出pose残差（标明旧失败、非新运行）。

每幅图在图内标 `CPU CONTRACT TEST / NOT NEW MODEL OUTPUT`；本轮无需新A→B神经预测/新GLB。必须提供本地完整文件夹与HTML绝对路径，3–4个核心PNG Git增量上传。输出state：`C0_PASS/C0_LIMITED/C0_BLOCKED`和各C1子门禁状态；不能只总结“整体成功”。

## 5. 明确停止规则与交付门禁

- 若真实源SHA、位姿或native深度缺失：该源`DATA_INELIGIBLE`并继续核查其余源；不能自行补造。
- SDF旧E0配置需通过**负例检测能力**（即预期FAIL）；候选无有效ray ROI或零交叉则`ADAPTER_INVALID`，停止该分支，仅提交证据。
- Map source-to-depth投影没有正确遮挡/源索引、无法合法表示无效深度或没有证据官方消费该条件：该配置`ADAPTER_INVALID/UNSUPPORTED_NATIVE_INPUT`，**不要为了让Map可跑而修改官方网络**。其他合法配置仍可单独通过。
- 审计不等于训练。任何GPU/权重下载/训练、Map forward、额外Camera/ICP、GT、旧目录清理请求必须停止并提交人工授权需求。
- 四组报告独立统计：`AUDITED_N`、`ELIGIBLE_N`、`ADAPTER_TESTED_N`、`MODEL_RUN_N=0`、`SCIENTIFIC_SUCCESS_N=0/NOT_EVALUATED`；严格holdout仍0则明说。
- 结束后只申请研究者与RA审批**后续C2 Task**；禁止自动进入C2/C3/C4。

**最终交付问答**：E0错误如何在零训练被拦截？G01 004/005的多参考闭环是否成立？MonoSDF ROI/ray/CAD合同是否可执行？Map是否能合法消费F1/F2/F3派生深度，哪种信息只是相关先验？冻结相机是否全程不变？有哪些确定不能进入下一轮的输入？
