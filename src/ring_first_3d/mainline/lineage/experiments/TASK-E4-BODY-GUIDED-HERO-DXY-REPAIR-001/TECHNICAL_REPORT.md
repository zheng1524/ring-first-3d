# Body-E DXY初始化修复技术报告

本轮已按顺序执行Phase0–5。官方DXY重新计算75/75产生候选；四组主分析及两个附加005池的E1/E2均产生独立收敛数值解，但**无结果达到预登记的完整下一阶段门槛**，本轮不建议接入HERO对应。高IoU不能消除多初值、Ring穿透或留出轮廓矛盾。

## 输入审计纠错

前一条聊天所称“32来源缺位姿”有误：只查了新Git checkout和RAW initial_pose，漏查原始资产目录的FINAL_CAMERA_POOL。现已按旧prepare的真实绑定核验75来源原生K/T；原错误产物完整归档于provenance/SUPERSEDED_PHASE0。18个OLD018原生位姿与最终池存在小幅版本差异，采用原native T并逐源记录，未修改相机。详见METHOD_AND_INPUT_AUDIT.md。

## 官方二维几何

DXY固定commit `75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95`，VERSION=DXY-MID-1.0.0rc1，Geometry=V9.1；73个measure_files和2个640×360缓存measure_frame。R10内径10mm。质量为{'Q_conflict_recovery': 37, 'normal_Gate_pass': 38}；75/75是候选覆盖，不等于解剖边界正确。没有缺失candidate，缺失名单为空；没有读取/保存DXY毫米结果。所有Ring/P/Q质量和原生basis见metrics/DXY_QUALITY_AUDIT.csv。

预测冻结后才重算旧DT+AMS作对照：中心位移median=18.555px、p95=44.172px、max=54.505px；新旧几何区域IoU median=0.740。逐源数值见metrics/DXY_VS_OLD_DT_AMS.csv。差异来自完整正式Ring/P/Q/候选选择流程，不能称官方几何只是旧AMS的缩放；此对照未进入拟合。

## 公平性、视角与实际代码

E1仅将官方中心/basis按A1矩阵约定转换；E2完整原始Mask，柄和外围结构均保留。九参数模型、解析投影、二维损失与TRF.solve均从历史源码AST原样执行，非另写近似损失。唯一拟合适配为当前75源接口、删除所有depth_parts调用、成功资格筛选和轨迹保存。相同R0、三初值、权重、边界、预算经实际参数逐项核对。max_nfev=60，36次拟合；两个预算耗尽结果保留并排除。实际复用函数、行号、完整源码SHA和AST SHA见CODE_REUSE_MAP.md与provenance/CODE_REUSE_FUNCTIONS.json。

四组004各8FIT，未使用原来的固定三帧名单；G01/G03的005独立6/4FIT。所有未选合格帧留出，全部75登记，重复RGB不作独立证据。未证明跨视频坐标关系可忽略版本与条件依赖，故不合并；两个独立照片及G05单帧005不足多视角，不生成椭球。021身份审计实际重放553个描述子观察和547条RGB-RANSAC链接，但证据只适用于G01且全部背景；不推广至G03/G05/G06。MAX直接PnP共用004地图仅提供条件证据。

## 数值输出与完整验收

