# SIM_PROTOCOL_REV1：执行完成，二维主体配准尚未达标

**G0–G4全部实际运行，Runner 14个阶段及产物检查通过，82项回归通过。科学结论：M2在5/5主条件产生独立数值输出，但0/5同时满足冻结的0.5°/0.2mm相对位姿门限。没有按GT结果重调参数、重新选择Body或重跑DXY。**

S1的M2相对误差由2.000°/0.500mm变为1.925825°/0.126307mm；GT曲面MAE/p95为0.015705/0.060733mm。Robust ICP为1.500132°/0.009874mm，曲面MAE/p95约0.003588/0.012816mm；这些小曲面残差均不能证明正确相对旋转。Ring-only在本轮Y倾斜设置下5/5通过，不能将这项恢复归功于二维主体。

实现提交：`4bc294b982b07df97bc609c1af8a303f2c7d9dfa`。原始Runner冻结指纹：`60d5d4a602cd3c24dffebc9e163f9aa43f3e70be5e3ba80ff3a8a2616c2ec4ad`。历史原G0、TASK与失败记录原样保留，本轮为独立SIM_PROTOCOL_REV1。

[完整曲面交互](visualization/mesh_registration.html) · [真实对应逐点CSV](visualization/G2_CANDIDATE_AUDIT.csv) · [全部负结果/未匹配台账](visualization/FAILURE_LEDGER.json) · [共同数值条件配对](visualization/PAIRED_COMPARISONS.json)

DXY仅为当前Body初始化与中介映射提供冻结API的中心、basis、质量；没有算法修改或P/Q/直径精度研究。合成/原图各33帧数值候选；严格稳定分别11/33和5/33，不能将数值候选称为严格测量通过。E1/E2/显式代理各三初值均收敛；Body依冻结优先级选E1，并在全部配准中保持SHA不变。原TRF多初值使用冻结历史源码中的20261104+start种子；仿真协议的20261116种子与无随机误差矩阵分开记录。

G2数值覆盖和独立可评价覆盖分开报告：合成中介2670/3168有Body候选，984/3168同时可独立评价且非Ring接触未知；直接原像素1549/3168有候选，117/3168独立可评价。真实原图分支仅为G01-like虚拟射线诊断。所有12672个目标查询点、Face ID=-1、NaN、接触未知及置信度均已导出，不只展示成功点。

本地运行共822.655s，低于7200s预算；没有新的主体重建训练、实际HERO推理或跨视频BA。表面统计为完整局部Mesh顶点对独立GT三角面的距离，所有视频完整顶点均在分母内；这不是直径精度评估。L1与主S0–S4独立。

---

# TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1

G01_LIKE_SIMULATION / SYNTHETIC_HERO_PROXY。G0–G4已实际执行；科学结果等待人工审阅。真实性为质量指标，内部几何/坐标/GT权限失败仍阻断。历史G0失败和冻结文件完整保留。

[离线首页](visualization/index.html) · [完整曲面五阶段交互](visualization/mesh_registration.html) · [全部指标](visualization/REGISTRATION_METRICS.json) · [失败台账](visualization/FAILURE_LEDGER.json)

## 来源、固定协议与角色隔离

真实004/005各自原生Camera-to-Ring和33帧分区原样继承（25 FIT、8 HOLDOUT）；统一虚拟R10坐标系为明确的仿真假设，不宣称两真实视频已认证共同世界。原始G01 Blender形状不缩放；仅按冻结FIT轮廓规则选择一个共享静态平移。置放候选、分数、CAD尺度和逐帧射线/PyTorch3D独立检查见G0审计。

静态摆放：[0.0, 0.0, -4.0]mm，旋转I，缩放1。原图Ring投影差异继续记录，不再阻断。所有受试网格为完整可见原始三角形并集，不是实际HERO输出；未平滑、未投到Body、未替换观测点。

S0 I/I；S1 I/A；S2 I/B；S3 A/B；S4 A/A（004/005）。A=+Ry2°、+X0.5mm；B=+Ry3°、+X0.3mm；旋转中心Ring原点，世界左乘，种子20261116。相机/Ring/局部Mesh共同变换，段内相对相机及Camera-to-Ring不变；独立L1仅005相机局部A、CAD固定，不与主矩阵混合。

G0 generator可读GT，G1/G2/G3 predictor拒绝GT和评价目录；G3额外拒绝干净相机目录及G2干净三维锚点，必须用实际受扰相机重算对应。Body与预测先SHA冻结，G1/G2/Smoke/G4独立evaluator才读GT。任何方法不收敛或误差大均保留，不使用其他方法补值。

