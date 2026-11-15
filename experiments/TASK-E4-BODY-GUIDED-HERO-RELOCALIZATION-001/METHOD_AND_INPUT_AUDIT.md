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
