# Phase E3-N0｜预注册实验与评价协议 v0.1

**状态：PROPOSED / RESEARCHER_APPROVAL_REQUIRED；2026-11-02。** 只定义未来可执行科学比较；本文件不授权运行。实验对象G01一个物理组、视频004；绝不跨视频混合。NeuralFusion与历史Open3D D0、未来G2/G3并行。**研究者已明确决定：各视角独立等比例裁剪，统一320×240输出，不强制各视角相同像素缩放系数。** 此决策为Gate A前置冻结原则，不等于整体Task执行授权。

## 1. 科学问题、假设及不可变约束

H0（首要可证伪）：官方预训练NeuralFusion在冻结输入下不能比**同裁剪输入**Open3D获得更好连续性且不损害真实首层解释/原HERO主面。H1：可改善碎片、接缝、合法新增方向覆盖，且无不可接受收缩/错误闭合/首层恶化。若改善光滑但丢失大量原始有效面，应拒绝“改进成功”。本项目没有经认证的物理GT，因此不能通过H1推断毫米形状准确率。

输入禁止：GT/Oracle、历史F1/F2/F3融合Mesh伪装深度、清洗后的3D面变成新HERO、照片不合格位姿、G01_005、Dxy、训练数据回填。相机/K/c2w、Ring实体、原生HERO、原始Face ID与source DAG冻结。用真实Polyp Mask且Ring/CAD不进入Polyp积分。E3-C条件Free-space不能用作硬删标签。

## 2. 预先固定来源顺序、角色和对照

| 版本 | 累积顺序 | 角色/资格 | 授权阶段 |
|---|---|---|---|
| F0 | ref08 | B3，诊断锚点，不是GT | Gate B |
| F1 | ref08→ref13 | B3+B5，旧CORE条件性 | Gate B |
| F2 | ref08→ref13→ref03 | +B2，三CORE；ref03匹配敏感 | Gate B |
| F2_REVERSE | ref03→ref13→ref08 | 同三源，同输入新空场，顺序敏感性 | Gate B |
| F3 | F2→growth_r04 | B3冗余/桥；Ring+部分RGB证据、资格不足 | Gate C |
| F4 | F3→new_r00 | +B1新方向；Ring略超容差、候选 | Gate C |
| F5 | F4→growth_r14 | +B4新方向；未完整独立Camera Gate | Gate C |
| F5_REVERSE | 上述六源严格逆序 | 同源新空场；不是随机排列后选优 | Gate C |

保留在E3-A白名单的其他growth不因最终Mesh选择进入。所有前缀重新从全零latent/count reset或精确持久化同一次不可变序列快照；记录checkpoint SHA256、配置、随机种子、融合顺序、硬件和代码commit。**主checkpoint暂定ShapeNet noise 0.005**，Gate A验证模型/训练域尺度后才由研究者确认；Tanks配置是独立备用静态兼容审计，不自动推理、不取结果较好者。

### 比较组

1. 原始单源HERO native深度+Raw开放Mesh/Face ID：输入证据锚，不是融合算法。
2. 历史 D0 SINGLE/G0/G1（Open3D 0.19.0 voxel=0.1mm/trunc=0.4mm，原完整native输入），作为历史参考；严格验收仍FAIL。
3. `MATCHED_OPEN3D`：在Gate B获批后用与NeuralFusion完全相同的裁剪有效深度、Polyp Mask、K/c2w和F0/F1/F2顺序，以预先冻结并记录的物理voxel/trunc建立同输入基线。**同输入**消除裁剪分辨率混淆，但Open3D与网络的模型分辨率不会数值相等；参数依据输入像素物理足迹预注册、不得依结果搜索。F3–F5按Gate C批准才延伸。
4. 原始Mask-CAD只读轮廓诊断；Gate D若获批，另建派生输入副本的安全清理消融，不覆盖上列结果。

同一视角用作融合与评价时标 `IN_SAMPLE`；未纳入某个前缀的现存视角是条件性 `HELD_OUT_WITH_SHARED_UPSTREAM`（HERO上游RGB可能共享），不得声称独立盲测。真实独立外部图像/物理GT认证样本数初始为0。

## 3. Crop/Mask/毫米变换冻结合同（Gate A先确定，Gate B不得改）