## 独立Body初始化

复用T01/T03正式像素API、T04椭圆basis约定、T05九参数模型、T06/T07解析投影及完整Mask损失、T08原样三初值TRF、T09的2D-only策略。没有整体导入历史含HERO深度的Problem。二维参数只来自当前观测；固定FIT优先次序E1→E2→显式代理，不依据GT选择。

选用Body臂：E1。各臂多初值、数值/收敛状态、轮廓误差、Ring穿透代理及独立GT表面误差详见[G1指标](visualization/G1_METRICS.json)。隐藏表面是椭球先验推断，不冒充可观测轮廓。

## 二维中介与真正曲面配准

中介以观察椭圆的规范化坐标映射到Body投影椭圆，再求可见Face/重心和候选区域，径向收缩0.97用于切线邻域诊断；其查询像素一般不同于原像素。直接原像素Pixel-to-Face单独对照。Ring接触切边保留为物理轮廓未知、零置信度；未匹配点NaN且保留全分母。实际原始/映射像素、Face、重心、XYZ、basis和置信度在每帧G2冻结数组中。真实原图轮廓亦单独映射，但GT只是假定G01-like虚拟射线诊断，不是对真实物理对应的认证。

M0不修正；M1 Open3D Tukey Robust ICP（固定004，估计005）；M2每视频共享6参数，联合二维中介三维锚点、Body轮廓和鲁棒局部曲面几何；M2_DIRECT改用直接像素；M2_RING加入Ring中心/法向约束。RING_ONLY只用未标记3D CAD的中心/法向，绕Ring法向的扭转不可观察，采用最小扭转规范。主扰动为Y倾斜，可由Ring直接解释；其恢复不能归功于二维Body。L1中3D CAD先验固定，因此此Ring-only对照本身不观察局部相机误差。

所有实际修正作用于完整原网格全部顶点，Face拓扑与边长断言验证；优化可抽样约束点，输出和可视化始终是完整曲面。Body保持冻结。S4共有世界误差属于规范自由度，评价同时给绝对GT误差和004规范对齐后的误差，主要位姿指标为(E004)^-1 E005。不能仅由两曲面间距离判定成功。

## 全部实测条件

