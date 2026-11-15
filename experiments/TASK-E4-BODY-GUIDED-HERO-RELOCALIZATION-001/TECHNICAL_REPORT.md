# Body-Guided HERO重定位：技术报告摘要

已完成四组真实实验与受控验证。**二维区域候选可以突破旧三维近邻门控，但尚不能把Body自洽当作可靠真实重定位。** 本轮没有更新Body、没有融合、没有新模型训练；所有原始曲面和相机只读。

## 输入与实际方法

G03→G05→G01→G06全部运行。Body-E是从固定参考视频三幅二维Mask/通用核心椭圆新拟合的九参数椭球，未读HERO XYZ或旧训练Body参数；Body-U为正式R3 B3 FINAL。算法以二维归一化区域建立Body首层候选，联合区域误差、实际Ring和真实背景SIFT优化来源级六自由度派生位姿。同一个刚体作用HERO与来源相机，完整局部形态/原像素关系保持。**这不是019–021的视频共享T，不是正式新轨迹；不能证明源间相对相机变形是正确修复。** A1实际复现旧受限射线修正，四组theta与历史FINAL最大差均0。

区域描述子新采用同一Mask核心AMS椭圆，不声称DXY最终算法；外围细长区域不作为椭球头部强对应，但完整网格保留。原设计/实际逐项对照与源码位置见METHOD_AND_INPUT_AUDIT.md。实际PyTorch3D Body优化未运行，因本任务明确冻结Body。

## 固定分母独立评价

| group | arm | numerical | conditionally_supported | heldout_fixed_N | heldout_known | heldout_MAE_mm | heldout_P95_mm | heldout_support | heldout_fixed_penalty_mm |
|---|---|---|---|---|---|---|---|---|---|
| G03 | A0 | 18 | baseline; not new pose | 55296 | 0.903 | 2.842 | 13.561 | 0.229 | 3.136 |
| G03 | A1 | 18 | baseline; not new pose | 55296 | 0.903 | 2.842 | 13.561 | 0.229 | 3.136 |
| G03 | A2-E | 18 | 0 | 55296 | 0.889 | 2.631 | 11.516 | 0.195 | 3.150 |
| G03 | A2-U | 18 | 0 | 55296 | 0.886 | 2.471 | 11.102 | 0.223 | 3.061 |
| G05 | A0 | 16 | baseline; not new pose | 49152 | 0.935 | 0.593 | 1.963 | 0.574 | 1.206 |
| G05 | A1 | 16 | baseline; not new pose | 49152 | 0.939 | 0.434 | 1.524 | 0.707 | 1.018 |
| G05 | A2-E | 16 | 0 | 49152 | 0.936 | 0.676 | 1.942 | 0.500 | 1.272 |
| G05 | A2-U | 16 | 7 | 49152 | 0.915 | 0.679 | 2.113 | 0.525 | 1.470 |
| G01 | A0 | 26 | baseline; not new pose | 133120 | 0.854 | 1.293 | 3.437 | 0.248 | 2.563 |
| G01 | A1 | 26 | baseline; not new pose | 133120 | 0.864 | 1.142 | 3.067 | 0.312 | 2.349 |
| G01 | A2-E | 26 | 10 | 133120 | 0.841 | 1.256 | 3.257 | 0.243 | 2.646 |
| G01 | A2-U | 26 | 0 | 133120 | 0.832 | 1.280 | 3.295 | 0.231 | 2.740 |
| G06 | A0 | 15 | baseline; not new pose | 46080 | 0.949 | 0.299 | 0.837 | 0.759 | 0.794 |
| G06 | A1 | 15 | baseline; not new pose | 46080 | 0.949 | 0.206 | 0.504 | 0.901 | 0.701 |
| G06 | A2-E | 15 | 11 | 46080 | 0.928 | 0.451 | 1.123 | 0.588 | 1.139 |
| G06 | A2-U | 15 | 6 | 46080 | 0.908 | 0.452 | 1.164 | 0.580 | 1.330 |