- 数据原生深度352×640、历史RGB/Mask 360×640。首先回查逐源K及0.5像素中心/历史重采样；以native深度像素为主坐标系建立可复算变换。
- **逐源独立裁剪（用户已批准）**：在每个来源自己的合法源像素系，ROI=`bbox(Polyp ∪ visible Ring)`，建议外扩原bbox最大边20%或≥16像素；将内容区扩为4:3，等比映射至W320×H240，剩余区域letterbox padding。每来源有独立`u0_i,v0_i,a_i,px_i,py_i`与`A_i`，绝不要求`a_08=a_13`，也不因某个来源缩得较多便修改其相机位姿。**20%/16px是候选，须在Gate A所有6源的边界/细结构检查后冻结，不是可事后按F结果修改的阈值。**
- 原生有效Polyp深度经nearest主方案、labels nearest、RGB可AREA；pad深度=0，valid=0；非Polyp/无深度/Ring/背景也无效，永不填远深度或伪背面。禁止因ROI失去细柄而只保留大头部。
- 约定像素中心变换：`u'=a(u-u0+.5)-.5+px`、`v'=a(v-v0+.5)-.5+py`；`fx'=a fx`、`fy'=a fy`、`cx'=a(cx-u0+.5)-.5+px`、`cy'=a(cy-v0+.5)-.5+py`，实际按现有内参中心约定以数值反投影验证。
- 统一公制局部框：由六源原生有效深度+冻结位姿（含保护余量、剔除已标注极端孤立候选仅**定义诊断bbox、不剔除输入**）确定 `O_mm, L_mm`。必须保存所有超出框的合法输入数量；若框不能容纳真实有支持域就Gate A失败。建议设置模型归一坐标 `X_model=(X_mm-O_mm)/L_mm`；若网格N=128，`resolution_model=1/128`，模型体素物理边长`L_mm/128`。对深度及相机中心使用相同线性尺度。不能只把c2w平移缩放而忘记深度。
- ROI外推/体素出界记`OUT_OF_GRID`且算失败分母，绝不静默clip。Mask裁剪后被剔除的原合法像素在原始分母记`CROP_LOST`。
- Gate A验证1000个固定且可追溯采样原合法像素/全部边界特殊例的裁前后**解析射线**和实际采样XYZ，二者独立验收；解析往返目标`max ≤1e-5mm`（建议，需按数据float精度在批准前锁定），实际重采样量化不得混同解析误差；若误差无法满足应报告而非调宽到PASS。Ring CAD外径约12.4mm的公制逆变换误差单独报告，不用GT拟合。

### 新增：不同裁剪比例下的跨视角不变性合同（Gate A硬门禁）

对来源`i`与目标`j`，保留冻结相机投影`π_j`和逐源像素仿射`A_j`。对来源`i`原始深度恢复的同一物理三维点`X_w`，必须检验：

`X_w_original(i) ≈ X_w_crop_analytic(i)`；`π'_j(X_w) ≈ A_j[π_j(X_w)]`；其中`π'_j`仅使用更新后的`K'_j=A_jK_j`与**未改变**的`c2w_j`。这是连续坐标的解析条件，**不要求不同来源的输出像素对应同一个栅格索引**。

- 三CORE要求六个有向对：`08→13,13→08,08→03,03→08,13→03,03→13`；其他3个条件性来源各自和CORE有合法投影时也须校验，且保留相机资格标签。
- 每源固定至少1000个有完整原像素身份的有效深度点，另含Ring邻域、Mask边界、细结构和深度跳变；每有向对对投影合法点记录原像素、原/裁后目标连续像素、重投影反变换误差、几何世界XYZ误差与有效/遮挡/ROI外状态。点在裁后目标内容区外，应标`OUT_OF_CROP_FIELD`而非算错位；若原目标合法Polyp支持因此被裁掉，单列`CROP_LOST_SUPPORT`。
- 解析投影闭环建议`max ≤1e-4 target px`（FP64几何，锁定前可由代码数值精度校核）；解析世界XYZ往返建议`max ≤1e-5mm`。实际320×240 nearest重采样会改变离散射线，**单独**报告采样量化像素/毫米误差，禁止将它纳入解析闭环造FAIL或隐藏采样损失。
- 必须报告每来源有效区域原/新像素数、`a_i`、物理像素足迹`Z/f'_x, Z/f'_y`的中位和p95、相对ref08的足迹比、细结构最窄输出有效像素数，以及重采样后Mask/CAD次序冲突数。采样密度差是未来Gate B分析因素，不能用每视角自定义米制缩放来消除。
- 六来源使用**同一**世界到模型场的`O_mm,L_mm`；逐视角图像`A_i`不同不允许导致3D体素`resolution_model`不同。Gate A严禁优化R/t以让裁剪后的两片云“看起来更对齐”。

