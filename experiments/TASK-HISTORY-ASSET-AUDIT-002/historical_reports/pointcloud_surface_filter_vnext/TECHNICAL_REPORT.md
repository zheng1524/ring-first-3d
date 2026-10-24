# Ring-First VNext：点云过滤与开放表面重建

## 1. 结论与人工摘要

本轮完整处理8组9视频，恢复原始像素点身份，完成SOR/ROR、受限多视角与2.5D邻接对照。过滤使均值略降，却损失GT支持面；完美合成几何经2.5D后可见覆盖从99.60%降至95.07%。004多视角只删6点，其中5点受Oracle GT支持；005不删。现阶段不将任何过滤分支默认接入主线，保留原始HERO点和开放面。

**决策：本轮没有证明“前移点云清理”比历史Mesh后处理更可靠。** SOR/ROR只作密度诊断；P3保留模型一致性/冲突状态，暂不自动删点；P4暴露了单纯距离阈值对真实倾斜/高曲率面过于激进。不要继续围绕MAE或视觉整洁调阈值。本轮结束即停止。

独立目录`ring_anchor_3d/experiments/pointcloud_surface_filter_vnext/`；只新建本报告一份Markdown。未训练、未新增推理/匹配器、未改相机/Ring尺寸/DXY-MID、未跨视频配准、未覆盖或删除历史资产。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 8独立测量组、9视频；G01两视频同组且保持独立坐标 |
| 本算法独立成功 | P0/P1/P2/P4均8/8组数值输出；P3/P5仅G01的2/9视频可评价，统计1/8组；数值输出不等于清理正确 |
| 本算法失败 | 54个视频×方法组合中40数值输出、14个NOT_EVALUABLE，程序FAILED=0；G04的GT分数NaN；真实独立GT坐标8/8缺失；预设DEV安全门槛全部候选失败 |
| 历史测量值回退 | 0。按用户授权复用冻结HERO深度、相机、Mask，历史测量直径/别路线数值未用于补预测 |
| 失败组及具体原因 | 全部组保留；G02—G08多参考证据不足；G03/G05/G07相机筛选0/8；G04无GT；SOR/ROR删真点，P4删真面，详见第8节及`metrics/failure_ledger.csv` |
| 最终统计样本 | 7/8组可做冻结Oracle形状诊断；原始完整分母8组；P3/P5只有1组，不与7组全均值直接比较；独立真实坐标精度0/8可评分 |
| 是否使用GT选择算法 | 否。开发只看采样密度和保留率，正式点/面/状态/SHA在GT评分前冻结；沿用历史P0的H，所有分支共享，不重新ICP；历史GT暴露已说明 |

## 2. 冻结输入、分组和算法继承

| 资产ID | 实际视频 | 形态/环 | 原划分 | 参考索引/raw | 筛选相机 | 多参考深度 | P3/P5可评价 | 同名可信GT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G01_004 | 004 | Ip R10 | DEV | 8/676 | 16/16 | 2 | True | 有，Oracle映射 |
| G01_005 | 005 | Ip R10 | DEV | 10/459 | 15/22 | 2 | True | 有，Oracle映射 |
| G02_004 | 004 | Ip R10 | DEV | 4/570 | 2/8 | 0 | False | 有，Oracle映射 |
| G03_004 | 004 | Ip R10 | DEV | 4/554 | 0/8 | 0 | False | 有，Oracle映射 |
| G04_004 | 004 | Is R10 | VALIDATION | 4/437 | 1/8 | 0 | False | 缺失，NaN |
| G05_004 | 004 | Is R10 | VALIDATION | 4/542 | 0/8 | 0 | False | 有，Oracle映射 |
| G06_004 | 004 | IIa R10 | TEST | 4/596 | 4/8 | 0 | False | 有，Oracle映射 |
| G07_004 | 004 | Is R5 | VALIDATION | 4/369 | 0/8 | 0 | False | 有，Oracle映射 |
| G08_004 | 005 | IIa R10 | TEST | 4/669 | 2/8 | 0 | False | 有，Oracle映射 |


G08资产`G08_004`实际来自005，沿用上一轮来源绑定，未因名字换帧。G01_004参考8按实际冻结缓存/来源清单绑定raw676，不把旧文字“raw674”直接替代像素。G01_005参考索引10/raw459。004/005未合并；不使用未来保留组。本轮没有为了好看增加参考视角：004固定3/8/13，005固定raw57/459/745；所有辅助相机与深度在处理前核对已有质量标记。

继承`multigroup_surface_gt_vnext/inputs/surfaces.json`中9份原始深度，非从Mesh采样伪造原始点；G01多参考深度复用`independent_confidence_fusion_v1/depths/`。完整入口：[输入帧与来源](inputs/entries.json)、[输入配置](config.json)、[原始请求](inputs/USER_REQUEST.txt)。同名GT7组全部按人工确认为可信形状；G04不替换其他模型。

HERO、U-Net/Ring处理、Ring-First冻结相机均未改动。K640×360：fx=fy490、cx319.5、cy179.5；深度为相机轴向Z毫米；`Pworld=Rc2w (Z K^-1 [u,v,1]) + C`。PLY/NPZ毫米；GLB除1000转米。R10主半径5.6mm、R5为3.1mm；两者截面半径0.6mm不变。环平面仅坐标基准，非息肉基底。

## 3. 原始反投影审计与永久像素身份

原始点以`(group_id, actual_video_id, reference_frame_id, u, v)`确定永久身份。所有Polyp Mask像素保留raw_depth、XYZ、Mask、到可见边界及Ring像素距离、相机版本/矩阵、RGB源哈希、原Mesher接受面标记。无效Z单独INVALID，不通过删Mask掩盖失败。深度反投影后未获三角面支持的点仍完整保存，过滤前不丢失。

| 资产 | 有效原始点 | P0有面支持点 | 无面原始点 | 历史/重生成面 | 最大坐标差 mm | 1NN中位 mm | 1NN p95 mm | 近Ring中位 mm | 边缘中位 mm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G01_004 | 14029 | 13771 | 258 | 26621/26621 | 0.000000520 | 0.082 | 0.148 | 0.087 | 0.101 |
| G01_005 | 12775 | 12444 | 331 | 24030/24030 | 0.000000534 | 0.078 | 0.126 | 0.086 | 0.089 |
| G02_004 | 3885 | 3874 | 11 | 7504/7504 | 0.000000125 | 0.058 | 0.080 | NaN | 0.061 |
| G03_004 | 26966 | 26320 | 646 | 51525/51525 | 0.000001738 | 0.096 | 0.169 | 0.097 | 0.141 |
| G04_004 | 3663 | 3663 | 0 | 7097/7097 | 0.000000237 | 0.072 | 0.102 | 0.106 | 0.087 |
| G05_004 | 31600 | 31477 | 123 | 61796/61796 | 0.000000533 | 0.067 | 0.100 | 0.074 | 0.075 |
| G06_004 | 9282 | 9282 | 0 | 17829/17829 | 0.000000324 | 0.080 | 0.088 | 0.078 | 0.078 |
| G07_004 | 19784 | 19718 | 66 | 38518/38518 | 0.000000371 | 0.059 | 0.098 | 0.059 | 0.062 |
| G08_004 | 19631 | 19601 | 30 | 38284/38284 | 0.000000565 | 0.089 | 0.136 | 0.091 | 0.090 |


