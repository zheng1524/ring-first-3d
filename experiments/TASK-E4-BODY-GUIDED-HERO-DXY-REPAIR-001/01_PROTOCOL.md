# E4 DXY 修复：正式协议 v2

本任务来源于 `492725ffd8e2fac86fe18099a87f7ef6d6d93b3b`，分支为 `exp/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001`。本协议在正式 DXY / 主体优化之前冻结，全部预测冻结后才进行留出评价和 Body-U 对照。旧 Phase-0 错误记录保存在 `provenance/SUPERSEDED_PHASE0/`，更正证据见 `provenance/PHASE0_CORRECTION.json`。

## 输入及坐标

目标为 G03=18、G05=16、G01=26、G06=15，共4物理组75来源。其中 video004=58，video005=15，独立照片=2。正式相机池来自原始资产目录的 `TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/config/FINAL_CAMERA_POOL.json`，不能因 Git 未收录该文件而改用原始候选池。

沿用旧prepare.py的source ID/aliases + target RGB SHA绑定；29个OLD018来源优先采用自身target_cache。相机只读原生OBS_TRUSTED.npz的K/T/native_shape，使用原有半像素中心仿射映射到640×360，绝不读取其中X/z/normal参与拟合。最终相机池与旧观测的位姿差异全部登记，不用另一个版本覆盖。RGB/原始uint8标签Mask的字节SHA、文件SHA、相机SHA、Ring CAD SHA记录于库存。

DXY固定75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95，VERSION=DXY-MID-1.0.0rc1，Geometry=V9.1。73个源直接measure_files；两张原照片与640×360相机分辨率不同，measure_frame(cache_RGB[:,:,::-1], original_uint8_cache_labels)，不新增JPEG。所有组Ring=R10，参数为内径10mm。仅导出candidate.center_native/basis_native和质量/来源，禁止读毫米预测。

## 多视角及坐标资格

每组每视频独立建池。021只研究G01，不能证明其他组跨视频一致；MAX的005直接PnP已使用004 RGB地图，属于条件性同坐标证据，不能冒充独立SfM恢复。本轮保守地分别拟合004和005，不重估相机或跨视频变换。照片单列独立池。单视角池记录NOT_EVALUABLE_INSUFFICIENT_MULTIVIEW。

每池至少3个独立RGB来源、至少2个FIT和1个HOLDOUT；只用已资格检查的条件性相机。图像质量沿用015：log锐度、边界完整度、细结构骨架proxy、非Ring比例分别min-max归一化，权重.1/.1/.1/.05；从质量最高帧出发，用`.65*最小方向夹角/pi + quality`贪心选择。方向使用Ring原点到相机，不用旧Body中心。FIT数`min(8,N-max(1,ceil(N/4)))`，未选全部留出；不按DXY/拟合/GT更换名单。主分析为各组004；足够视角的005为独立附加分析。

## E1/E2公平拟合

E1为官方DXY区域：`q=(p-c)@inv(B).T`，`sum(q*q)<=1`；E2为整个原始labels==1，外围与柄全部保留。任一必要FIT缺官方candidate，整池E1不可评价，不回退。

直接复用A1 COARSE decode/sphere_mesh九参数模型，初值`[0,0,-2,0,0,0,log(5),log(5),log(3)]`。R0调用A1 camera_frame，由全部FIT相机中心均值减初始中心及首FIT相机x轴确定。E1/E2共享R0与初值。

直接复用A1 losses的ellipse_projection、signed_distance、target_data、cad_visibility、two_d_parts，保持128预测轮廓采样、全部原始观察轮廓、4×4面积池化、Ring未知、实际CAD首层和原鲁棒归一化。禁止depth_parts/HERO XYZ。视角权重按相机资格和上游RGB SHA集合Jaccard沿用A1，归一后同用于E1/E2。先验与A1相同，权重.05。

优化直接执行A1 Problem.solve：float64 SciPy TRF、3-point Jacobian、max_nfev=60、ftol/xtol/gtol=1e-5；中心各分量[-10,10]mm、旋转[-.8,.8]rad、半轴[.25,15]mm。三个初值seed20261104+start，非零start扰动标准差.4mm/.08rad/.12log轴。共享预算，不按结果重跑。保存所有调用轨迹和失败结果。主解仅从optimizer_success、有限、全部FIT投影合法、正深度、几何约束通过的结果中按FIT目标选择；无合格结果保存null/NaN。

## 评价及验收（预先固定）

全部预测冻结后在相同完整Mask上评价FIT/HOLDOUT：IoU、FN/FP固定分母、双向及固定源轮廓距离mean/median/p95/max。Ring像素未知，接触Ring边界不标真实息肉轮廓。真实GT不读取，绝对3D准确度和相对误差NOT_EVALUABLE。

多初值直接调用A1 analyze.difference/surface_distance，含中心、排序半轴、轴符号等价旋转、2048实际表面采样。半轴>=14.85或<=.2525mm、轴比>20、active bound标风险；中心差>2mm或表面p95>2mm标不稳定。不含先验的二维残差有限差分Jacobian做SVD，参数尺度1mm/.1rad/.2log轴，秩阈值smax*1e-6，记录奇异值/条件数/列敏感度/最弱方向。单FIT与全部FIT在同一解处作局部信息对比，不冒充独立反事实拟合。

进入HERO下一阶段的门槛：3个初值全部合格，无边界/轴比风险，表面p95<=2mm，观测Jacobian满秩且条件数<=1e6，HOLDOUT中位IoU>=.5、固定源轮廓MAE<=10px、最差IoU>=.35，Ring密集表面无<-0.05mm有符号穿透。该门槛只给条件资格，不证明测量正确。隐藏背面均为先验推断。Body-U仅预测冻结后读取与可视化，不作GT。禁止A2/resection、HERO修改、融合、训练。完成报告后停止。
