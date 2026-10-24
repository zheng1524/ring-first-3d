# Ring-First VNext：多测量组表面处理与可信GT验证

## 1. Executive Summary

本轮处理8组、9个独立视频表面，新增R5与大IIa的Ring-First/HERO实际推理，并使用7组同名可信Blender GT。保守拓扑修复保住几何；004/005融合网格非流形边从586/1993降至1/0。碎块处理在合成注入实验有效，但真实004的TSDF误删了GT支持面，不能默认启用。真实绝对空间映射仍未知；Oracle形状误差不代表端到端精度。头部与蒂部分区尚不足以支持正式物理测量。

实验目录：`ring_anchor_3d/experiments/multigroup_surface_gt_vnext/`。唯一人工技术报告为本文件。所有新增结果独立保存；未修改DXY-MID、HERO权重或旧实验，未开展跨视频配准、训练、3DGS、重标定、删除或压缩。没有登记清理候选：历史资产仍承担基线/来源证据。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 8组；G01的004/005合计1组，共9视频表面 |
| 本算法独立成功 | 8/8组、9/9视频产生B0/B1/B2数值表面；13个输入含4个历史C/TSDF额外对照，全部实际处理。数值成功不等于几何准确 |
| 本算法失败 | 可信同名GT缺失1/8组G04，相关GT分数NaN；真实独立空间映射缺失8/8，端到端空间精度全NaN；Ip头部语义分区未认证 |
| 历史测量值回退 | 0；复用明确授权的Ring-First/HERO几何输入，不读取其他路线的直径值补预测 |
| 失败组及具体原因 | G04缺GT；G03头/蒂代理失效；G03/G05/G07筛选通过相机0/8；004 TSDF有支持面误删；详见第11节和`metrics/failure_ledger.csv` |
| 最终统计样本 | 全体分母8组；可信形状GT7/8，Oracle形状7/8；真实独立坐标GT0/8；不把帧或顶点当独立样本 |
| 是否使用GT选择算法 | 否；预测和指标在测试GT几何读取前冻结。评价用GT ICP仅标Oracle，不改变正式Mesh或筛选阈值。历史GT信息已暴露，不能宣称整个研究从未见过GT |

## 2. Experimental Groups

| 冻结资产ID | 形态 | 环 | 划分 | 真实视频后缀 | 参考索引/raw | 既有相机筛选通过 | 可三角化留出Polyp点 | 可信GT目录 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G01_004 | Ip | R10 | DEV | 004 | 8/676 | 16/16 | 14 | 01p-12- |
| G01_005 | Ip | R10 | DEV | 005 | 10/459 | 15/22 | 7 | 01p-12- |
| G02_004 | Ip | R10 | DEV | 004 | 4/570 | 2/8 | 1 | 01p-4- |
| G03_004 | Ip | R10 | DEV | 004 | 4/554 | 0/8 | 6 | 01p-20- |
| G04_004 | Is | R10 | VALIDATION | 004 | 4/437 | 1/8 | 0 | 缺失，NaN |
| G05_004 | Is | R10 | VALIDATION | 004 | 4/542 | 0/8 | 0 | 01s-18-6.99 |
| G06_004 | IIa | R10 | TEST | 004 | 4/596 | 4/8 | 0 | 02a-14-1.6 |
| G07_004 | Is | R5 | VALIDATION | 004 | 4/369 | 0/8 | 4 | 01s-14 |
| G08_004 | IIa | R10 | TEST | 005 | 4/669 | 2/8 | 2 | 02a-22-4.4 |


G01只统计为一个测量组，004/005各自处理、各自环坐标，**未合并或重新注册**。G08的实际视频后缀是005；`G08_004`是复用包装器留下的冻结产物名，不代表另一个输入。所有图注保留此警示，完整绑定在[来源绑定表](inputs/SOURCE_BINDINGS.csv)。G01参考8缓存绑定raw676，沿用冻结文件/哈希，不把历史“raw674”名称自动解释为相同像素。新组每视频固定8帧，参考索引4；不是按GT误差重新选帧。

| 组 | 完整视频输入 | 同名可信GT原文件 |
| --- | --- | --- |
| G01 | /home/liu/polyp_research/smart_endoscope_20260805/raw/GP_Ip_12.0mm_closed_R10_single_refY_004.mp4<br>/home/liu/polyp_research/smart_endoscope_20260805/raw/GP_Ip_12.0mm_closed_R10_single_refY_005.mp4 | /home/liu/polyp_research/01p型/01p-12-/息肉.blend |
| G02 | /home/liu/polyp_research/smart_endoscope_20260805/raw/GP_Ip_4.0mm_closed_R10_single_refY_004.mp4 | /home/liu/polyp_research/01p型/01p-4-/息肉.blend |
| G03 | /home/liu/polyp_research/smart_endoscope_20260805/raw/GP_Ip_20.0mm_closed_R10_single_refY_004.mp4 | /home/liu/polyp_research/01p型/01p-20-/息肉.blend |
| G04 | /home/liu/polyp_research/smart_endoscope_20260805/raw/GP_Is_6.5mm_closed_R10_single_refY_004.mp4 | NaN：未找到确切Is6.5文件 |
| G05 | /home/liu/polyp_research/smart_endoscope_20260805/raw/GP_Is_18.0mm_closed_R10_single_refY_004.mp4 | /home/liu/ultralytics-main/polyp_detection/息肉建模/01s-18-6.99/息肉.blend |
| G06 | /home/liu/polyp_research/smart_endoscope_20260805/raw/GP_IIa_14.0mm_closed_R10_single_refY_004.mp4 | /home/liu/ultralytics-main/polyp_detection/息肉建模/02a-14-1.6/息肉.blend |
| G07 | /home/liu/polyp_research/smart_endoscope_20260805/raw/GP_Is_14.0mm_closed_R5_single_refY_004.mp4 | /home/liu/polyp_research/新建息肉建模(1)/01s-14/息肉.blend |
| G08 | /home/liu/polyp_research/smart_endoscope_20260805/raw/GP_IIa_22.0mm_closed_R10_single_refY_005.mp4 | /home/liu/ultralytics-main/polyp_detection/息肉建模/02a-22-4.4/息肉.blend |