9/9输入通过历史三角形集合等价检查；坐标差为PLY浮点存储量级，最大低于1e-5mm。新P0保留全部有效像素，历史部分Mesh曾去除无引用顶点；这是**点身份数量差异而非新增几何恢复**。历史基线不覆盖。所有对照沿用原`depth_mesh`：像素方格两种固定三角形、Polyp Mask、有效Z、面内最大Z跳变0.75mm。新P0的GT采样种子20261024，上一轮为20261023，数值采样误差可略变；不得把这种变化称改进。

永久记录：`points/*_RAW_PIXEL_IDENTITIES.npz`；后续保留/拒绝掩码与状态为`points/*_FILTER_STATES.npz`；每个Mesh顶点/面回溯原点ID见`provenance/*_MESH_SOURCE.npz`。任何被拒绝身份均未永久删除。

## 4. 成熟过滤、多视角及像素邻接方法

### 4.1 SOR/ROR开发对照与冻结

调用已有Open3D0.19的`remove_statistical_outlier`和`remove_radius_outlier`，不自写替代滤波器。DEV沿用Ip三个组的四份深度图：每图内部非边缘/非Ring像素的1NN中位，跨图取中位，得到`s_DEV=0.078607mm`。这是开发输入采样标尺，不把4图当4独立测量组。测试组不单独重选半径，统一使用同一mm物理半径。

候选预先固定SOR(16,2)/(24,3)/(32,4)；ROR半径3s/4s/5s，对应最低邻居6/8/8。选择仅看开发各视频拒绝≤5%、边缘保留≥99%、近Ring保留≥99%；符合者选拒绝最多，无符合者选拒绝最少并明确**未通过DEV安全门槛**。绝不因结果失败再放松门槛：

| 方法 | 预设参数 | DEV平均拒绝% | 4视频边缘保留最小% | 4视频近Ring保留最小% | 预设门槛通过 |
| --- | --- | --- | --- | --- | --- |
| SOR | {"nb_neighbors": 16, "std_ratio": 2.0} | 2.560 | 80.011 | 87.845 | False |
| SOR | {"nb_neighbors": 24, "std_ratio": 3.0} | 1.539 | 83.113 | 92.265 | False |
| SOR | {"nb_neighbors": 32, "std_ratio": 4.0} | 1.100 | 85.009 | 94.645 | False |
| ROR | {"radius": 0.23582120488955766, "nb_points": 6} | 8.393 | 24.354 | 74.463 | False |
| ROR | {"radius": 0.31442827318607686, "nb_points": 8} | 5.256 | 35.382 | 83.978 | False |
| ROR | {"radius": 0.39303534148259606, "nb_points": 8} | 2.982 | 49.684 | 90.650 | False |


最终SOR为邻居32、std_ratio4；ROR为半径0.393035mm、nb_points8。两者独立，不串联。不同组1NN及Ring/边缘的密度差异已在第3节给出；固定半径/全局统计对细小结构本就有风险。没有通过门槛，因此后续仅作失败基线，不能自动部署。

### 4.2 多视角几何（只对G01可评价）

固定相机，将每个源点投到其他同视频深度图；用最近像素索引对比轴向Z，记录`r=Zprojected-Dj`、相机基线、点视差、Mask类别、源深度有效性、质量标记。只接受参考相机和至少2个辅助相机通过既有筛选且点视差≥2°的证据；几何阈值为`max(0.5mm, 0.01 Dj)`。相机标记是既有独立残差筛选，不是相机GT认证。

当r>阈值，另一个预测表面在前：归为正常遮挡可能/UNKNOWN，不直接删点。当r<−阈值，标为前方冲突；Ring像素使用完整torus首交Z作前方/后方检查，Ring后方保留UNKNOWN，不将整个环平面作深度。背景/其他身份也不无条件雕刻其后方空间；无深度、出界、相机不可靠、视差不足分别记录事件。

逐点SUPPORTED需2个辅助相机同意且无前方冲突；WEAK至少一个同意；CONFLICT至少一个前方冲突；无证据/遮挡为UNKNOWN；INVALID仅无效数值。只有≥2个前方冲突、没有同意或后方遮挡、稳健非遮挡残差中位<−0.5mm，且参考Mask距离可见边界>2px时，P3才拒绝点。中位/MAD、完整视图残差及事件均保存。

全部同视频HERO深度属于一个相关模型块，逐点总权重≤1；绝不把两次预测当两个独立GT样本。实际删除规则仍使用两相机几何共识，因此只是**相关模型条件下的候选错误证据**，GT结果显示它并不保证真实错误。复用既有稀疏三角化点仅输出附近距离作辅助审计，未直接替换深度、不影响保留Mask；轨迹仍受原相机误差影响，不当GT。

| 资产 | SUPPORTED | CONFLICT | WEAK | UNKNOWN | INVALID | 可评价 | 最大相关模型块数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G01_004 | 703 | 129 | 5846 | 7351 | 0 | True | 1 |
| G01_005 | 4836 | 271 | 5085 | 2583 | 0 | True | 1 |
| G02_004 | 0 | 0 | 0 | 3885 | 0 | False | 0 |
| G03_004 | 0 | 0 | 0 | 26966 | 0 | False | 0 |
| G04_004 | 0 | 0 | 0 | 3663 | 0 | False | 0 |
| G05_004 | 0 | 0 | 0 | 31600 | 0 | False | 0 |
| G06_004 | 0 | 0 | 0 | 9282 | 0 | False | 0 |
| G07_004 | 0 | 0 | 0 | 19784 | 0 | False | 0 |
| G08_004 | 0 | 0 | 0 | 19631 | 0 | False | 0 |


CONFLICT点不全被删除：004为129个、005为271个，严格P3只删6/0个。其他7视频不具足够深度/相机证据，P3/P5记NOT_EVALUABLE；其原始像素状态UNKNOWN完整保留。NPZ的keep_P3/keep_P5在不可评价组表示“未获反证、保留”，**不是可运行的P3/P5预测成绩**，评价表和Mesh均不回填P0。

