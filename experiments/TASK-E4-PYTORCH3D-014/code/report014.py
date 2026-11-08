"""Write reports from actual completed outputs. No prediction or method selection."""
from common import *
from collections import Counter
from scipy.stats import spearmanr
def fmt(x):
 if x is None:return 'NOT_EVALUABLE'
 if isinstance(x,(float,np.floating)):return f'{x:.4f}'if np.isfinite(x)else'NaN'
 return str(x)
def md(rows,cols):return '| '+' | '.join(cols)+' |\n| '+' | '.join('---'for _ in cols)+' |\n'+'\n'.join('| '+' | '.join(fmt(r.get(k))for k in cols)+' |'for r in rows)
def main():
 assert(R/'provenance/INDEPENDENT_EVALUATION_COMPLETE.json').exists();cases=load(R/'config/CASE_LOCK.json');names=[c['name']for c in cases];native=load(R/'metrics/NATIVE_SUMMARY.json');gt=load(R/'metrics/BLENDER_ALIGNMENT_METRICS.json');geom=load(R/'metrics/POST_GEOMETRY_AUDIT.json');N={(r['case'],r['label']):r for r in native};G={(r['case'],r['label']):r for r in gt};Q={(r['case'],r['label']):r for r in geom};C=load(R/'config/C_SELECTION.json')['method'];D=load(R/'config/D_SELECTION.json')['method'];E=load(R/'config/E_SELECTION.json')['method'];final=[];fail=[];runs=[];grad=[]
 blender={(q['case'],q['label']):q for q in load(R/'metrics/POST_GEOMETRY_VALIDITY.json')}
 for tag in ['C0','C1_8','C2_16','C3_32','C4_ALL','D_D1_split','D_D2_bidir','D_D3_combo','E0_none','E1_global','E2_adaptive','FINAL_014','B_A_ONLY','B0_UNCORRECTED']:
  for n in names:
   p=R/'arms'/tag/'metrics'/(n+'_RUN.json')
   if p.exists():runs.append(load(p))
   p=R/'arms'/tag/'metrics'/(n+'_GRADIENT_DIAGNOSTIC.json')
   if p.exists():grad+=load(p)['rows']
 for n in names:
  a=N[n,'FINAL014'];b=G[n,'FINAL014'];q=Q[n,'FINAL014'];run=next(v for v in runs if v['case']==n and v['tag']=='FINAL_014');final.append(dict(case=n,type=next(c['morphology']for c in cases if c['name']==n),FIT_IoU=a['FIT_IoU'],HOLDOUT_IoU=a['HOLDOUT_IoU'],HERO_fixed_N=a['FIT_HERO_fixed_N'],HERO_hit_rate=a['FIT_HERO_hit_rate'],HERO_fixed_cost=a['FIT_HERO_fixed_cost'],HERO_MAE_active_mm=a['FIT_HERO_MAE_active_mm'],Chamfer_mm=b['Chamfer_MAE_mm'],Dxy_AE_mm=b['Dxy_AE_mm'],Dxy_ARE_percent=100*b['Dxy_relative_error']if b['Dxy_relative_error']is not None else None,height_AE_mm=b['height_max_AE_mm'],H95_AE_mm=b['H95_AE_mm'],IoU3D=b['IoU_3D'],IoU3D_status=b['IoU_3D_status'],Ring_penetration_mm=q['Ring_max_material_penetration_mm'],Ring_new_vs011_mm=q['new_penetration_vs011_mm'],Ring_numeric_nonworsening=q['Ring_worsening_within_epsilon'],self_intersections=q['self_intersections_Open3D'],nonmanifold_edges=q['nonmanifold_edges_N'],final_attempts=run['attempts'],final_accepted=run['accepted'],final_displacement_mm=run['maximum_displacement_mm']))
  final[-1].update(Blender_self_intersections=blender[n,'FINAL014']['self_intersections_N'],Blender_Ring_pairs=blender[n,'FINAL014']['Ring_pairs_N'])
  if blender[n,'FINAL014']['self_intersections_N']:fail.append(dict(case=n,stage='FINAL014',reason='Independent Blender BVH nonadjacent self-intersection pairs detected',evidence='metrics/POST_GEOMETRY_VALIDITY.json'))
  if not q['Ring_worsening_within_epsilon']:fail.append(dict(case=n,stage='FINAL014',reason='Independent64-stage Ring worsening exceeds frozen1e-5mm epsilon',evidence='metrics/POST_GEOMETRY_AUDIT.csv',amount_mm=q['new_penetration_vs011_mm']))
  if q['self_intersections_Open3D']or q['nonmanifold_edges_N']:fail.append(dict(case=n,stage='FINAL014',reason='Mesh entity validity failure',evidence='metrics/POST_GEOMETRY_AUDIT.csv'))
  if b['Chamfer_MAE_mm']>=G[n,'FINAL013']['Chamfer_MAE_mm']:fail.append(dict(case=n,stage='FINAL014',reason='No Chamfer improvement against013 under the same best rigid evaluator',evidence='BLENDER_ALIGNMENT_METRICS.csv'))
  if b['IoU_3D']is None:fail.append(dict(case=n,stage='EVALUATION',reason=b['IoU_3D_status'],evidence='BLENDER_ALIGNMENT_METRICS.csv'))
  if b['height_max_AE_mm']is None:fail.append(dict(case=n,stage='EVALUATION',reason='No verified author base; height remains NaN',evidence='BLENDER_ALIGNMENT_METRICS.csv'))
 table('metrics/FINAL_CASE_SUMMARY.csv',final);save('metrics/FINAL_CASE_SUMMARY.json',final);table('metrics/ALL_RUNS.csv',runs);table('metrics/LOSS_COMPONENT_GRADIENTS.csv',grad)
 def merged(n,tag):
  a=N[n,tag];b=G[n,tag];q=Q[n,tag];rr=next((r for r in runs if r['case']==n and r['tag']==tag),{});return dict(case=n,model=tag,training_views_N=a['training_views_N'],FIT_IoU=a['FIT_IoU'],HOLDOUT_IoU=a['HOLDOUT_IoU'],FIT_FP_per_mask=a['FIT']['FP_per_mask'],FIT_recall=a['FIT']['Recall'],boundary_MAE_px=a['FIT']['boundary_MAE_px'],HERO_fixed_N=a['FIT_HERO_fixed_N'],HERO_hit_rate=a['FIT_HERO_hit_rate'],HERO_fixed_cost=a['FIT_HERO_fixed_cost'],Chamfer_MAE_mm=b['Chamfer_MAE_mm'],GT_to_pred_p95_mm=b['GT_to_prediction_mm']['p95'],Ring_penetration_mm=q['Ring_max_material_penetration_mm'],accepted=rr.get('accepted'),attempts=rr.get('attempts'))
 table('VIEW_COUNT_ABLATION.csv',[dict(condition=t,**merged(n,t))for n in names for t in ['C0','C1_8','C2_16','C3_32','C4_ALL']]);table('LOSS_ABLATION.csv',[dict(condition=label,**merged(n,tag))for n in names for label,tag in [('D0',C),('D1','D_D1_split'),('D2','D_D2_bidir'),('D3','D_D3_combo')]]);table('MESH_REFINEMENT_ABLATION.csv',[dict(condition=t,**merged(n,t),**{k:v for k,v in load(R/'metrics/refinement'/(n+'_'+t+'.json')).items()if k not in ['case','arm','per_view']})for n in names for t in ['E0_none','E1_global','E2_adaptive']])
 summary=[]
 for tag in ['FINAL011','FINAL012','FINAL013','FINAL014']:
  rr=[G[n,tag]for n in names];ae=np.array([r['Dxy_AE_mm']for r in rr if r['Dxy_AE_mm']is not None]);re=np.array([r['Dxy_relative_error']for r in rr if r['Dxy_relative_error']is not None]);cd=np.array([r['Chamfer_MAE_mm']for r in rr if r['Chamfer_MAE_mm']is not None]);summary.append(dict(stage=tag,target_N=11,numerical_models_N=sum((n,tag)in N for n in names),Dxy_evaluable_N=len(ae),Dxy_median_ARE_percent=float(100*np.median(re)),Dxy_MAE_mm=float(ae.mean()),Dxy_p95_AE_mm=float(np.quantile(ae,.95)),Dxy_max_AE_mm=float(ae.max()),Chamfer_group_mean_mm=float(cd.mean()),height_evaluable_N=sum(r['height_max_AE_mm']is not None for r in rr),strict_solid_IoU_evaluable_N=sum(r['IoU_3D']is not None for r in rr)))
 table('metrics/PAIRED_STAGE_STATISTICS.csv',summary);save('metrics/PAIRED_STAGE_STATISTICS.json',summary);cd_delta=np.array([G[n,'FINAL014']['Chamfer_MAE_mm']-G[n,'FINAL013']['Chamfer_MAE_mm']for n in names]);iou_delta=np.array([N[n,'FINAL014']['FIT_IoU']-N[n,'FINAL013']['FIT_IoU']for n in names]);paired=[dict(case=n,Chamfer014_minus013_mm=float(cd_delta[i]),IoU014_minus013=float(iou_delta[i]),DxyAE014_minus013_mm=G[n,'FINAL014']['Dxy_AE_mm']-G[n,'FINAL013']['Dxy_AE_mm'])for i,n in enumerate(names)];table('metrics/PAIRED_FINAL013_014.csv',paired)
 rho=spearmanr(iou_delta,-cd_delta).statistic if len(np.unique(iou_delta))>1 and len(np.unique(cd_delta))>1 else None
 consistency=dict(physical_group_N=len(names),comparison='FINAL014 minus FINAL013, same014 native cameras and same bestSE3 evaluator; whole-pipeline descriptive comparison, not an isolated-factor test',FIT_IoU_improved_N=int((iou_delta>0).sum()),Chamfer_improved_N=int((cd_delta<0).sum()),FIT_IoU_improved_but_Chamfer_worsened_N=int(((iou_delta>0)&(cd_delta>0)).sum()),same_change_direction_N=int((np.sign(iou_delta)==np.sign(-cd_delta)).sum()),Spearman_IoU_change_vs_Chamfer_improvement=float(rho)if rho is not None else None,GT_used_for_method_selection=False,not_a_predeclared_scientific_acceptance_gate=True)
 save('metrics/METRIC_CONSISTENCY.json',consistency)
 rejected=[]
 for root in sorted((R/'arms').iterdir()):
  for p in (root/'metrics').glob('*_CANDIDATES.json'):
   hh=load(p);counter=Counter(v for x in hh for v in x['reasons']);rejected.append(dict(arm=root.name,case=p.stem.replace('_CANDIDATES',''),candidate_trials=len(hh),accepted_trials=sum(x['accepted']for x in hh),reason_counts=dict(counter)))
 save('metrics/REJECTION_REASON_COUNTS.json',rejected);table('metrics/REJECTION_REASON_COUNTS.csv',rejected)
 for r in runs:
  if r['status']!='ACCEPTED_TARGET_REACHED':fail.append(dict(case=r['case'],stage=r['tag'],reason=r['status'],accepted=r['accepted'],attempts=r['attempts'],evidence='arms/'+r['tag']+'/metrics/'+r['case']+'_TRAINING.json'))
 fail+= [dict(case='G01',stage='POSE',reason='B1 held background residual remains large; B2 not justified; time-negative control drifts0.381mm',evidence='POSE_CORRECTION_REPORT.md'),dict(case='G08',stage='OBSERVATION',reason='video00640 raw candidates have no anchored metric camera; retained unknown, not fabricated',evidence='metrics/UNPOSED_RAW_CANDIDATES.json'),dict(case='ALL',stage='OBSERVATION',reason='34 independent photos lack verified metric projection; retained in inventory',evidence='config/RAW_ASSETS.json'),dict(case='G06',stage='ENGINEERING_RESOLVED',reason='C0 resource interruption; exact optimizer/RNG checkpoint resume, original log retained',evidence='provenance/G06_RESOURCE_INTERRUPT.json'),dict(case='G01',stage='ENGINEERING_RESOLVED',reason='Repeated-key score serialization failure after first C0 model; no retraining',evidence='provenance/IMPLEMENTATION_AMENDMENTS.md')]
 unknown=load(R/'metrics/UNPOSED_RAW_CANDIDATES.json')
 for n in names:
  missing=[r for r in unknown if r['case']==n]
  if missing:fail.append(dict(case=n,stage='OBSERVATION_PARTIAL',reason=f"{len(missing)} raw candidates remain without a metric camera, not a group rejection",ids=[r['id']for r in missing],evidence='metrics/UNPOSED_RAW_CANDIDATES.json'))
 table('metrics/FAILURES.csv',fail);save('metrics/FAILURES.json',fail)
 per=load(R/'metrics/PER_VIEW_METRICS.json');posequality=[]
 for n in names:
  for video in sorted({r['video']for r in per if r['case']==n and r['tag']=='FINAL014'}):
   vv=[r for r in per if r['case']==n and r['tag']=='FINAL014'and r['video']==video];posequality.append(dict(case=n,video=video,posed_N=len(vv),median_Ring_CAD_Mask_IoU=float(np.median([r['Ring_CAD_mask_IoU_diagnostic']for r in vv])),zero_CAD_projection_N=sum(r['CAD_visible_pixel_N']==0 for r in vv),old_Gate_used_for_rejection=False,qualification='numeric derived pose, not certified camera'))
 table('metrics/INPUT_POSE_QUALITY_BY_VIDEO.csv',posequality)
 badgeom=sum(not r['Ring_numeric_nonworsening']or r['self_intersections']or r['Blender_self_intersections']or r['nonmanifold_edges']for r in final);height_na=sum(r['height_AE_mm']is None for r in final);iou_na=sum(r['IoU3D']is None for r in final)
 audit=f'''| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 11个独立真实物理组，不将多视频或多实验臂算成独立病例 |
| 本算法独立成功 | 11/11生成本路线FINAL014数值模型；继承人工授权011初值，数值输出不等于测量正确 |
| 本算法失败 | 数值模型失败0/11；几何验收失败{badgeom}/11；高度NaN {height_na}/11，严格实体IoU NaN {iou_na}/11；逐组见FAILURE_LEDGER.md，未剔除困难病例 |
| 历史测量值回退 | 0；011/012/013仅作明确标识的初值或评价对照，没有补填014测量值 |
| 失败组及具体原因 | metrics/FAILURES.csv、逐臂运行日志、全部原始模型及核心图 |
| 最终统计样本 | 数值模型11/11；各评价项实际可计算N分别汇报，空白CSV为NaN而非0 |
| 是否使用GT选择算法 | 否；C/D/E仅用预登记FIT规则；全部模型/尺度先冻结，GT访问时间在provenance/GT_ACCESS_START.json |
'''
 invalid=sum(not r['Ring_numeric_nonworsening']for r in final);good=int((cd_delta<0).sum());ec=np.array([G[n,'E2_adaptive']['Chamfer_MAE_mm']-G[n,'E1_global']['Chamfer_MAE_mm']for n in names]);questions=[('Q1','SUPPORTED','资产索引、方向聚类、代表帧、SIFT/PnP、渲染及最佳SE3评价复用；旧Polyp-HERO配准和稀疏Ring检查拒绝复用。CODE_REUSE_AUDIT.md'),('Q2','PARTIALLY_SUPPORTED'if any(G[n,'C4_ALL']['Chamfer_MAE_mm']<G[n,'C0']['Chamfer_MAE_mm']for n in names)else'NOT_SUPPORTED','见VIEW_COUNT_ABLATION.csv；新增条件相机并不等于可靠新观测，不能将数量效应与输入误差混为一谈。'),('Q3','SUPPORTED','候选方向/块/实际N见metrics/VIEW_COVERAGE.csv和VIEW_SELECTION.json；这不是经GT认证的物理覆盖。'),('Q4','PARTIALLY_SUPPORTED','逐视角FN、FP、Ring-front与边界误差全部保留；以PER_VIEW_METRICS.csv和Fig4/8为据，局部改善不自动代表全局改善。'),('Q5','PARTIALLY_SUPPORTED','存在稳定大yaw坐标修正候选，不能区分纯Gauge差异与真实位姿错误。BG独立残差仍大。'),('Q6','NOT_SUPPORTED','尚不能证明Ring/背景/息肉独立投影都稳定改善；负对照非零漂移。B2 NOT_EVALUABLE。'),('Q7','PARTIALLY_SUPPORTED','B_A_ONLY/B0_UNCORRECTED/C1_8共享Mesh原004指标见Fig3与逐视频表；不期待005必然新增可见面积。'),('Q8','PARTIALLY_SUPPORTED','D0-D3的FN/FP分别记录，未单独为G02选择方法；LOSS_ABLATION.csv。'),('Q9','PARTIALLY_SUPPORTED','观察、远轮廓梯度、CAD/几何回缩、局部密度同时可能限制。Fig5/6与G03逐候选拒绝原因提供实证，不能仅凭Dxy近似就声称长柄恢复。'),('Q10','SUPPORTED'if ec.mean()<0 and(ec<0).sum()>=6 else'PARTIALLY_SUPPORTED'if(ec<0).any()else'NOT_SUPPORTED',f'E2-E1配对平均Chamfer差{ec.mean():.4f}mm，改善{int((ec<0).sum())}/11；共同粗网格先验控制及不训练细分几何检查另列；软光栅密度影响也单列。'),('Q11','PARTIALLY_SUPPORTED', 'G07-G11逐例见Fig7和配对表，不以整体均值掩盖未改善病例。'),('Q12','PARTIALLY_SUPPORTED',f'014相对013的Chamfer改善{good}/11；最佳刚性对齐是形状评价，不是相机定位精度。'),('Q13','SUPPORTED','官方渲染、共享参数梯度、有限安全更新和真实Mesh输出可运行；工程可行性不代表主线已验收。'),('Q14','PARTIALLY_SUPPORTED','仍需可靠公制视角/背景静态性、可观测几何对应、接触约束可行方向和网格表达研究。未执行SDFStudio/BundleSDF或其他新路线。')]
 table('metrics/SCIENTIFIC_QUESTIONS.csv',[dict(question=q,status=s,evidence=e)for q,s,e in questions]);table('metrics/FINAL_INTERPRETATION.json.csv',paired)
 report=f'''# TASK-E4-PYTORCH3D-014 技术报告

11个独立物理组完成统一共享Mesh实验与冻结后Blender评价。原九例精确继承011 FINAL；G10/G11继承013中已冻结的配方等效011初值，不能冒称历史011原实验曾包含这两例。方法仅用预登记FIT规则选定：C={C}，D粗结果={D}，E={E}；同一方法用于全部组。014相对013的双向Chamfer改善{good}/11，配对平均变化{cd_delta.mean():.4f}mm；独立64阶Ring非恶化检查仍失败{invalid}/11，均未删面掩盖。是否采用交由人工审核，未替换正式主线。

{audit}

## A：资产与视角组织

22视频、34照片、942固定原帧候选；820取得数值背景PnP相机解，含历史参考后826个规范候选。122原帧缺pose及全部照片的未知字段保留，旧Gate未排除任何物理组。C4是固定40+历史候选池中除预冻结Mesh更新HOLDOUT之外的全部可执行观测，不是每个原视频帧都进入优化。完整原帧时间索引、本体身份和SHA见VIEW_COVERAGE_REPORT.md、VIEW_INVENTORY.csv。相机误差仍是研究对象；数值PnP成功不等于相机真实。

## B：参考视频锚定

G01主004恒Identity，005一个共享SE3研究候选，无尺度。使用真实静态背景RGB三角化和Ring先验，未用Polyp HERO/ICP。留出BG MAE341.99→73.72px但p95仍452px；逆向FIT仅18点；真正同视频时间负对照产生0.381mm/0.214°漂移。不能认证相机修复，B2未执行。原相机不覆盖。004/005的共同Mesh稳定性与新增覆盖分开，见POSE_CORRECTION_REPORT.md、Fig2/3。

## C/D/E：受控几何实验

C0/8/16/32/全部候选均同011初值，视频、方向块均衡。无HERO新帧仅轮廓。原始HERO同视角绝对/相对深度及边界权重固定，深度集合独立归一，不随新增无深度视角稀释。跨视角HERO不进入损失、权重、筛选或停止。22份实际HERO监督的原生640×352深度像素与640×360 RGB像素具有不同fy/cy，已按冻结RGB_uv映射验证相机射线相同，c2w一致；见provenance/DEPTH_RENDER_CAMERA_CONSISTENCY.json，不把两套K数值不同误判为相机错误。

013 A3已含分离FN/FP和双向轮廓，因此D1仅增强FP权重、D2仅增强已有双向轮廓、D3组合，均为预登记小增量，不冒称新机制。全部条件沿用相同Adam、4个通用局部方向、8级回缩及精确回滚。候选80/接受40，正式延续160/接受80，固定停滞30/60；未按GT挑选checkpoint。

E0/E1/E2从同一冻结粗结果出发。官方SubdivideMeshes全局一次或BMesh局部插值，不平滑、不造柄。实际未训练几何误差、面积和体积变化记录在metrics/refinement。共同粗网格限制先验+面积归一细尺度残差控制密度影响；每例仿射对照见DENSITY_NORMALIZATION_CONTROLS.csv，初始软轮廓光栅变化另列，不能将软alpha变化当作真实几何改善。

未知区域形状保护使用同一公式，其支持代理随可用FIT证据变化，属于数据依赖部分；并非完全固定的可见性掩码。HOLDOUT由渲染器预加载和预处理，但没有进入几何损失、模型选择或停止；上游初始化、相机和HERO可能已使用这些RGB，因此这里只称本轮Mesh更新留出，不称端到端独立测试。共同FIT评价池与每模型实际更新视角分开标记。

## 几何与数值审计

旧稀疏Ring检查的真实盲区在控制中复现：旧最小距离+3.8499mm，新密集查询−0.5735mm，FCL亦相交。新候选32阶面内采样+FCL+反向包含+Open3D自交检查，最终独立64阶检查；同一CAD的可证明外部剔除和场景缓存仅做等价加速，逐例查询对照保留。正间隙可为保守下界，材料穿透查询仍使用实际CAD；不声称有限采样是连续空间完全证明。

第一次C0/G01后处理重复字典键错误已修复并复用原FINAL；C0/G06资源中断从完整Adam/RNG检查点恢复，原日志保留，尾段有重做成本，不冒称位级无缝重现。见provenance/IMPLEMENTATION_AMENDMENTS.md。逐轮各损失和实际参数梯度、真实位移、接受/拒绝全部留存。

## F：独立GT评价

**After Ring-based Metric Recovery and Best 6-DoF Rigid Alignment**。Ring CAD恢复系数接近1且只核验不重复缩放。GT只在所有预测、方法和尺度冻结后打开；全部阶段使用同96正旋转初值、top8双向表面刚性优化，一模型一个SE3服务所有指标，无尺度、镜像或非刚性。最佳是已测初值中最佳，不提供全局最优证明。Ring/背景不参与主体配准。旧011/012/013与014使用同一评价实现，缓存复用及精确函数来源另列。

{md(summary,['stage','target_N','Dxy_evaluable_N','Dxy_median_ARE_percent','Dxy_MAE_mm','Dxy_p95_AE_mm','Dxy_max_AE_mm','Chamfer_group_mean_mm','height_evaluable_N','strict_solid_IoU_evaluable_N'])}

{md(final,['case','FIT_IoU','HOLDOUT_IoU','HERO_hit_rate','HERO_MAE_active_mm','Chamfer_mm','Dxy_AE_mm','height_AE_mm','Ring_new_vs011_mm','final_accepted'])}

主轮廓指标继承013的观测Ring忽略规则，另报告全像素可见IoU和Ring前方冲突，不能用主IoU隐藏物理冲突。HERO原始合格观测分母另行按射线数汇总，不把无深度视角的零项当作深度正确。命中MAE必须结合固定N、命中率和9.5未命中代价。GT表面距离为统一面积采样估计；NA保留，推断底盖不混称可见真实组织。真实部署基底与作者基底可能不同，刚性对齐后的高度/体积属于条件形状比较，不代表真实部署测量精度。

014相对013的二维—三维变化同向为{consistency['same_change_direction_N']}/11，FIT IoU改善但Chamfer恶化为{consistency['FIT_IoU_improved_but_Chamfer_worsened_N']}/11；IoU变化与Chamfer改善的Spearman相关为{fmt(consistency['Spearman_IoU_change_vs_Chamfer_improvement'])}。这只是11个物理组的描述性配对关系，不是用GT设立新的验收门槛，也不能替代逐例形态判读。见metrics/METRIC_CONSISTENCY.json及PER_CASE_ANALYSIS.md。

## 十四项科研问题

{md([dict(问题=q,判断=s,证据=e)for q,s,e in questions],['问题','判断','证据'])}

## 原始结果与可视化

Fig1–10在figures/，原始模型/参数与运行时间见RESULT_INDEX.md。全部C/D/E、历史三阶段和014的逐参考指标见PER_VIEW_METRICS.csv；配对比较见metrics/PAIRED_FINAL013_014.csv，失败见FAILURE_LEDGER.md。没有根据GT重训、删面、后平滑或重选病例。完成后停止，等待研究者与PM审核。
''';(R/'TECHNICAL_REPORT.md').write_text(report);(R/'FINAL_FINDINGS.md').write_text('# 最终发现\n\n'+f'统一方法C={C} / coarse={D} / E={E}。014 Chamfer相对013改善{good}/11，均值差{cd_delta.mean():.4f}mm；独立Ring非恶化失败{invalid}/11。\n\n'+md([dict(问题=q,判断=s,证据=e)for q,s,e in questions],['问题','判断','证据'])+'\n\n'+audit)
 (R/'FAILURE_LEDGER.md').write_text('# 失败记录（原始结果完整保留）\n\n'+audit+'\n\n'+md(fail,['case','stage','reason','evidence'])+'\n\n逐候选级原因数并非独立物理病例数，见metrics/REJECTION_REASON_COUNTS.csv。未修改阈值制造PASS。')
 index=[asset(p)for p in sorted((R/'arms').glob('*/local_results/*/FINAL.*'))];save('provenance/LOCAL_CHECKPOINT_AND_MESH_INDEX.json',dict(files=index,large_artifacts_local_only=True));(R/'RESULT_INDEX.md').write_text('# 结果索引\n\n'+ '\n'.join(f'- [{p.name}](figures/{p.name})'for p in sorted((R/'figures').glob('Fig*.png')))+'\n\n最终原始模型：meshes/Gxx/FINAL014_mm.npz；可审阅模型：review_models/Gxx/FINAL014_mm.ply、FINAL014_scene_m.glb。NPZ/PLY为mm，GLB仅展示转换为m。\n\n全部阶段：arms/<condition>/local_results/Gxx/；FINAL.pt包含参数、Adam、随机状态、迭代与配置。源文件哈希、绝对路径及字节数见provenance/LOCAL_CHECKPOINT_AND_MESH_INDEX.json；输入视频/HERO/权重不复制上传。\n\n统一指标：VIEW_COUNT_ABLATION.csv / LOSS_ABLATION.csv / MESH_REFINEMENT_ABLATION.csv / PER_VIEW_METRICS.csv / BLENDER_ALIGNMENT_METRICS.csv。')
 (R/'REPRODUCE.md').write_text('''# 复现

工作树：/home/liu/ring_first_3d_e4_sdf_localization；Python：/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python；Blender：/home/liu/blender/blender-5.0.1-linux-x64/blender。依赖复用，无新大模型下载。完整数据需要恢复provenance中的SHA对应路径，不能只clone代码就假设原视频/HERO/预训练INIT权重存在。

1. 在独立新副本准备TASK/config/code；保留现有014冻结结果不覆盖。
2. 依次运行code/inventory.py、prepare_views.py、expand_cameras.py、propagate_background.py、pose_correction.py、true_time_negative.py --solve、pose_audit.py、partition_views.py（--solve仅限无旧结果的新复现副本）。现有目录运行true_time_negative.py仅核对244条冻结背景观测，不重跑优化；B1仅研究候选，具体采用策略见POSE_ADOPTION_AUDIT。
3. CPU控制：code/geometry_preflight.py、depth_camera_audit.py、true_time_negative.py。正式串行GPU：code/driver014.py C，然后code/pipeline_remaining.py。后者包括工程检查点恢复、B控制、D/E及最终冻结。
4. 全部预测与尺度冻结后运行code/wait_evaluate.py：只读梯度诊断→固定原生观测→64阶几何/Blender BVH→统一最佳SE3。GT访问由显式冻结门控。
5. code/figures_A.py、figures_B.py、figures_final.py、report014.py。中断后已完成FINAL不重训；未完成的训练从完整ACCEPTED checkpoint恢复。旧的源码版本按SHA归档。若需逐字节重现早期C0实现，使用provenance/source_versions对应快照；后续工程加速的等价检查另列。相同种子不宣称CUDA原子运算的位级一致。

本实验的正式预测与尺度已冻结，train014.py禁止在原目录继续更新。检查点迁移必须建立新隔离运行，保持参数、优化器、RNG和原始坐标；仅加载权重不能称完整续训。除评价GT访问外，优化器路径禁止读取audit_only/evaluation_only/.blend及原始GT资产。
''')
 for name in ['VIEW_COVERAGE_REPORT.md','POSE_CORRECTION_REPORT.md']:
  p=R/name;text=p.read_text()
  if '| 审计项目 |'not in text:p.write_text(text+'\n\n'+audit)
 # Per-case evidence, including the difficult G07-G11: never hide them in a mean.
 sections=[]
 for n in names:
  old=N[n,'FINAL013'];now=N[n,'FINAL014'];init=N[n,'FINAL011'];q=Q[n,'FINAL014'];g0=G[n,'FINAL013'];g1=G[n,'FINAL014'];run=next(v for v in runs if v['case']==n and v['tag']=='FINAL_014')
  cr=[merged(n,t)for t in ['C0','C1_8','C2_16','C3_32','C4_ALL']]
  dr=[merged(n,t)for t in [C,'D_D1_split','D_D2_bidir','D_D3_combo']]
  er=[merged(n,t)for t in ['E0_none','E1_global','E2_adaptive']]
  init_note=f"011起点在本轮共同FIT池的IoU={fmt(init['FIT_IoU'])}、HERO首层命中率={fmt(init['FIT_HERO_hit_rate'])}。初始轮廓与深度支持分别记录，不将椭球外观视为合理性的证明。"
  sides='三维表面距离改善'if g1['Chamfer_MAE_mm']<g0['Chamfer_MAE_mm']else'三维表面距离未改善'
  txt=f"## {n} / {next(c['morphology']for c in cases if c['name']==n)}\n\n{init_note}\n\n"
  txt+=f"最终模型相对013：共同FIT IoU {fmt(old['FIT_IoU'])}→{fmt(now['FIT_IoU'])}，Mesh更新HOLDOUT IoU {fmt(old['HOLDOUT_IoU'])}→{fmt(now['HOLDOUT_IoU'])}；FIT漏覆盖率 {fmt(1-old['FIT']['Recall'])}→{fmt(1-now['FIT']['Recall'])}，背景越界/Mask {fmt(old['FIT']['FP_per_mask'])}→{fmt(now['FIT']['FP_per_mask'])}。两种错误单列，不以IoU替代。\n\n"
  txt+=f"最佳同尺度刚性对齐后Chamfer {fmt(g0['Chamfer_MAE_mm'])}→{fmt(g1['Chamfer_MAE_mm'])} mm（{sides}）；GT→预测p95 {fmt(g0['GT_to_prediction_mm']['p95'])}→{fmt(g1['GT_to_prediction_mm']['p95'])} mm。该指标仍包括完整GT与部分观测表面的覆盖差异。\n\n"
  txt+=f"本轮最终延续接受 {run['accepted']}/{run['attempts']} 次，最大实际位移 {fmt(run['maximum_displacement_mm'])} mm。独立Ring材料穿透 {fmt(q['Ring_max_material_penetration_mm'])} mm；相对011非恶化={q['Ring_worsening_within_epsilon']}，Open3D自交对数={q['self_intersections_Open3D']}，非流形边={q['nonmanifold_edges_N']}。未用删面或后平滑掩盖。\n\n"
  txt+='新增视角作用（同一共同评价池；新方向不等同于真实新增侧面）：\n\n'+md(cr,['model','training_views_N','FIT_IoU','HOLDOUT_IoU','FIT_recall','FIT_FP_per_mask','HERO_hit_rate','Chamfer_MAE_mm'])+'\n\n'
  txt+='轮廓权重与细分控制：\n\n'+md(dr+er,['model','FIT_IoU','HOLDOUT_IoU','FIT_FP_per_mask','boundary_MAE_px','Chamfer_MAE_mm','Ring_penetration_mm','accepted'])+'\n\n'
  txt+=f"原始空间形态、更新位置及误差分布见figures/details/{n}_Pure_Body_Six_Views.png、核心Fig4–7及Fig10。局部拉伸、折棱应结合真实面片图与metrics/POST_GEOMETRY_AUDIT.csv；无观测支持区域保持UNKNOWN，不能仅据新增面积声称真实侧面恢复。\n\n"
  sections.append(txt)
 (R/'PER_CASE_ANALYSIS.md').write_text('# 十一例逐例证据\n\n旧013与014的全过程比较包含视角、预算和更严格几何保护的变化；内部C/D/E才是对应因素的等预算对照。GT仅冻结后读取。\n\n'+''.join(sections)+audit)
 version=REPO/'docs/KEY_TECHNICAL_VERSION_E4_MULTI_VIEW_REFINEMENT_CANDIDATE_v0.19.md';version.write_text('# E4关键技术候选v0.19：参考视频共享Mesh、轮廓增量与自适应细分\n\n状态：AWAITING_HUMAN_REVIEW；不替换正式主线。\n\n[014技术报告](../experiments/TASK-E4-PYTORCH3D-014/TECHNICAL_REPORT.md)。继承011/013冻结资产，11个物理组；新派生观测和相机不覆盖原始文件，Ring唯一公制尺度。\n\n'+f'统一FIT选定C={C}、D粗结果={D}、E={E}，全部模型和尺度冻结后才进行同一最佳6DoF GT评价。014相对013 Chamfer改善{good}/11、均值变化{cd_delta.mean():.4f}mm；独立Ring非恶化仍失败{invalid}/11，原始失败完整保留。G01共享SE3只是研究候选，独立BG残差和负对照尚不足以认证修复，B2未执行。\n\n原生观测、全部对照、密集32/64阶实际CAD检查、全局/局部插值零形变及共同粗先验密度控制均可追溯。新相机数值成功、新顶点数增加、二维IoU改善均不单独代表三维真值正确；详见14项证据结论。\n\n'+audit)
 g03rows=[]
 for tag in ['C0','C1_8','C2_16','C3_32','C4_ALL','D_D1_split','D_D2_bidir','D_D3_combo','E0_none','E1_global','E2_adaptive','FINAL_014']:
  r=next(v for v in runs if v['case']=='G03'and v['tag']==tag);reasons=next(v for v in rejected if v['case']=='G03'and v['arm']==tag);g03rows.append(dict(stage=tag,accepted=r['accepted'],attempts=r['attempts'],max_displacement_mm=r['maximum_displacement_mm'],vertices=r['vertices'],faces=r['faces'],dominant_rejection=max(reasons['reason_counts'],key=reasons['reason_counts'].get)if reasons['reason_counts']else'NONE'))
 gd=[]
 for tag in [C,'D_D1_split','D_D2_bidir','D_D3_combo']:
  p=R/'arms'/tag/'metrics/G03_GRADIENT_DIAGNOSTIC.json';d=load(p);arr=np.load(p.with_suffix('.npz'));mask=arr['far_associated'];im=arr['silhouette']+arr['missing']+arr['extra']+arr['contour'];deep=arr['absolute']+arr['relative'];gd.append(dict(arm=tag,far_associated_vertices=d['far_associated_vertex_N'],far_vertices_in_local_candidate_bands=d['far_vertices_in_jointgradient_local_bands_N'],image_gradient_on_far_vertices=float(np.linalg.norm(im[mask])),depth_gradient_on_far_vertices=float(np.linalg.norm(deep[mask])),Ring_uncertain_target_contour_samples=sum(v['Ring_uncertainty_band_target_N']for v in d['localization']),target_contour_samples=sum(v['target_contour_N']for v in d['localization'])))
 table('metrics/G03_UPDATE_BOTTLENECK.csv',g03rows);table('metrics/G03_LOCALIZATION_GRADIENTS.csv',gd);gb=[]
 for tag in ['FINAL011','FINAL013','FINAL014']:
  v=G['G03',tag];gb.append(dict(stage=tag,Dxy_AE_mm=v['Dxy_AE_mm'],author_axis_span_mm=v.get('prediction_top_to_bottom_span_mm'),GT_span_mm=v.get('GT_top_to_bottom_span_mm'),lowest_point_vs_author_base_mm=v.get('lowest_point_vs_author_base_mm'),GT_to_pred_p95_mm=v['GT_to_prediction_mm']['p95'],Chamfer_MAE_mm=v['Chamfer_MAE_mm']))
 text='# G03 更新瓶颈的实际证据\n\n'+md(g03rows,['stage','accepted','attempts','max_displacement_mm','vertices','faces','dominant_rejection'])+'\n\n'+md(gd,['arm','far_associated_vertices','far_vertices_in_local_candidate_bands','image_gradient_on_far_vertices','depth_gradient_on_far_vertices','Ring_uncertain_target_contour_samples','target_contour_samples'])+'\n\n'+md(gb,['stage','Dxy_AE_mm','author_axis_span_mm','GT_span_mm','lowest_point_vs_author_base_mm','GT_to_pred_p95_mm','Chamfer_MAE_mm'])+'\n\n远目标只表示二维最近投影代理，不是真实三维对应；Ring带目标也可能是遮挡截断边而非真实主体外轮廓。本轮只诊断、不事后过滤或调整权重。局部候选带由总梯度选择，不能假设已覆盖全部远漏轮廓区域。应结合实际梯度分量、覆盖比例和逐候选Ring/目标拒绝原因，区分区域分配、约束不可行与顶点密度。旧013的大变形同时存在稀疏Ring漏检，不能将更严格物理检查后的位移减小单独归因于学习率。FACE_ORIENTATION检查使用候选面法向与该阶段初始面法向点积为正这一保守代理；大于90°的合法面片转向也可能被拒绝，不能把该拒绝原因直接等同于已证明的网格翻面或自交。AREA_DEGENERACY同样是相对初始面积的10%限制。这些固定保护与定位/优化的限制共同存在，本轮没有为G03放宽。\n\nE1/E2增顶点本身不改变形状；只有继续更新后的实际Mesh和GT空间缺失才构成恢复证据。Dxy或高度跨度接近不能替代柄部完整性判断。三维GT只是冻结后的独立审计，未参与定位、选择或停止。\n\n'+audit;(R/'G03_FAILURE_DIAGNOSIS.md').write_text(text)
 print('REPORT014_WRITTEN',len(final),len(fail),len(runs),flush=True)
if __name__=='__main__':main()