复用：G01—G06来自`multigroup_ring_hero_visual_audit_v1`；G01原始表面及附加C/TSDF来自Surface Fusion V2和`independent_confidence_fusion_v1`。本轮实际新增G07/G08分割、Ring候选、视觉轨迹、局部相机以及官方MVSAnywhere HERO推理，非旧结果冒充新运行。[HERO运行记录](metrics/HERO_runs.json)、[新组几何运行记录](metrics/new_group_geometry.json)、[全部表面来源](inputs/surfaces.json)记录完整路径、相机及帧身份。新组几何运行分别约44.5s/40.9s；HERO运行约4.80s/0.33s，不含首次环境/加载与分割耗时。

模型：复用官方HERO权重与既有推理包装器，不训练、不改变Mesh生成阈值；新组只向既有通用torus求解器传入元数据R5中心半径3.1mm或R10中心半径5.6mm，截面均0.6mm。R5不是把R10整体缩放，截面不随环半径缩放。DXY-MID仅调用已有INIT/二维Ring适配器，只读。

## 3. GT Coordinate Mapping

接受人工前提：**同名Blender原模型即可信三维形状GT**，不再要求实物扫描或制造证明。本轮实际在Blender5.0.1读取7个原文件、对象`matrix_world`、场景单位、对象及Ring清单，并导出几何用于评分。对象优先精确主体名，Is18采用其最大主体网格；完整选择证据在[GT资产审计](gt_mapping/GT_ASSET_AUDIT.json)。未保存任何原.blend。

统一公式：`P_world = R_c2w P_cam + C`；反投影`P_cam = Z K^-1 [u,v,1]^T`。K为640×360像素坐标：fx=fy490，cx319.5，cy179.5；深度是相机轴向Z、毫米。新HERO原生352行深度按既有流程恢复360行并使用相应完整图像K，不将射线距离当轴向Z。真实畸变未重新估计，沿用冻结候选。Ring中心为局部原点、XY平面为环平面，法向z；轴内yaw为规范自由度。PLY毫米；GLB按规范除1000转米，仅格式单位转换，未改几何尺度。

原GT对象世界坐标换算`mm = scene_scale_length × 1000 × matrix_world × vertex`。本次原文件均未包含经过真实拍摄标定的Ring—息肉部署关系；有可信形状不意味着拍摄姿态自动已知。即使作者文件存在相机/环，也不能无证据当作真实录像中的相机/环。

| 评价模式 | 本轮有效范围 | 可以说明什么 | 不能说明什么 |
| --- | --- | --- | --- |
| INDEPENDENT_FRAME_GT | 真实0/8；既有Blender受控场景有效 | 相同独立世界坐标下的几何距离、真实可见GT覆盖 | 真实数据目前不能得到绝对空间定位精度 |
| GAUGE_INVARIANT_GT | 7组完整GT的最大弦、面积、水密体积；预测同定义量可对照 | 无需决定Ring轴内角的标量形态差异 | 可见局部与完整GT的定义差异不能算纯重建错误 |
| GAUGE_ALIGNED_DIAGNOSTIC | 合成S2仅一次全局Ring yaw对齐，固定尺度 | 消去已声明对称规范后的比较 | 不允许逐帧配准、逐MeshICP或GT尺度拟合 |
| ORACLE_ALIGNED_DIAGNOSTIC | 真实7组/8视频；8次刚体ICP初始化，尺度固定1 | 最优刚体解释下的条件性形状差异、误删诊断 | 低误差不证明Ring-First自行定位正确，不证明真实Ring相对姿态正确 |

Oracle从每个视频**原始B0**确定一个H，B1/B2以及该视频C/TSDF均共享此H；不对清理分支独立ICP。H只存`gt_mapping/*_ORACLE_H.json`，正式Mesh保持原坐标。ICP训练采用3mm对应门限、Huber0.3mm、8初始化、40次迭代、最小80%训练距离选解；**最终评分包括全部面积采样**，不丢困难面。未确定独立映射的矩阵明确写NaN；完整协议见[映射模式](gt_mapping/MAPPING_MODES.json)。Oracle条件参考视图是把冻结相机随H变换后射线与GT相交的诊断补丁，不是独立已知的真实`S_visible_GT`。

## 4. GT Leakage Audit

组别/划分冻结UTC：`2026-10-23T09:30:50.926693+00:00`。正式预测、物理量、代码/阈值/SHA256冻结UTC：`2026-10-23T09:47:08.870392+00:00`。首次测试GT几何导出UTC：`2026-10-23T09:47:30.413395+00:00`；顺序已独立核验。冻结证据：[预测清单](provenance/FINAL_PREDICTIONS_BEFORE_TEST_GT.json)、[组别划分](provenance/group_and_split_selection.json)、[最终核验](metrics/FINAL_VALIDATION.json)。

保守按潜在共享底层形态族划分：Ip全DEV，Is全VALIDATION，IIa全TEST；同一CAD的多个视频不跨侧。不是随机顶点/帧划分；只有2个IIa测试组，形态与split混杂，不能泛化为所有类别的独立统计。参数在实际GT几何评价前统一冻结，本轮没有根据开发/验证或测试误差再选参数，也没有对某一组特调。

预测阶段用Python审计钩子拒绝读取`.blend`、`gt_mapping`和`private_gt`；只使用既有权重、代码和已核验底层分割/相机/HERO缓存。此前全项目研究曾暴露GT；本轮寻找文件路径的初期文本检索还返回过旧Dxy汇总数值，**未将这些数值送入预测、阈值、分组或评分**。因此只主张本轮预测与测试几何读取隔离，不宣称历史全项目盲测。GT体积/面积等均由本轮实际导出网格重算，不从历史Dxy数值回填。