### 4.3 2.5D邻接和统一Mesh

P4保持所有有效点。对原像素水平/垂直/固定对角邻接，计算3D长度L；阈值`max(0.15mm, 4·mean(Z)·||Δu/fx,Δv/fy||)`，任何一条边超限则禁止该三角形。仍先执行所有分支共有的原Mesher0.75mm轴向跳变限制。此阈值只作固定试验，**不假设长边一定是噪声**：真实倾斜面或轮廓处斜率也会放大L，GT-clean对照就是其反例。

按原始像素邻接而非GT，将超阈值边分为近Ring（≤5px）、其他可见边缘（≤2px）或内部深度不连续UNKNOWN。以下是邻接边数量，不能与拒绝三角面数混淆；归类不证明Mask误分割，也不证明几何接触。

| 资产 | 近Ring异常邻接边 | 其他可见边缘/Mask不确定邻接 | 内部深度不连续UNKNOWN |
| --- | --- | --- | --- |
| G01_004 | 462 | 595 | 816 |
| G01_005 | 953 | 100 | 780 |
| G02_004 | 0 | 163 | 26 |
| G03_004 | 296 | 1766 | 637 |
| G04_004 | 0 | 41 | 20 |
| G05_004 | 501 | 406 | 273 |
| G06_004 | 0 | 0 | 0 |
| G07_004 | 7 | 342 | 387 |
| G08_004 | 92 | 141 | 27 |


P0原始；P1独立SOR；P2独立ROR；P3多视角候选删除；P4像素邻接仅禁面；P5=P3再加同一邻接。不腐蚀Polyp Mask、不重采样平滑、不Poisson、不补洞、不闭合。可见边缘2px保护只用于P3删点，SOR/ROR原样执行，以揭示真实风险；P1/P2可能删去多视角UNKNOWN点，作为独立统计失败基线明确保留，不能包装为通过多视角验证的删除。

所有40个数值输出又执行上一轮同一冻结B1保守拓扑：去重复/退化/无引用、非流形Split Vertices、零位移拆点。格式上压紧滤镜遗留孤立顶点缓冲，所有面逐个映射到原始像素，未加入新几何。RAW与B1分别保存，排除不同后处理造成的混淆。

## 5. 实际运行规模与完整结果

| 输入 | P0原点 | P1删点 | P2删点 | P3删点 | P4删点 | P4拒绝面 | P5删点 | P5拒绝面 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G01_004 | 14029 | 156 | 436 | 6 | 0 | 1290 | 6 | 1272 |
| G01_005 | 12775 | 220 | 465 | 0 | 0 | 1085 | 0 | 1085 |
| G02_004 | 3885 | 23 | 21 | NaN | 0 | 158 | NaN | NaN |
| G03_004 | 26966 | 263 | 1251 | NaN | 0 | 1205 | NaN | NaN |
| G04_004 | 3663 | 42 | 0 | NaN | 0 | 92 | NaN | NaN |
| G05_004 | 31600 | 298 | 154 | NaN | 0 | 1002 | NaN | NaN |
| G06_004 | 9282 | 38 | 0 | NaN | 0 | 0 | NaN | NaN |
| G07_004 | 19784 | 169 | 88 | NaN | 0 | 655 | NaN | NaN |
| G08_004 | 19631 | 132 | 115 | NaN | 0 | 287 | NaN | NaN |


总计54个视频×方法条件：40数值输出、14 NOT_EVALUABLE；全部9输入做P0/P1/P2/P4。没有重新HERO推理，没有新增参考视角或GPU训练。`metrics/FILTER_RESULTS.json`含每个分支的原点/保留点/拒绝点、环邻近/边缘保留率、面拓扑。数值输出与通过几何验收分开。

### 5.1 GT评分与防污染

同名Blender模型可信，但真实预测到GT的独立位姿映射仍未知。**只读取上一轮从原P0得到的冻结OracleH；P0—P5以及RAW/B1共用同一视频H，完全不运行新ICP、尺度拟合或GT校正点。** P0与历史Mesh先通过几何等价核验。评分模式全为ORACLE_ALIGNED_DIAGNOSTIC；真实端到端绝对误差与真实Acquisition Visibility均NaN。

原组划分沿用Ip DEV、Is VALIDATION、IIa TEST，相关CAD族不跨侧；G01两视频同侧。过滤阶段读取防火墙拒绝`.blend`、`gt_mapping`、`private_gt`。输入候选配置、DEV观测选择、正式点掩码/状态/Mesh/源码先冻结，之后独立评价才读GT：冻结UTC`2026-10-24T02:05:47.974295+00:00`。证据：[正式预测SHA256](provenance/FORMAL_PREDICTIONS_BEFORE_GT.json)、[开发参数冻结](provenance/PARAMETERS_BEFORE_GT.json)、[GT来源及H哈希](metrics/GT_INPUT_SOURCES.json)。历史报告已经暴露过GT，本轮不是全新盲测；只主张当前固定预测未按本轮GT结果调参。

GT点到连续三角面；预测面12000物理面积均匀点、GT完整面20000点，固定种子20261024。好点/好面定义距离GT≤0.25mm；完整GT覆盖分母一直20000，保留点数变化不能缩分母。“原好面丢失”对同一批P0面积采样作当前Mesh距离>1e-4mm判定，不只看当前剩余面的均值。点误差含原来没三角面的像素，表面误差与点误差分开。

