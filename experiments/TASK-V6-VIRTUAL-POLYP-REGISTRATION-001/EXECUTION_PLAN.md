# TASK-V6-VIRTUAL-POLYP-REGISTRATION-001 执行协议

基础提交：115e41fe5e57deff2898258d2ee836c83d686982（V6 RAW→HERO）。独立分支 exp/TASK-V6-VIRTUAL-POLYP-REGISTRATION-001。用户已批准核对后直接执行；不修改上游。不使用 H004 前半段产物。

## 资产复用与组合（先于代码与运行冻结）
|复用资产/能力|本轮用途|必要适配/状态|
|---|---|---|
|原 multisurface TASK.yaml / VIEW_SOURCES / parent FREEZE|16 FIT + 8 HOLDOUT、两条独立生成轨迹，保持原角色|REUSE；保留原模拟轨迹，不把它标成新 V6 相机；旧018来源仅定义既有虚拟环境|
|virtual_GT SHA 1c857568… / canonical_ring SHA 30bd8448…|唯一静止几何与固定R10|REUSE；已在本任务 inputs 保护；真值仅生成器/冻结后评价可读|
|sim.scene.synthesize / synthetic.raster.ray_map|RGB/Mask/轴深度、真实遮挡|ADAPT；原像素背景纹理不适用，按用户授权新增物体坐标稳定纹理；几何/遮挡/深度不变|
|multisurface.geometry.depth_grid_mesh|逐视角独立三角网格|REUSE；stride2、edge_limit1mm；SYNTHETIC_HERO_PROXY|
|V6 track005.main + v6_common.triangle|自动SIFT/互检比率/同类别/一致轨迹、DLT三角化|ADAPT；原函数AST原样调用，绑定本任务RGB与FIT清单，pair_offsets扩展为全部FIT对；6000特征、ratio .72；不读HOLDOUT|
|sim.geometry rigid_fit/se3/transform + scipy least_squares|视频级公制SE(3)、鲁棒估计|ADAPT；新增环中心/法向与RGB的组合残差；禁止主体/ICP/逐帧自由度|
|contracts.coordinates + multisurface.sample_mesh/mesh_sections + sim.closest/cast|投影契约、固定可见GT域、真实三角截面|REUSE；所有方法共用004规范，无GT拟合对齐|
|新V6 HIST两视频实际camera/tracks/ledger/原生HERO/surface/mesh|接口、单位/身份/视角范围/误差参照|ADAPT；只读并哈希保护小型接口快照，不把预测作为模拟GT|

## 固定实验
一个物理G01静止息肉。原清单16 FIT（每视频8）、8 HOLDOUT（原样）。每视角重新光线投射，生成不同RGB/Mask/理想轴深度/独立网格。世界/物体坐标确定性多尺度纹理，背景常量，无图像坐标纹理。保持原K=490及640×360；原模拟视角与新V6视角范围分别列出。

M0恒等；M1对齐Ring中心和有向法向的最小旋转，故绕法向yaw不可辨识，禁止使用CAD离散顶点索引消除yaw。M2：M1后72格yaw初始化，以训练地标3D距离中位数选初值；6参数rotvec(rad)+t(mm)，最多100函数评价，soft_l1，RGB三维残差/0.2mm，Ring中心残差/0.1mm与5.6×法向差/0.1mm；RGB不预缩小鲁棒残差，Ring残差乘训练地标数平方根，Ring相对权重1；不优化scale。训练轨迹原V6 modulo5留出；至少6训练跨视频轨迹（每视频至少2个观测），各视频三角化重投影最大≤6px、正深度、视差≥0.5°。不按GT选点。没有足够轨迹则REJECT，不补已知对应替代。

V0恒等。V1对005整个坐标系施加Rz(30°)@Ry(3°)、世界X平移0.3mm（保留原B条件倾斜/平移）；004恒等。包括相机、地标、全部网格、Ring表示。注入矩阵仅生成器/评价器访问。
V2在V1之上只改005逐帧相机测量：原noise_vectors规则中心化高斯，旋转sigma0.3°、平移sigma0.1mm，种子20261117..20261121；固定物理Ring/RGB/深度不变。C_est = D @ C_true @ N_frame。网格依测量相机定位；地标依测量相机重新三角化。每方法相同噪声。不能用一个T消除逐帧残差。

## 运行前验收门槛
- 刚体/换坐标契约：detR误差1e-6；视频内相对相机/投影/轴向Z差≤1e-8（float64）；光线重建误差≤0.001mm（原生成器精度）。
- 原SIM精度门槛沿用旋转≤0.5°、平移≤0.2mm；留出RGB MAE≤3px/P95≤6px沿用V6；固定GT可见域覆盖阈值0.2mm沿用multisurface。V0新增表面P95≤0.02mm，覆盖下降≤1个百分点。V1 M2满足位姿门槛且比M1改善yaw。V2报告5种子全结果，不以失败调整门槛。
- 表面目标从原GT按面积采12000点（固定种子），以真实相机可见性确定004/005交集/并集；共同分母冻结。缺面距离Inf、覆盖失败，不删；另报反向预测面到GT距离。留出视角固定可见物理点重投影；自动留出轨迹另列，不冒称全链路真实数据留出成功。

## 执行清单
- [x] 资产SHA/父运行/实际基提交核对；保护必要小资产。
- [ ] 测试先行：坐标换基不变性、Ring yaw不可辨识、6DoF及尺度拒绝、无匹配拒绝、稳定纹理世界锁定。
- [ ] 新V6 HIST适配审计；冻结配置/源码/数据身份。
- [ ] 生成独立双视频观测，调用原V6自动匹配与三角化；先运行V0/V1实施契约，再V2五种子。
- [ ] 预测独立进程冻结后评价；已知对应仅单列诊断（如执行）。
- [ ] 六视角GT/前/后、真实网格截面、RGB匹配/重投影、失败图；逐条件小表与唯一技术报告。
- [ ] 原函数回归/接口检查、独立代码审查、显式git add与提交push、远端SHA核验。

实现文件：code/common.py（I/O与固定路径），code/v6_adapter.py（原V6 AST与实际快照读取），code/generate.py（生成器），code/registration.py（仅公开观测求解），code/evaluate.py（冻结后评价），code/visualize.py（图），code/test_contracts.py。入口 bash run_python.sh code/<stage>.py；运行中失败追加evidence/FAILURES.json，不覆盖。

运行前单元测试修正：最初把RGB残差除以sqrt(N)，扩大了soft_l1有效截断尺度，4/80离群点导致6DoF合成测试失败（矩阵误差0.205）。正式观测生成前改为RGB保持0.2mm鲁棒尺度、Ring乘sqrt(N)。无GT实验结果参与此修正；失败日志保留。