**实际独立结果偏负，不能推广替换：** G03原生留出MAE由2.842mm降到A2-U的2.471mm，但known从90.3%降到88.6%、支持率22.9%降到22.3%，两种Body条件资格均0/18；这不是可靠错层修复。G05的A2-E/U为0.676/0.679mm，均差于A0的0.593mm与A1的0.434mm。G01的A2-E条件MAE略降，但固定分母代价2.563→2.646mm、支持下降；A1更稳定。G06负对照明显被扰动，A0→A2-E/U为0.299→0.451/0.452mm，支持75.9%降到58.8%/58.0%。因此即使某些来源满足Ring/背景/区域条件检查，也不能将其称为完整独立几何验收通过。条件性通过仅为34/150状态（E=21/75，U=13/75），不支持全组替换。

MAE/P95仅在有效原生HERO留出对应上，support与known以全源–目标查询N为分母；10mm未解释代价为评价代理，不是GT误差。所有A2数字包含未获资格的**数值提案**，不能当作全来源合格新几何。原生留出HERO也有预测/相机噪声，不是GT。相同上游图像的来源并非独立统计证据。

## 控制实验

| control | Body | initial_mm | final_mm | pose_translation_mm | pose_rotation_deg | zero_pass | qualification |
|---|---|---|---|---|---|---|---|
| C0_ZERO | Body-E | 0.000 | 0.045 | 0.045 | 0.258 | True | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C0_ZERO | Body-U | 0.000 | 0.156 | 0.155 | 0.488 | False | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C1_DEPTH | Body-E | 3.052 | 2.785 | 0.266 | 0.665 | None | INDEPENDENT_CONFLICT_OR_UNEXPLAINED |
| C1_DEPTH | Body-U | 3.052 | 2.743 | 0.309 | 0.752 | None | INDEPENDENT_CONFLICT_OR_UNEXPLAINED |
| C2_POSE | Body-E | 1.948 | 0.043 | 0.043 | 0.269 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C2_POSE | Body-U | 1.948 | 0.157 | 0.155 | 0.547 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C3_FAR | Body-E | 10.221 | 0.043 | 0.043 | 0.262 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C3_FAR | Body-U | 10.221 | 0.158 | 0.157 | 0.501 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C4_LEFT | Body-E | 0.000 | 0.023 | 0.029 | 0.297 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C4_LEFT | Body-U | 0.000 | 0.139 | 0.149 | 0.429 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C4_RIGHT | Body-E | 0.000 | 0.038 | 0.041 | 0.218 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |
| C4_RIGHT | Body-U | 0.000 | 0.036 | 0.035 | 0.112 | None | CONDITIONAL_CONSTRAINT_SUPPORTED |

C2/C3能恢复较大的刚体错位，说明不依赖旧世界距离准入。C1的加性轴向深度误差改变三维局部形状，严格刚体A2没有足够表达能力，恢复失败。零扰动Body-U产生约0.156mm漂移，超过0.1mm预登记门槛，即使Ring/背景条件检查通过，也不能称定位精度已证明。C4保留独立真实左右曲面，未平均或合并；仅是最小控制，不证明任意复杂多分支都可判别。

## 五个科研回答

