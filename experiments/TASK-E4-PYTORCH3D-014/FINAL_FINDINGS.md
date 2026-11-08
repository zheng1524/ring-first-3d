# 最终发现

不建议将014整体替换历史基线；保留新视角组织与几何保护作为待审组件，不宣称三维普遍改善。

统一方法C=C4_ALL / coarse=D_D2_bidir / E=E0_none。014 Chamfer相对013改善4/11，均值差0.0331mm；独立Ring非恶化失败1/11。

| 问题 | 判断 | 证据 |
| --- | --- | --- |
| Q1 | SUPPORTED | 资产索引、方向聚类、代表帧、SIFT/PnP、渲染及最佳SE3评价复用；旧Polyp-HERO配准和稀疏Ring检查拒绝复用。CODE_REUSE_AUDIT.md |
| Q2 | PARTIALLY_SUPPORTED | C0实际视角数依组变化，并非每组均为3。C4相对C0平均Chamfer变化-0.00512mm，二维均值有小幅改善；G03仍缺完整长柄，不能证明仅增加视角即可解决。 |
| Q3 | SUPPORTED | 候选方向/块/实际N见metrics/VIEW_COVERAGE.csv和VIEW_SELECTION.json；这不是经GT认证的物理覆盖。 |
| Q4 | PARTIALLY_SUPPORTED | G02的C0→C4背景FP/Mask从0.4446降至0.3411，但Recall从0.8355降至0.8246；错误越界改善伴随额外漏覆盖。其他组见同固定分母配对表。 |
| Q5 | PARTIALLY_SUPPORTED | 存在稳定大yaw坐标修正候选，不能区分纯Gauge差异与真实位姿错误。BG独立残差仍大。 |
| Q6 | NOT_SUPPORTED | 尚不能证明Ring/背景/息肉独立投影都稳定改善；负对照非零漂移。B2 NOT_EVALUABLE。 |
| Q7 | NOT_SUPPORTED | B1=C1_8加入005后，004 FIT IoU 0.8947→0.8709、HOLDOUT 0.8898→0.8620。004受支持顶点相对A-only平均漂移0.165mm。005-only支持只是观测代理，不是新增真实表面。不能认证不破坏004。 |
| Q8 | PARTIALLY_SUPPORTED | G02固定视角D0→D2的FP/Mask 0.3411→0.3229，Recall 0.8246→0.8162。正负损失能调节取舍，但未证明同步改善3D；最终G02 Chamfer恶化。 |
| Q9 | PARTIALLY_SUPPORTED | G03远轮廓代理涉及239顶点，4个局部候选带只覆盖30个；远区图像梯度非零，深度梯度范数更大。约47.5%目标轮廓样本落在Ring不确定带；Ring包含/穿透保护是主要拒绝原因。细分未恢复长柄，不能把失败唯一归因于顶点密度或零梯度。 |
| Q10 | NOT_SUPPORTED | E2相对E1平均Chamfer差0.00319mm，仅2/11改善；相对E0有局部收益，但未显示优于全局细分。E1事后GT均值较好不用于改选已冻结E0。 |
| Q11 | PARTIALLY_SUPPORTED | G07–G11中Chamfer改善为['G07', 'G09', 'G11']，G08/G10恶化；G09虽轻微改善但作者基底Hmax误差0.793mm，不能称低隆起形态已恢复。逐例报告及Fig7保留失败。 |
| Q12 | PARTIALLY_SUPPORTED | 二维/三维变化同向8/11，但3例IoU提高且Chamfer恶化；整体Chamfer0.4474→0.4806mm，G03长柄缺失与GT→预测p95恶化一致。G03 Hmax误差小不能掩盖低端缺失。 |
| Q13 | SUPPORTED | 官方渲染、共享参数梯度、有限安全更新和真实Mesh输出可运行；工程可行性不代表主线已验收。 |
| Q14 | PARTIALLY_SUPPORTED | 仍需可靠公制视角/背景静态性、可观测几何对应、接触约束可行方向和网格表达研究。未执行SDFStudio/BundleSDF或其他新路线。 |

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 11个独立真实物理组，不将多视频或多实验臂算成独立病例 |
| 本算法独立成功 | 11/11生成本路线FINAL014数值模型；继承人工授权011初值，数值输出不等于测量正确 |
| 本算法失败 | 数值模型失败0/11；几何验收失败或自交精度分歧3/11；另G01有Ring接触精度分歧；高度NaN 1/11，严格实体IoU NaN 9/11；逐组见FAILURE_LEDGER.md，未剔除困难病例 |
| 历史测量值回退 | 0；011/012/013仅作明确标识的初值或评价对照，没有补填014测量值 |
| 失败组及具体原因 | metrics/FAILURES.csv、逐臂运行日志、全部原始模型及核心图 |
| 最终统计样本 | 数值模型11/11；各评价项实际可计算N分别汇报，空白CSV为NaN而非0 |
| 是否使用GT选择算法 | 否；C/D/E仅用预登记FIT规则；全部模型/尺度先冻结，GT访问时间在provenance/GT_ACCESS_START.json |
