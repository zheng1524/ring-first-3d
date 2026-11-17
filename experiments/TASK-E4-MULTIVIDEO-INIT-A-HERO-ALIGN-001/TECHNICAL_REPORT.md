# TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001

![Figure1: actual historical Init-A and multivideo predictions, true scale1 GT alignment copies](visualization/figures/Fig1_All_InitA_Bodies.png)

**最终回答：004+005在合法实体IoU可评价的3组（G01/G10/G11）上更好，但没有证据证明全11组普遍更好；这种形状收益没有进一步带来稳定的真实HERO统一定位收益。**

- 严格IoU共同有效3/11组：均值 **0.746908→0.767866**，3/3提高。不能将其余无效实体的条件占据值冒充严格IoU。
- A1/A2共同数值10/11组：条件占据IoU仅5/10提高；曲面Chamfer仅6/10下降，均值 **0.465918→0.458505mm**。G08缺004，两条新臂均为NaN，不用005冒充。
- 真实HERO：4/11组有来源绑定完整多曲面（其中3组含004+005，G06仅004）；其余组保留旧深度库存但本轮未接入可核验的完整多曲面接口，列为迁移未完成/NOT_EVALUABLE，不能当成算法失败或成功。
- 3个双视频组中，A2相对A1的跨视频最近表面一致性仅G05略好 **0.275479→0.275344mm**；G01 **0.480163→0.480198mm**、G03 **1.930246→1.953501mm**均未改善。G05收益极小；真实数据没有独立三维GT，不能解释为绝对位置精度。

G02确认的半椭球起点没有被本轮成功纠正：条件IoU **0.537035→0.524640**，曲面MAE **0.339934→0.364178mm**；实际GT刚体对齐图仍显示错误半体形态。G03仍没有长柄。所有负结果与六个独立A2S控制保留，不用GT事后改选S臂。

## 版本来源与科学范围

015正式来源`905e2a9b3615a5f429553837a05e5d53826cef03`；A0为历史Init-A FINAL不可修改参考。A1与A2全部从真实FREE_VERTEX_013/inputs/.../INITIAL.npz开始，V/F/F_solid/基底标记与015 Init-A完全核验一致，没有E1/E2/Init-B/Init-C替代。训练调用原train_mesh.main、PyTorch3D Case/RingAware、FreeVertices、密集32/FCL/反向包含/自交保护、Adam/线搜索/顶点更新和80提案/40接受/30连续拒绝停止。只增加输入与多视频分母适配，原代码逐文件SHA锁定。所有预测取最后接受状态，不按GT或HOLDOUT挑checkpoint。

004 FIT为015原8视角；005从014已有Ring-First/明确标记的派生相机中按方向最远点选8视角，GT不参与。每视频/每方向/每视角使用历史weights函数；弱深度项保留历史原始观测，仅将可用深度按视频/视角均衡，未生成新HERO。HOLDOUT不参与梯度、共享修正或模型选择。A2是一个共享Mesh，不是拼接两个Body。G08只有005，004-only和004+005均NOT_EVALUABLE，未冒充004。原014 G01跨视频共享位姿候选并无部署认证；直接版本如实使用既有相机来源，不能宣称绝对坐标正确。

G02经实际初始Mesh和RGB/Mask核验为半椭球/扁帽状起点；G03原椭球未表达图像长柄。两者同算法，不使用形态补丁。A2若FIT005 IoU比004低>0.10或005<0.5，另行A2S：004固定、005一个共享SE3、FIT轮廓/Ring/先验求解后，从同一013起点重新跑原训练。A2/A2S独立报告，没有GT或逐帧相机优化，也未静默替换直接结果。

## 真正的GT刚体评价与IoU有效性

所有适用cohort预测先冻结，再逐模型复用best_rigid015.align：96固定旋转起点、top8双向真实最近曲面/刚性Kabsch与SE3回溯，尺度1；不认证数学全局最优。每组保存完整T、起点日志及实际对齐NPZ/PLY。GT变换只作用评价副本，训练Mesh、相机、Ring、HERO输入均逐SHA保护。Figure1所有预测使用各自真正对齐副本以便统一GT坐标比较，原公制结果另存Figure2/4和运行文件。

