# TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001

![Figure1: actual historical Init-A and multivideo predictions, true scale1 GT alignment copies](visualization/figures/Fig1_All_InitA_Bodies.png)

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
