# 018 方法、输入及实现忠实性审计

本任务沿用016共享自由顶点主体、同视频冻结相机、公制Ring CAD及017原生HERO面片分类。没有拟合独立逐视角主体、ICP融合、TSDF或新网络训练；HERO前向使用已经安装的完整官方网络。全部预测在独立018目录产生，历史主体仅为明确授权的统一初始化，无历史测量值回退。

## 数据与身份

逐视角清单见 `VIEW_HERO_COMPLETENESS_MANIFEST.csv`：G06 7FIT+3HOLDOUT；G05 8+3；G01 8+5；G03 6+3，共29FIT与14HOLDOUT。精确ID继承016 `S1_BALANCED`。39次真正官方HERO推理、4份合格原生资产复用；未将他视角重投影、稀疏256射线或诊断NATIVE_GRID冒充新增来源。新推理每目标使用3份同视频FIT支持图，官方checkpoint中num_views=8是原配置，本次实际3支持数被明确记录。

原始视频帧身份经解码像素及文件SHA核对；G01遗留JPEG另复现“原帧→JPEG95→AREA缩放”链，逐帧证明原图绑定。旧metadata中不准确帧号仅在新清单登记纠正，RGB、K、T、Mask不改动。重复视频帧保留所有完全匹配索引，不猜测唯一身份。

原生HERO轴向深度为352×640；工作RGB/Mask为360×640。HERO官方接口使用米，输入相机平移mm/1000、输出深度m×1000。工作K到原生K使用像素中心变换 `u_new=(u_old+.5)*s-.5`。官方HERO loader、权重SHA和所有支持图记录在 `SOURCE.json`、`provenance/HERO_MODEL.json`。

## 017分类与未清理对照

所有43来源均运行原017分类及冻结gap规则；能精确匹配原资产者复用原标签。TRUSTED导出真实原面片子集，原始V、Face ID和native Pixel ID不改动。HERO法向来自其原始面片，统一朝来源相机；没有面片见证的FULL原生点法向记NaN而非捏造法向。

首轮R1诊断曾错误地让FULL原生观测也要求历史Raw Mesh见证，这会排除历史mesher因0.75mm深度跳变而省略的三角面附近点。R1结果、观测副本、代码快照完整保留。主实验R2的FULL修复为全部有限正值Polyp原生深度，仅执行与TRUSTED相同的CAD前可见和非材料内部资格；不要求原Raw面片存在。TRUSTED观测字节和标签完全不变。没有额外构造缺失三角面。详见 `metrics/FULL_NATIVE_INPUT_FIDELITY_REPAIR.csv`。

## 官方组件与项目算法逐项对应

|设计|实际实现|位置|
|---|---|---|
|共享自由顶点Mesh|`V=V016+q`，所有FIT视角更新同一q；可见主体F与闭合检查F_solid区分|`code/free_model.py:FreeVertices`|
|官方Mesh与相机|PyTorch3D `Meshes`、`cameras_from_opencv_projection`，公制中心化归一|`code/p3d.py`|
|官方第一层光栅化|`MeshRasterizer`/`RasterizationSettings`，原生352×640，hard `bin_size=0`，透视正确barycentrics|`code/hero_objective018.py:HeroDepth018`|
|毫米深度恢复|`interpolate_face_attributes`插值归一化世界点，再乘scale加center，投到原相机z轴|同上；不将zbuf当mm|
|原生固定观测|每个合法原生像素，固定Ω、w=1、W不随命中变化；没有256稀疏替代|同上|
|新HERO鲁棒损失|`Huber((zM-zH)/.5)`，不作常数上限截断；λH=.01|同上|
|未命中|每射线固定的最坏可行深度Huber+1；没有不受限的背面最近点梯度|同上|
|轮廓|016 Ring-aware、FN/FP与ContourDistance及固定40轮ramp；λS=1，所有路线一致|`Objective018.compute`, `multiview.py`, `contour_objective.py`|
|形状|相对016初值边长、相对Laplacian、官方`mesh_normal_consistency`及无观测位移项；λP=1|`components.py:RelativePrior`, `relative_total`|
|稀疏Laplacian|官方`Meshes.laplacian_packed()`加PyTorch sparse.mm；没有另声称调用mesh_laplacian_smoothing损失|同上|
|采样接口|导入的`sample_points_from_meshes`并非本轮损失路径；本轮是全部原生像素射线，不能声称使用该接口采样|实际HERO代码|
|Ring|原GeometryGuard硬可行性指示项0/∞；无可微Ring梯度，不虚构加权梯度|`safe_geometry.py`|
|优化|PyTorch Adam提案+016回溯/局部归一提案；完整目标接受与参数/动量回退|`train018.py`|
|邻域协同R2|原016接触面固定、λ=1图Sobolev `(I+L)d=d_raw`，不增加ARAP、不改变网格拓扑|`coherent016.py`|
|几何保护|毫米信赖域、累计1D、基底/交界、面积比≥.1、方向、自交、CAD正反向/FCL检查|`safe_geometry.py`, `free_model.py`|
|独立评价|冻结后读取14HOLDOUT，全分辨率Mask与全部TRUSTED射线，Ring三角内部64阶采样|`evaluate018.py`|