IoU采用每例统一三维范围和相同2^17 Sobol三维点计算交并，不是原世界坐标假叠加。严格IoU要求双方闭合/一致朝向/无自交且无未认证推断基底；否则严格IoU为NaN。另报conditional_occupancy_IoU，实体无效时只是原F_solid射线奇偶诊断，不能称合法实体IoU。8192样本/方向查询实际三角面给Chamfer、P95、最大值、GT覆盖和0.5mm F-score。相对表面误差明确定义为绝对距离/GT包围盒对角线，不冒充DXY直径相对误差。

## 全部主体结果

| Case / arm | Strict IoU status | Conditional occupancy IoU | Chamfer MAE / P95 mm | F-score0.5 |
| --- | --- | --- | --- | --- |
| G01 / A0 | VALID_SOLID_SOBOL_ESTIMATE | 0.816343 | 0.402707 / 1.012536 | 0.775279 |
| G01 / A1 | VALID_SOLID_SOBOL_ESTIMATE | 0.816302 | 0.402749 / 1.012765 | 0.775600 |
| G01 / A2 | VALID_SOLID_SOBOL_ESTIMATE | 0.834192 | 0.379809 / 1.025947 | 0.825755 |
| G02 / A0 | NOT_EVALUABLE_ENTITY_VALIDITY | 0.537102 | 0.339596 / 1.558552 | 0.801218 |
| G02 / A1 | NOT_EVALUABLE_ENTITY_VALIDITY | 0.537035 | 0.339934 / 1.558527 | 0.801901 |
| G02 / A2 | NOT_EVALUABLE_ENTITY_VALIDITY | 0.524640 | 0.364178 / 1.626153 | 0.788052 |
| G02 / A2S | NOT_EVALUABLE_ENTITY_VALIDITY | 0.517339 | 0.392342 / 1.686385 | 0.770390 |
| G03 / A0 | NOT_EVALUABLE_ENTITY_VALIDITY | 0.777050 | 1.269663 / 9.055126 | 0.638772 |
| G03 / A1 | NOT_EVALUABLE_ENTITY_VALIDITY | 0.777050 | 1.269663 / 9.055126 | 0.638772 |
| G03 / A2 | NOT_EVALUABLE_ENTITY_VALIDITY | 0.775788 | 1.273195 / 9.086725 | 0.632349 |
| G03 / A2S | NOT_EVALUABLE_ENTITY_VALIDITY | 0.760706 | 1.270143 / 8.374495 | 0.446875 |
| G07 / A0 | NOT_EVALUABLE_ENTITY_VALIDITY | 0.593302 | 0.737184 / 2.421801 | 0.385946 |
| G07 / A1 | NOT_EVALUABLE_ENTITY_VALIDITY | 0.593302 | 0.737184 / 2.421801 | 0.385946 |
| G07 / A2 | NOT_EVALUABLE_ENTITY_VALIDITY | 0.593261 | 0.737234 / 2.422401 | 0.385970 |
| G04 / A0 | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | 0.693277 | 0.193776 / 0.983894 | 0.850810 |
| G04 / A1 | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | 0.693277 | 0.193776 / 0.983894 | 0.850810 |
| G04 / A2 | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | 0.725057 | 0.197434 / 0.993852 | 0.847698 |
| G04 / A2S | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | 0.777360 | 0.205313 / 0.915475 | 0.871781 |
| G05 / A0 | NOT_EVALUABLE_ENTITY_VALIDITY | 0.812951 | 0.661555 / 3.875955 | 0.745475 |
| G05 / A1 | NOT_EVALUABLE_ENTITY_VALIDITY | 0.812951 | 0.661555 / 3.875955 | 0.745475 |
| G05 / A2 | NOT_EVALUABLE_ENTITY_VALIDITY | 0.817150 | 0.654087 / 3.884900 | 0.754022 |
| G06 / A0 | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | 0.870115 | 0.251145 / 1.221020 | 0.784660 |
| G06 / A1 | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | 0.870115 | 0.251145 / 1.221020 | 0.784660 |
| G06 / A2 | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | 0.863473 | 0.251043 / 1.220673 | 0.786011 |
| G06 / A2S | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | 0.867249 | 0.250520 / 1.224399 | 0.784660 |
| G08 / A0 | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | 0.801611 | 0.650531 / 3.351707 | 0.635424 |
| G08 / A1 | NOT_EVALUABLE_NO_PREDICTION | NaN | NaN / NaN | NaN |
| G08 / A2 | NOT_EVALUABLE_NO_PREDICTION | NaN | NaN / NaN | NaN |
| G09 / A0 | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | 0.133699 | 0.187363 / 0.815075 | 0.874803 |
| G09 / A1 | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | 0.133699 | 0.187363 / 0.815075 | 0.874803 |
| G09 / A2 | NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE | 0.124211 | 0.180399 / 0.823393 | 0.869445 |
| G10 / A0 | VALID_SOLID_SOBOL_ESTIMATE | 0.782682 | 0.236531 / 0.504953 | 0.946652 |
| G10 / A1 | VALID_SOLID_SOBOL_ESTIMATE | 0.782682 | 0.236534 / 0.504956 | 0.946652 |
| G10 / A2 | VALID_SOLID_SOBOL_ESTIMATE | 0.799753 | 0.213822 / 0.447284 | 0.964955 |
| G10 / A2S | VALID_SOLID_SOBOL_ESTIMATE | 0.809846 | 0.207768 / 0.493218 | 0.956177 |
| G11 / A0 | VALID_SOLID_SOBOL_ESTIMATE | 0.639473 | 0.381452 / 0.739930 | 0.735687 |
| G11 / A1 | VALID_SOLID_SOBOL_ESTIMATE | 0.641742 | 0.379274 / 0.824645 | 0.733231 |
| G11 / A2 | VALID_SOLID_SOBOL_ESTIMATE | 0.669654 | 0.333854 / 0.713954 | 0.750774 |
| G11 / A2S | VALID_SOLID_SOBOL_ESTIMATE | 0.681437 | 0.325237 / 0.775149 | 0.757784 |