| 资产 | 方法 | 运行状态 | 点MAE mm | 面MAE mm | 面p95 mm | 完整GT覆盖% | 好点误删% | 原好面丢失% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G01_004 | P0 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.367 | 0.315 | 1.306 | 22.075 | 0.000 | 0.000 |
| G01_004 | P1 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.358 | 0.316 | 1.347 | 22.075 | 0.611 | 0.000 |
| G01_004 | P2 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.353 | 0.311 | 1.309 | 21.265 | 1.721 | 3.833 |
| G01_004 | P3 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.367 | 0.312 | 1.308 | 22.020 | 0.057 | 0.474 |
| G01_004 | P4 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.367 | 0.310 | 1.344 | 19.535 | 0.000 | 14.075 |
| G01_004 | P5 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.367 | 0.320 | 1.389 | 19.525 | 0.057 | 14.126 |
| G01_005 | P0 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.230 | 0.243 | 0.632 | 15.990 | 0.000 | 0.000 |
| G01_005 | P1 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.223 | 0.241 | 0.629 | 15.930 | 0.494 | 0.176 |
| G01_005 | P2 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.221 | 0.228 | 0.609 | 14.940 | 1.675 | 4.366 |
| G01_005 | P3 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.230 | 0.243 | 0.632 | 15.990 | 0.000 | 0.000 |
| G01_005 | P4 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.230 | 0.212 | 0.524 | 13.680 | 0.000 | 12.760 |
| G01_005 | P5 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.230 | 0.212 | 0.524 | 13.680 | 0.000 | 12.760 |
| G02_004 | P0 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.109 | 0.104 | 0.258 | 37.255 | 0.000 | 0.000 |
| G02_004 | P1 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.109 | 0.102 | 0.257 | 35.630 | 0.528 | 2.750 |
| G02_004 | P2 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.109 | 0.103 | 0.258 | 35.745 | 0.472 | 2.255 |
| G02_004 | P3 | NOT_EVALUABLE | NaN | NaN | NaN | NaN | NaN | NaN |
| G02_004 | P4 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.109 | 0.102 | 0.259 | 32.760 | 0.000 | 11.620 |
| G02_004 | P5 | NOT_EVALUABLE | NaN | NaN | NaN | NaN | NaN | NaN |
| G03_004 | P0 | NUMERIC_OUTPUT_NOT_CERTIFIED | 1.144 | 1.603 | 9.605 | 15.925 | 0.000 | 0.000 |
| G03_004 | P1 | NUMERIC_OUTPUT_NOT_CERTIFIED | 1.045 | 1.603 | 9.605 | 15.925 | 0.077 | 0.000 |
| G03_004 | P2 | NUMERIC_OUTPUT_NOT_CERTIFIED | 1.002 | 1.566 | 9.599 | 14.995 | 2.010 | 5.815 |
| G03_004 | P3 | NOT_EVALUABLE | NaN | NaN | NaN | NaN | NaN | NaN |
| G03_004 | P4 | NUMERIC_OUTPUT_NOT_CERTIFIED | 1.144 | 1.631 | 9.778 | 15.085 | 0.000 | 6.415 |
| G03_004 | P5 | NOT_EVALUABLE | NaN | NaN | NaN | NaN | NaN | NaN |
| G04_004 | P0 | NUMERIC_OUTPUT_NOT_CERTIFIED | NaN | NaN | NaN | NaN | NaN | NaN |
| G04_004 | P1 | NUMERIC_OUTPUT_NOT_CERTIFIED | NaN | NaN | NaN | NaN | NaN | NaN |
| G04_004 | P2 | NUMERIC_OUTPUT_NOT_CERTIFIED | NaN | NaN | NaN | NaN | NaN | NaN |
| G04_004 | P3 | NOT_EVALUABLE | NaN | NaN | NaN | NaN | NaN | NaN |
| G04_004 | P4 | NUMERIC_OUTPUT_NOT_CERTIFIED | NaN | NaN | NaN | NaN | NaN | NaN |
| G04_004 | P5 | NOT_EVALUABLE | NaN | NaN | NaN | NaN | NaN | NaN |
| G05_004 | P0 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.633 | 0.654 | 1.390 | 6.755 | 0.000 | 0.000 |
| G05_004 | P1 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.629 | 0.650 | 1.376 | 6.610 | 0.508 | 1.233 |
| G05_004 | P2 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.631 | 0.659 | 1.395 | 6.705 | 0.246 | 0.617 |
| G05_004 | P3 | NOT_EVALUABLE | NaN | NaN | NaN | NaN | NaN | NaN |
| G05_004 | P4 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.633 | 0.632 | 1.351 | 6.525 | 0.000 | 3.740 |
| G05_004 | P5 | NOT_EVALUABLE | NaN | NaN | NaN | NaN | NaN | NaN |
| G06_004 | P0 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.102 | 0.097 | 0.293 | 26.920 | 0.000 | 0.000 |
| G06_004 | P1 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.101 | 0.094 | 0.284 | 26.860 | 0.190 | 0.393 |
| G06_004 | P2 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.102 | 0.097 | 0.293 | 26.920 | 0.000 | 0.000 |
| G06_004 | P3 | NOT_EVALUABLE | NaN | NaN | NaN | NaN | NaN | NaN |
| G06_004 | P4 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.102 | 0.097 | 0.293 | 26.920 | 0.000 | 0.000 |
| G06_004 | P5 | NOT_EVALUABLE | NaN | NaN | NaN | NaN | NaN | NaN |
| G07_004 | P0 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.200 | 0.238 | 0.676 | 18.600 | 0.000 | 0.000 |
| G07_004 | P1 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.199 | 0.231 | 0.639 | 17.780 | 0.757 | 1.821 |
| G07_004 | P2 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.199 | 0.236 | 0.655 | 18.050 | 0.447 | 0.897 |
| G07_004 | P3 | NOT_EVALUABLE | NaN | NaN | NaN | NaN | NaN | NaN |
| G07_004 | P4 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.200 | 0.225 | 0.605 | 17.255 | 0.000 | 4.838 |
| G07_004 | P5 | NOT_EVALUABLE | NaN | NaN | NaN | NaN | NaN | NaN |
| G08_004 | P0 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.533 | 0.590 | 1.458 | 7.145 | 0.000 | 0.000 |
| G08_004 | P1 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.527 | 0.570 | 1.327 | 7.055 | 0.189 | 0.856 |
| G08_004 | P2 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.528 | 0.578 | 1.368 | 7.040 | 0.208 | 0.856 |
| G08_004 | P3 | NOT_EVALUABLE | NaN | NaN | NaN | NaN | NaN | NaN |
| G08_004 | P4 | NUMERIC_OUTPUT_NOT_CERTIFIED | 0.533 | 0.579 | 1.390 | 7.005 | 0.000 | 2.140 |
| G08_004 | P5 | NOT_EVALUABLE | NaN | NaN | NaN | NaN | NaN | NaN |


表中NOT_EVALUABLE均保留，G04因缺GT所有GT字段NaN。GT-supported标记基于冻结Oracle位置，不是无误差的真实材料点身份；这些误删率是Oracle条件诊断。所有B1对应分数另存完整108行`metrics/GT_EVALUATION.csv`，不隐藏失败。RAW/B1表面几何相同，不把拓扑处理误称GT精度增益。

### 5.2 按独立测量组配对统计

先对G01两视频等权平均，再对独立组统计。P0/P1/P2/P4的GT共同组为G01/G02/G03/G05/G06/G07/G08，分母7/8；P3/P5只有G01，不能拿其MAE同7组均值直接比。“p95”列为各组内表面误差p95的组间平均，不是伪造全体独立点分布p95。

