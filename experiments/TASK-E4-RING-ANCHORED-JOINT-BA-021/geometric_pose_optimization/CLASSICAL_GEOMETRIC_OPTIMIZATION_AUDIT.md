# 成熟方法与实际实现审计

本轮采用几何重投影/鲁棒核/局部重线性化与有界信赖域的常见结构，未运行COLMAP、ORB-SLAM3或DROID-SLAM系统，未声称复现其完整BA。参考：[Ceres残差与求导](https://ceres-solver.org/nnls_tutorial.html)、[COLMAP Ceres BA源码](https://github.com/colmap/colmap/blob/main/src/colmap/estimators/bundle_adjustment_ceres.cc)、[ORB-SLAM3 Optimizer.cc](https://github.com/UZ-SLAMLab/ORB_SLAM3/blob/master/src/Optimizer.cc)、[DROID几何BA](https://github.com/princeton-vl/DROID-SLAM/blob/main/droid_slam/geom/ba.py)、[SciPy least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)。只借鉴几何机制，未引入网络。

本地pycolmap4.2.1可用，但未暴露可承接自定义Ring残差的Problem/Ceres接口；pyceres与g2o缺失。选择SciPy有界TRF，而非把不支持约束的LM直接套上，也不称调用Ceres求解器。本轮没有正式调用该TRF封装，不能声称优化收敛已验收。P1只有6维pose块，未做Schur消元；可选P2共同地标BA及G01共享/局部调度未执行。

| 原设计 | 实际实现/位置 | 运行状态与差异 |
| --- | --- | --- |
| 公制c2w、左SE3更新 | `code/geometric.py::pose`，camera-centred world retraction `Exp(Ad_Trans(c0)xi) C0` | q前三轴0.6mm、后三轴5°，旋转围绕初始相机中心，等价明确的世界左扰动；shared参数围绕世界原点。六自由度probe已实测，无尺度自由度 |
| 实体CAD、真实I/O | 原021 `CADCurves.segments`，本轮`Problem.relinearize` | 保留完整CAD厚度、原Mask支持I/O。仅Ring分支以绕z规范消除虚假yaw；无完整外推椭圆监督。继承可见性判据发现Inf问题，未修复后冒称相同方法 |
| 新几何目标 | `residual_t` | L=.5 mean Huber(dInner/3)+.5 mean Huber(dOuter/3)+.2 mean Huber(norm(reprojection)/3)+.01 sum(q²)/12。曲线实际为二维最近线段矢量范数；最近线段ID在内循环固定，垂足t仍clamp。等价距离目标在分支切换处不光滑 |
| RGB几何 | `code/prepare.py`调用既有019features/matches/landmarks；`residual_t` | 只用真实SIFT互检和RANSAC。跨帧描述子银行去除目标图本身的描述子，单地标/单目标feature唯一；固定地图仍含原相机三角化偏差。不以3D最近点建身份 |
| 权重与候选 | 每I/O通道/每目标视角按N归一，SIFT .2、prior .01 | 已登记，未用HERO/body/GT/留出改权重。当前仅代表视角single-pose块被测试；多视角/轨迹总量联合归一与共享优化尚未运行，不宣称全局BA已实现 |
| 可微几何Jacobian | `jac`，torch.func.jacfwd、CPU float64矩阵指数/投影 | 4组×2状态×5分量×3步长×6轴，局部数值结果完整保存；不调用P3D软Ring梯度 |
| 信赖域与实际接受 | `solve`封装SciPy TRF，外部relinearized true_cost+物理检查+回溯 | 已写代码，正式运行0；没有实际接受轨迹、最终P1或收敛图。门禁失败后不能把未运行函数称验证成功 |
| 相机保护 | 计划中心变化≤1.2mm、旋转≤10°、CAD正深度，先验保持初值 | 仅封装，未运行相机候选，不声称全部保护回归通过 |
| P0独立评价 | `baseline_audit.py` | 98相机/51原生源全处理。旧HERO未改；正式P1不存在，因此不生成POSE_CHANGED_DEPTH_NOT_REINFERRED几何。以后若局部pose改变，必须标该身份并核查是否需要重新推理 |
| 12独立照片 | 读取quick已核验的资产manifest身份作为未来清单 | 新相机/照片匹配/照片间约束/HERO全部NOT_RUN_STAGE_A_GATE，不能复用旧photo候选冒充新方法 |

精确函数行号与SHA见`metrics/CODE_LOCATION_INDEX.csv`。所有目标、实现差异、失败门禁均保留，未静默换目标或阈值。绝对位姿与真实几何精度NOT_EVALUABLE。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4个物理组；98个canonical视频视角（81FIT/17HOLDOUT），照片阶段12张仅条件授权 |
| 本算法独立成功 | 正式P1派生相机输出0/98；四组正式精修完成0/4；98/98原始输入审计、4/4代表视角数值探针完成不算优化成功 |
| 本算法失败 | 3/4代表视角局部J多步长门禁失败；全局门禁FAIL，全部4组P1未运行，结果NaN。12照片NOT_RUN_STAGE_A_GATE |
| 历史测量值回退 | 0；用户指定021B3与旧相机仅作P0/初始化，不冒充新P1输出 |
| 失败组及具体原因 | G01/G05/G06在1e-4的Outer残差跨clamp分支；G03局部J通过但重线性化可见边也切换。四组均发现CAD边射线可见性切换，详见逐组报告和真实图 |
| 最终统计样本 | P0全部98视角和51个原生TRUSTED来源；新P1独立输出0，改进指标NaN；绝对GT误差MedARE/MAE/P95/max均NOT_EVALUABLE |
| 是否使用GT选择算法 | 否；未读取GT。原相机/Mask/HERO/主体/CAD/DXY未修改，未用HERO或主体生成位姿 |