## 真实HERO定位与接口限制

复用近期真实原生HERO适配器，严格验证深度/K/C/源像素/原Mask/DXY哈希/完整网格拓扑。对于无>=2个来源绑定完整Mesh的物理组逐组NOT_EVALUABLE，不把旧融合结果、采样点或新生成模型补齐。所有11组保留原HERO来源库存，缺接口并不删除目标分母。G01/G03/G05优先端到端Smoke后才扩展全组。

使用实际Init-A Mesh的表观轮廓拟合二维投影椭圆作为中介，所有射线必须命中实际Init-A Face/重心；没有三维椭球替换。BODY_HIER的优化函数代码不变，只适配其投影数据提供器。M0、BODY_A0、BODY_A1、BODY_A2及原Robust ICP分开输出；每视频共享SE3和0.3°/0.10mm先验约束帧残余，Body容差0.5mm，所有Body固定，曲面保持整体刚性和完整原顶点/拓扑。GT对齐Body从不进入HERO。

最近表面一致性使用配准前投影Mask冻结支持查询，不是独立材料真值。真实HERO无独立GT，绝对位置/误差NOT_EVALUABLE；保留跨视频原坐标不确定性、留出投影、对应拒绝、修正幅度和边长不变断言。Figure4没有最终融合层遮住局部曲面。

## 配对回答

{
  "target_cases": 11,
  "numeric_body_rows": 37,
  "strict_IoU_rows": 11,
  "paired_body_cases": 10,
  "conditional_IoU_A2_better_cases": 5,
  "Chamfer_A2_better_cases": 6,
  "HERO_numeric_groups": 4,
  "HERO_absolute_accuracy": "NOT_EVALUABLE",
  "GT_aligned_world_inputs": false
}

同组共同数值样本比较A2-A1，不按结果剔除失败。严格实体IoU不足时不把conditional值升级为严格主要指标。最终结论需同时核查对照表、图像、条件占据限制与HERO留出表现。

## 固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 历史全部11个物理组，不将实验臂或视频当作独立病例 |
| 本算法独立成功 | 数值输出、严格IoU可计算、形状正确、真实HERO多视频定位分别统计，见完整JSON/CSV |
| 本算法失败 | G08缺004等逐组NOT_EVALUABLE/NaN；IoU实体无效、HERO接口缺失与科学负结果全部保留 |
| 历史测量值回退 | 0；A0仅不可修改参考，授权013输入Mesh不作为最终结果回填 |
| 失败组及具体原因 | FAILURE_LEDGER、主体GT有效性、真实HERO来源缺口和每病例图 |
| 最终统计样本 | 所有目标11组保留；各项可计算N及共同样本配对独立报告 |
| 是否使用GT选择算法 | 否；协议/源码/输入及最后接受checkpoint冻结，GT只在评价副本中作尺度固定SE3 |

### G01

![G01 actual aligned Meshes](visualization/figures/G01_BODY_GT.png)