## 新旧深度不能重复加权

B1/B2及G01来源数消融完全移除旧D2绝对/相对项，使用上述新HERO项。OLD_D2独立路线保留旧.01绝对+.01相对损失与旧9.5截断，以当前无HOLDOUT支持污染的原生深度重建其固定256点/来源及同视角点对。它是旧**损失**基线，不伪称使用旧历史HERO数值的逐位复现。

新HERO来源权重：每个实际direction_block相同总质量；分区内按目标RGB和上游支持RGB集合Jaccard相关度的逆度归一。共享RGB不视为独立来源，也不删除任何来源。多HERO冲突仅在全部预测冻结后单独输出，不进入损失、样本筛选或权重选择。

## 未命中及覆盖限制

未命中保留固定分母，命中代价不截断；无命中射线本身没有HERO几何梯度，依靠已有轮廓项可能扩张覆盖，但这不是已经验证的受限Point–Mesh恢复机制。每射线miss_cost取初始顶点轴向范围±累计位移D内最大Huber+1，故丢失单条射线会增加其代价；总目标仍可能通过其他射线改善抵消覆盖下降，所以必须同时报告覆盖。不能以命中条件MAE降低宣布成功。

## R1→R2及冻结边界

G06 R1 FULL/TRUSTED全向量诊断具有大量Ring拒绝和微小位移。R2仅统一接入016已有接触-Sobolev提案；全部14条主路线相同；预算80候选/40接受/30连续拒绝停止，原Ring/自交/全目标保护不变。R1 FULL筛选缺陷另行修正，不能将两种修改的联合效果包装为单因素科学消融。没有查看GT/HOLDOUT性能选择该修订。

HOLDOUT有独立资产生成和分类流程，新的FIT HERO支持图严格排除HOLDOUT。优化Case只含FIT，并安装文件读取拒绝防火墙。继承016主体的**历史初始化祖先可能使用过现在的HOLDOUT图像**；因此本轮HOLDOUT是更新阶段独立评价，不宣称整个历史流水线完全独立。所有真实GT指标为NOT_EVALUABLE，本轮不执行ICP或Blender评价。

## 最终独立诊断补充

`paired018.py`按完全相同原生Pixel ID输出共同命中、新增和丢失，另存HIT_TRANSITIONS.npz（原生ID、HERO XYZ、前后body Face ID与Z）。`aggregate_residuals018.py`对全部有效射线合并计算median/p95/max，未用“平均各来源分位数”替代真实池化分位数。共同TRUSTED和共同FULL均评价所有方法；FULL评价不作为独立物理GT。

`conflicts018.py`和`missing018.py`只在预测冻结后执行。前者比较原生TRUSTED点跨相机投影，后者检验全局最近点的可见性和投影偏离。均未用于训练/筛选/选模。官方point_face_distance实现已检查，不能自动提供来源相机可见性限制。本轮没有将不合格全局最近点接入损失。

`export_sources018.py`补充所有原始Face ID的相机朝向法向到ORIGINAL_FACE_NORMALS.npz，坐标和三角面不变；无法由原始面片定义的FULL孤立原生像素仍保持normal=NaN。

Ring指示项实际上表示**相对于继承状态不得恶化**的硬可行性。G06/G05/G03的继承穿入未消除，不能据该项在接受状态为0声称绝对无穿透。独立64阶检查保留真实负距离。

实际运行种子差异：冻结PROTOCOL.seed为20261110，继承train018实际调用torch.manual_seed/np.random.seed(20261108)。14个INITIAL.pt逐一验证一致。该元数据偏差公开保留，不覆盖原冻结文件、不重新抽随机种子；旧深度采样独立固定为20261110。见config/ACTUAL_RUNTIME_CONTRACT.json。
