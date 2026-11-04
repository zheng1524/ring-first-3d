# 来源与渲染器核验

父分支实际本地和远端均4a09aedc669092d264f070ccac4fd12851097dd1，无用户脏修改。新工作树独立，未改旧CPU保护。inputs.py只AST提取纯IO/数学函数，逐文件SHA及函数名见metrics/PURE_SOURCE_EXTRACTION.json；没有导入A1 common.py。DXY仅使用父任务已输出的E1九参数结果。

官方nvdiffrast commit253ac4fcea7de5f396371124af597e6cc957bfae，源码文档明确OpenGL clip-space、bottom-up存储及antialias梯度。任务专用runtime安装ninja1.13.2和nvdiffrast0.4.0，未改历史环境。PyTorch2.7.1+cu128，CUDA12.8，RTX3060 Laptop6GiB。实际CV+Z→clip后翻回顶行，对26相机/初值通过P0_RENDERER_GATE；原生352×640/归档360×640映射保持pixel-center。

可微Mask为GPU实际三角面和黑色CAD联合zbuffer；精确原生深度选实际三角面首次命中，再求相机轴向Z的分段可微交点，没有把欧氏射线长度当Z。Native深度导数已与真实像素有限差分核验。历史A→B render函数采用Open3D相同射线/face/bary约定；此处的CPU对照是该渲染内核的受控重用，不运行历史GT评价程序。

每源路径/SHA和清理版本见assets_index/LOCAL_DATA_SOURCES.json，原始输入只读。G07缺当前合格清理，Raw压力状态未升级；G04/G05资格不足。背景G06旧ref04与当前A不同且Gate不足，所有Base关闭。B仅用于冻结评价，不反传。

libigl Python bindings未安装；使用SciPy1.15.3 generalized sparse eigsh，8份实际冻结网格的前158个特征值已分别与稠密广义eigh参考核对一致。额外精确球体控制暴露ARPACK重复特征值漏计，原失败保留，未改变阈值或替换当前输入。稠密球体参考在原3%阈值内（约0.57%误差）；不将它偷换成原稀疏测试PASS。见LAPLACIAN_SYNTHETIC_CONSISTENCY和LAPLACIAN_DENSE_REFERENCE_AUDIT。

<!-- FINAL_AUDIT -->

| 审计项目 | 必须汇报 / 本轮结果 |
| --- | --- |
| 目标组数 | 4个独立物理组G01/G06/G07/G08，4单视频；G01_005不入组；16个初值/seed案例不是16个息肉 |
| 本算法独立成功 | 4/4组均独立输出数值网格；本路线数值执行80/80臂运行；条件性2物理组、压力2组；科学真实几何/测量正确率不可评价 |
| 本算法失败 | 数值网格输出失败0/4组（NaN 0组）；运行硬失败0、未运行0；真实合格Is不可评价；几何/覆盖/FD风险见[失败账本](05_FAILURE_LEDGER.md)，测量及GT误差NaN |
| 历史测量值回退 | 0；父E1/E2九参数只作本轮明确批准P0，不以历史直径或融合模型补输出 |
| 失败组及具体原因 | [逐臂与来源](metrics/FAILURES.csv)、[完整分母](metrics/CASE_ARM_SEED_RESULTS.csv)、[Fig4](figures/Fig4_Ablation_Conflict.png) |
| 最终统计样本 | 4/4物理组的条件/压力配对；80臂只是同4组的重复条件；严格独立验证覆盖0/4（正确性未知），MedARE/MAE/p95/max均NOT_EVALUABLE |
| 是否使用GT选择算法 | 否；GT/Oracle读取0；51116d0预注册、2f7e042最终CAD工程修正后冻结，未以B选参数/模式/初值/展示 |