![G01 native Mask explanations](visualization/figures/G01_FIG2_MASKS.png)

[G01实际GT对齐Mesh交互](visualization/G01/index.html)

![G01 full HERO actual cuts](visualization/figures/G01_FIG4_HERO_CUTS.png)

[G01完整HERO逐曲面交互](visualization/G01_HERO/index.html)

### G02

![G02 actual aligned Meshes](visualization/figures/G02_BODY_GT.png)

![G02 native Mask explanations](visualization/figures/G02_FIG2_MASKS.png)

[G02实际GT对齐Mesh交互](visualization/G02/index.html)

### G03

![G03 actual aligned Meshes](visualization/figures/G03_BODY_GT.png)

![G03 native Mask explanations](visualization/figures/G03_FIG2_MASKS.png)

[G03实际GT对齐Mesh交互](visualization/G03/index.html)

![G03 full HERO actual cuts](visualization/figures/G03_FIG4_HERO_CUTS.png)

[G03完整HERO逐曲面交互](visualization/G03_HERO/index.html)

### G07

![G07 actual aligned Meshes](visualization/figures/G07_BODY_GT.png)

![G07 native Mask explanations](visualization/figures/G07_FIG2_MASKS.png)

[G07实际GT对齐Mesh交互](visualization/G07/index.html)

### G04

![G04 actual aligned Meshes](visualization/figures/G04_BODY_GT.png)

![G04 native Mask explanations](visualization/figures/G04_FIG2_MASKS.png)

[G04实际GT对齐Mesh交互](visualization/G04/index.html)

### G05

![G05 actual aligned Meshes](visualization/figures/G05_BODY_GT.png)

![G05 native Mask explanations](visualization/figures/G05_FIG2_MASKS.png)

[G05实际GT对齐Mesh交互](visualization/G05/index.html)

![G05 full HERO actual cuts](visualization/figures/G05_FIG4_HERO_CUTS.png)

[G05完整HERO逐曲面交互](visualization/G05_HERO/index.html)

### G06

![G06 actual aligned Meshes](visualization/figures/G06_BODY_GT.png)

![G06 native Mask explanations](visualization/figures/G06_FIG2_MASKS.png)

[G06实际GT对齐Mesh交互](visualization/G06/index.html)

![G06 full HERO actual cuts](visualization/figures/G06_FIG4_HERO_CUTS.png)

[G06完整HERO逐曲面交互](visualization/G06_HERO/index.html)

### G08

![G08 actual aligned Meshes](visualization/figures/G08_BODY_GT.png)

![G08 native Mask explanations](visualization/figures/G08_FIG2_MASKS.png)

[G08实际GT对齐Mesh交互](visualization/G08/index.html)

### G09

![G09 actual aligned Meshes](visualization/figures/G09_BODY_GT.png)

![G09 native Mask explanations](visualization/figures/G09_FIG2_MASKS.png)

[G09实际GT对齐Mesh交互](visualization/G09/index.html)

### G10

![G10 actual aligned Meshes](visualization/figures/G10_BODY_GT.png)

![G10 native Mask explanations](visualization/figures/G10_FIG2_MASKS.png)

[G10实际GT对齐Mesh交互](visualization/G10/index.html)

### G11

![G11 actual aligned Meshes](visualization/figures/G11_BODY_GT.png)

![G11 native Mask explanations](visualization/figures/G11_FIG2_MASKS.png)

[G11实际GT对齐Mesh交互](visualization/G11/index.html)

![G02/G03 failure details](visualization/figures/Fig3_Verified_Ip_Failures.png)

## 最终共同样本回答与实际优化证据

```json
{
  "task_id": "TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001",
  "implementation_commit": "6ee15cff25f96bea02073428da6ce6cd2af91947",
  "target_physical_cases": 11,
  "paired_body_cases": 10,
  "strict_IoU_pair_cases": 3,
  "conditional_IoU_A2_better_cases": 5,
  "Chamfer_A2_better_cases": 6,
  "mean_conditional_IoU_delta": 0.0069023720481076935,
  "mean_Chamfer_delta_mm": -0.007412238279970282,
  "HERO_numeric_groups": 4,
  "HERO_two_video_groups": 3,
  "HERO_cross_A2_better_cases": 1,
  "HERO_cross_paired_cases": 3,
  "GT_used_for_training": false,
  "GT_aligned_HERO": false,
  "historical_measurement_fallback": 0,
  "strict_IoU_A2_better_cases": 3,
  "mean_strict_IoU_delta": 0.02095783106445137
}
```