| pool | arm | FIT | HOLDOUT | numerical | eligible_starts | heldout_IoU | fixed_boundary_MAE_px | surface_multistart_p95_mm | Ring_min_mm | HERO_gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G01_004 | E1 | 8 | 9 | True | 3 | 0.8135 | 12.25 | 1.484 | 0.01999 | False |
| G01_004 | E2 | 8 | 9 | True | 3 | 0.8541 | 9.501 | 4.455 | -0.08509 | False |
| G01_005 | E1 | 6 | 2 | True | 3 | 0.9313 | 4.572 | 1.731 | -0.4582 | False |
| G01_005 | E2 | 6 | 2 | True | 3 | 0.9142 | 6.622 | 7.763 | -0.5768 | False |
| G01_PHOTO | E1 | 0 | 1 | False | 0 | None | None | None | None | False |
| G01_PHOTO | E2 | 0 | 1 | False | 0 | None | None | None | None | False |
| G03_004 | E1 | 8 | 4 | True | 3 | 0.8401 | 11.38 | 1.484 | 0.3523 | False |
| G03_004 | E2 | 8 | 4 | True | 3 | 0.859 | 11.93 | 2.288 | -0.05597 | False |
| G03_005 | E1 | 4 | 2 | True | 3 | 0.8669 | 7.153 | 11.85 | 0.97 | False |
| G03_005 | E2 | 4 | 2 | True | 2 | 0.8928 | 6.53 | 9.84 | -0.1111 | False |
| G05_004 | E1 | 8 | 5 | True | 3 | 0.8995 | 6.489 | 10.46 | -0.5633 | False |
| G05_004 | E2 | 8 | 5 | True | 2 | 0.8902 | 6.57 | 9.653 | -0.5487 | False |
| G05_005 | E1 | 0 | 1 | False | 0 | None | None | None | None | False |
| G05_005 | E2 | 0 | 1 | False | 0 | None | None | None | None | False |
| G05_PHOTO | E1 | 0 | 1 | False | 0 | None | None | None | None | False |
| G05_PHOTO | E2 | 0 | 1 | False | 0 | None | None | None | None | False |
| G06_004 | E1 | 8 | 5 | True | 3 | 0.9289 | 1.933 | 3.774 | -0.2596 | False |
| G06_004 | E2 | 8 | 5 | True | 3 | 0.8588 | 15.78 | 7.193 | -0.114 | False |

IoU在相同完整原始Mask上、排除Ring未知像素。轮廓距离单位px；实际每帧双向/固定源mean、median、p95、maximum及FN/FP固定分母见metrics/ALL_VIEW_EVALUATION.csv，FIT/HOLDOUT明确区分。主分析共同成功23张HOLDOUT的配对比较见metrics/PAIRED_HOLDOUT_COMPARISON.csv；按4物理组汇总而非把23帧当独立物理组。

这些HOLDOUT未参与本轮Body拟合，但历史相机/RGB地图/分割祖先可能已经用过相关图像；因此是条件性留出，不冒充完全外部独立测试。全部来源原来属于HERO FIT库存，新的Body FIT/HOLDOUT身份与旧任务身份分别记录。

## E1/E2何者更适合

主组HOLDOUT中位IoU：E2高于E1的是G01/G03；E1高于E2的是G05/G06。G01/G03的E1三初值更稳定且没有<-0.05mm表面Ring穿透，但完整Mask固定源轮廓误差仍未过门槛。E2可提高完整Mask覆盖，却可能通过不同三维形状解释类似二维轮廓。结论为MIXED/INSUFFICIENT_EVIDENCE，不宣布某方案普适更优，不用GT或Body-U挑结果。

## 退化与可辨识性

新主解不再出现上一轮20mm长轴或0.3mm薄轴；G06 E1仍触及旋转参数边界。许多池存在大于2mm的多初值表面差异；G05近球形使旋转本身歧义，不能把旋转差单独当形状差。actual mesh表面距离已经计算，失败台账不隐藏这种区别。

不含先验的二维观测Jacobian已SVD。全多视角局部条件数显著优于大多数单视角，但含CAD软可见性及float32射线离散时，单视角数值rank9也可能出现；它不是九个独立轮廓自由度的证据。另提供每视角5个解析椭圆系数的conic-only Jacobian，单视角至多rank5。多视角局部信息改善不证明全局唯一，更不能消除多初值和Ring矛盾；未跑单视角反事实拟合，因此不能声称严格因果改善。

## Ring与历史对照

所有六方向图采用mm等比例，灰色真实Ring CAD，粉色E1、蓝色E2、橙色历史Body-U。Body-U仅预测冻结后读取，属于历史正式R3 B3多HERO训练结果，含历史整合，不能作GT。metrics/BODY_U_COMPARISON.json只报告差异。整个椭球背面及被遮挡轮廓都是推断，绿色原Mask可观察轮廓与Ring接触未知边界在图中区分。Ring检查为实际网格/2048表面样本、11射线有符号距离的有限采样证据，不冒充无穿透数学证书；G03 E2最浅穿透接近阈值，需结合数值精度审阅。

## 失败和下一阶段