1. **初始椭球还是更新Body？** 上表必须结合独立指标与资格率判断，不按Body距离或漂亮截面选胜者。Body-E在G03拉长、G01/G05扁平，说明本次有限预算二维拟合未得到稳定合理的粗主体；相机、区域描述子和局部优化搜索都可能参与，不能据此唯一证明几何不可辨识；Body-U含更强历史观测，也会将形态偏差传入对应。没有一个Body已证明普适正确区域对应。
2. **远距离能生成合理候选？** 可以突破旧门控；控制C3恢复与真实旧距离/候选数见逐来源CSV。候选产生不等同真实身份正确。
3. **是否独立改善定位？** 只能按上表、背景留出、Ring全CAD和来源间可见性给局部条件证据。某些误差下降同时可能失去支持/覆盖；不足以认定四组错层可靠解决。绝对位姿精度NOT_EVALUABLE。
4. **G03长柄？** A2完整刚体保留原柄、连接、面片、长度和曲率，未将柄吸附椭球头；这只是局部形态保持，世界方向/位置仍受独立约束与歧义限制，不宣称长柄已经准确重定位。全部原面与候选图均保留。
5. **误差来自哪里？** C1证明深度形变不能由严格刚体表达；新椭球退化与零扰动U漂移证明Body区域并非精确材料对应；真实背景/Ring矛盾也可能来自原相机、背景非静态/重复纹理、Mask/CAD投影或HERO。现有真实数据不能唯一拆分所有原因，不把全部误差归因相机。

## 失败与结论

控制契约修复前结果归档，正式真实参数未按留出或GT调整。没有删除错层面制造改善。建议保留二维区域候选和独立约束的诊断接口，**暂不把本轮全部A2提案替换正式HERO/相机或进入自动融合**；下一步应先人工检查关键区域身份与独立背景/相机证据，若另行授权再隔离刚体定位与射线深度误差。完成后停止。

## 核心图与复现

- figures/Fig1_Region_Correspondences.png：实际二维对应与原图。
- figures/Fig2_Body_E_U.png：两种Body及同来源候选。
- figures/Fig3_HERO_All_Group_Comparison.png：全部原生三角面、同尺度错层对照。
- figures/Fig4_Independent_and_Control_Evaluation.png：独立评价与控制失败。
- 各组Three_Fixed_Directions、Actual_Common_Sections及GLB完整图层。

精确绝对路径与SHA见RESULT_INDEX.md、assets_index。运行命令见REPRODUCE.md。大数据/GLB/全部逐步记录本地保留，只有明确列入Git交付清单的文件声称上传。

## 固定审计表

|审计项目|必须汇报|
|---|---|
|目标组数|4个独立物理组；75来源；150个Body-E/U来源状态；A0/A1独立基线|
|本算法独立成功|150/150产生数值候选；34/150满足预登记条件性验证；不能等同真实定位准确或独立来源数量|
|本算法失败|0无数值候选；116未获条件性资格，accepted_H=null/NaN；绝对真实三维精度4/4 NOT_EVALUABLE|
|历史测量值回退|0；A0/A1与授权Body-U是明示对照/输入，未填入失败A2预测|
|失败组及具体原因|FAILURE_LEDGER.md及metrics/VALIDATION.csv逐来源原因与真实图集|
|最终统计样本|全部4组、75来源、150状态；每源最多1024固定原生ID；有效N与全N并列；没有融合Mesh监督|
|是否使用GT选择算法|否；provenance/REAL_SOLVER_CODE_FREEZE.json与ALL_REAL_PREDICTIONS_FROZEN.json；控制GT仅生成/冻结后审计|

## 新椭球参数与视角

| group | center_mm | semiaxes_mm | FIT_views | image_cost |
|---|---|---|---|---|
| G03 | [-2.9653, 0.8966, -11.9093] | [19.9999, 10.195, 7.6517] | G03_v004_raw00834, G03_key00_raw00100, G03_key04_raw00554 | 16.415 |
| G05 | [-0.4702, 0.6795, -6.9943] | [8.8135, 0.307, 9.5407] | G05_v004_raw00796, G05_v004_raw00117, G05_v004_raw00377 | 0.868 |
| G01 | [0.046, -0.5121, 0.3484] | [4.7163, 3.9933, 0.3233] | G01_video004_004_15, G01_004_new_r00, G01_004_ref08 | 0.786 |
| G06 | [-0.2652, 0.0274, -0.3316] | [0.9533, 4.8272, 5.5413] | G06_v004_raw00940, G06_004_new_r00, G06_004_growth_r03 | 0.087 |