受控Blender实验是另一个评价程序，可显式使用GT作为输入；S0/S3使用GT深度与辅助自由空间证据，S1使用GT相机与HERO，全部有理想GT Mask。S2的**原始几何**是冻结预测相机/HERO；其B2辅助可见性检查使用GT辅助相机，只是诊断，且实际删面0、与B0/B1完全相同。JSON中的`GT_camera_input`指HERO输入相机，不覆盖辅助检查，不能把S2 B2描述为完全无GT运行。详见[受控代码](code/controlled_ablation.py)。不把任何GT辅助分支混入正式真实预测成绩。

## 5. Surface Failure Audit

| 输入 | B0面 | B1面 | B2面 | 非流形B0→B1 | 连通分量B0→B1 | 原最大分量面积% | B2删面 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G01_004 | 26621 | 26621 | 26621 | 0→0 | 8→8 | 50.8 | 0 |
| G01_005 | 24030 | 24030 | 24030 | 0→0 | 3→3 | 72.1 | 0 |
| G02_004 | 7504 | 7504 | 7504 | 0→0 | 1→1 | 100.0 | 0 |
| G03_004 | 51525 | 51525 | 51525 | 0→0 | 4→4 | 89.4 | 0 |
| G04_004 | 7097 | 7097 | 7097 | 0→0 | 1→1 | 100.0 | 0 |
| G05_004 | 61796 | 61796 | 61796 | 0→0 | 5→5 | 66.8 | 0 |
| G06_004 | 17829 | 17829 | 17829 | 0→0 | 2→2 | 82.6 | 0 |
| G07_004 | 38518 | 38518 | 38518 | 0→0 | 4→4 | 87.5 | 0 |
| G08_004 | 38284 | 38284 | 38284 | 0→0 | 3→3 | 73.2 | 0 |
| G01_004_C | 96048 | 96048 | 96048 | 586→1 | 21→231 | 48.2 | 0 |
| G01_004_TSDF | 32703 | 32703 | 32690 | 0→0 | 610→610 | 51.9 | 13 |
| G01_005_C | 76256 | 76256 | 76256 | 1993→0 | 19→1159 | 66.8 | 0 |
| G01_005_TSDF | 20279 | 20275 | 20195 | 0→0 | 490→490 | 71.7 | 80 |


连通分量定义为**所有共享边的面均连通**，含非流形边；面积为三角面面积和，不等于不重复真实可见面积。C原融合采用顶点焊接产生大量多重边；切分顶点可消除错误拓扑连接，但不会改变交叉面、重复深度层或系统深度偏移。004C最终仍有1条非流形边，明确保留失败，不在测试后增补过滤器追求零。

每块的面数、面积、bbox直径上界、与主体最小距离、Ring邻近、Ip细长代理、有效源视角数、点支持、负证据比例和状态保存在[碎块表](metrics/fragments.csv)。尺寸仅记录，绝不以小为由删除。真正“空间直径”此处用bbox对角线上界而非精确直径；来源视角由输入Mesh和来源映射追溯。分类统计：

| 输入 | SUPPORTED分量 | REJECTED分量 | CONFLICT分量 | UNKNOWN分量 |
| --- | --- | --- | --- | --- |
| G01_004 | 0 | 0 | 1 | 7 |
| G01_005 | 0 | 0 | 1 | 2 |
| G02_004 | 0 | 0 | 0 | 1 |
| G03_004 | 0 | 0 | 0 | 4 |
| G04_004 | 0 | 0 | 0 | 1 |
| G05_004 | 0 | 0 | 0 | 5 |
| G06_004 | 0 | 0 | 0 | 2 |
| G07_004 | 0 | 0 | 0 | 4 |
| G08_004 | 0 | 0 | 0 | 3 |
| G01_004_C | 11 | 0 | 3 | 217 |
| G01_004_TSDF | 1 | 2 | 39 | 568 |
| G01_005_C | 54 | 0 | 3 | 1102 |
| G01_005_TSDF | 0 | 6 | 15 | 469 |


原单参考Mesh边缘撕裂和Ring遮挡不自动当作噪声；UNKNOWN全部保留。只有少量合格独立图像证据时，无法证明错层哪一层正确。对缺乏证据组不强行输出“已清理”。仅使用Ring身份像素作前方自由空间检验，不把Ring/Polyp邻接解释为接触，不把隐藏轮廓补线作为直接观测。

## 6. Mature Processing Methods