| Condition | Method | Numeric | Rel rot before→after deg | Rel trans before→after mm | GT surface MAE / p95 mm | Common-visible MAE mm | Pose criterion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | M0 | NUMERIC | 0.000000→0.000000 | 0.000000→0.000000 | 0.000000 / 0.000000 | 0.000000 | True |
| S0 | M1 | NUMERIC | 0.000000→1.500132 | 0.000000→0.009874 | 0.003588 / 0.012816 | 0.103152 | False |
| S0 | M2 | NUMERIC | 0.000000→0.648233 | 0.000000→0.045463 | 0.013454 / 0.045211 | 0.059328 | False |
| S0 | RING_ONLY | NUMERIC | 0.000000→0.000000 | 0.000000→0.000000 | 0.000000 / 0.000000 | 0.000000 | True |
| S0 | M2_DIRECT | NUMERIC | 0.000000→2.301536 | 0.000000→0.229505 | 0.020984 / 0.079248 | 0.246082 | False |
| S0 | M2_RING | NUMERIC | 0.000000→0.933472 | 0.000000→0.003772 | 0.001665 / 0.007471 | 0.065415 | False |
| S1 | M0 | NUMERIC | 2.000000→2.000000 | 0.500000→0.500000 | 0.085036 / 0.320686 | 0.478637 | False |
| S1 | M1 | NUMERIC | 2.000000→1.500132 | 0.500000→0.009874 | 0.003588 / 0.012816 | 0.103152 | False |
| S1 | M2 | NUMERIC | 2.000000→1.925825 | 0.500000→0.126307 | 0.015705 / 0.060733 | 0.173623 | False |
| S1 | RING_ONLY | NUMERIC | 2.000000→0.000000 | 0.500000→0.000000 | 0.000000 / 0.000000 | 0.000000 | True |
| S1 | M2_DIRECT | NUMERIC | 2.000000→6.179961 | 0.500000→0.365077 | 0.034310 / 0.121093 | 0.539061 | False |
| S1 | M2_RING | NUMERIC | 2.000000→0.601219 | 0.500000→0.004940 | 0.001142 / 0.004459 | 0.042374 | False |
| S2 | M0 | NUMERIC | 3.000000→3.000000 | 0.300000→0.300000 | 0.028176 / 0.097212 | 0.332300 | False |
| S2 | M1 | NUMERIC | 3.000000→1.500129 | 0.300000→0.009874 | 0.003588 / 0.012816 | 0.103152 | False |
| S2 | M2 | NUMERIC | 3.000000→2.519707 | 0.300000→0.166034 | 0.017194 / 0.067527 | 0.227852 | False |
| S2 | RING_ONLY | NUMERIC | 3.000000→0.000000 | 0.300000→0.000000 | 0.000000 / 0.000000 | 0.000000 | True |
| S2 | M2_DIRECT | NUMERIC | 3.000000→3.056373 | 0.300000→0.234313 | 0.025518 / 0.092372 | 0.296124 | False |
| S2 | M2_RING | NUMERIC | 3.000000→0.699801 | 0.300000→0.006512 | 0.001251 / 0.004675 | 0.049181 | False |
| S3 | M0 | NUMERIC | 1.000000→1.000000 | 0.200000→0.200000 | 0.060440 / 0.242878 | 0.224587 | False |
| S3 | M1 | NUMERIC | 1.000000→3.741372 | 0.200000→0.017019 | 0.004658 / 0.014716 | 0.256356 | False |
| S3 | M2 | NUMERIC | 1.000000→0.889022 | 0.200000→0.044301 | 0.013299 / 0.047125 | 0.073472 | False |
| S3 | RING_ONLY | NUMERIC | 1.000000→0.000000 | 0.200000→0.000000 | 0.000000 / 0.000000 | 0.000000 | True |
| S3 | M2_DIRECT | NUMERIC | 1.000000→4.412674 | 0.200000→0.276657 | 0.019495 / 0.086469 | 0.384724 | False |
| S3 | M2_RING | NUMERIC | 1.000000→1.378149 | 0.200000→0.004089 | 0.001908 / 0.006982 | 0.095463 | False |
| S4 | M0 | NUMERIC | 0.000000→0.000000 | 0.000000→0.000000 | 0.000000 / 0.000000 | 0.000000 | True |
| S4 | M1 | NUMERIC | 0.000000→1.500132 | 0.000000→0.009874 | 0.003588 / 0.012816 | 0.103152 | False |
| S4 | M2 | NUMERIC | 0.000000→0.715766 | 0.000000→0.043409 | 0.013410 / 0.044578 | 0.063073 | False |
| S4 | RING_ONLY | NUMERIC | 0.000000→0.000000 | 0.000000→0.000000 | 0.000000 / 0.000000 | 0.000000 | True |
| S4 | M2_DIRECT | NUMERIC | 0.000000→1.879272 | 0.000000→0.181910 | 0.020498 / 0.078833 | 0.200375 | False |
| S4 | M2_RING | NUMERIC | 0.000000→1.280459 | 0.000000→0.003879 | 0.001845 / 0.007075 | 0.088851 | False |
| L1 | M0 | NUMERIC | 2.000000→2.000000 | 0.500000→0.500000 | 0.085036 / 0.320686 | 0.478637 | False |
| L1 | M1 | NUMERIC | 2.000000→1.500132 | 0.500000→0.009874 | 0.003588 / 0.012816 | 0.103152 | False |
| L1 | M2 | NUMERIC | 2.000000→1.925825 | 0.500000→0.126307 | 0.015705 / 0.060733 | 0.173623 | False |
| L1 | RING_ONLY | NUMERIC | 2.000000→2.000000 | 0.500000→0.500000 | 0.085036 / 0.320686 | 0.478637 | False |
| L1 | M2_DIRECT | NUMERIC | 2.000000→6.179961 | 0.500000→0.365077 | 0.034310 / 0.121093 | 0.539061 | False |
| L1 | M2_RING | NUMERIC | 2.000000→2.825325 | 0.500000→0.462757 | 0.073786 / 0.274063 | 0.428883 | False |

逐视频曲面MAE/中位数/p95/最大值、可见材料点一致性、0.1mm覆盖、完整目标顶点数及8帧HOLDOUT投影误差均在JSON内。直径MAE/相对直径误差N/A：本任务评价对应与配准，不产生直径测量。所有方法有共同分母，失败留NaN，不只统计成功条件。

## 数值覆盖与科学通过的区别

