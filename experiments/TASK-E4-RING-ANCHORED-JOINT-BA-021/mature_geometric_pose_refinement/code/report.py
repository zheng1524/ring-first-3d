from refine import *
import ast,platform,scipy,collections

def md(rows,keys):
 def val(v):
  if v is None:return 'NaN / NOT_EVALUABLE'
  if isinstance(v,float):return f'{v:.6g}'
  return str(v).replace('|','/')
 return '| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+''.join('| '+' | '.join(val(r.get(k))for k in keys)+' |\n'for r in rows)
def write(n,s):(M/n).write_text(s,encoding='utf8')
def main():
 summary=load(M/'metrics/FOUR_GROUP_POSE_COMPARISON.json');runs=load(M/'metrics/ACTUAL_SOLVER_COUNTS.json');pairs=load(M/'metrics/PAIRED_COMMON_VIEW_COMPARISONS.json');cov=load(M/'metrics/RENDER_COVERAGE_CAUSAL_AUDIT.json');syn=load(M/'metrics/CONICS_SYNTHETIC_MID_AUDIT.json');mid=load(M/'metrics/CONICS_MID_CONTINUOUS_CURVE_CHECK.json');hero=load(M/'metrics/FROZEN_DEPTH_COUNTERFACTUAL.json');gate=load(M/'STAGE_GATE_DECISION.json');vv=load(M/'config/VIEWS.json');j=load(M/'metrics/FIXED_CORRESPONDENCE_JACOBIAN.json');fit=[r for r in summary if r['role']=='FIT'];hold=[r for r in summary if r['role']=='HOLDOUT']
 audit='''\n| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4个物理组×4条新方法；81FIT×4=324条目标相机路线（不是324个独立物理样本），另17HOLDOUT只作冻结保护 |
| 本算法独立成功 | S0 81/81，A1 46/81，A2 81/81，A3 46/81：合计254/324独立数值位姿；不等于真实位姿正确或主线验收通过 |
| 本算法失败 | A1/A3各35例初始化不满足冻结界限，合计70/324条失败NaN；逐帧见FAILED_CAMERA_ROUTES。CAD轮廓完整性FAIL，12照片统一NOT_RUN_VIDEO_COMPLETENESS_GATE |
| 历史测量值回退 | 0；P0为用户要求的对照/先验，HOLDOUT按协议保留原相机，两者不冒充新拟合结果；Conics失败未用S0/P0补齐 |
| 失败组及具体原因 | G01 Conics32/60，G03 1/6，G05 2/8，G06 0/7失败；四组primitive邻接过滤均导致渲染曲线缺口，见初始化JSON、Figure4与失败台账 |
| 最终统计样本 | 全部4组、98canonical视角；254数值结果/324目标，70缺失完整保留。成对比较只用同一成功视角，并报告共同N；17HOLDOUT相机均未独立拟合 |
| 是否使用GT选择算法 | 否；已知CAD/合成相机仅作几何自检，不读真实息肉GT。无HERO/body位姿损失、无HOLDOUT调权/选初始化，照片A2在评价前已登记 |
'''
 compact=md(fit,['group','method','target_N','numeric_N','Ring_IoU','inner_MAE_px','outer_MAE_px','SIFT_HELD_MAE_px','body_IoU','max_center_change_mm'])
 selectedpairs=[r for r in pairs if(r['baseline'],r['candidate'])in [('S0','A1'),('A2','A3')]];pairtable=md(selectedpairs,['group','baseline','candidate','common_N','Ring_IoU_before','Ring_IoU_after','held_SIFT_before_px','held_SIFT_after_px','final_pose_center_difference_mm'])
 cvtable=md([r for r in cov if r['variant']=='ACTUAL_ACCEPTED'],['group','key','N_render_boundary','CAD_segments_N','distance_px','render_boundary_fraction_farther2px'])
 main='''# Mature geometric pose refinement — 四组真实对照结果

**四组324条FIT路线尝试已完成，实际254次相机求解产生数值位姿；70条Conics初始化失败保留NaN。当前状态PAUSED_FOR_HUMAN_DIAGNOSIS，12张独立照片未运行。** 其中8次同配置代表视角结果在Stage1实际求解后直接复用于正式表，没有重复运行。没有HERO推理、主体更新、融合或真实息肉GT读取。

## 结论先行

**局部求导和有界TRF现在能真实运行并下降；但本轮加入的CAD primitive邻接筛选过严，导致几何轮廓不完整，因此A2/A3不能升级为可信相机主线。** 这是本项目Python适配的问题，不是M3T官方方法失败的证据。Stage1初版检查覆盖了圆反演、旧MISS反例、固定对应Jacobian及实际下降，却遗漏“已选CAD曲线能否覆盖自身渲染轮廓”的完整性检查；阶段3补检发现后立即停止照片扩展。没有事后更改权重、阈值或采用修正版本重新拟合。

- S0/A2均完成全部81个FIT数值位姿；81FIT+17HOLDOUT总计98个canonical视角完整保留。
- A1/A3各完成46/81；其余35个选定yaw规范后的Conics候选超出相同P0的冻结公制位置/角度约束，没有回退。
- A2的FIT Ring Mask IoU在G01/G03/G05/G06分别为0.8790→0.8976、0.8662→0.8924、0.9086→0.9198、0.9182→0.9285。但未拟合SIFT轨迹MAE分别从1.400→1.682、0.605→0.913、0.652→1.063、0.742→0.795px；这不是全面几何改善。
- 同一成功视角上，S0与A1最终几乎相同：平均相机中心差约6e−9–2.4e−8mm。当前设置下未证明Conics初始化提供额外稳定性；这不等于Conics数学错误或真实相机已经准确。
- A3相对A2在共同视角上有小幅Ring IoU改善，但四组未拟合SIFT误差均变差，且只有46/81覆盖，不能按有利子集均值宣布A3最好。
- 实际完整性缺口非常明确：自己的渲染轮廓到接纳CAD边的P95为4.00–10.42px；保持相同渲染关联带宽、仅去掉新增primitive邻接门槛的只读诊断，P95全部低于0.91px。该诊断不是第六条优化路线，没有生成替代位姿。不能简单认为其中每个候选都物理可见，仍需正确三维遮挡证据。

**当前建议：保留P0冻结基线；S0保留为有界RGB精修对照；Conics保留为多解初始化工具；暂缓A2/A3及12照片推广。** 下一步只需修复项目新增的轮廓采样/对应完整性，优先直接借鉴M3T从渲染边界产生三维轮廓点的流程，而不是扩大数据、释放尺度或调整权重掩盖缺口。

## 四组全部方法（FIT，条件宏平均）

'''+compact+'''
单位：I/O和SIFT为640×360工作像素，中心变化mm；IoU无量纲。Conics均值只覆盖其成功视角，不与全81覆盖直接排名。I/O距离基于当前有缺口的预测曲线，应读作有偏几何代理；全CAD硬渲染Mask IoU是独立计算。所有P95、最差视角、样本数、真实IoU交并集分母、极线残差、信息矩阵与逐帧结果见CSV。真实绝对位姿精度、MedARE、真实直径/高度误差均NOT_EVALUABLE。

## 相同视角的公平比较

'''+pairtable+'''
上述最终中心差是同两种方法的刚性相机位置差，不是对GT的误差。S0/A1同SIFT目标、A2/A3同CAD+SIFT目标；全部方法使用同一个P0先验中心。初始化效果和损失变化严格分开。G01视角宏均值受005的52FIT多于004的8FIT影响，逐视频分层见PER_VIDEO_SCOPE_SUMMARY；不将密集相邻帧当作额外独立物理组。

## HOLDOUT与旧HERO

17个HOLDOUT没有局部拟合，也没有新共享视频变换，所以五种方法的这些相机及直接投影完全相同，不能声称留出相机精修收益。但它们与已更新FIT参考相机之间的极线误差会变化，提供独立相对几何诊断。P0→A2的HOLDOUT未拟合轨迹极线MAE在G01/G03/G05/G06分别为0.558→0.730、0.517→0.597、0.395→0.748、0.432→0.521px，四组均变差。FIT上的未参与位姿损失轨迹另作独立指标，但其3D地图仍来自原相机三角化，非外部标定GT。

原生HERO深度、面片、像素ID均冻结。新相机相对位姿改变后，只有反事实重新投影/重表达诊断，统一标记POSE_CHANGED_DEPTH_NOT_REINFERRED；不将其称为新深度精度。G01同视频与跨视频分别统计，其他三组仅004同视频。完整固定/共同/新增/丢失命中与Unknown见FROZEN_DEPTH_COUNTERFACTUAL。A2在四组的原深度相容性代理总体下降，不能忽视，亦不能从它单独断言真实相机更差——旧HERO依赖旧相对相机。

## 七个科研问题

1. **Conics初始化改善稳定性？** 未证明。公式自检通过；真实输入46/81可行，35/81不满足本轮相对P0的界限。P0也不是GT，初始化不合规不能解释为Conics物理错误。同目标成功集合S0/A1收敛几乎相同。
2. **M3T式处理解决旧问题？** 部分。13条历史反例分类稳定、无MISS自动visible，局部Jacobian通过且实际TRF下降；但新增的primitive所有权限制破坏曲线完整性，整体未通过。未声称移植或运行完整M3T。
3. **CAD相对Mid+SIFT独立收益？** 有完整Ring投影代理改善，也有未拟合SIFT及旧深度相容性变差。轮廓模型缺陷阻止可靠归因，不能宣布真实位姿获益。
4. **A3优于A1/A2？** 无充分证据。与A2共同集合Ring略好、SIFT更差，覆盖更低且模型有缺口。
5. **哪个统一方案稳定运行？** S0和A2数值输出均81/81，全部方法共254/324。S0可作为控制基线，A2/A3在几何表达审计上失败，不升级主线。
6. **足以支持后续全部视角更新共享主体？** 尚不足。需要可信完整CAD几何，以及对POSE_CHANGED_DEPTH_NOT_REINFERRED的后续处理；本轮不启动主体或HERO更新。
7. **可推广12照片吗？** 当前不可以。原Stage2初步指标检查曾允许扩展，但在真正进入照片前补充自洽审计发现重大缺陷；原决定另存PRE_COMPLETENESS_VIDEO_GATE，当前门禁明确暂停，照片12/12保留NOT_RUN而非失败补齐。

'''+audit+'\n[四张核心图](RESULT_INDEX.md) · [方法复用](MATURE_ALGORITHM_REUSE_AUDIT.md) · [可见性修复与失败](RING_VISIBILITY_FIX_AND_TEST.md) · [复现](REPRODUCE.md)。\n'
 write('TECHNICAL_REPORT_SUMMARY.md',main);write('TECHNICAL_REPORT.md',main)
 method='''# 成熟算法复用与实际差异

- [Conics estimate_pose](https://github.com/sergiud/conics/blob/c38fffd10125c42772656e8c7f69724959154342/conics/_conic.py)：实际提取并执行未修改的官方函数，保留Apache2许可证、源码与SHA。由KᵀEK构造圆的锥面；使用实际CAD中心线半径约5.6mm，而非把Inner/Outer当成共面圆。保留多解/正深度/法向分支。实际使用官方返回的c/n，不直接把R/t当作OpenCV外参；负Z约定显式转为OpenCV正Z。圆内yaw由P0规范初始化，再对入域分支由真实SIFT约束。未实现全yaw族预消歧，是本轮限制。合成圆验证只用于审计分支存在正确解，不参与真实选择。
- [M3T RegionModel](https://github.com/DLR-RM/3DObjectTracking/blob/f02106186a1e756450226b3b793e309506817c58/M3T/src/region_model.cpp)、[RegionModality](https://github.com/DLR-RM/3DObjectTracking/blob/f02106186a1e756450226b3b793e309506817c58/M3T/src/region_modality.cpp)、[Optimizer](https://github.com/DLR-RM/3DObjectTracking/blob/f02106186a1e756450226b3b793e309506817c58/M3T/src/optimizer.cpp)、[SilhouetteRenderer](https://github.com/DLR-RM/3DObjectTracking/blob/f02106186a1e756450226b3b793e309506817c58/M3T/src/silhouette_renderer.cpp)：阅读并保留MIT源码，用其渲染轮廓、对应/位姿交替、局部重线性化思想；**没有运行官方C++跟踪器、没有复现其区域概率模型或直接移植GeneratePointData**。Python使用Open3D全CAD深度/primitive渲染、OpenCV轮廓和CAD前后面候选边。新增一圈vertex-face primitive邻接门槛是项目适配，现已证实过严，不应称官方M3T行为。
- OpenCV SIFT、互检/RANSAC PnP及原019三角化缓存复用。原地图建立时已用原相机、至少3FIT、视差>0.5°、重投影<2px；不读HERO。当前没有额外调用solvePnPRefineLM替换真实方案，优化实际由SciPy TRF完成；不冒称所有列出的组件都运行。没有下载网络或模型。
- SciPy有界least_squares(method=trf)实际执行；float64 SE3/Jacobian沿用已验证PyTorch实现；并非Ceres、g2o、COLMAP或完整M3T优化程序。

| 设计 | 实际代码 | 差异/限制 |
| --- | --- | --- |
| 共同c2w/mm/无尺度 | base_geometric.pose + refine.q_from_pose | 相机中心为旋转参考，等价明确的世界左SE3；CAD分支绕Ring法向规范消除虚假yaw，SIFT保留真实方向信息 |
| 相同目标公平比较 | refine.Problem | S0/A1只SIFT+prior；A2/A3额外完整CAD尺寸的I/O残差；P0不更新。P0先验中心一致，不在Conics终点重置 |
| 固定对应求导 | cad_render.material_points | 冻结透视正确的最近CAD三维点，内循环不再对clamp分支求导；每个候选重新渲染/关联实际目标并回溯验收 |
| M3T式可见性 | cad_render.RenderedCAD.segments | 2倍分辨率渲染边界、1工作像素关联带、可见primitive邻接证据；MISS不直接visible，2µm深度阈值未增加。该邻接适配产生大缺口，是本轮失败机制 |
| 成熟优化 | refine.solve | 5轮对应更新×最多20nfev，8次回溯。外包q盒2，相对P0真实中心≤1.2mm/角度≤10°仍严格执行；不是事后提高危险位移限值 |
| Conics候选选择 | run_videos.run | 全部分支保留，只以FIT SIFT+同P0先验选可行候选；超界则NaN，不用P0/S0补齐。不以HOLDOUT或HERO决定候选 |
| 真实输入来源 | setup_inputs + frozen upstream | 原98canonical与RGB/Mask/特征/轨迹只读复用；不新选帧，不按Ip/Is/IIa改参数 |
| 独立评价 | evaluate_videos + enrich_metrics + facts | 全硬CAD图像投影、SIFT未拟合轨迹/极线、原HERO反事实、精确分母、共同成功集合；不做ICP或GT评价 |

目标：L_R=.5 meanHuber(dI/3)+.5 meanHuber(dO/3)；L_F=.2 meanHuber(norm(reprojection)/3)；L_P=.01 sum(q²)/12。Mid无损失项。相同方法的初始化对照只改变初值，预算/自由度/数据/先验均相同。

完整函数行号、源码SHA见CODE_LOCATIONS.csv。Stage2之前协议/源码回执保留，四组预测冻结后才读取独立指标。缺陷发现后的控制只有只读几何计算，未执行第六条路线或覆盖任何最终矩阵。
'''+audit;write('MATURE_ALGORITHM_REUSE_AUDIT.md',method)
 cvtext='''# 可见性旧问题修复与新问题

1. 旧CADCurves的点射线+Inf比较不再用于判定VISIBLE。当前以CAD渲染边界、投影候选边及可见primitive证据关联，只有可靠渲染证据才能接纳；其余按有限前层深度或UNKNOWN区分。保留旧2µm深度阈值，没有通过提高它或删掉所有MISS解决问题。
2. 四组13条保存的旧反例在q0/±1e−4下分类稳定。固定三维对应的4组×5分量×3步长×6轴数值检查均通过，最大块相对误差为'''+str(max(r['relative']for r in j))+'''。四组8次代表TRF均真实降低重新计算目标，正式254次结果保持物理界限。
3. 但是“旧反例修复”不代表轮廓整体正确。补充审计以自己渲染的CAD边界为目标，实际曲线P95达4–10px，16.7%–51.7%边界像素距曲线>2px。渲染关联带不变、仅取消新增primitive邻接限制的只读几何控制，将全部P95降到0.91px以下，明确定位过严邻接过滤及其后续深度拒绝分支。

'''+cvtable+'''
这里的2px统计是发现缺口后的描述性诊断，不是事后制定的通过阈值；明显大于1px关联带及光栅量化尺度。控制未使用真实息肉GT、未重新优化。不能简单把该控制当可靠可见性：投影重合的后层候选仍须正确处理三维遮挡。下一步应更忠实复用M3T从渲染边界采样并恢复三维对应的流程，而非任意扩大topological邻域或放宽阈值。

原Stage1门禁和初步视频门禁均原样保留；完整性失败追加为POST_VIDEO_CONTOUR_COMPLETENESS_GATE，并暂停照片，不偷偷回写历史结果。
'''+audit;write('RING_VISIBILITY_FIX_AND_TEST.md',cvtext)
 midrows=[dict(depth_mm=r['depth_mm'],tilt_deg=r['tilt_deg'],valid=r['Mid_valid'],continuous_MAE_px=r['true_circle_vs_Mid_continuous_px']['MAE']if r['Mid_valid']else None,continuous_P95_px=r['true_circle_vs_Mid_continuous_px']['p95']if r['Mid_valid']else None,center_bias_mm=r['Mid_conics_camera_center_bias_mm'])for r in mid]
 write('CONICS_MID_GEOMETRY_AUDIT.md','''# Conics与厚Ring Mid审计

官方commit c38fffd10125c42772656e8c7f69724959154342，未修改estimate_pose。实际CAD中心线半径约5.6mm、管半径0.6mm、内径10mm；K490，640×360。已知相机距离35/50mm、倾角10/35/55/70°八个自检；圆本身连续投影反演均有正确分支，最近正确相机中心误差0.6e−6–5.7e−6mm。已知相机只用于自检，不用于真实初值/拟合/选模。

'''+md(midrows,list(midrows[0]))+'''
早期720离散点最近邻的0.10–0.17px含采样相位误差，不应称系统偏差。8192段连续曲线复核给出0.014–0.032px MAE；两个70° DXY Mid失败保留NaN。理想无Polyp遮挡Mask中的小误差不能证明真实分割的Mid无偏，故协议始终只将Mid用于初始化，没有添加Mid强损失或与I/O重复计权。

真实Conics的35个不可行初值相对的是冻结P0边界，不是GT误差；每例均保留4个数值候选。**实现限制：剩余yaw先固定为P0规范，未在整个yaw族上先单独做RGB消歧，再执行物理域预检。对已入域分支由SIFT六自由度精修；提前拒绝可能漏掉可经yaw调整进入域的候选。35个失败只能归于本实现的初始化流程，不能视为整个Conics几何族无解。** 可能涉及分割/内参、P0本身偏差、几何多解及先验限制，当前不能单独区分。所有分支、正常/反向法向、正深度、源文件、候选公制位置与q均完整保存。Ring不能提供yaw，初始化yaw是规范继承，最终约束来自真实RGB。
'''+audit)
 write('FOUR_GROUP_RESEARCH_DECISION.md','# 四组研究决策\n\n'+main)
 fails=load(M/'metrics/FAILED_CAMERA_ROUTES.json');write('FAILURE_LEDGER.md','''# 失败台账

| 项目 | 结果与保留方式 |
| --- | --- |
| 新增primitive邻接筛选过严 | 四组自身CAD轮廓有明显缺口；明确是项目适配失败，不归因官方M3T。实际源边ID、XYZ、render像素、state在RENDER_COVERAGE_GAP_LOCATIONS |
| 初版门禁遗漏完整性检查 | 局部Jacobian、旧反例、实际下降通过，却未覆盖完整轮廓；补检失败后停止照片。旧Gate原样保留，当前为PAUSED |
| Conics消歧实现限制 | 预检先于完整yaw族RGB消歧，可能过早拒绝；不将35个失败解释为Conics公式或真实相机错误 |
| A1/A3初始化失败 | 各35/81，G01 32、G03 1、G05 2、G06 0；FAILED_CAMERA_ROUTES含70条方法/帧、原因与初始化证据。不以S0/P0补齐 |
| 独立代理冲突 | A2 Ring投影提升，四组未拟合SIFT及冻结深度相容性变差；不按IoU宣称真实精度。HERO未重推，不能孤立断定相机误差 |
| 70°合成Mid失败 | 2/8无有效Mid，非Circle公式失败；不生成假椭圆。真实未知遮挡/形变未以GT补齐 |
| StageB未运行 | 12张独立照片统一NOT_RUN_VIDEO_COMPLETENESS_GATE；不复制quick旧位姿，不启动HERO或主体 |
| 显示脚本一次语法拼写错误 | else9修正后绘图，错误日志保留；不涉及参数、数据或预测 |

逐条初始化失败CSV与JSON保留，不隐藏失败组。CAD完整性控制没有生成替代预测，禁止将其当成训练改进。真实绝对位姿/直径/高度精度无GT，NOT_EVALUABLE。
'''+audit)
 write('REPRODUCE.md',f'''# 复现与保全

目录 `{M}`。Python{platform.python_version()}，SciPy{scipy.__version__}，Torch{torch.__version__}，NumPy{np.__version__}。沿用已安装OpenCV/Open3D，无新大型框架/模型。Conics/M3T准确commit、完整源码SHA与许可证见vendor及MATURE_SOURCE_FETCH。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
N21={M}
$PY -B "$N21/code/setup_inputs.py"
# 正式结果已冻结；run_videos/refine对已有FINAL只读复用，不重新初始化。
$PY -B "$N21/code/stage1.py"
$PY -B "$N21/code/run_videos.py" G01
$PY -B "$N21/code/run_videos.py" G03
$PY -B "$N21/code/run_videos.py" G05
$PY -B "$N21/code/run_videos.py" G06
$PY -B "$N21/code/evaluate_videos.py"
$PY -B "$N21/code/completeness_audit.py"
$PY -B "$N21/code/facts.py"
$PY -B "$N21/code/enrich_metrics.py"
$PY -B "$N21/code/mid_continuous.py"
$PY -B "$N21/code/figures.py"
$PY -B "$N21/code/report.py"
$PY -B "$N21/code/verify.py"
```

当前状态为PAUSED；不要依据evaluate_videos单独产生的初步门禁跳过completeness审计启动照片。完整性控制只作几何计算，不取消约束重新训练。严格回放应在独立目录，先恢复同SHA的旧geometric_pose输入链接和原021资产；不覆盖当前FINAL。

实际本轮四组CPU进程并行，GPU未用于训练或新HERO，8次Stage1正式同配置结果复用于Stage2。sum_process_seconds不是并行墙钟。大原件/特征/原生HERO留原路径，LOCAL_ARTIFACTS为路径SHA索引，不声称全部上传。
''')
 index='# 结果索引\n\n[摘要](TECHNICAL_REPORT_SUMMARY.md) · [完整技术报告](TECHNICAL_REPORT.md) · [五方案表](FOUR_GROUP_POSE_COMPARISON.csv) · [共同成功集合](metrics/PAIRED_COMMON_VIEW_COMPARISONS.csv) · [失败70条](metrics/FAILED_CAMERA_ROUTES.csv) · [当前暂停原因](STAGE_GATE_DECISION.json)\n\n'
 for p in sorted((M/'figures').glob('*.png')):index+=f'- [{p.stem}](figures/{p.name})\n'
 index+='\n各帧公制相机矩阵：results/{group}/{method}/{canonical_id}/FINAL.json；原始初始化分支initialization/{group}/{id}.json；实际TRF轨迹optimization同层级。原HERO反事实诊断、固定/共同/新增/丢失分母在FROZEN_DEPTH_COUNTERFACTUAL。HOLDOUT均未局部拟合。照片阶段未运行，无新照片相机/深度产物。\n';write('RESULT_INDEX.md',index)
 loc=[]
 for p in(M/'code').glob('*.py'):
  for a in ast.walk(ast.parse(p.read_text())):
   if isinstance(a,(ast.FunctionDef,ast.ClassDef)):loc.append(dict(file=str(p),symbol=a.name,line=a.lineno,sha256=sha(p)))
 table('metrics/CODE_LOCATIONS.csv',loc);save('assets_index/LOCAL_ARTIFACTS.json',[asset(p)for p in M.rglob('*')if p.is_file()and(p.suffix in ['.npz','.log'])]);save('provenance/DELIVERY_MANIFEST.json',dict(epoch=time.time(),reports=[asset(p)for p in M.glob('*.md')],code=[asset(p)for p in(M/'code').glob('*.py')],figures=[asset(p)for p in(M/'figures').glob('*.png')],stage=asset(M/'STAGE_GATE_DECISION.json'),predictions=[asset(p)for p in(M/'results').rglob('FINAL.json')],photos_run=0,scientific_status='PAUSED_FOR_HUMAN_DIAGNOSIS'));print('MATURE_REPORTS_COMPLETE',flush=True)
if __name__=='__main__':main()