## 条件资格与原因

| group | Body | numerical | accepted | total | reasons |
|---|---|---|---|---|---|
| G03 | Body-E | 18 | 0 | 18 | {'BODY_REGION_GEOMETRY_UNEXPLAINED': 18, 'BACKGROUND_HOLDOUT_CONFLICT': 3, 'RING_RASTER_WORSENING': 2, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 1} |
| G03 | Body-U | 18 | 0 | 18 | {'BODY_REGION_GEOMETRY_UNEXPLAINED': 17, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 7, 'RING_RASTER_WORSENING': 2, 'BACKGROUND_HOLDOUT_CONFLICT': 5} |
| G05 | Body-E | 16 | 0 | 16 | {'BODY_REGION_GEOMETRY_UNEXPLAINED': 16, 'BACKGROUND_HOLDOUT_CONFLICT': 4, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 2, 'RING_RASTER_WORSENING': 2} |
| G05 | Body-U | 16 | 7 | 16 | {'BODY_REGION_GEOMETRY_UNEXPLAINED': 2, 'BACKGROUND_HOLDOUT_CONFLICT': 5, 'RING_RASTER_WORSENING': 2, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 6} |
| G01 | Body-E | 26 | 10 | 26 | {'BODY_REGION_GEOMETRY_UNEXPLAINED': 8, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 4, 'BACKGROUND_HOLDOUT_CONFLICT': 9, 'INSUFFICIENT_INDEPENDENT_INFORMATION': 2, 'INSUFFICIENT_BACKGROUND_HOLDOUT': 1} |
| G01 | Body-U | 26 | 0 | 26 | {'BODY_REGION_GEOMETRY_UNEXPLAINED': 20, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 8, 'BACKGROUND_HOLDOUT_CONFLICT': 9, 'INSUFFICIENT_INDEPENDENT_INFORMATION': 2, 'RING_RASTER_WORSENING': 1, 'INSUFFICIENT_BACKGROUND_HOLDOUT': 1} |
| G06 | Body-E | 15 | 11 | 15 | {'BACKGROUND_HOLDOUT_CONFLICT': 4, 'RING_RASTER_WORSENING': 1, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 2} |
| G06 | Body-U | 15 | 6 | 15 | {'BACKGROUND_HOLDOUT_CONFLICT': 6, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 6, 'RING_RASTER_WORSENING': 2} |

# 方法与输入审计

本轮研究区域对应与重新定位，不优化主体、不融合、不训练。正式比较 A0、A1、A2-E、A2-U，四个独立物理组共75个原生FIT来源（G03=18、G05=16、G01=26、G06=15）。其中两份照片单列 PHOTO，不冒充视频或新独立物理组。有效几何为历史017/MAX的TRUSTED原面，不重新删除或修复。

## 历史方法为何不足

- A1/ELLIPSE-VS-FULLMASK提供九参数椭球、解析投影；其历史拟合使用了深度。本轮只复用数学投影，重新从二维输入拟合，不读取HERO XYZ决定Body-E。
- 015 INITIAL不是原始解析椭球，不能重命名使用。
- 018 B2提供共享主体及可见性诊断。019–021的一个视频共享刚体无法改变该视频内部HERO的相对位置；共同二维地标BA也没有证明全部独立HERO几何改善。
- BODY-ANCHORED正式R3只对已通过三维距离/法向/可见性门禁的MATCHED来源估计b,a,c。独特新面、远距离错层难以进入强对应；固定射线三参数也不能任意消除横向/旋转误差。该限制是数学表达与实际门控的结果，不等同所有异常都来自相机。

历史精确源码依赖和SHA在provenance/INPUT_SHA.json、各BODY_SOURCES、A1_REPLAY与运行源码冻结中记录。

## 原设计与实际实现