| 分支 | 数值成功/目标组 | Oracle组数 | 面MAE mm | 组内p95均值 mm | 点MAE mm | 完整GT覆盖% | 原好面丢失% | 配对MAE差 mm | 配对覆盖差pp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0 | 8/8 | 7 | 0.509 | 2.093 | 0.431 | 18.805 | 0.000 | 0.000 | 0.000 |
| P1 | 8/8 | 7 | 0.504 | 2.068 | 0.414 | 18.409 | 1.020 | -0.005 | -0.396 |
| P2 | 8/8 | 7 | 0.501 | 2.075 | 0.408 | 18.223 | 2.077 | -0.008 | -0.582 |
| P3 | 1/8 | 1 | 0.277 | 0.970 | 0.299 | 19.005 | 0.237 | -0.002 | -0.027 |
| P4 | 8/8 | 7 | 0.504 | 2.087 | 0.431 | 17.451 | 6.024 | -0.006 | -1.354 |
| P5 | 1/8 | 1 | 0.266 | 0.957 | 0.299 | 16.602 | 13.443 | -0.013 | -2.430 |


七组配对P1：MAE改善约0.00515mm，完整GT覆盖下降0.396个百分点；P2改善0.00822mm，下降0.582个百分点；P4改善0.00558mm，下降1.354个百分点、GT支持原面平均丢失6.024%。**均不满足Accuracy与Coverage同时改善的无条件成功标准。** 这些MAE小差异还受面积采样误差影响，不能作显著性声明。P3在G01仅改善0.00157mm，覆盖下降0.0275个百分点；004删6点中5个GT好点、1个坏点（删除精度16.7%），不存在独立优越性证据。

中位绝对相对误差在本任务定义为“原点到GT的中位距离 / GT完整bbox对角线”，仅归一化形状距离，不是Dxy测量ARE。P0/P1/P2/P4的组间中位分别约0.826%/0.818%/0.811%/0.826%；最坏表面点仍约13.2mm。完整最大误差、逐组p95、中位及区域误删均保留JSON。未做或优化息肉直径。

| 子集 | 分支 | 可评分独立组 | 面MAE均值 mm | 完整GT覆盖均值% |
| --- | --- | --- | --- | --- |
| Ip | P0 | 3 | 0.662 | 24.071 |
| Ip | P1 | 3 | 0.661 | 23.519 |
| Ip | P2 | 3 | 0.646 | 22.948 |
| Ip | P4 | 3 | 0.665 | 21.484 |
| Is | P0 | 2 | 0.446 | 12.678 |
| Is | P1 | 2 | 0.441 | 12.195 |
| Is | P2 | 2 | 0.447 | 12.377 |
| Is | P4 | 2 | 0.428 | 11.890 |
| IIa | P0 | 2 | 0.343 | 17.032 |
| IIa | P1 | 2 | 0.332 | 16.957 |
| IIa | P2 | 2 | 0.337 | 16.980 |
| IIa | P4 | 2 | 0.338 | 16.962 |
| R5 | P0 | 1 | 0.238 | 18.600 |
| R5 | P1 | 1 | 0.231 | 17.780 |
| R5 | P2 | 1 | 0.236 | 18.050 |
| R5 | P4 | 1 | 0.225 | 17.255 |
| R10 | P0 | 6 | 0.555 | 18.839 |
| R10 | P1 | 6 | 0.550 | 18.514 |
| R10 | P2 | 6 | 0.545 | 18.251 |
| R10 | P4 | 6 | 0.550 | 17.484 |


R5只有G07一组、IIa两组，样本不足且形态/尺度混杂，不能归因Ring规格。较好G06几乎不需ROR/P4处理；错误较大的G03仍保留深度错层，单纯密度滤波不能修复稠密系统偏差。

### 5.3 边缘、近Ring和Ip细结构风险

| 资产 | 方法 | 点删除中GT错误点比例% | GT边缘好点误删% | 近Ring好点误删% | Ip下1/4好点误删代理% |
| --- | --- | --- | --- | --- | --- |
| G01_004 | P1 | 65.385 | 8.033 | 0.264 | 0.000 |
| G01_004 | P2 | 65.138 | 18.837 | 1.671 | 0.000 |
| G01_004 | P3 | 16.667 | 0.000 | 0.000 | 0.000 |
| G01_005 | P1 | 81.364 | 3.846 | 3.088 | 0.000 |
| G01_005 | P2 | 70.108 | 6.250 | 5.677 | 0.776 |
| G01_005 | P3 | NaN | 0.000 | 0.000 | 0.000 |
| G02_004 | P1 | 17.391 | 6.397 | NaN | 0.458 |
| G02_004 | P2 | 19.048 | 5.724 | NaN | 0.458 |
| G03_004 | P1 | 95.817 | 2.644 | 0.000 | NaN |
| G03_004 | P2 | 76.978 | 43.269 | 4.037 | NaN |
| G05_004 | P1 | 88.926 | 15.441 | 4.665 | NaN |
| G05_004 | P2 | 89.610 | 11.029 | 2.332 | NaN |
| G06_004 | P1 | 57.895 | 1.869 | 0.877 | NaN |
| G06_004 | P2 | NaN | 0.000 | 0.000 | NaN |
| G07_004 | P1 | 37.870 | 10.215 | 0.000 | NaN |
| G07_004 | P2 | 29.545 | 6.586 | 0.000 | NaN |
| G08_004 | P1 | 92.424 | 5.114 | 2.381 | NaN |
| G08_004 | P2 | 90.435 | 6.250 | 2.679 | NaN |


Ip的GT nativeZ下1/4是形态代理，不是人工确认的蒂部；Is/IIa不强行定义蒂部。P1/P2可删掉GT支持边缘及近Ring点，005 ROR下1/4好点也有丢失。P3虽保护参考边缘，仍会误删内部GT支持点，说明错误源可能是相机/相关HERO深度，而不是边缘本身。二维Mask接触不当作物理接触。

## 6. 拓扑、孔洞和碎片