Python3.12、Open3D0.19、隔离目录中的PyMeshLab2023.12.post3；复用既有CUDA/HERO环境。PyMeshLab E57插件有libffi加载警告，但本轮不读E57，实际使用的mesh滤镜成功运行并通过玩具几何测试；未为无关插件改造主环境。方法依据：[PyMeshLab官方滤镜接口](https://pymeshlab.readthedocs.io/en/latest/filter_list.html)。

**B0**：原始开放面完整复制，历史多参考C/TSDF单列而不替代原始基线。**B1**依次调用：`meshing_remove_duplicate_vertices`、`meshing_remove_duplicate_faces`、`meshing_remove_null_faces`、`meshing_remove_unreferenced_vertices`、`meshing_repair_non_manifold_edges(method='Split Vertices')`、`meshing_repair_non_manifold_vertices(vertdispratio=0)`。不使用默认RemoveFaces修复，不位移、不平滑、不补洞。重复面只合并几何身份，保留多对一来源。逐面几何键及最近旧顶点验证没有无法解释的新三角形，坐标误差<1e-6mm。

**B2**：按B1连通分量。稀疏点支持来自未参与既有相机拟合的Polyp轨迹，排除当前参考帧，选最大基线两源帧三角化：正深度、重投影≤3px、视差≥1°；面中心距点≤0.3mm作局部支持。这些点被用于清理后，**不再是清理效果的独立验证集**。负证据只使用筛选通过相机中、侵蚀3×3后的Ring内部像素；完整torus首交深度可靠且候选Polyp位于Ring前方超过0.3mm时记录矛盾。每块≥5面、至少90%面具有≥2视图负证据且没有点支持才删，否则SUPPORTED/CONFLICT/UNKNOWN。平面/背景自由空间仅在受控GT分支显式开启；真实背景不无条件雕掉其后空间。

`config.json`统一阈值，`provenance/*_operations.json`保存滤镜与前后数量；`*_processing.npz`保存B0面→B1面、B1顶点→B0顶点、B1→B2保留Mask和支持状态。不新增面、不移动面。拓扑修复使部分孤立顶点缓冲未压紧，例如004原表面B1有104623缓存顶点但只有13777被引用；**这些不是新增恢复点**。正式PLY保留原输出供审计，GLB仅压紧未引用缓冲，不改任何三角面。冻结物理统计的中位数受顶点重复密度影响，应作为诊断而非面积加权物理真值。

**B3**：NOT_RUN。当前独立可靠密集点与法向不足；BPA可能跨无观测区新建面，无证据不执行。未安装CGAL/OpenMVS或新增深度模型。

## 7. Quantitative Evaluation

面积均匀采样：预测12000点、完整GT20000点；固定随机种子20261023，几何面键排序后采样，避免面索引重排制造假差异。点到**连续三角面**最近距离，法向角采用无向法向。Accuracy是预测→GT全样本MAE/p95；Coverage为GT面积样本中到预测距离≤0.25mm比例。完整GT覆盖分母与真实已观察表面分母不同，必须明确区分。

### 7.1 真实各组Oracle诊断：B0/B1/B2原单参考几何相同

下表B2与B0/B1完全重合，因为9个原始单参考输入没有面被B2删除，B1保持全部非零面。它们不是清理带来低误差的新方法成绩。**全部属于ORACLE_ALIGNED_DIAGNOSTIC**；真实端到端坐标精度、Acquisition Visibility、真实Reconstruction Coverage均NaN。

| 输入 | 表面MAE mm | 中位 mm | p95 mm | 最大 mm | 法向MAE° | 完整GT覆盖@0.25 % | 预测错误面积% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G01_004 | 0.305 | 0.187 | 1.243 | 2.749 | 23.865 | 22.115 | 33.733 |
| G01_005 | 0.240 | 0.192 | 0.634 | 1.242 | 21.514 | 15.680 | 37.392 |
| G02_004 | 0.103 | 0.082 | 0.255 | 0.463 | 18.940 | 37.635 | 5.592 |
| G03_004 | 1.564 | 0.228 | 9.628 | 13.215 | 26.847 | 15.145 | 46.575 |
| G04_004 | NaN | NaN | NaN | NaN | NaN | NaN | NaN |
| G05_004 | 0.653 | 0.618 | 1.383 | 1.879 | 44.315 | 6.655 | 79.858 |
| G06_004 | 0.097 | 0.076 | 0.296 | 0.831 | 12.377 | 27.915 | 6.917 |
| G07_004 | 0.237 | 0.195 | 0.658 | 0.991 | 19.837 | 19.180 | 38.383 |
| G08_004 | 0.589 | 0.514 | 1.452 | 2.648 | 40.174 | 7.220 | 74.892 |


**错误面积比例**定义为预测面积采样中距离GT>0.25mm，并非语义错误像素。法向、面积与距离都以冻结同一OracleH计算，不能据此选择真实相机或参考视角。G04缺同名GT，其3个分支均保留NaN。

### 7.2 历史多参考C/TSDF的处理消融

| 冻结额外对照 | 分支 | Oracle表面MAE mm | p95 mm | 完整GT覆盖@0.25 % |
| --- | --- | --- | --- | --- |
| G01_004_C | B0 | 0.409 | 1.266 | 29.995 |
| G01_004_C | B1 | 0.409 | 1.266 | 29.995 |
| G01_004_C | B2 | 0.409 | 1.266 | 29.995 |
| G01_004_TSDF | B0 | 0.420 | 1.454 | 25.410 |
| G01_004_TSDF | B1 | 0.420 | 1.454 | 25.410 |
| G01_004_TSDF | B2 | 0.421 | 1.448 | 25.410 |
| G01_005_C | B0 | 0.361 | 1.025 | 21.575 |
| G01_005_C | B1 | 0.361 | 1.025 | 21.575 |
| G01_005_C | B2 | 0.361 | 1.025 | 21.575 |
| G01_005_TSDF | B0 | 0.307 | 1.373 | 19.035 |
| G01_005_TSDF | B1 | 0.307 | 1.373 | 19.035 |
| G01_005_TSDF | B2 | 0.305 | 1.314 | 19.035 |


C的几何误差保持不变，虽然非流形显著减少；拓扑改善不能冒称形状改善。004TSDF B2存在有支持面的误删，不能因总体均值变化很小就认为安全。被删除面直接做3顶点+中心的4点GT距离审计，面积加权基线为B1面中心支持面积，以下是**采样近似率，不是完整面内距离上界证明**：

| 输入 | B2删面 | 4点全支持面 | 4点全不支持面 | 混合面 | 支持误删面积 mm² | 支持误删率% | 不支持移除率% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G01_004_TSDF | 13 | 5 | 6 | 2 | 0.023 | 0.020 | 0.015 |
| G01_005_TSDF | 80 | 0 | 80 | 0 | 0.000 | 0.000 | 0.688 |


9个原始Mesh和两份C：B2删面0，GT支持结构误删0是“没删”的结果。GT下部1/4的Ip代理区域单独采样：各分支误删率0；但该代理没有人工头/蒂标注，**不等于已证实解剖蒂部完整恢复**。Ring邻近/源Mask边缘因B1保持几何而保持原覆盖，B2对原始Mesh没有独立改善；真实局部可见真值仍受坐标限制。完整逐样本误删数据见`metrics/GT_structure_removal.json`。

### 7.3 既有Blender受控验证

复用V4现成16视角，不新渲染。完整GT面积采样20000点；按GT相机Z-buffer、Polyp实例及0.1mm深度一致性求实际可见集合。全16视角Acquisition Visibility=35.215%，参考8为27.300%；下表恢复率分母固定为参考8实际可见GT。不是把完整GT未被拍摄背面作为重建失败，也不把16视角可见面积称为单帧覆盖。

| 分支 | 处理 | 输入状态 | 预测→GT MAE mm | p95 mm | 参考可见GT恢复率% | 错误面面积% | GT支持采样误删% | 面数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | B0 | ORACLE_DIAGNOSTIC_GT_INPUT | 0.001 | 0.007 | 99.597 | 0.000 | 0.000 | 25659 |
| S0 | B1 | ORACLE_DIAGNOSTIC_GT_INPUT | 0.001 | 0.007 | 99.597 | 0.000 | 0.000 | 25659 |
| S0 | B2 | ORACLE_DIAGNOSTIC_GT_INPUT | 0.001 | 0.007 | 99.597 | 0.000 | 0.000 | 25659 |
| S1 | B0 | ORACLE_DIAGNOSTIC_GT_CAMERA_ONLY | 0.303 | 0.267 | 91.612 | 5.800 | 0.000 | 24997 |
| S1 | B1 | ORACLE_DIAGNOSTIC_GT_CAMERA_ONLY | 0.303 | 0.267 | 91.612 | 5.800 | 0.000 | 24997 |
| S1 | B2 | ORACLE_DIAGNOSTIC_GT_CAMERA_ONLY | 0.303 | 0.267 | 91.612 | 5.800 | 0.000 | 24997 |
| S2 | B0 | GAUGE_ALIGNED_DIAGNOSTIC_RING_YAW_ONLY | 0.441 | 0.479 | 78.828 | 20.200 | 0.000 | 24929 |
| S2 | B1 | GAUGE_ALIGNED_DIAGNOSTIC_RING_YAW_ONLY | 0.441 | 0.479 | 78.828 | 20.200 | 0.000 | 24929 |
| S2 | B2 | GAUGE_ALIGNED_DIAGNOSTIC_RING_YAW_ONLY | 0.441 | 0.479 | 78.828 | 20.200 | 0.000 | 24929 |
| S3 | B0 | ORACLE_DIAGNOSTIC_CONTROLLED_CORRUPTION | 0.057 | 0.007 | 99.597 | 0.242 | 0.000 | 25701 |
| S3 | B1 | ORACLE_DIAGNOSTIC_CONTROLLED_CORRUPTION | 0.057 | 0.007 | 99.597 | 0.242 | 0.000 | 25651 |
| S3 | B2 | ORACLE_DIAGNOSTIC_CONTROLLED_CORRUPTION | 0.001 | 0.007 | 99.597 | 0.000 | 0.000 | 25639 |


S0纯几何误差0.00139mm，表明反投影、轴向Z及尺度基本正确。S1/S2分别0.30304/0.44097mm，参考可见覆盖91.61%/78.83%；HERO深度和相机条件构成主要限制。S1/S2是不同相机条件下冻结HERO预测，深度本身也可能变化，**差值不是纯相机误差的单变量因果估计**。S2消去一次Ring轴内yaw，不做表面ICP。

S3在S0原始面上预先删除20边缘面、添加50重复面和0.2mm边长悬浮立方体12面。B1移除50重复身份，B2通过多视图已知背景前方自由空间拒绝立方体12面，MAE从0.05698降至0.00132mm，参考可见覆盖仍99.60%，支持表面采样误删0。20个故意断开的边缘面不补回；这证明处理能排除有证据的错误碎块，**不证明真实相机不确定时同样安全**。受控S0/S3使用GT输入，全部明确Oracle诊断。

## 8. Physical Metrics

三类实际计算：①可见分量最大三维弦及端点；②Ring坐标下z/rho/中心偏移/到torus距离；③稀疏多帧支持面片面积，重复拓扑身份只记一次。不计算开放预测体积，不将Ring平面作为组织基底，不把z称真实凸起高度。

**头部定义失败需明确保留**：预测Ip采用最大二维可见连通分量；冻结配置文字误写“tallest”，实际冻结源码是“largest area”。它不是解剖头部分类器，G03甚至把蒂部/错深点计入30.79mm弦，不能称头部测量正确。正式“已确认解剖头部宽度”在这些Ip组记UNKNOWN；以下数字原名为`visible_component_max_3D_chord_mm`。GT端Ip也只有nativeZ半径阈值分区代理，G03该代理未分离长蒂，不能把其32.46mm直接称真实头宽。Is/IIa不强制定义蒂部。

| 输入 | 可见分量3D弦 mm | Oracle条件GT弦 mm | 条件ARE% | 环z中位 mm | rho中位 mm | 中心偏移 mm | 环面距离中位 mm | 稀疏支持面积 mm² |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G01_004 | 9.926 | 11.622 | 14.596 | 0.609 | 3.306 | 1.332 | 1.783 | 1.212 |
| G01_005 | 9.979 | 10.605 | 5.909 | 0.867 | 3.285 | 1.104 | 1.949 | 1.049 |
| G02_004 | 4.445 | 4.189 | 6.107 | 0.079 | 1.317 | 0.378 | 3.726 | 0.125 |
| G03_004 | 30.792 | 18.804 | 63.757 | -5.129 | 8.910 | 10.015 | 5.850 | NaN |
| G04_004 | 6.209 | NaN | NaN | -0.706 | 2.007 | 1.458 | 3.059 | NaN |
| G05_004 | 17.947 | 15.299 | 17.306 | -1.514 | 6.673 | 4.255 | 2.337 | NaN |
| G06_004 | 12.796 | 12.008 | 6.556 | -0.151 | 3.503 | 1.066 | 1.513 | NaN |
| G07_004 | 13.251 | 12.577 | 5.361 | -1.495 | 4.888 | 3.351 | 1.850 | NaN |
| G08_004 | 21.358 | 19.308 | 10.620 | -1.173 | 6.557 | 3.814 | 2.416 | 0.207 |


表中GT条件弦是OracleH下、同一参考可见Mask射线命中GT后的诊断补丁弦，不是独立已知真实可见范围；因此ARE是**Oracle条件补丁差异**，不是正式头部精度。未匹配GT补丁的G04为NaN。Ring相对量是冻结局部相机条件下的模型输出，真实GT部署关系未知，Ring量的GT误差全部NaN。支持面积非整片真实面积，且支持轨迹依赖未独立认证的相机，故称POSE_CONDITIONAL_SPARSE_SUPPORT；没有支持的组保留NaN，不记0准确面积。

可信原GT的完整标量如下，均GAUGE_INVARIANT_GT。完整3D最大弦可包含蒂部、对角线，不能等同标签中XY标称直径。面积/体积可作为完整形状参照；未观察背面不能从开放预测推导。

| 组 | GT完整3D最大弦 mm | GT头部分区代理弦 mm | GT面积 mm² | GT闭合体积 mm³ | 水密 |
| --- | --- | --- | --- | --- | --- |
| G01 | 16.575 | 12.300 | 503.458 | 958.103 | True |
| G02 | 4.609 | 4.165 | 53.134 | 34.083 | True |
| G03 | 32.462 | 32.462 | 1499.997 | NaN | False |
| G04 | NaN | NaN | NaN | NaN | NaN |
| G05 | 18.000 | 18.000 | 684.288 | 1154.023 | True |
| G06 | 14.000 | 14.000 | 316.213 | 128.403 | True |
| G07 | 14.000 | 14.000 | 401.261 | 486.732 | True |
| G08 | 22.000 | 22.000 | 819.775 | 871.962 | True |


G03 GT不是水密网格，体积NaN；其形状仍是可信GT，不通过补洞人为制造体积。GT头部分区代理不足不是GT形状不可信，缺的是语义分区。GT Ring相对量因真实部署映射未知，均UNKNOWN。

## 9. Ablation & Generalization

统计以8个独立测量组为单位；G01两视频先等权平均，再进入组间统计。只有7组可得Oracle条件GT；下面同时给出MAE、中位绝对相对差、p95和最大差，不只报告均值或挑选最好组。**此表不是已认证物理测量精度**，分区/条件可见范围/预测误差共同贡献差异。

| 统计子集 | 独立GT组数 | 条件宽度MAE mm | 条件宽度中位ARE% | 条件宽度p95AE mm | 最大AE mm | Oracle表面组均MAE mm |
| --- | --- | --- | --- | --- | --- | --- |
| ALL | 7 | 2.795 | 10.252 | 9.186 | 11.989 | 0.502 |
| Ip | 3 | 4.469 | 10.252 | 10.906 | 11.989 | 0.647 |
| Is | 2 | 1.661 | 11.333 | 2.549 | 2.648 | 0.445 |
| IIa | 2 | 1.419 | 8.588 | 1.987 | 2.050 | 0.343 |
| R5 | 1 | 0.674 | 5.361 | 0.674 | 0.674 | 0.237 |
| R10 | 6 | 3.149 | 10.436 | 9.653 | 11.989 | 0.546 |


B0/B1/B2在9份原始单参考Mesh的共同支持集、完整面积样本和GT分母上几何相同，配对MAE与覆盖差均0；不存在用删点换均值的“改善”。额外TSDF对照不能当新增独立测量组。R5只有G07一组、R10七组，类别与尺寸混杂，不能据此宣称R5或R10更优。IIa14的OracleMAE约0.097mm是本次较好组；Is18约0.653mm较差，全部保留。组别名单并未按这些误差改动。

按原始输入Oracle表面MAE，最好为G06 IIa14（0.09676mm），最差为G03 Ip20（1.56404mm）；这只是已对齐的形状诊断，不是按效果重新挑选或删组。7组宏平均Oracle表面MAE为0.50216mm；条件可见补丁弦差MAE为2.79509mm，中位ARE为10.252%，p95绝对差9.18632mm，最大11.98859mm，主要受G03分区与形变失败影响。

最稳定可复用的正面结果是**不改变几何的拓扑整理**和有可靠自由空间时去已知错误碎块。负面结果是：真实跨视图几何证据稀疏、某些相机0/8通过；仅靠Ring前后顺序不足以证明错误面；没有清理方法能修复系统性深度变形。B3不具备证据条件，不强行造面。

## 10. Visualization Index

所有PNG为不透明白底真实像素，程序检查标准差>5、尺寸和SHA256；12张主图均已通过，不是生成模型图片。色阶/观察方向明确；图4统一44mm窗口，不按每组误差独立配准。所有组主图保留，不以显示裁片删除预测几何。

### 1. 8组/9视频的RGB、Mask、原始Mesh；包括GT缺失和相机失败组。

![Fig1_all8groups_inputs](visualizations/Fig1_all8groups_inputs.png)

### 2. 碎块、边缘、连通性、586/1993条非流形边的实际处理；灰色UNKNOWN保留。

![Fig2_surface_failure_audit](visualizations/Fig2_surface_failure_audit.png)

### 3. B0/B1/B2同尺度；B3明确未执行，不虚构新面。

![Fig3_processing_comparison](visualizations/Fig3_processing_comparison.png)

### 4. 预先按形态挑选Ip/Is/IIa四视图；相同44mm窗口。

![Fig4_morphology_four_views](visualizations/Fig4_morphology_four_views.png)

### 5. GT作者坐标、真实预测坐标分开；Oracle叠加仅用于诊断。

![Fig5_GT_mapping](visualizations/Fig5_GT_mapping.png)

### 6. 四种评价模式及真实缺失映射；不把Ring规范当唯一物理方向。

![Fig6_coordinate_modes](visualizations/Fig6_coordinate_modes.png)

### 7. 仅合成场景中的真实可见GT、正确恢复和漏失；明确不同分母。

![Fig7_actual_visible_GT](visualizations/Fig7_actual_visible_GT.png)

### 8. Accuracy与Coverage联报；左Oracle完整GT、右合成实际可见GT。

![Fig8_accuracy_coverage](visualizations/Fig8_accuracy_coverage.png)

### 9. TSDF被删13/80面及4点支持检验；展示误删而非隐藏。

![Fig9_false_removal](visualizations/Fig9_false_removal.png)

### 10. 3D弦、Ring相对量、局部支持面积；不把弦代理称头部真值。

![Fig10_physical_measurements](visualizations/Fig10_physical_measurements.png)

### 11. 8组均保留，G04为NaN；条件宽度误差与GT完整面积分开。

![Fig11_group_physical_metrics](visualizations/Fig11_group_physical_metrics.png)

### 12. Ip分区失败、缺失GT、残余非流形、深度/位姿影响与VH适用边界。

![Fig12_failures_and_VH](visualizations/Fig12_failures_and_VH.png)

### 可交互三维资产

| 资产 | 状态及用途 |
| --- | --- |
| [G01_004_B2_LOCAL_SCENE.glb](meshes/G01_004_B2_LOCAL_SCENE.glb) | LOCAL_PREDICTED_UNCERTIFIED；GLB单位m；Ring与Polyp独立身份 |
| [G01_005_B2_LOCAL_SCENE.glb](meshes/G01_005_B2_LOCAL_SCENE.glb) | LOCAL_PREDICTED_UNCERTIFIED；GLB单位m；Ring与Polyp独立身份 |
| [G02_004_B2_LOCAL_SCENE.glb](meshes/G02_004_B2_LOCAL_SCENE.glb) | LOCAL_PREDICTED_UNCERTIFIED；GLB单位m；Ring与Polyp独立身份 |
| [G03_004_B2_LOCAL_SCENE.glb](meshes/G03_004_B2_LOCAL_SCENE.glb) | LOCAL_PREDICTED_UNCERTIFIED；GLB单位m；Ring与Polyp独立身份 |
| [G04_004_B2_LOCAL_SCENE.glb](meshes/G04_004_B2_LOCAL_SCENE.glb) | LOCAL_PREDICTED_UNCERTIFIED；GLB单位m；Ring与Polyp独立身份 |
| [G05_004_B2_LOCAL_SCENE.glb](meshes/G05_004_B2_LOCAL_SCENE.glb) | LOCAL_PREDICTED_UNCERTIFIED；GLB单位m；Ring与Polyp独立身份 |
| [G06_004_B2_LOCAL_SCENE.glb](meshes/G06_004_B2_LOCAL_SCENE.glb) | LOCAL_PREDICTED_UNCERTIFIED；GLB单位m；Ring与Polyp独立身份 |
| [G07_004_B2_LOCAL_SCENE.glb](meshes/G07_004_B2_LOCAL_SCENE.glb) | LOCAL_PREDICTED_UNCERTIFIED；GLB单位m；Ring与Polyp独立身份 |
| [G08_004_B2_LOCAL_SCENE.glb](meshes/G08_004_B2_LOCAL_SCENE.glb) | LOCAL_PREDICTED_UNCERTIFIED；GLB单位m；Ring与Polyp独立身份 |
| [G01_ORACLE_COMPARISON.glb](meshes/G01_ORACLE_COMPARISON.glb) | ORACLE_ALIGNED_DIAGNOSTIC；GLB单位m；Ring与Polyp独立身份 |
| [G05_ORACLE_COMPARISON.glb](meshes/G05_ORACLE_COMPARISON.glb) | ORACLE_ALIGNED_DIAGNOSTIC；GLB单位m；Ring与Polyp独立身份 |
| [G06_ORACLE_COMPARISON.glb](meshes/G06_ORACLE_COMPARISON.glb) | ORACLE_ALIGNED_DIAGNOSTIC；GLB单位m；Ring与Polyp独立身份 |


`meshes/*_B0/B1/B2.ply`是正式局部预测，毫米；9个LOCAL_SCENE GLB只含该视频Polyp和已知Ring，压紧孤立顶点以节省显示内存，不移动坐标。三个ORACLE_COMPARISON GLB把GT逆H放入预测坐标作诊断对照，名称和元数据均标Oracle；**不能交给后续算法当正式配准真值**。GT原始网格另存`gt_mapping/G*_TRUSTED_GT.ply`，作者坐标毫米。未输出004/005共同注册场景。

## 11. Failures & Limitations

1. G04 Is6.5确切同名.blend在限定可用文件中未找到；不替用Is7、IIa6.5或缩放其他GT，GT行NaN保留。其预测Mesh仍在输出中。
2. 真实GT形状7组可信且实际读取，但没有独立真实相机/Ring到作者坐标映射；独立端到端位置、真实可见面覆盖和Ring相对量GT误差未知。Oracle评价不能补成正式成绩。
3. 004TSDF证据清理误删5个GT支持面、2混合面；模型先验/相机不准会污染“自由空间”。B2不得默认推广；不增大负证据权重或调阈值掩盖结果。
4. B1仍留004C一条非流形边；顶点切分不消除交叉/错层。Mesh缓冲有未引用顶点；冻结物理中位数依赖顶点重复密度，不是面积加权稳定测量。
5. Ip头部/蒂部语义分区不成立，G03为明确失败；GT nativeZ代理也未保证分离其长蒂。未宣称任何Ip获得准确解剖头宽，未利用GT修正预测分区。
6. G03/G05/G07相机筛选0/8；G04仅1/8。即便输出连续深度，几何支持不充分。相机筛选标记继承既有协议，非新增真实位姿GT证据。
7. G08资产ID为004但源视频005。已另存精确来源/哈希表，不覆盖冻结文件，不把修正文件标签当精度提升。G01参考raw标签也以本轮输入清单为准，而非旧文字标签。
8. S0/S3是GT输入诊断；S1为GT相机诊断；S2原始预测几何无GT面修正，但B2辅助检查读GT相机，且实际改动0。所有理想Mask分支不能冒充真实自动分割的端到端结果。
9. 开发初始出现适配器命名空间缺`subprocess`以及面键数组形状错误，均在测试GT读取前修复；初始失败日志完整保留`logs/new_groups_initial_namespace_failure.log`、`logs/processing_initial_mapping_failure.log`。测试后没有调正式预测。受控显示曾请求不存在的RGB路径，使用中性色仅为Mesh着色，不影响GT数值；Fig1真实RGB均来自实际缓存。
10. 完整GT面积采样、0.25mm阈值及4点支持不是所有薄结构逐点的数学保证；Ip下1/4代理不等于人工蒂部分区。低样本量不支持显著性推断，历史GT暴露限制严格盲测表述。

### 可复现命令与冻结路径

工作目录均为仓库根，环境已存在；不重新安装主环境。所有预测脚本有GT读取防火墙；评价独立执行。复现应复制到新的实验目录，避免覆盖本轮冻结资产。

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/multigroup_surface_gt_vnext/code/setup.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/multigroup_surface_gt_vnext/code/new_groups.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/multigroup_surface_gt_vnext/code/prepare_entries.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/multigroup_surface_gt_vnext/code/process_surfaces.py
/home/liu/blender/blender-5.0.1-linux-x64/blender --background --disable-autoexec -t 2 --python ring_anchor_3d/experiments/multigroup_surface_gt_vnext/code/export_gt_blender.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/multigroup_surface_gt_vnext/code/evaluate_gt.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/multigroup_surface_gt_vnext/code/controlled_ablation.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/multigroup_surface_gt_vnext/code/audit_removed_faces.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/multigroup_surface_gt_vnext/code/visualize_results.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/multigroup_surface_gt_vnext/code/build_report.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/multigroup_surface_gt_vnext/code/final_validate.py
```

PyMeshLab从本实验vendor加载，依赖版本记录在`provenance/report_environment.json`。预测输入、代码和输出SHA256见`provenance/FINAL_PREDICTIONS_BEFORE_TEST_GT.json`；后续GT/图/报告核验另列，不改早期冻结清单。最终日志`logs/final_validation.log`及`metrics/FINAL_VALIDATION.json`汇报旧文件/用户修改保护、几何来源、覆盖分母、图像非空和唯一Markdown检查。处理测试见`tests/test_processing.py`和`logs/tests.log`。

## 12. Final Decision

**保留B1为实验性拓扑整理，不把B2作为自动删除默认项；不启动更复杂表面重建或闭合体积测量。** 目前主要障碍是预测几何/相机一致性与语义分区，进一步调碎块阈值不会解决。

| 人工问题 | 基于本轮证据的回答 |
| --- | --- |
| Q1 成熟处理能否稳定清理错误碎块？ | 可稳定整理重复/非流形拓扑；受控悬浮12面可去除。真实多数碎块UNKNOWN，004TSDF有误删，尚不能稳定自动删错块 |
| Q2 是否损害真实表面尤其Ip蒂部？ | B1不改变非退化三角形；原始9视频B2不删。004TSDF有GT支持面误删；下1/4代理未发现误删，但没有人工蒂部标签，不能认证全部蒂部保留 |
| Q3 Accuracy与Coverage同时改善？ | 原始9视频两者均不变。注入控制实验Accuracy提升且可见覆盖保持；真实没有普遍同步提升证据 |
| Q4 可信GT是否正确利用且无测试污染？ | 7组同名原文件实际读取，尺度/坐标/四种模式审计；预测早于测试几何冻结，未以GT改面。历史GT暴露已披露；真实独立映射仍缺失 |
| Q5 哪些物理指标准确恢复？ | 能输出公制可见弦、Ring相对量、局部支持面积；它们是条件性数值。尚无真实独立坐标/头部分区证据认证绝对精度；GT完整标量可可靠计算（水密体积除外NaN） |
| Q6 哪些受视角覆盖限制？ | 完整头宽/后侧面积/细蒂和闭合体积；真实完整与可见定义差异必须保留，不能用完整GT尺寸差直接代表重建误差 |
| Q7 形态/Ring规格共同规律？ | 不变几何的修复可跨Ip/Is/IIa；共同瓶颈是支持稀疏和系统偏差。R5只有1组，无法归因环型优劣 |
| Q8 仍需拓扑改善？ | 有限需要：残余1条非流形、输出缓冲压紧及交叉/错层审计；不能靠删面换好统计 |
| Q9 Visual Hull能否帮助？ | 可作为有可信位姿时的保守自由空间不等式；Ring遮挡保留UNKNOWN。未在本轮新增VH实验，不宣称可恢复未见形状 |
| Q10 下一步成熟路线？ | 优先固定可靠相机下的多参考深度一致性与局部显式表面约束；先建立不借GT的Ip头/蒂分区和同定义可见指标，再推进物理量认证 |

下一轮仅建议两项：①以本轮冻结组与全部原始覆盖为分母，检验多参考深度联合修正能否同时降低GT形状误差并保持支持区域，不继续无界跨视频配准；②建立人工可审阅、预测独立的头/蒂区域标注和GT坐标映射记录，用于真正同定义的可见宽度/面积验证。没有这些证据前，不把Oracle低误差或网格整洁程度当作测量成功。

本轮到此停止，等待人工审核。
