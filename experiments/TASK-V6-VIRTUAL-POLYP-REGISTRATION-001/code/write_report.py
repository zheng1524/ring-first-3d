from common import *
r=read(T/'evidence/RESULTS.json');v6=read(T/'evidence/V6_REFERENCE_CONTEXT.json');diag=read(T/'evidence/POSTRUN_AUDIT.json')['diagnostics'];zero=next(x for x in r if x['condition']=='V0'and x['method']=='M0')
text='''# TASK-V6-VIRTUAL-POLYP-REGISTRATION-001 技术报告

## 首先回答四个问题

1. **已知双视频关系：V1通过，V2未通过。** 在一个既有G01虚拟息肉、原16 FIT/8 HOLDOUT、自动RGB地标条件下，M2恢复含30° yaw、3°倾斜、0.3 mm平移的关系，旋转误差0.134°、平移误差0.00112 mm。小幅逐帧相机误差下5/5种子未通过预注册0.5°/0.2 mm门槛；不宣称稳健注册已完成。
2. **RGB确实消除了该受控场景的Ring yaw歧义。** M1仍为30° yaw；M2残余yaw约0.132°。主实验调用原V6自动SIFT/互检/轨迹与DLT，不使用已知对应替代。解析单元测试只检验求解器实现，不当成科学结果。
3. **残差分层。** 原始无噪声深度栅格本身有离散/断边缺面；RGB定位/三角化带来很小V0漂移；V2逐帧相机误差使独立三角化位置变化，部分种子大量轨迹因几何检查被拒，单个视频级刚体不能消除内部不一致。部分种子软Ring约束也被带偏。此证据支持上述解释，尚未逐因果消融分离全部贡献。
4. **接口可调用，真实数据能力未验证。** 新V6 HIST两视频相机/轨迹/39张原生HERO与打包表均核对，两个实际Target例子完成完整传输契约测试；尚未在真实HIST视频执行自动跨视频注册。当前最值得验证的是相机误差下地标的不确定度与Ring硬几何约束，不能直接把V1成功推广到真实主体拟合。

## 身份、范围与复用

基础提交 `115e41fe5e57deff2898258d2ee836c83d686982`；独立分支 `exp/TASK-V6-VIRTUAL-POLYP-REGISTRATION-001`，工作树 `/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-VIRTUAL-REG-001`。运行前协议提交 `dc880b778a82dc5feb294df852054baa6fc1722f`。前半段唯一引用为 `TASK-V6-RAW-TO-HERO-MAINLINE-001/HIST`，不使用H004任务产物、不更改上游算法或HERO运行。

原 `g01_multisurface` 目录已迁到 `assets/retained_sources`。按迁移后的TASK.yaml，virtual_GT `1c857568eee39f39d2b18c15abe23e227827eb89215df067d1140ece5a6b0f4f`、Ring `30bd84488045adada6155fe00df2154ecde3a8e4531f02494fada77637c3b4af`、VIEW_SOURCES `e3bdf620…` 和父FREEZE `45c07b81…`逐项相符。真实文件已保护在inputs，不仅保留路径；原始共享资产只读。

[资产复用表](ASSET_REUSE.csv)列出真实入口；[固定协议](EXECUTION_PLAN.md)、[配置](config.json)、[身份记录](evidence/ASSET_IDENTITIES.json)可复核。沿用 `sim.scene.synthesize/ray_map` 的几何、遮挡和轴深度，仅替换为物体坐标确定性多尺度颜色纹理，背景常量。24张RGB和24份独立深度栅格网格各自SHA不同；没有复制稀疏点云充当双视频。纹理是理想化固定材质，无真实反光/光照变化，外观域差异仍是限制。

模拟相机来自用户指定原VIEW_SOURCES，原004/005轨迹与角色不改：FIT各8，HOLDOUT分别5/3。旧018身份只定义既有虚拟环境的生成视角，不作为本轮新V6测量、不冒称HIST输出。真实V6预测仅确定接口、视角跨度及误差参照；虚拟场景生成器定义真值。未引入第二套替代几何。

## 新V6 HIST接口与误差参照

|视频|HIST相机/轨迹/训练点|HERO面源|原模拟FIT轴向跨度|HIST轴向跨度|HIST Q0/Q1相机|原留出RGB逐帧MAE中位数/最大(px)|
|---|---|---|---|---|---|---|
'''
for v in v6:
 video=v['video'];n=1028 if video=='004'else 904;sources=18 if video=='004'else 21
 text+=f"|{video}|22 / {n} / 500|{sources}|{v['simulation_FIT']['axis_pair_max_deg']:.2f}°|{v['V6']['axis_pair_max_deg']:.2f}°|{v['Q0']} / {v['Q1']}|{v['held_RGB_per_frame_MAE_median_px']:.3f} / {v['held_RGB_per_frame_MAE_max_px']:.3f}|\n"