## 4. 三维输出与完整分母定义

每F版本保存：实际latent和count摘要、官方Translator输出与使用区域、SDF/occupancy量纲、含`OBSERVED_SUPPORT/INFERRED/UNKNOWN`归属的三角面、未修复Mesh(mm)、首次交点深度（真实相机）和完整原面保存距离、配置/源SHA/显存/时长。若官方没有可靠支持域分离语义，应显式`SUPPORT_UNCERTIFIED`，**不得把count=0全域提取的零面认证为表面**。

三个评价维度互不加权、不拼单分数：

| 维度 | 主要冻结指标 | 反作弊规则 |
|---|---|---|
| 真实（观察解释） | 固定原Mask有效射线的FIRST_HIT `AGREE≤0.25mm / NEAR / FAR / MISS / CAD_OCCLUDED / UNKNOWN`；Mask越界距离；Ring穿插；合法未输入视角 | HERO差是输入一致性不是GT；miss保留全分母，完整分母p95可为+∞ |
| 完整（支持与覆盖） | 三CORE原完整Face ID近邻保留≤0.25mm、面积加权；合法新方向原面/方向格保留；已支持/模型推断Unknown面积分开、细柄/独特侧面标注 | 不以移除不利来源改变分母；重复源面积不相加成解剖面积 |
| 光滑（结构） | 连通分量/最大面积比例、开放边、局部小封闭组件面积、法向接缝跳变、曲率及远端孤立面 | 删除真实主面会单列损失，不因“少碎片”宣告成功 |

统一评价面板至少报告所有6源各自完整输入分母；其中仅有三CORE为Gate B正式融合。固定相机渲染ref08、ref13、ref03，另侧向/世界轴；每版本不可挑更美观摄像机。真实RGB、Mask和黑色CAD必须一起展示，物体和Ring为mm同尺度；背景不使用假纹理平面。

## 5. 强制四张核心图及GLB

1. Fig1 输入契约：真实RGB/Mask/CAD、原生HERO、320×240 ROI、Pad、K和XYZ闭环；标明细结构受损。
2. Fig2 历史D0、matched Open3D、Raw与F0–F5统一3D对照（Gate B只展示F0–F2；不存在的F3–F5标NOT_RUN）。同视角同尺度，黑CAD。
3. Fig3 真实ref08→ref13及固定目标的首层与Mask越界、CAD遮挡、UNKNOWN、条件性留出身份。
4. Fig4 头部/可能细柄/接缝/侧面/封闭碎片及远端异常的固定局部，不得只选成功样本。

每批上传3–4核心PNG，正式推理F0/F2/F5（若已执行）保留实际Mesh及可见小型GLB，巨型文件仅本地索引+SHA。图像未能独立人工审阅时状态为`NOT_EVALUABLE_VISUAL`。

## 6. 授权与停机

Gate A：**只有**依赖/权重静态检查、严格CPU载入与无GT形状/几何接口验证；不允许神经融合前向、GPU、训练、产生模型场。通过后提交PM/RA/研究者。

Gate B：**NOT_APPROVED**。首次真实F0、F1、F2、F2_REVERSE和matched Open3D小规模对照，需要用户单独批准；若F0单位/主面严重失真停止。

Gate C：**NOT_APPROVED**。F3→F5及F5_REVERSE；需人工审阅Gate B后决定是否让条件性r00/r14入场。

Gate D：**NOT_APPROVED**。只在有独立合法轮廓越界证据及用户许可时对派生深度Mask做保守只读/删除消融，保留原始输入与前阶段全部输出。

禁止自动跨门续跑、任意超参搜索、新HERO、再训练或用GT作权重选择。结论可为`INCOMPATIBLE / NOT_EVALUABLE / ENGINEERING_PASS_SCIENCE_UNKNOWN / NEGATIVE_RESULT`，不得用空输出伪装PASS。