|要求|实际代码与数学实现|限制/差异|
|---|---|---|
|新Body-E，九参数|fit_body.py:body_fit；c、旋转向量、log半轴；geometry.py复用A1 decode/sphere_mesh与旧解析ellipse_projection/signed_distance|三幅固定原018 FIT视角；通用Mask核心椭圆，而非DXY最终椭圆。固定3初值×80nfev；无HERO/旧Body几何初始化。二维退化不隐藏|
|Body-U冻结|local_results/Gxx/Body-U.npz|精确继承上一任务正式R3 B3 FINAL，不使用早期工程轮；历史018 B2仅登记备用|
|二维区域先行|geometry.py:ellipse_descriptor/sample_spatial；resection.py:region_candidates|DT最大值25%核心+AMS椭圆描述子，同一规则；96个极坐标均衡锚。归一化半径≤.85才建核心对应；外围保留UNKNOWN，不能称精确头柄分割|
|初始不邻近也可建对应|Body投影的归一化椭圆区域→第一可见面Q；没有源点到Body世界距离准入阈值|Q仍依赖Body形态、初始候选相机和椭圆相位；可发生区域错误|
|多候选|四个Ring法向yaw初值×两个椭圆相位×两次重新对应|每次固定对应TRF最多30nfev；不按GT/HOLDOUT扩大搜索|
|重定位且保持原投影|resection.py:solve_fixed；X'=HX，C'=HC，同一个H∈SE(3)，无尺度|本轮是**来源级派生相机重定位候选**，不保持原视频内部相对轨迹；不是019–021视频共享T，不宣称已恢复正式轨迹。原文件不变|
|不只三维最近点|候选身份来自二维极坐标区域；proper_rigid仅初始化；最终联合区域三维残差+Body点到源像素重投影+Ring+真实背景SIFT|不是ICP；形态相似/归一化区域不是物理材料同名点，必须独立验证|
|相同E/U输入与预算|同75来源、相同2D锚、背景FIT、seed与最大nfev|实际可见/正常法向候选数不同，失败记录；不删困难来源|
|独立约束|真实背景SIFT mutual .72，70/30拆分在RGB-RANSAC前；FIT选参考，HOLDOUT不筛除|背景固定参考相机也有历史误差；极线约束不能单独提供绝对位姿真值|
|Ring物理约束|实际CAD前后相邻面轮廓边、Open3D第一层；材料Mask与轮廓段距离，Polyp遮挡未知；消除CAD离散yaw伪约束|最终全CAD硬光栅是独立算子，使用同一Ring观测，不能称未见Ring数据|
|A1复现|replay_a1.py调用旧run_multi.py B1，固定旧018 Body，全部来源theta与历史FINAL最大差0|历史对照，不是A2初值；不把A1较好结果填入A2失败|
|独立评价|evaluate_real.py、validate_pose.py；原生留出HERO、真实留出Mask/背景像素、来源间CAD遮挡深度查询|本轮更新留出，不保证历史Body祖先从未使用相关图像；无真实位姿GT|
|保持局部形态/柄|刚体变换作用完整TRUSTED网格；原顶点/面片/PixelID完全保留|能保留曲率/连接，不能由此证明柄的世界位置/方向准确；椭球不强行拟合外部细长结构|

## 目标函数及鲁棒归一化

每轮固定二维区域候选，优化六参数位姿增量，不优化Q或Body：

`L = 0.5 mean rho((H X-Q)/1mm) + 0.5 mean rho((project(Q,C')-u)/3px) + mean rho(Ring/2px) + mean_ref mean_match rho(Sampson/1.5px) + 0.002 L_prior`。

`rho(r²)=2(sqrt(1+r²)-1)`，先按物理噪声尺度鲁棒化，再按块样本量归一化。代码使用等价变换残差并调用SciPy TRF `loss=linear`，避免样本量改变离群点尺度。初始化正交Procrustes（SO(3)，非镜像/尺度），不是最终目标或三维最近点配准。每轮位姿图平移增量界±20mm、旋转向量各分量±π；总H由真实候选/独立约束诊断，非旧1mm门控。