text+='''
详情含相机到Ring距离范围：[V6_REFERENCE_CONTEXT](evidence/V6_REFERENCE_CONTEXT.json)。误差均为上游预测条件诊断，不是GT；并未据这些数值调整本轮噪声或选帧。

- 原图640×360，K=(490,490,319.5,179.5)，OpenCV c2w毫米，单视频Ring参考yaw规范，不是双视频共同yaw。
- 原生HERO是352×640的 **depth_mm轴向Z**；K_index_native的fy=479.1111、cy=175.5，正确采用半像素缩放；模型内部米单位不能误当成保存数组单位。
- 打包面源恢复到360×640，保存pose/K/reference/source_frames，references和sources是ledger索引；本轮核对真实RAW帧身份和RGB/Mask SHA。
- 实际raw0示例：004 Support原索引[11,21,1]；005为[7,10,12]，具体RAW见[V6_TRANSPORT_TEST](evidence/V6_TRANSPORT_TEST.json)。所有相机左乘、原生深度反投影/重投影、可投影地标同步变换均实测；非正深度地标另计，不用于声称精度。
- 只保护必要小快照和内核原文；完整39面依赖路径/SHA在[V6_INTERFACE](evidence/V6_INTERFACE.json)。单视频track ID不是公共物理ID，真实跨视频仍须自动匹配、支持度/退化检查及独立评价。

## 固定方法、真值隔离与运行

M0不变；M1最小旋转对齐Ring中心/有向法向，保留yaw；M2先在M1上72格yaw训练地标中位距离初始化，再优化六参数rotvec(rad)+t(mm)，无scale。RGB residual/0.2mm，Ring中心与5.6×法向差 residual/0.1mm×sqrt(N)，SciPy soft_l1，最多100次函数评价。Ring是具有已定向法向的理想观测参数，本轮没有模拟Ring提取错误或法向翻转。M2是鲁棒损失，**不是RANSAC**；没有ICP、主体先验、形变、逐帧校正。

V6 `track005.main` 与 `v6_common.triangle` 原函数由AST原样调用；仅绑定本任务I/O、6000特征、ratio .72、所有FIT帧对。原一致轨迹≥3次观测、modulo5留出保持；两视频各≥2观测、各自DLT正深度、视差≥0.5°、最大重投影≤6px才进入三维配对。这个最大值筛选是本轮预登记适配，原V6 training函数用中位数筛选，未宣称完整原BA复现。414条RGB轨迹含83留出；V0/V1中108训练+25留出具备两视频有效三角化。其余轨迹保留在TRIANGULATION清单，不默默缩小83的分母。

V1只对005整个坐标系施加 `Rz(30°)@Ry(3°), t=(0.3,0,0)mm`；所有相机、Ring坐标、由RGB重建的地标和局部曲面随之变换。V2在同一D下加入 `C_est = D @ C_true @ N_frame`，仅005逐帧相机sigma=0.3°/0.1mm；RGB、理想轴深度、物理Ring不变。同一条件所有方法共用噪声、匹配及评价域。

噪声复用原noise_vectors算法，但本次对全部24帧生成，即005的8 FIT+3 HOLDOUT共同中心化；不同于旧运行只对FIT中心化的实例。这在生成器内发生，不让预测器读HOLDOUT图像/GT；但噪声统计相关，不称独立未见帧泛化。

预测进程拒绝读取private/virtual_GT，公开输入没有注入矩阵、真值相机、GT face/bary。每条件先写预测及FREEZE，再由独立进程评价；不依GT择yaw、选匹配、调参或选种子。GT轴与004原坐标共同固定，所有方法无额外最佳对齐。`export_prediction.py`在同一GT拒绝保护下同步实体化所有24张网格、全部相机和地标，每视频只有一个T。

原有坐标契约实测：纯换坐标投影最大1.14e-13px、Z最大1.42e-14mm；生成反投影最大0.000137mm，小于原0.001mm容差。V0/V1契约通过后才求解V2，未用V2失败修改预登记门槛。

## 逐条件结果（共同域，不删除失败）

只有 **1个物理组、2段模拟视频、5个噪声重复**。固定GT面积采样12000；FIT可见并集6655、交集4549，004/005互补1293/813。表面为固定GT点到实际三角网格的距离，覆盖阈值0.2mm；并集距离选两视频最近面，单视频和重叠另报，避免并集掩盖005错误。未见GT部分不作为已观测目标；六视角图仍显示完整GT与全部缺面。

|条件|方法|旋转°|平移mm|表面中位/P95 mm|覆盖%|重叠P95 mm|005留出MAE/P95 px|位姿门槛|
|---|---|---|---|---|---|---|---|---|
'''
for x in r:
 text+=f"|{x['condition']}|{x['method']}|{x['rotation_deg']:.3f}|{x['translation_mm']:.4f}|{x['surface_median_mm']:.4f} / {x['surface_p95_mm']:.4f}|{100*x['coverage_fraction']:.2f}|{x['overlap_p95_mm']:.4f}|{x['held_005_MAE_px']:.3f} / {x['held_005_p95_px']:.3f}|{'PASS'if x['pose_pass']else'FAIL'}|\n"