| 资产 | 分支 | 面数 | 连通分量 | 非流形边RAW/B1 | 重复像素三角形 | 边界环数 | 新内部缺口代理数 | 丢失原有面像素 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G01_004 | P0 | 26621 | 8 | 0/0 | 0 | 4 | 0 | 0 |
| G01_004 | P1 | 26617 | 7 | 0/0 | 0 | 3 | 0 | 6 |
| G01_004 | P2 | 26323 | 2 | 0/0 | 0 | 1 | 22 | 194 |
| G01_004 | P3 | 26598 | 8 | 0/0 | 0 | 4 | 2 | 9 |
| G01_004 | P4 | 25331 | 14 | 0/0 | 0 | 4 | 6 | 603 |
| G01_004 | P5 | 25326 | 14 | 0/0 | 0 | 4 | 6 | 605 |
| G01_005 | P0 | 24030 | 3 | 0/0 | 0 | 1 | 0 | 0 |
| G01_005 | P1 | 24024 | 3 | 0/0 | 0 | 1 | 2 | 4 |
| G01_005 | P2 | 23681 | 8 | 0/0 | 0 | 8 | 18 | 178 |
| G01_005 | P3 | 24030 | 3 | 0/0 | 0 | 1 | 0 | 0 |
| G01_005 | P4 | 22945 | 11 | 0/0 | 0 | 5 | 3 | 563 |
| G01_005 | P5 | 22945 | 11 | 0/0 | 0 | 5 | 3 | 563 |
| G02_004 | P0 | 7504 | 1 | 0/0 | 0 | 0 | 0 | 0 |
| G02_004 | P1 | 7479 | 2 | 0/0 | 0 | 0 | 0 | 13 |
| G02_004 | P2 | 7483 | 1 | 0/0 | 0 | 0 | 0 | 11 |
| G02_004 | P4 | 7346 | 3 | 0/0 | 0 | 1 | 0 | 61 |
| G03_004 | P0 | 51525 | 4 | 0/0 | 0 | 4 | 0 | 0 |
| G03_004 | P1 | 51525 | 4 | 0/0 | 0 | 4 | 0 | 0 |
| G03_004 | P2 | 50333 | 4 | 0/0 | 0 | 2 | 16 | 607 |
| G03_004 | P4 | 50320 | 3 | 0/0 | 0 | 7 | 26 | 570 |
| G04_004 | P0 | 7097 | 1 | 0/0 | 0 | 1 | 0 | 0 |
| G04_004 | P1 | 6992 | 1 | 0/0 | 0 | 1 | 2 | 44 |
| G04_004 | P2 | 7097 | 1 | 0/0 | 0 | 1 | 0 | 0 |
| G04_004 | P4 | 7005 | 5 | 0/0 | 0 | 1 | 2 | 25 |
| G05_004 | P0 | 61796 | 5 | 0/0 | 0 | 2 | 0 | 0 |
| G05_004 | P1 | 61480 | 2 | 0/0 | 0 | 2 | 0 | 176 |
| G05_004 | P2 | 61710 | 3 | 0/0 | 0 | 1 | 0 | 52 |
| G05_004 | P4 | 60794 | 8 | 0/0 | 0 | 4 | 2 | 464 |
| G06_004 | P0 | 17829 | 2 | 0/0 | 0 | 2 | 0 | 0 |
| G06_004 | P1 | 17757 | 2 | 0/0 | 0 | 2 | 0 | 38 |
| G06_004 | P2 | 17829 | 2 | 0/0 | 0 | 2 | 0 | 0 |
| G06_004 | P4 | 17829 | 2 | 0/0 | 0 | 2 | 0 | 0 |
| G07_004 | P0 | 38518 | 4 | 0/0 | 0 | 2 | 0 | 0 |
| G07_004 | P1 | 38333 | 2 | 0/0 | 0 | 2 | 5 | 107 |
| G07_004 | P2 | 38457 | 4 | 0/0 | 0 | 4 | 3 | 36 |
| G07_004 | P4 | 37863 | 6 | 0/0 | 0 | 5 | 3 | 307 |
| G08_004 | P0 | 38284 | 3 | 0/0 | 0 | 1 | 0 | 0 |
| G08_004 | P1 | 38090 | 2 | 0/0 | 0 | 2 | 0 | 102 |
| G08_004 | P2 | 38119 | 2 | 0/0 | 0 | 2 | 0 | 87 |
| G08_004 | P4 | 37997 | 4 | 0/0 | 0 | 2 | 0 | 132 |


“新内部缺口”是P0原有面支持源像素在处理后失去所有面、且不靠原Mask/Ring边缘的连通区域代理；闭合边界环亦只是网格边界连通图中degree2循环，**不等于解剖孔洞个数**。P4在G03形成26个内部源像素缺口代理；004/005为6/3个。所有点虽被保留，面覆盖仍可损失，这是不能只汇报“点保留100%”的原因。

本轮原始单参考Mesh没有历史C融合焊接的586/1993条非流形边；P0—P5此处多数非流形0，不能将输入差别当作新算法修复能力。B1用于所有方法的统一对照，顶点/面仍有完整来源映射。像素邻接使三角面局限于同一Mask内，无跨Ring遮挡补面；过滤可增加新边界和碎片，不能因为点数减少就宣称更连续。

与上一轮Mesh后清理的关系：相同原始输入的保守B1基本只整理拓扑而不改几何；本轮P1/P2/P4可改变预测有效域，但伴随误删和缺口。目前没有证明前移清理更可靠，不以两个Mesh外观比较代替同原始GT分母。

## 7. 独立Blender GT-input受控测试

不新建/渲染场景，直接用既有V4参考8和源0/14的GT相机、深度、实例Mask，标为**ORACLE_DIAGNOSTIC_GT_INPUT / INDEPENDENT_FRAME**。过滤参数与真实组完全相同；受控结果不回传选择任何参数。

两输入：CLEAN完全正确几何；INJECTED在同一Mask中加64个分散内点和64像素连续块，各沿相机Z后移3mm，再对64个边缘像素后移1.5mm，并把24边缘输入置NaN。所有身份和注入标记保存，无效点状态INVALID；不使用注入标签筛选点。注入方向固定为后方错误，不能把本实验推广为所有符号噪声类型。

| 受控输入 | 方法 | 点拒绝数 | 点MAE mm | 面MAE mm | 实际可见GT覆盖% | GT好点误删% | 原好面丢失% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CLEAN | P0 | 0 | 0.001 | 0.001 | 99.597 | 0.000 | 0.000 |
| CLEAN | P1 | 172 | 0.001 | 0.001 | 97.839 | 1.308 | 4.200 |
| CLEAN | P2 | 100 | 0.001 | 0.001 | 98.681 | 0.761 | 2.883 |
| CLEAN | P3 | 0 | 0.001 | 0.001 | 99.597 | 0.000 | 0.000 |
| CLEAN | P4 | 0 | 0.001 | 0.001 | 95.073 | 0.000 | 10.650 |
| CLEAN | P5 | 0 | 0.001 | 0.001 | 95.073 | 0.000 | 10.650 |
| INJECTED | P0 | 0 | 0.024 | 0.008 | 99.524 | 0.000 | 0.000 |
| INJECTED | P1 | 144 | 0.015 | 0.009 | 99.487 | 0.478 | 0.058 |
| INJECTED | P2 | 233 | 0.015 | 0.008 | 98.462 | 1.156 | 2.464 |
| INJECTED | P3 | 0 | 0.024 | 0.008 | 99.524 | 0.000 | 0.000 |
| INJECTED | P4 | 0 | 0.024 | 0.009 | 94.945 | 0.000 | 8.814 |
| INJECTED | P5 | 0 | 0.024 | 0.009 | 94.945 | 0.000 | 8.814 |