成熟求解与射线机制参考 [SciPy least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html) 和 [Open3D RaycastingScene](https://www.open3d.org/docs/release/python_api/open3d.t.geometry.RaycastingScene.html)。运行使用本机固定包版本，不按在线最新版替换依赖。在线文档只作数学/API核对，不代替本地源码与实际运行。

## 候选选择、资格与NaN

仅FIT目标选数值候选，先冻结全部150个E/U来源状态，再读取真实HOLDOUT。独立资格只标注原候选，不回选其他seed。Ring+背景信息矩阵排除Body/先验，使用1mm/1°参数尺度；满秩也不代表准确。近等目标、显著不同位姿的候选保留歧义。缺约束为UNKNOWN，独立冲突为不通过；accepted_H为null/NaN，native A0仅独立对照，不回退冒充新结果。

## 控制实验与先修契约

已有IIa6.5五相机、原生GT和CAD冻结。旧虚拟RGB实为标签彩图，不拿它做SIFT。只为控制生成相同场景/相机的静态纹理背景真实Blender RGB；没有修改DXY或原.blend。原GT→相机/Ring投影门禁先通过，才运行定位。C0零扰动、C1+3mm轴向深度、C2已知旋平移、C3约10mm级刚体错位、C4左右真实不同曲面分别保存。GT只用于控制源生成与所有控制预测冻结后审计。控制Body-U历史训练含理想GT深度，明确为上限/方法控制，不代表独立真实输入。

首轮控制暴露CAD顶点子采样漏管截面和鲁棒化顺序错误；修复为实际轮廓段及物理尺度先鲁棒化。旧结果完整归档runtime/CONTROL_RING_AND_ROBUST_CONTRACT_FIX。Body-E遗漏bounds、控制导入/随机拆分身份等早期工程记录也保留。真实定位开始前完成修复与源码冻结；没有按真实留出结果调参。刚性A2不能精确修复C1非刚性的沿射线深度扭曲，失败必须保留。

## 评价口径

- 来源间每个源固定最多1024个均匀原生ID，目标仍原生深度格；0.5mm支持带，CAD前后关系与目标深度可信次序；前方分歧、更深层、CAD遮挡、UNKNOWN独立列出。更深层可能合法遮挡，非物理错误标签。
- 同视频、跨视频、照片参与、原生HERO留出分开。不把相同/相关上游RGB当独立统计样本；逐来源/有向对N可复核。
- 有效对应MAE/median/P95与固定总N、10mm未解释代价并列。该固定代价是评价代理，不是优化损失或真实毫米误差。
- 部分HERO曲面投影到留出RGB：IoU是partial-patch IoU，前景固定分母覆盖和预测精度同时给出，不冒充完整Body重建IoU。自己的源像素不变只是契约测试，不是独立定位准确性。
- 局部边长/曲率与面积刚体不变；A1沿射线修正会改变局部形态，单列统计。累计来源面积不是唯一解剖面积。真实GT与绝对姿态精度NOT_EVALUABLE。

## 原生观测与历史Raw Mesh离散身份

46份MAX网格含native_pixel_id；29份旧018网格只有归档360行UV/K和原面ID，而原生深度观测为352行网格，两者不能直接将归档uv整型编码成原生PixelID。区域优化及源间深度评价始终使用OBS_TRUSTED的真实原生pixel_id、K和XYZ；完整Mesh保持旧网格顶点/面原样刚体移动。派生Mesh保留original_vertex_id、original_mesh_uv/K、original_face_id；对未供应的native_pixel_id写-1/UNKNOWN，**不伪造原生身份**。两套离散化的几何差异不归因为定位误差，区域候选记录的原生PixelID仍完整。