[全部11组HERO方法CSV](visualization/HERO_ALL11_METRICS.csv) · [同病例A1/A2完整配对](visualization/FINAL_PAIRED_ANSWERS.csv) · [004/005 FIT/HOLDOUT逐帧投影](visualization/WORLD_MASK_PROJECTION.csv) · [实际优化/拒绝/可动顶点支持](visualization/OPTIMIZATION_DIAGNOSTICS.json) · [005互补视角与留出隔离](visualization/VIEW_COMPLEMENTARITY_AND_ISOLATION.json) · [实际共享与帧残余修正](visualization/HERO_PREDICTIONS_AND_TRANSFORMS.json)。

没有新增主体结构：每个初始网格仍为原N×3顶点自由度，并保留原基底约束/保护。若新增视角仍不能恢复头柄，本轮仅由实际支持区、梯度、接受/拒绝和真实三维形变诊断；没有足够对照将原因唯一归结为拓扑、先验或优化失败。

原INIT_A_001在科学开始前回归门禁失败；校验顺序修复后新INIT_A_002重新执行原35项与全部130项回归，未绕过门禁。原失败与源码版本证据完整保留。GT仅作用评价副本。

## 失败Ip的可动自由度、实际支持与优化瓶颈

G02 A1/A2的名义线性几何自由度均1683；FIT支持顶点由358增至573，但实际最大位移仅0.482/0.570mm，形状并未可靠恢复。G03均1926自由度，支持顶点由292增至369；A1/A2分别只接受22/25步，最大位移0.471/0.439mm。A2候选原因统计：Ring穿透恶化1675、反向包含恶化1712、完整FIT目标拒绝107次；拒绝原因可同时出现，不能当作独立候选数相加。

这直接支持“新视角增加了支持，但现有几何约束下优化停滞”，不是顶点没有自由度。当前固定预算/约束的对照不足以唯一分离分辨率、初始形状、可见性、先验与优化器的因果贡献，不能据此断言必须换主体架构。G03共享005版本也在23接受后停滞，没有形态专项补丁。

初始与最终均以同一密集64三角面/Ring查询及自交API独立复核。训练原有密集32/FCL/反向包含检查未删；本轮未发现超过原1e-5mm容差的新增穿透恶化，已有微小穿入仍保留。完整前后有符号距离、自交、面积比、步长上限与位移见OPTIMIZATION_DIAGNOSTICS。原损失ramp随attempt变化，跨attempt总目标不能当作固定权重单调曲线；接受比较仍是同次权重。

## 来源版本与留出范围

[完整版本来源表](VERSION_SOURCES.csv)逐文件列出52个015源码、全部11个013初值/A0、继承HERO API及新接口SHA。[历史提交数据核验](evidence/HISTORICAL_905_DATA_VERIFICATION.json)确认初始和A0与905e2a9提交内清单一致。精确双精度世界模型和GT评价副本在review_meshes，包含观测F、F_solid、推断基底及T；不是仅供显示的采样点。

新增005是否提供互补方向见每例VIEW_COMPLEMENTARITY_AND_ISOLATION；角度来自既有相机/初始主体中心，不是独立世界部署认证。HERO留出图与本轮Body FIT无RGB内容哈希重合；留出是本轮更新的留出，不声称整个历史相机/初始化链从未见过。历史Init-A已有弱HERO深度项按用户要求保留；第二部分不再据HERO更新主体，所有HERO对照均使用原公制世界模型，不读取GT对齐坐标。

[精确模型目录](review_meshes/index.html)按病例提供WORLD/ALIGNED NPZ；全部完整HERO原几何/拓扑、优化器/RNG检查点、候选拒绝与对齐PLY在本地原始runs中保留。Git只提交精选几何和离线审阅资产，不上传原视频、HERO权重或完整训练缓存。

## 实测验收

130项回归、13阶段执行/产物门禁通过；15个实际Mesh离线页面逐一通过Chrome渲染（11个真正GT对齐页面、4个完整HERO页面），JavaScript异常0，逐视频/曲面开关有效。严格IoU有效性、科学失败、执行完成分开。最初INIT_A_001门禁失败和修复经过见ENGINEERING_FIXES，未启动那次科学训练。最终整理时仅回收本会话已关闭浏览器的临时缓存，实验文件和历史证据没有清理。