实际参考8可见GT为全20000面积采样中的27.300%，全16视角Acquisition Visibility35.215%；上表恢复率分母始终是参考8真实可见GT，不混成完整GT覆盖。CLEAN P4/P5从99.597%降至95.073%，原GT好面丢失10.65%；即便面MAE从约0.00139mm降至0.00113mm，也应判失败。SOR/ROR在正确几何上同样造成好点和好面丢失。

注入P1/P2降低原始**点**误差0.02408→0.01501/0.01489mm，但表面变化较小，原因之一是原Mesher已拒绝很多孤立异常点的连接，剩余连续错误深度片不能由密度可靠识别。P3不拒绝这类后方错误，因为其他视图有更近表面时按规则保留遮挡UNKNOWN；这是保守可见性处理的局限，不是擅自放宽删除阈值。P4在注入场景仍降低真实可见覆盖约4.58个百分点，未显示优势。

## 8. 失败、限制与可复核证据

1. SOR/ROR的全部DEV候选未通过预设99%边缘/近Ring保留门槛。仍完整运行作负面对照，不追加参数搜索。其输出不得自动当真实表面。
2. P4/P5在GT-clean就损害覆盖；固定3D距离阈值把真实斜面/曲率边缘也当异常，点100%保留并不能防止面误删。当前实现不应默认接入主线。
3. G02—G08仅单参考深度或不可靠相机，不足以多视角删除，P3/P5全部NOT_EVALUABLE；G03/G05/G07质量标记0/8。没有借GT相机补这些真实分支。
4. G01虽然相机/深度足够执行，所有HERO源相关；004拒绝6点中5个被冻结Oracle GT支持。支持/冲突不能自动当GT。无法单凭此试验区分全部误差是相机还是连续深度偏差，因为两者没做新的独立定位GT实验。
5. G04缺确切同名GT，仍参与点密度/保留/孔洞评价，GT NaN不回退。真实8组独立坐标映射均缺，所有真实几何距离仅Oracle诊断，不能声称端到端毫米精度已认证。
6. Ip解剖头/蒂标注缺失，仅用源可见小分量、边缘和GT下1/4代理呈现风险；不能据此宣称蒂部准确保留。GLB不补隐藏面、不计算完整体积。
7. 当前P3使用最近像素深度而非亚像素光度/真实对应验证，残差可受遮挡边界、插值、相机和模型误差影响。无深度/出界/背景像素保留未知，未强行雕去其后体积。
8. 统计单位仅8组，完整GT7组，P3/P5只1组；帧/点不作独立样本。原GT/Hero历史研究结果已暴露，当前隔离不是全新盲测。未根据GT再次选择阈值、参考视角或保留区域。
9. PyMeshLab加载非使用的E57插件有libffi警告；mesh过滤功能实际可用并经过测试。无主环境修复或外部依赖扩张。处理和5个几何单元测试均完成，日志保留。

全部失败与不可用条件：[failure_ledger.csv](metrics/failure_ledger.csv)。没有删文件、自动清理候选或历史数据移动，本轮保留所有输入/失败证据。

## 9. 可视化与三维资产

12张PNG均基于本轮实际算法输出，不使用生成图。固定44mm观察窗口；统计包含全部组和NaN；点云显示最多7000个均匀索引点用于绘图，完整NPZ/PLY/GLB未删点。误差/置信颜色只作标注，不以显示筛除困难预测。

### 1. 8组/9视频的RGB、冻结HERO深度、原始点云和原始Mesher。

![Fig1_all_groups_inputs](visualizations/Fig1_all_groups_inputs.png)

### 2. 原始无面像素、最近邻采样密度和三维深度跳变；它们不是同一个问题。

![Fig2_point_and_depth_failures](visualizations/Fig2_point_and_depth_failures.png)

### 3. 全部视频SOR/ROR删点红色叠加，保留失败与GT缺失组。

![Fig3_SOR_ROR_rejections](visualizations/Fig3_SOR_ROR_rejections.png)

### 4. 004/005可用视角的残差、支持数量和遮挡UNKNOWN。

![Fig4_multiview_depth_consistency](visualizations/Fig4_multiview_depth_consistency.png)

### 5. 原始点的五类状态；SUPPORTED只是模型条件一致性。

![Fig5_layered_point_states](visualizations/Fig5_layered_point_states.png)

### 6. 按原始跳变选取的局部像素三角化示例；P4只禁边、不移动点。

![Fig6_25D_edge_guard](visualizations/Fig6_25D_edge_guard.png)

### 7. P0—P5同尺度/同视角开放面，未执行分支明确NOT_EVALUABLE。

![Fig7_P0_P5_surface_comparison](visualizations/Fig7_P0_P5_surface_comparison.png)

### 8. 004/005 Ring遮挡与蒂部样可见小分量放大，非人工解剖蒂部GT。

![Fig8_Ring_boundary_and_lower_regions](visualizations/Fig8_Ring_boundary_and_lower_regions.png)

### 9. Ip/Is/IIa代表性原始与处理面，统一44mm窗口。

![Fig9_morphology_scale_comparison](visualizations/Fig9_morphology_scale_comparison.png)

### 10. Oracle Accuracy—完整GT Coverage、GT-clean实际可见覆盖及误删。

![Fig10_accuracy_coverage_false_removal](visualizations/Fig10_accuracy_coverage_false_removal.png)

### 11. 8组统计与NaN；004/005先平均后计一组。

![Fig11_all_group_statistics](visualizations/Fig11_all_group_statistics.png)

### 12. 9个P4实验性GLB的实际几何预览；不是认证后的默认结果。

![Fig12_interactive_GLBS](visualizations/Fig12_interactive_GLBS.png)

### 可交互GLB