- G01_004/E1: HELDOUT_PROJECTION_INCONSISTENT; [实际投影图](figures/G01_004_ALL_VIEW_OVERLAYS.png)，[三维关系](figures/G01_004_SIX_DIRECTION_BODIES.png)，[冻结主解](local_results/G01_004/E1/SELECTION.json)。
- G01_004/E2: MULTISTART_UNSTABLE, RING_BODY_SURFACE_PENETRATION; [实际投影图](figures/G01_004_ALL_VIEW_OVERLAYS.png)，[三维关系](figures/G01_004_SIX_DIRECTION_BODIES.png)，[冻结主解](local_results/G01_004/E2/SELECTION.json)。
- G03_004/E1: HELDOUT_PROJECTION_INCONSISTENT; [实际投影图](figures/G03_004_ALL_VIEW_OVERLAYS.png)，[三维关系](figures/G03_004_SIX_DIRECTION_BODIES.png)，[冻结主解](local_results/G03_004/E1/SELECTION.json)。
- G03_004/E2: MULTISTART_UNSTABLE, HELDOUT_PROJECTION_INCONSISTENT, RING_BODY_SURFACE_PENETRATION; [实际投影图](figures/G03_004_ALL_VIEW_OVERLAYS.png)，[三维关系](figures/G03_004_SIX_DIRECTION_BODIES.png)，[冻结主解](local_results/G03_004/E2/SELECTION.json)。
- G05_004/E1: MULTISTART_UNSTABLE, RING_BODY_SURFACE_PENETRATION; [实际投影图](figures/G05_004_ALL_VIEW_OVERLAYS.png)，[三维关系](figures/G05_004_SIX_DIRECTION_BODIES.png)，[冻结主解](local_results/G05_004/E1/SELECTION.json)。
- G05_004/E2: NOT_ALL_THREE_STARTS_ELIGIBLE, MULTISTART_UNSTABLE, RING_BODY_SURFACE_PENETRATION; [实际投影图](figures/G05_004_ALL_VIEW_OVERLAYS.png)，[三维关系](figures/G05_004_SIX_DIRECTION_BODIES.png)，[冻结主解](local_results/G05_004/E2/SELECTION.json)。
- G06_004/E1: PARAMETER_BOUND_OR_AXIS_RATIO_RISK, MULTISTART_UNSTABLE, RING_BODY_SURFACE_PENETRATION; [实际投影图](figures/G06_004_ALL_VIEW_OVERLAYS.png)，[三维关系](figures/G06_004_SIX_DIRECTION_BODIES.png)，[冻结主解](local_results/G06_004/E1/SELECTION.json)。
- G06_004/E2: MULTISTART_UNSTABLE, HELDOUT_PROJECTION_INCONSISTENT, RING_BODY_SURFACE_PENETRATION; [实际投影图](figures/G06_004_ALL_VIEW_OVERLAYS.png)，[三维关系](figures/G06_004_SIX_DIRECTION_BODIES.png)，[冻结主解](local_results/G06_004/E2/SELECTION.json)。

附加005两个池同样未通过全部门槛。G05_005、G01_PHOTO、G05_PHOTO只有1个源，E1/E2均为null/NaN、不能声称充分多视角。失败来源/帧、候选、图像和三维证据见FAILURE_LEDGER.md。没有执行A2、resection、融合、新训练或修改HERO。下一步是人工审阅这些失败证据，不是自动启动重定位。

真实GT未读取，因此中位绝对相对误差、真实mm MAE/p95/max均NOT_EVALUABLE，不能用投影px指标冒充真实尺寸准确度。可计算的投影误差完整报告固定分母、mean/median/p95/max。验证通过不等于科学验收。

## 固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4独立物理组；75来源（74唯一RGB）；主分析每方案4组，附加005有2池 |
| 本算法独立成功 | E1=4/4、E2=4/4主组独立数值输出；附加各2/2池；完整科研验收0/4组每方案，不能当作测量正确 |
| 本算法失败 | 主组无数值输出失败；完整验收8/8主组方案失败；3单视角池×2方案为null/NaN；36初值有2个未收敛且排除主解 |
| 历史测量值回退 | 0；Body-U和旧DT+AMS只在预测冻结后作对照 |
| 失败组及具体原因 | [逐组失败台账](FAILURE_LEDGER.md)，关联候选、逐帧投影和图集 |
| 最终统计样本 | 仅独立成功主分析4组每方案；23张相同HOLDOUT（各池9/4/5/5）；全部75来源始终登记；不把来源数当独立组数 |
| 是否使用 GT 选择算法 | 否；GT未读，协议→DXY→视角/源码冻结→全部预测冻结→独立评价的SHA回执见provenance |