| Method | Primary targets | Independent numeric | Relative pose criterion pass |
| --- | ---: | ---: | ---: |
| M0 | 5 | 5 | 2 |
| M1 | 5 | 5 | 0 |
| M2 | 5 | 5 | 0 |
| RING_ONLY | 5 | 5 | 5 |
| M2_DIRECT | 5 | 5 | 0 |
| M2_RING | 5 | 5 | 0 |

L1单列不混入主条件分母。优化器未收敛、Body失配和对应偏差均为真实负结果，见失败台账；未自动晋升永久规则。Smoke先执行S0/S1并独立核验实际全Mesh扰动、相机相对不变和优化导致真实顶点位移，再扩展完整矩阵。

## 固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | G01-like静态场景1；5主条件、独立L1；每条件2视频；25 FIT / 8 HOLDOUT |
| 本算法独立成功 | 每方法数值输出与位姿正确性分别见上表，不等同 |
| 本算法失败 | 每方法/条件负结果及NaN保留；见FAILURE_LEDGER.json |
| 历史测量值回退 | 0 |
| 失败组及具体原因 | 每条件、方法、阶段和关联真实指标/图均保留 |
| 最终统计样本 | 每方法全体5主条件分母，L1单列；共同成功条件可配对，无历史融合 |
| 是否使用 GT 选择算法 | 否；参数/TASK/源码先冻结，Body先冻结，GT仅生成与独立后验评价 |

## 可视化与实际修正

- [S1_M2_PIPELINE_front.png](visualization/figures/S1_M2_PIPELINE_front.png)：Actual complete meshes, fixed metric views; error colors 0-1+mm
- [S1_M2_PIPELINE_side.png](visualization/figures/S1_M2_PIPELINE_side.png)：Actual complete meshes, fixed metric views; error colors 0-1+mm
- [S1_M2_PIPELINE_top.png](visualization/figures/S1_M2_PIPELINE_top.png)：Actual complete meshes, fixed metric views; error colors 0-1+mm
- [MATRIX_COMPLETE_MESHES.png](visualization/figures/MATRIX_COMPLETE_MESHES.png)：All primary conditions, actual complete registered local meshes
- [004_FIT_PIXEL_BODY_CORRESPONDENCE.png](visualization/figures/004_FIT_PIXEL_BODY_CORRESPONDENCE.png)：Original real contour, actual synthetic observations, fitted ellipse and nontrivial Body warp
- [004_HOLDOUT_PIXEL_BODY_CORRESPONDENCE.png](visualization/figures/004_HOLDOUT_PIXEL_BODY_CORRESPONDENCE.png)：Original real contour, actual synthetic observations, fitted ellipse and nontrivial Body warp
- [005_FIT_PIXEL_BODY_CORRESPONDENCE.png](visualization/figures/005_FIT_PIXEL_BODY_CORRESPONDENCE.png)：Original real contour, actual synthetic observations, fitted ellipse and nontrivial Body warp
- [005_HOLDOUT_PIXEL_BODY_CORRESPONDENCE.png](visualization/figures/005_HOLDOUT_PIXEL_BODY_CORRESPONDENCE.png)：Original real contour, actual synthetic observations, fitted ellipse and nontrivial Body warp
- [ACTUAL_METRICS.png](visualization/figures/ACTUAL_METRICS.png)：Actual all-method numerical results; S4 common gauge retained

完整估计变换、优化trace、每视频最大实际顶点位移和完整网格输出均在G3预测冻结产物中。交互HTML包含所有条件/方法的原始、错层、候选、实际配准、GT阶段，可直接离线打开。所有静态3D图使用相同毫米范围和0–1+mm色标，超过色标的实际误差未从数值表裁剪。

## 冻结后只读审阅补充

下列图仅导出已冻结的源图、二维候选、相机、Body和完整Mesh；没有新增DXY评估、拟合、优化或GT选参。完整Runner快照保留。

- [真实原图Ring与原生相机CAD投影差异](visualization/figures/REAL_CAMERA_RING_AUDIT.png)
- [真实轮廓、已冻结API椭圆及虚拟Body候选区域](visualization/figures/REAL_CONTOUR_ELLIPSE_BODY.png)
- [真实双轨迹来源在声明的共同虚拟坐标系和完整局部曲面](visualization/figures/VIRTUAL_CAMERA_RING_FULL_MESH.png)
- [所有GT表面误差图共享Turbo色标0–1+mm](visualization/figures/GT_ERROR_COLORBAR.png)
