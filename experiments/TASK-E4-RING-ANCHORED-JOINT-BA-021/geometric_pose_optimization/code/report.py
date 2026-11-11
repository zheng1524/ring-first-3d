"""Report exact preflight stop; never invent P1 matrices, optimizer runs or photo results."""
from gcommon import *
import ast,platform,scipy,torch,collections

def md(rows,keys):
 def fmt(v):
  if v is None:return 'NaN / NOT_RUN'
  if isinstance(v,float):return f'{v:.7g}'
  return str(v).replace('|','/')
 return '| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+''.join('| '+' | '.join(fmt(r.get(k))for k in keys)+' |\n'for r in rows)
def write(n,s):(M/n).write_text(s,encoding='utf8')
def main():
 assert not load(M/'config/JACOBIAN_GATE.json')['pass_required_geometric_J'];score=load(M/'metrics/FOUR_GROUP_POSE_OPTIMIZATION_SCORECARD.json');jac=load(M/'metrics/JACOBIAN_VALIDATION.json');diag=load(M/'metrics/FAILURE_BRANCH_ISOLATION.json');edges=load(M/'metrics/CAD_VISIBILITY_SWITCH_CAUSES.json');vv=load(M/'config/VIEWS.json');counts=load(M/'metrics/REAL_SIFT_INPUT_COUNTS.json');hero=load(M/'metrics/P0_NATIVE_HERO_PROXIES.json');loc=[]
 for p in(M/'code').glob('*.py'):
  for node in ast.walk(ast.parse(p.read_text())):
   if isinstance(node,(ast.ClassDef,ast.FunctionDef)):loc.append(dict(file=str(p),symbol=node.name,line=node.lineno,sha256=sha(p)))
 table('metrics/CODE_LOCATION_INDEX.csv',loc)
 audit='''\n| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4个物理组；98个canonical视频视角（81FIT/17HOLDOUT），照片阶段12张仅条件授权 |
| 本算法独立成功 | 正式P1派生相机输出0/98；四组正式精修完成0/4；98/98原始输入审计、4/4代表视角数值探针完成不算优化成功 |
| 本算法失败 | 3/4代表视角局部J多步长门禁失败；全局门禁FAIL，全部4组P1未运行，结果NaN。12照片NOT_RUN_STAGE_A_GATE |
| 历史测量值回退 | 0；用户指定021B3与旧相机仅作P0/初始化，不冒充新P1输出 |
| 失败组及具体原因 | G01/G05/G06在1e-4的Outer残差跨clamp分支；G03局部J通过但重线性化可见边也切换。四组均发现CAD边射线可见性切换，详见逐组报告和真实图 |
| 最终统计样本 | P0全部98视角和51个原生TRUSTED来源；新P1独立输出0，改进指标NaN；绝对GT误差MedARE/MAE/P95/max均NOT_EVALUABLE |
| 是否使用GT选择算法 | 否；未读取GT。原相机/Mask/HERO/主体/CAD/DXY未修改，未用HERO或主体生成位姿 |
'''
 jtable=[]
 for g in GROUPS:
  info=next(r for r in load(M/'metrics/OBSERVABILITY_GATE_SAMPLES.json')if r['group']==g);row=dict(group=g,local_J_max_rel_h1e4=max(r['relative_Frobenius']for r in jac if r['group']==g and r['h']==.0001),local_J_max_rel_h1e5=max(r['relative_Frobenius']for r in jac if r['group']==g and r['h']==.00001),data_only_J_rank=info['data_information']['rank'],condition_J=info['data_information']['condition'],yaw_invariance_error=info['yaw_canonical_invariance_max_abs']);jtable.append(row)
 table('FOUR_GROUP_POSE_OPTIMIZATION_SCORECARD.csv',[{k:('NaN'if v is None else v)for k,v in r.items()}for r in score])
 pairs=load(M/'metrics/P0_HERO_PER_PAIR.json');scope_rows=[]
 for g in GROUPS:
  for scope in ['SAME_VIDEO_ONLY','CROSS_VIDEO_ONLY']:
   pp=[r for r in pairs if r['group']==g and ((r['source_video']==r['target_video'])==(scope=='SAME_VIDEO_ONLY'))]
   if not pp:continue
   N=sum(r['known_N']for r in pp);scope_rows.append(dict(group=g,scope=scope,pairs_N=len(pp),fixed_N=sum(r['N']for r in pp),known_N=N,MAE_mm=sum(r['depth_mm']['MAE']*r['known_N']for r in pp if r['known_N'])/N if N else None))
 table('metrics/P0_HERO_SEPARATE_VIDEO_SCOPE.csv',scope_rows);save('metrics/P0_HERO_SEPARATE_VIDEO_SCOPE.json',scope_rows)
 compact=md(score,['group','target_video_views_N','FIT_N','HOLDOUT_N','FIT_P0_Ring_IoU','HOLDOUT_P0_Ring_IoU','FIT_P0_Inner_MAE_px','FIT_P0_Outer_MAE_px','P1_status'])
 jj=md(jtable,['group','local_J_max_rel_h1e4','local_J_max_rel_h1e5','data_only_J_rank','condition_J','yaw_invariance_error'])
 summary='''# 几何位姿精修：前置门禁失败，按任务停止

**当前状态：PAUSED_FOR_HUMAN_DIAGNOSIS。阶段A正式相机优化尚未启动，阶段B全部12张照片NOT_RUN_STAGE_A_GATE。** 本轮完成成熟方法源码调研、98视角输入审计、真实SIFT准备、几何残差与TRF封装、四组代表视角的实际Jacobian/目标探针、51原生来源P0诊断以及6张真实故障图。没有将输入准备、三角化或PnP内点过滤冒充四组正式P1位姿优化。

## 已确定的故障

1. **新局部几何AD并非全面失效。** 固定可见边及最近线段时，`h=1e−5`下四组所有已测分量/六自由度的J相对Frobenius误差均小于3.3e−9。SIFT/先验正常。但登记的多步长检查还要求`h=1e−4`通过；G01/G05/G06的Outer矢量残差跨越线段垂足clamp分支，最大块误差分别1.13%/0.45%/3.43%，不能事后只保留最小步长宣布PASS。G03局部J通过，不代表完整可见性目标通过。
2. **更严重的问题在重新计算CAD可见边。** 继承的`../code/ring020.py::CADCurves.segments`使用`t_hit >= point_depth−0.002mm`。Open3D射线无命中返回`+Inf`时，这个比较仍为True。它将“无可靠命中/未知”当作可见，而相邻微扰下可能出现有限命中并被剔除。这不是PyTorch3D软光栅梯度，也不是SIFT问题。
3. **真实反例已定位到CAD顶点ID。** G05、tx、h=1e−4：局部AD=−0.15287488，同一可见集合的FD=−0.15287488，重新计算可见边后FD=+0.40653856。改变的是边(9065,9129)，中点投影约(217.892,117.216)px；基础/负扰动为MISS_PLUS_INF且被判可见，正扰动的gap=−0.002430mm而被剔除。G06的ty也从局部−0.04276784变为全目标+0.01990642。4组所选诊断方向的全部13条切换边均为ray-culling切换，未观察到该批样本的Inner/Outer类型切换。

不能把这解释为相机已经到达观测极限，也没有证据说明SciPy/TRF不能处理当前数据。**当前可见性供应器含明确的未知状态处理缺陷，局部代理下降尚不能保证真实重线性化目标下降。** 按任务第五、十四节停止；未改阈值、未静默修复后继续，也未运行照片、HERO推理、主体形变或融合。

'''+jj+'''
J的参数尺度为0.6mm/5°；条件数为κ(J)，不是κ(JᵀJ)。信息只测每组第一个FIT的局部数据块，未含先验，不能推及全部98相机或认证绝对姿态。Ring纯yaw通过规范不变性测试；方向信息来自RGB。

## 四组完整P0清单及新路线缺失结果

'''+compact+'''
G01的随附HERO总表涵盖同视频及跨视频有向对，仅为多来源基线；两者单独的固定分母/MAE见metrics/P0_HERO_SEPARATE_VIDEO_SCOPE.csv，不混成跨视频成功率。其他三组仅同视频。\n\nRing IoU在已知区域计算：排除Polyp遮挡未知；边界为实际Mask支持I/O→完整CAD轮廓、640×360工作像素。P0主体投影另见逐视角表，仅是独立代理。P1平移、旋转、改善、收敛和独立HERO收益全部NaN/NOT_RUN，不填0、不回退历史候选。

98=G01的68（00413+00555）+G03的9+G05的11+G06的10，来自021冻结canonical清单；原有别名不重复计帧。本轮未将文件系统其他未经本清单绑定的旧缓存增加为实验视角。全部81FIT/17HOLDOUT身份保留。保护视角不用于局部位姿拟合；计划中的G01共享变换若将来执行，只由FIT估计后作用于005HOLDOUT。G05一个HOLDOUT没有可用SIFT内点，保留MISSING特征身份，不剔除病例。

G01复用004/005的153/980地标；G03/G05/G06按同一既有019三角化代码得到424/76/113个初始化地标。它们来自真实RGB、不是HERO或GT；现有固定相机参与三角化，所以不等于独立相机真值。feature track ID%5==0未进入PnP输入过滤/预期位姿损失；其3D初值仍由FIT影像和原相机建立，称“未参与位姿拟合轨迹”，不是新的外部标定。

**下一步建议仅限独立修复和验证CAD轮廓可见性。** 无命中应保留UNKNOWN，不能简单删除全部miss边——真实切线轮廓也可能数值无命中。应检验切线几何、射线精度/偏置、边线可见性与连续性，再复测六自由度真实目标，并经人工诊断后恢复四组P1。没有依据扩大数据、释放更多相机自由度或启动12照片来绕过问题。

'''+audit+'''
[全部6张真实图](RESULT_INDEX.md) · [复现](REPRODUCE.md) · [精确CAD边与射线状态](metrics/CAD_VISIBILITY_SWITCH_CAUSES.json)。原始21/20/quick结果全部只读保留。
'''
 write('TECHNICAL_REPORT_SUMMARY.md',summary);write('TECHNICAL_REPORT.md',summary)
 methods='''# 成熟方法与实际实现审计

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
'''+audit
 write('CLASSICAL_GEOMETRIC_OPTIMIZATION_AUDIT.md',methods)
 write('RING_JACOBIAN_VALIDATION.md','# Ring几何Jacobian与真实目标门禁\n\n'+jj+'\n\n'+'''相对误差为||J_AD−J_FD||F/max(||J_AD||F,||J_FD||F,1e−12)。完整逐列还报告绝对误差；每轴采用relative≤1e−3或absolute≤1e−5，要求登记的h≤1e−4两级均通过。G01/G05/G06在Outer的部分旋转轴未通过；不能事后删除1e−4。h1e−3也保留作为跨分支诊断。

小步长的收敛说明固定分支AD正确，不等于重新选择可见曲线的完整目标已经通过。`FAILURE_BRANCH_ISOLATION.json`进一步分离：固定edge/nearest-foot；固定可见集合重选最近；重新计算全部可见边。G05反号主要发生在第三步，G06亦如此。`CAD_VISIBILITY_SWITCH_CAUSES.json`明确记录13条实际变化边，均属于射线culling开关。`MISS_PLUS_INF`不是零深度，更不是可信可见。原helper把+Inf纳入visible的独立布尔反例已保存；本轮只定位，不修复或继续求解。

实际归一参数h1e−4对应平移6e−5mm或转角0.0005°。部分近切线射线的hit/miss与有限深度差在此微扰下切换，改变几何目标。不能将这类差异全部归因于最近点/相机不确定性，也不能认为只需更小学习率。

'''+audit)
 write('FOUR_GROUP_POSE_OPTIMIZATION_DECISION.md','# 四组统一决策\n\n**PAUSED_FOR_HUMAN_DIAGNOSIS；阶段A未完成，阶段B未启动。**\n\n'+compact+'\n\n四组都完成原始输入与P0审计，均没有本轮派生相机，故“合理更新、Ring/SIFT改善、独立指标退化、是否可用”均NOT_TESTED。没有观察到新相机漂移，因为未生成新相机；不能把未运行写成“稳定无漂移”。代表视角的数据J为6秩，只说明该局部代理的代数可观测性。G03局部数值门禁通过，仍受共同可见性实现缺陷影响，不能单独放行该组或12照片。\n\n下一轮先处理Inf未知状态及真实CAD边界的稳定可见性，做局部隔离测试；本轮不自动改算法、不调整阈值、不给所有旧标签重新盖章。\n'+audit)
 for s in score:
  g=s['group'];gg=[r for r in load(M/'metrics/ALL_VIDEO_P0_METRICS.json')if r['group']==g];sc=[r for r in counts if r['group']==g];hh=next(r for r in hero if r['group']==g);ee=next(r for r in edges if r['group']==g)
  text='# '+g+' 位姿研究记录\n\n**正式P1：NOT_RUN_JACOBIAN_GATE。** 原坐标及源相机保持不变。\n\n'+md([s],list(s))+'\n\n## 实际输入与可计算指标\n\n'+md(sc,['id','role','map_points','RGB_matches','fit_PNP','held_features','fallback_epi_N'])+'\n\n原生HERO固定代理：\n\n'+md([hh],['sources_N','native_TRUSTED_pixels_N','cumulative_source_area_mm2','fixed_source_target_N','known_N','depth_mm','visibility_categories'])+'\n累计来源面积不是去重解剖面积；已知深度误差是可见性代理、非GT精度，更深层可为正常自遮挡。完整逐视角Ring I/O P95、Mask轮廓与SIFT残差见ALL_VIDEO_P0_METRICS.csv。\n\n## 故障定位与八项判断\n\n'+md([next(r for r in jtable if r['group']==g)],list(jtable[0]))+f'\n该组已定位{len(ee["changed_edges"])}条在登记微扰中切换的实际CAD边，原始vertex ID/XYZ/投影/射线状态完整保留。\n'
  text+='\n1. 成熟求解器正式执行成功：NOT_RUN。\n2. 合理位姿更新：NOT_RUN，无派生矩阵。\n3. Ring边界改善：NaN，只有P0。\n4. SIFT几何改善：NaN，真实输入匹配计数已给。\n5. 独立观测退化：NOT_TESTED，不用基线数值替代。\n6. 不合理漂移：NOT_TESTED；当前未产生相机更新。\n7. 弱自由度：本组代表视角局部数据J秩6，条件数见表；Ring自身yaw无约束。其余视角未逐个做完整J审查。\n8. 后续研究资格：原P0可作为明确标注的研究输入；本轮新方法不升级，先修复共同Ring可见性缺陷。\n'
  text+='\nG01使用既有B3统一004世界，其他三组仅004；未虚构额外视频姿态。冻结HERO和主体只用于上述P0独立评价。\n'+audit;write(g+'_POSE_REPORT.md',text)
 stage=dict(status='PAUSED_FOR_HUMAN_DIAGNOSIS',stage='A_GEOMETRIC_PREFLIGHT',stage_A_completed=False,stage_A_formal_solver_runs=0,stage_A_derived_camera_outputs_N=0,stage_A_video_inputs_N=98,stage_A_groups_N=4,geometric_J_gate=False,local_J_h1e5_all_groups_pass=True,multistep_gate_h1e4_failed_groups=['G01','G05','G06'],serious_implementation_issue='CAD ray miss +Inf satisfies inherited visibility comparison; actual relinearized geometric objective may reverse local descent direction',stage_B='NOT_RUN_STAGE_A_GATE',stage_B_photo_runs=0,body_updates=0,new_HERO_inferences=0,GT_used=False,no_automatic_algorithm_repair=True,reason_source_files=[asset(M/'config/JACOBIAN_GATE.json'),asset(M/'metrics/CAD_VISIBILITY_SWITCH_CAUSES.json')]);save('STAGE_GATE_DECISION.json',stage)
 failure='''# 失败台账

| 编号 | 真实问题 | 处理 |
| --- | --- | --- |
| F01 | G01/G05/G06局部Outer J在h1e−4未过冻结阈值 | 原始120块/720轴检查保留；更小步长通过只作诊断，不改规则 |
| F02 | 实际CAD可见集合在极小位姿微扰中改变 | 原始边ID与射线深度/UNKNOWN状态、实际目标反号保留；不进入正式优化 |
| F03 | 继承判据把t_hit=+Inf当作visible | 确认独立布尔反例及真实G05/G06 miss→有限hit切换，未自动修改代码或删除miss边 |
| F04 | 四组正式P1未运行 | 全部四组/98目标保留NaN/NOT_RUN，不复制历史矩阵作为本轮输出 |
| F05 | 12照片未启动 | 统一NOT_RUN_STAGE_A_GATE；不得将quick旧候选或视频帧改名作为新结果 |
| F06 | G05_v004_raw00257保护视角无SIFT内点/2D支持 | 保留该HOLDOUT，SIFT独立项MISSING，不删除该病例；不是本轮主要停机原因 |
| E01 | 首次准备重复解压同一SIFT缓存，耗时过长 | 仅中断自己的CPU准备进程；旧源码/日志保留，增加只读内存缓存并复用已完成输入，数学匹配/参数不变，正式位姿优化未开始 |
| E02 | 原生HERO审计最初未覆盖visibility_query的实际字段名 | 补齐supported/cad_occluded/Unknown真实计数，仅重算独立P0 HERO审计；未改变冻结任何预测或门槛 |
| E03 | 空心标记显示警告及随后删无用显示代码时的缩进错误 | 显示日志保留并修正；六图重画，数据/误差/相机不变 |

Ray miss不是已证明的遮挡或物理不存在。修复不能简单把全部miss边硬删以求PASS；需独立验证真正的切线轮廓与UNKNOWN。当前未证明四组观测不足，也未证明成熟求解器或几何路线科学失败。
'''+audit;write('FAILURE_LEDGER.md',failure)
 photos=load(P/'quick_solver_review/config/PHOTO_ASSETS.json');table('metrics/TWELVE_PHOTO_NOT_RUN.csv',[dict(id=r['id'],group=r['group'],capture_type=r['capture_type'],RGB=r['RGB'],Mask=r['Mask'],new_pose=None,status='NOT_RUN_STAGE_A_GATE')for r in photos])
 write('REPRODUCE.md',f'''# 最小故障复现（不启动优化）

目录：`{M}`。原021/020/quick、原相机/HERO/CAD/DXY严格只读。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
GEO={M}
# 既有INPUTS_FROZEN时prepare直接退出。全新准备需原SHA资产与原021代码。
$PY -B "$GEO/code/prepare.py"
$PY -B "$GEO/code/validate.py"
# gate失败后仅诊断，不调用geometric.solve，不运行阶段B。
$PY -B "$GEO/code/diagnose.py"
$PY -B "$GEO/code/edge_diagnostic.py"
$PY -B "$GEO/code/baseline_audit.py"
$PY -B "$GEO/code/figures.py"
$PY -B "$GEO/code/report.py"
$PY -B "$GEO/code/verify.py"
```

最小数值反例：G05的G05_key04_raw00542、q=0、axis0、h=1e−4。诊断脚本分别打印/保存固定可见集合和完整重新可见性目标；`+Inf>=40−.002`为True的单独predicate也保存。不得把该比较直接改成finite判据后自动继续；真实切线miss应保留UNKNOWN，修复和重新放行须后续人工诊断。

环境：Python{platform.python_version()}，NumPy{np.__version__}，SciPy{scipy.__version__}，PyTorch{torch.__version__}；pycolmap4.2.1存在但无自定义Problem接口，未新增依赖。CPU double几何诊断；没有模型训练/GPU推理。大数组/特征/原生HERO/原始视频留本地SHA索引，不上传复制数据集。
''')
 idx='# 实际产物索引\n\n[摘要](TECHNICAL_REPORT_SUMMARY.md) · [算法审计](CLASSICAL_GEOMETRIC_OPTIMIZATION_AUDIT.md) · [Jacobian门禁](RING_JACOBIAN_VALIDATION.md) · [阶段状态](STAGE_GATE_DECISION.json) · [四组表](FOUR_GROUP_POSE_OPTIMIZATION_SCORECARD.csv)\n\n'
 for p in sorted((M/'figures').glob('*.png')):idx+=f'- [{p.stem}](figures/{p.name})\n'
 for g in GROUPS:idx+=f'\n- [{g}独立报告]({g}_POSE_REPORT.md)'
 idx+='\n\n源码/数据SHA及函数行号见provenance/UPSTREAM_FROZEN.json、provenance/INPUTS_FROZEN.json、metrics/CODE_LOCATION_INDEX.csv。所有正式P1和阶段B结果均未运行，不列虚假FINAL路径。原始输入及局部三角化缓存留本地，路径与SHA见assets_index/LOCAL_FILES.json。\n';write('RESULT_INDEX.md',idx)
 save('assets_index/LOCAL_FILES.json',[asset(p)for p in M.rglob('*.npz')if p.is_file()]);save('provenance/REPORT_DELIVERY_MANIFEST.json',dict(epoch=time.time(),code=[asset(p)for p in(M/'code').glob('*.py')],reports=[asset(p)for p in M.glob('*.md')],figures=[asset(p)for p in(M/'figures').glob('*.png')],stage=asset(M/'STAGE_GATE_DECISION.json'),formal_solver_calls=0,stage_B_runs=0));print('PAUSED_REPORTS_COMPLETE',flush=True)
if __name__=='__main__':main()