text+='''
M1求解状态始终YAW_UNIDENTIFIABLE，即使V0偶然已处正确yaw也不变成可辨识。V2所有M2数值求解收敛/ACCEPT不等于科学验收通过，五种子全部FAIL。

|条件(M2)|训练/有效留出轨迹（全部留出83）|自动留出重投影MAE/P95 px|005单视频P95 mm|相对无噪声增加mm|相对同条件M0变化mm|
|---|---|---|---|---|---|
'''
for x in r:
 if x['method']=='M2':text+=f"|{x['condition']}|{x['train_tracks']} / {x['held_tracks']}/83|{x['auto_held_MAE_px']:.3f} / {x['auto_held_p95_px']:.3f}|{x['single005_p95_mm']:.4f}|{x['added005_p95_vs_clean_mm']:+.4f}|{x['single005_p95_change_vs_M0_mm']:+.4f}|\n"
text+=f"\n无噪声单视频原有P95：004={zero['single004_p95_mm']:.4f}mm，005={zero['single005_p95_mm']:.4f}mm；共同并集P95={zero['surface_p95_mm']:.4f}mm，未达0.2mm覆盖的点={zero['surface_uncovered_at_02mm']}/6655。它们来自有限视角/栅格网格缺口，不是HERO网络误差。没有靠删点抬高覆盖。\n"
text+='''
自动留出表只给有效双视频三角化轨迹的条件误差，同时显示83总分母；例如seed19只有2条有效留出轨迹（6个重投影观测），不能把小样本误差当成全面可靠。所有83条的缺观测/几何拒绝理由与原414轨迹保留。留出视角表使用固定GT可见材料点的相机投影误差；005单独报告，不让004零误差稀释结果。全部逐视角分母、004/005指标、预测面反向距离、未覆盖数见[RESULTS.json](evidence/RESULTS.json)与[RESULTS.csv](evidence/RESULTS.csv)。

V0 M2共同表面P95只增加约0.00056mm，覆盖+0.03个百分点，满足预设≤0.02mm/不下降1个百分点。V1 M2自动留出MAE=0.316px（M1=19.484px），005留出视角MAE=0.1175px。V2种子17/18出现约0.60/0.73mm Ring中心残差，说明当前软约束可被有偏地标拉动；单看共同覆盖或表面P95甚至可能看似改善，不能据此验收注册。

## 精选可视化

- [同一六视角GT／配准前／配准后](evidence/SIX_VIEWS.png)：全三角面、统一相机/毫米尺度、中心平面5mm尺；缺面保留。
- [真实三角面截面](evidence/TRIANGLE_SECTIONS.png)：X=0、Y=0、Z=-2mm平面精确相交，不是点云近似。
- [RGB自动匹配及留出重投影](evidence/RGB_MATCH_REPROJECTION.png)：真实本轮合成RGB；训练连线与modulo5留出分开，未人工赋对应。
- [代表性失败](evidence/FAILURE_CONDITIONS.png)：V1 Ring-only yaw不解、V2首个失败种子；只选图示例，不用于算法选优。

近旋转对称主体使表面图对yaw错误不敏感；yaw成立的证据是冻结后位姿和RGB对应/留出，不以外观接近冒充关系正确。

## 验证、失败与冻结边界

6项新边界测试通过；11项原刚体/独立网格/断边/噪声/截面测试通过。最初完整SIM协议测试17项中13项因历史TASK路径迁移而报错，未改旧实验以隐藏；适用几何类已单独执行并通过。首轮AST包装缺__file__，在匹配前失败，绑定源路径后重启，原内核未修改。运行前带离群点单元测试发现归一化扩大鲁棒截断尺度，在正式生成前修正；协议说明保留。详见[失败记录](evidence/FAILURES.json)。

预测FREEZE保存了实际脚本SHA、公共生成清单SHA、轨迹SHA和预测SHA。独立审查要求补完整核验：最终评价实测校验公共/私有生成文件、预测哈希、预测器三个核心源码、GT资产身份，以及ADAPTER帧表等于冻结FIT表。原V6外部内核与复用模块的完整保留清单是**事后审计绑定**，不追称预测开始前已经全部冻结；[POSTRUN_AUDIT](evidence/POSTRUN_AUDIT.json)清楚标注。预测冻结后的核心源码、观测与预测未漂移；生成阶段FREEZE中的registration/v6_adapter后来有GT守卫/AST包装修正，按实际阶段SHA保留；两内核保护副本与原文件SHA一致，9个复用源文件与基础提交一致。

独立审查确认原匹配/三角化调用、独立深度网格、无GT进入solve与公共分母，并指出005混合均值及冻结链缺项；已补005合并MAE/P95和全部留出分母、补输入校验，不改变冻结预测。科学负结果保留。

## 可复现入口与保留依赖

见[reproduce.sh](reproduce.sh)。运行环境复用既有Python3.12、NumPy/SciPy/OpenCV/Open3D/Matplotlib/Trimesh；本轮无安装、无训练、无RAW→HERO全链重跑。完整本地运行路径 `runs/RUN_001`；`code/export_prediction.py`产物在 `runs/RUN_001/exports/<条件>/<方法>`，共21套，每套24张真实独立源网格刚体变换结果及相机/地标。拒绝输出会明确记录，不能被替换成M1后宣称M2成功。

小输入、39面源索引、外核原文、选择性证据随Git保护；可复查观测/轨迹/冻结预测在 `evidence/RUN_EVIDENCE.tar.gz`（包含真值子目录仅供评价，不是预测输入）。大量可再生21套导出网格留本地，代表性V1/M2另保留；禁止清理其保留路径。源码、配置、输入、外部运行时的准确清单见 `evidence/RETAIN_DEPENDENCIES.json`。未上传全视频、权重、虚拟环境或旧整套实验。

## 下一轮最小问题

先固定本轮RGB匹配、五种子与共同评价域，单独验证“带逐帧相机不确定度的RGB注册，配合保持Ring中心/法向的约束”能否降低005留出误差且不制造Ring漂移；仍只估计每视频一个T，不用逐帧自由度或主体形变吸收残差。应另行预登记再运行。本轮不启动该新研究，也不把本轮理想Ring/深度结果升级为真实HIST配准或共同主体拟合成功。
'''
(T/'TECHNICAL_REPORT.md').write_text(text)