| GLB | 身份与状态 |
| --- | --- |
| [G01_004_P4_EXPERIMENTAL.glb](scenes/G01_004_P4_EXPERIMENTAL.glb) | Polyp点/P4候选面/KnownRing分层；m；UNVERIFIED / NOT_APPROVED；实际视频004 |
| [G01_005_P4_EXPERIMENTAL.glb](scenes/G01_005_P4_EXPERIMENTAL.glb) | Polyp点/P4候选面/KnownRing分层；m；UNVERIFIED / NOT_APPROVED；实际视频005 |
| [G02_004_P4_EXPERIMENTAL.glb](scenes/G02_004_P4_EXPERIMENTAL.glb) | Polyp点/P4候选面/KnownRing分层；m；UNVERIFIED / NOT_APPROVED；实际视频004 |
| [G03_004_P4_EXPERIMENTAL.glb](scenes/G03_004_P4_EXPERIMENTAL.glb) | Polyp点/P4候选面/KnownRing分层；m；UNVERIFIED / NOT_APPROVED；实际视频004 |
| [G04_004_P4_EXPERIMENTAL.glb](scenes/G04_004_P4_EXPERIMENTAL.glb) | Polyp点/P4候选面/KnownRing分层；m；UNVERIFIED / NOT_APPROVED；实际视频004 |
| [G05_004_P4_EXPERIMENTAL.glb](scenes/G05_004_P4_EXPERIMENTAL.glb) | Polyp点/P4候选面/KnownRing分层；m；UNVERIFIED / NOT_APPROVED；实际视频004 |
| [G06_004_P4_EXPERIMENTAL.glb](scenes/G06_004_P4_EXPERIMENTAL.glb) | Polyp点/P4候选面/KnownRing分层；m；UNVERIFIED / NOT_APPROVED；实际视频004 |
| [G07_004_P4_EXPERIMENTAL.glb](scenes/G07_004_P4_EXPERIMENTAL.glb) | Polyp点/P4候选面/KnownRing分层；m；UNVERIFIED / NOT_APPROVED；实际视频004 |
| [G08_004_P4_EXPERIMENTAL.glb](scenes/G08_004_P4_EXPERIMENTAL.glb) | Polyp点/P4候选面/KnownRing分层；m；UNVERIFIED / NOT_APPROVED；实际视频005 |


GLB固定展示P4只是为了检查本轮点保留与面丢失，不是按GT逐组挑选最优结果；全标EXPERIMENTAL/NOT_APPROVED。保留原有效点云、P4开放面及KnownRing独立身份，原P0/P1/P2/P3/P5和统一B1另存`meshes/`。NPZ保存全部分支点掩码与来源，`points/*_RAW_MM.ply`是完整原点云。没有004/005联合配准或融合。

## 10. 复现和验证

环境：既有`ring_anchor_3d/.venv`，Open3D0.19、上一轮隔离PyMeshLab2023.12.post3，未部署新模型。代码`code/filters.py`仅实现用户限定的小规模质量控制，原网格生成和保守拓扑函数只读复用。

复现请复制到新的独立目录并修改输出根，不覆盖本轮冻结资产；顺序为：

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/pointcloud_surface_filter_vnext/code/setup_inputs.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/pointcloud_surface_filter_vnext/code/prepare_and_select.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/pointcloud_surface_filter_vnext/tests/test_geometry.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/pointcloud_surface_filter_vnext/code/run_filters.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/pointcloud_surface_filter_vnext/code/controlled_test.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/pointcloud_surface_filter_vnext/code/evaluate_filters.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/pointcloud_surface_filter_vnext/code/summarize.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/pointcloud_surface_filter_vnext/code/visualize.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/pointcloud_surface_filter_vnext/code/build_report.py
ring_anchor_3d/.venv/bin/python ring_anchor_3d/experiments/pointcloud_surface_filter_vnext/code/final_validate.py
```

原始输入和旧文件保护：[protected.json](provenance/protected.json)。[正式冻结](provenance/FORMAL_PREDICTIONS_BEFORE_GT.json)保存点身份/滤波Mask/几何/源码，评分从不改其内容。五个测试涵盖后方遮挡不删点、两个前方冲突、失败相机禁删、ROR物理单位等价、禁面不删点。最终核验：[FINAL_VALIDATION.json](metrics/FINAL_VALIDATION.json)，包括旧文件和用户修改未变、原始点可追溯、Mesh来源、RAW/B1几何相同、完整失败分母、GT变换哈希、PNG非空不透明、GLB Ring物理尺寸及唯一Markdown。

## 11. 最终决策：逐项回答

| 问题 | 本轮证据支持的回答 |
| --- | --- |
| Q1 碎片主要由异常点造成？ | 只有一部分。原Mesher已隔离不少异常像素，稠密错层/连续深度偏差仍在；SOR删掉孤点可不改变任何原面，不能将碎片都归于点噪声 |
| Q2 SOR/ROR能安全删多少？ | 没有证实一个可默认使用的安全比例。总拒绝量和GT错点精度逐组列出，所有DEV候选安全门槛失败；正确GT输入也被删好点 |
| Q3 多视角比密度更有效？ | 当前未证实。只有G01可运行，004删6点含5好点、005不变；模型相关和局部相机不确定性限制判断 |
| Q4 2.5D优于点删除？ | 它能保留点身份并避免长连接，但本轮阈值显著损失真实面和覆盖；不优于原始基线，不默认启用 |
| Q5 重生成Mesh比历史后清理更可靠？ | 尚无证据。前移过滤可删好点/好面并生孔；保守Mesh后整理不改原几何，仍更适合保持证据 |
| Q6 出现真实蒂部/边缘误删？ | GT支持的边缘/近Ring点和原面有误删；005 ROR下部代理也丢失。缺解剖蒂标注，不扩大为全部蒂部结论 |
| Q7 哪些组不能可靠清理？ | G02—G08多视角不可评价；G03/G05/G07相机尤其弱。G01能运行但删除真实性也未通过；G04无GT不能验证准确性 |
| Q8 可直接支持物理指标？ | 可保留条件性局部点/深度统计和保守局部量，不足以认证解剖头宽、真实凸起高度或闭合体积；不用Dxy值校准 |
| Q9 清理有限的主因？ | 不是纯稀疏噪声；连续深度形变与相机/跨视角可见性不确定性共同存在。本实验不能将两者完全定量分离 |
| Q10 下一步优先方向？ | 优先固定已有可靠相机下的深度图/多参考连续性诊断；本轮质量状态用于不确定性标记，不继续强化删点。Mesh无关测量须先明确局部量与可靠区域，不能跳过GT验证 |

只建议下一轮一个小问题：在固定相机与原覆盖分母下，测试保留点/面不变的多参考深度偏差诊断，判断连续错层能否由一致的低自由度修正解释。需要人工决定后再执行。本轮不启动新匹配器、配准器、深度模型或无界调参。

**到此停止，回传结果供人工审核。**
