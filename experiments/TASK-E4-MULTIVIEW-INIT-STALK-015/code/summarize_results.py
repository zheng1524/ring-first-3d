"""Evidence-derived tables/report. Never changes or ranks a prediction by GT."""
from audit_models import *
from collections import Counter

def main():
 assert(R/'provenance/ALL_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json').exists();A=load(R/'metrics/PHASE_A_ALL_METRICS.json');B=load(R/'metrics/PHASE_B_RUNS.json');chosen=load(R/'config/PHASE_A_SELECTED.json');cases=load(R/'config/CASE_LOCK.json');gt=[];transforms=[]
 for c in cases:
  n=c['name'];p=R/'metrics/eval_case'/(n+'_BLENDER_GEOMETRIC_METRICS.json')
  if p.exists():gt+=load(p);transforms+=load(R/'metrics/eval_case'/(n+'_BLENDER_RIGID_ALIGNMENT.json'))
 save('metrics/BLENDER_GEOMETRIC_METRICS.json',gt);table('metrics/BLENDER_GEOMETRIC_METRICS.csv',gt);save('metrics/BLENDER_RIGID_ALIGNMENT.json',transforms);table('metrics/BLENDER_RIGID_ALIGNMENT.csv',transforms)
 bmetrics=[];failure=[];index=[]
 for c in cases:
  n=c['name']
  for t in ['Init-A','Init-B','Init-C']:
   run=load(R/'arms'/t/'metrics'/(n+'_RUN.json'));trials=load(R/'arms'/t/'metrics'/(n+'_CANDIDATES.json'));hist=load(R/'arms'/t/'metrics'/(n+'_TRAINING.json'));reason=Counter(k for q in trials for k in q['reasons']);failure.append(dict(case=n,phase='A',arm=t,run=run,rejection_counts=dict(reason),numerical_output=True,scientific_success_not_implied=True));index.append(dict(case=n,phase='A',arm=t,initial_npz=str(R/'initializations'/n/(t+'.npz')),final_npz=str(R/'arms'/t/'local_results'/n/'FINAL.npz'),full_optimizer_checkpoint=str(R/'arms'/t/'local_results'/n/'FINAL.pt'),case_figure=str(R/'figures/phase_A'/(n+'_Initialization_And_Update.png'))))
 for run in B:
  n,t=run['case'],run['arm'];root=R/'arms'/t;path=root/'local_results'/n/'FINAL.npz'
  if not path.exists():failure.append(dict(case=n,phase='B',arm=t,numerical_output=False,scientific_success=False,reason=run));continue
  sc=load(R/'metrics/scores'/(n+'_'+t+'_FINAL.json'));base=audit(n,root/'inputs'/n/'INITIAL.npz');geo=audit(n,path,base);d=fixed_depth(sc);trials=load(root/'metrics'/(n+'_CANDIDATES.json'));reason=Counter(k for q in trials for k in q['reasons']);row=dict(case=n,arm=t,FIT=sc['mean']['FIT'],HOLDOUT=sc['mean']['UPDATE_HOLDOUT'],HERO_FIT=d,HERO_HOLDOUT=fixed_depth(sc,'UPDATE_HOLDOUT'),geometry=geo,run=run,rejection_counts=dict(reason),surface_change=compare_surfaces(root/'inputs'/n/'INITIAL.npz',path));bmetrics.append(row);failure.append(dict(case=n,phase='B',arm=t,numerical_output=True,run=run,rejection_counts=dict(reason),scientific_success_not_implied=True));index.append(dict(case=n,phase='B',arm=t,initial_npz=str(root/'inputs'/n/'INITIAL.npz'),final_npz=str(path),full_optimizer_checkpoint=str(root/'local_results'/n/'FINAL.pt'),case_figure=str(R/'figures/phase_B'/(n+'_Stalk_Comparison.png'))))
 save('metrics/PHASE_B_ALL_METRICS.json',bmetrics);table('metrics/PHASE_B_ALL_METRICS.csv',bmetrics)
 flat=[]
 for q in A+bmetrics:
  flat.append(dict(case=q['case'],arm=q['arm'],stage=q.get('stage','FINAL'),FIT_IoU=q['FIT']['IoU'],HOLDOUT_IoU=q['HOLDOUT']['IoU'],FIT_contour_px=q['FIT'].get('contour_MAE_px'),HERO_fixed_N=q['HERO_FIT']['fixed_N'],HERO_hit_rate=q['HERO_FIT']['hit_rate'],HERO_hit_MAE_mm=q['HERO_FIT']['active_MAE_mm'],HERO_fixed_cost=q['HERO_FIT']['fixed_cost'],dense_Ring_penetration_mm=q['geometry']['dense_Ring_penetration_mm'],self_N=q['geometry']['self_intersections_N'],components=q['geometry']['components'],watertight=q['geometry']['watertight'],GT_selection=False))
 table('metrics/ALL_NATIVE_FLAT.csv',flat)
 save('metrics/FAILURE_LEDGER.json',failure);save('metrics/RESULT_INDEX.json',index)
 # Only paired common-success comparisons, explicit target group denominator.
 summaries=[];paired=[]
 labels=list(dict.fromkeys(x['label']for x in gt))
 for label in labels:
  rr=[q for q in gt if q['label']==label];dx=[q['Dxy_AE_mm']for q in rr if q.get('Dxy_AE_mm')is not None];rel=[q['Dxy_relative_error']for q in rr if q.get('Dxy_relative_error')is not None];cd=[q['Chamfer_MAE_mm']for q in rr if q.get('Chamfer_MAE_mm')is not None];target=5 if label.startswith('Stalk')else 11;summaries.append(dict(label=label,target_groups=target,numeric_prediction_N=sum(m['label']==label for m in load(R/'config/EVAL_MODELS.json')),GT_Chamfer_evaluable_N=len(cd),Dxy_evaluable_N=len(dx),Dxy_AE_mm=stats(dx),median_absolute_relative_error=float(np.median(rel))if rel else None,Chamfer_MAE_across_cases_mm=stats(cd),historical_prediction_fallback_N=0,GT_used_for_selection=False))
 for left,right in [('Init-A_FINAL','Init-B_FINAL'),('Init-A_FINAL','Init-C_FINAL'),('Stalk-A','Stalk-B'),('Stalk-A','Stalk-C')]:
  l={q['case']:q for q in gt if q['label']==left};r={q['case']:q for q in gt if q['label']==right}
  for n in l.keys()&r.keys():
   if l[n].get('Chamfer_MAE_mm')is not None and r[n].get('Chamfer_MAE_mm')is not None:paired.append(dict(case=n,left=left,right=right,Chamfer_delta_right_minus_left_mm=r[n]['Chamfer_MAE_mm']-l[n]['Chamfer_MAE_mm'],Dxy_AE_delta_right_minus_left_mm=(r[n]['Dxy_AE_mm']-l[n]['Dxy_AE_mm'])if l[n].get('Dxy_AE_mm')is not None and r[n].get('Dxy_AE_mm')is not None else None))
 save('metrics/GT_ROUTE_SUMMARIES.json',summaries);table('metrics/GT_ROUTE_SUMMARIES.csv',summaries);table('metrics/COMMON_SUCCESS_PAIRED_COMPARISONS.csv',paired)
 fmt=lambda q:'NOT_EVALUABLE'if q is None else ('%.4f'%q)
 lines=['# TECHNICAL_REPORT_SUMMARY','', '## 任务与范围','', 'TASK-E4-MULTIVIEW-INIT-STALK-015；11个独立物理组（Ip5、Is3、IIa3），Phase A三种初始化×11=33条统一更新；Phase B仅5个Ip×3=15条。原始GT坐标没有独立部署标定；根据研究者追加指令，使用冻结后逐预测最佳6DoF ICP，尺度固定1。','', '## 实际算法与设计对照','', '| 原定设计 | 实际实现和代码位置 | 差异/限制 |','|---|---|---|','| 三种初始化 | `initialize.py:Initializer` / `publish.py:export_A` | A为真实013起点；B当前网格六参数共享多视角；C复用011明确参数化族，不从GT生成 |','| 互补视角与独立留出 | `prepare.py` 固定8FIT和保护原HOLDOUT | 同视频；HERO仅既有16张FIT，其他RGB视角不冒充深度 |','| 一致下游 | `train_mesh.py` / `multiview.py:MultiObjective` | 复用014的013系数及方向平衡、独立深度分母；不是逐字013加载器 |','| Stalk-A/B/C | `stalk.py` / `train_stalk.py` / `PHASE_B_ALGORITHM_CONTRACT.md` | C是11中心线/截面参数+局部残差的现有连通片形变；不新增管状拓扑；种子为轮廓反投影代理，未证实解剖身份 |','| 几何保护 | `safe_geometry.py:GeometryGuard` / `audit_models.py:audit` | 训练密集32+FCL+反向包含；最终独立64；不得以旧稀疏PASS冒充无碰撞 |','| GT独立评价 | `best_rigid015.py:align/main` | 与014数学实现相同；逐模型固定SE3、96起点top8，不能证明全局最优；无自由尺度 |','', '## Phase A 实测','', '| 方法 | FINAL FIT IoU中位数 | HOLDOUT IoU中位数 | 深度固定覆盖中位数 | 密集几何标记组 |','|---|---:|---:|---:|---:|']
 for t in ['Init-A','Init-B','Init-C']:
  rr=[q for q in A if q['stage']=='FINAL'and q['arm']==t];ss=next(q for q in chosen['summary']if q['arm']==t);lines.append('|%s|%s|%s|%s|%s|'%(t,fmt(float(np.median([q['FIT']['IoU']for q in rr]))),fmt(float(np.median([q['HOLDOUT']['IoU']for q in rr]))),fmt(float(np.median([q['HERO_FIT']['hit_rate']for q in rr if q['HERO_FIT']['hit_rate']is not None]))),ss['geometry_flagged_N']))
 lines+=['', '全组 FIT-only 冻结推荐：**'+chosen['selected']+'**。该推荐先于GT，不按病例挑最优。参考子集扰动及未对齐形态差异见 INITIALIZATION_STABILITY.csv。', '', '## Phase B 实测','', '| 病例/方法 | 接受/提案 | FIT IoU | HOLDOUT IoU | HERO固定覆盖 | 最大位移mm |','|---|---:|---:|---:|---:|---:|']
 for q in bmetrics:lines.append('|%s/%s|%s/%s|%s|%s|%s|%s|'%(q['case'],q['arm'],q['run']['accepted'],q['run']['attempts'],fmt(q['FIT']['IoU']),fmt(q['HOLDOUT']['IoU']),fmt(q['HERO_FIT']['hit_rate']),fmt(q['run']['maximum_displacement_mm'])))
 lines+=['','历史014的239远轮廓代理/30局部覆盖已独立CPU复核；当前5例的实际覆盖和各分量梯度另存 `arms/Stalk-A/metrics/*_STALK_PROBE.json`，不能把历史数值当成当前诊断。每次拒绝的实际Ring/全目标/面翻折原因保存在各arm的CANDIDATES.json。', '', '## GT形状评价','', '**After Ring-based Metric Recovery and Best 6-DoF Rigid Alignment**；8192个面积采样点/方向查询实际三角曲面；F-score阈值0.1/0.25/0.5/1mm。预测和GT的作者基底身份不充分时，高度为条件值或NOT_EVALUABLE；未标注头/柄区域的独立柄部Chamfer、真实长度和半径精度NOT_EVALUABLE，不用全体尺寸掩盖缺柄。', '', '| 路线 | GT可评价/目标 | Chamfer跨组均值mm | Dxy MAE mm | Dxy中位ARE |','|---|---:|---:|---:|---:|']
 for q in summaries:
  if q['label'].endswith('_FINAL')or q['label'].startswith('Stalk'):lines.append('|%s|%s/%s|%s|%s|%s|'%(q['label'],q['GT_Chamfer_evaluable_N'],q['target_groups'],fmt(q['Chamfer_MAE_across_cases_mm']['MAE']),fmt(q['Dxy_AE_mm']['MAE']),fmt(q['median_absolute_relative_error'])))
 lines+=['','全部中位/p95/max、双方向距离、Dxy/高度/F-score/占据限制及共同成功配对见原始CSV。ICP后结果仅描述形状，不能证明原相机位置正确。HOLDOUT从不用于训练或方案选择。','', '## 失败、偏差及B0','', '数值输出成功不等于三维正确。初始已有CAD冲突允许记录且不恶化，不能称物理资格通过。密集64检查比训练采样更细，发现新增穿透必须保留失败。相对初值的法向方向检查也会限制大转动/长柄伸展；候选覆盖改进不保证有真实三维定位。','', 'B0需同时审查整体方向/尺度、FIT和HOLDOUT轮廓、初始化稳定性、无严重几何错误及Ip柄骨架；本次不以GT或事后阈值制造自动PASS。最终逐组B0判断见 `B0_REVIEW.md`。在人工确认前，不推进HERO适配或扩展优化。','', '## 固定审计表','', '| 审计项目 | 必须汇报 |','|---|---|','| 目标组数 | Phase A11；Phase B5 Ip；33+15条路线 |','| 本算法独立成功 | 以metrics/RESULT_INDEX.json中实际新运行输出计数；基线初始化继承不冒充新估计 |','| 本算法失败 | NO_SIGNAL/非有限/停滞/几何失败逐条保留；缺结果NaN |','| 历史测量值回退 | 0 |','| 失败组及具体原因 | FAILURE_LEDGER.md及每条原始候选日志、逐病例可视化 |','| 最终统计样本 | 每路线独立结果且GT可评价的共同样本，同时保留11/5分母 |','| 是否使用GT选择算法 | 否；Phase A选择与所有预测、尺度在GT_FIRST_ACCESS前冻结 |','', '## 复现与产物','', '`REPRODUCE.md`；`metrics/RESULT_INDEX.json`含全部Mesh与完整优化器checkpoint绝对路径。4张核心图在figures/Fig1–Fig4，逐病例图和六视角详情保留本地。源码/协议/输入/预测SHA见provenance。无HERO新推理、无相机优化、无跨视频修正、未修改DXY。']
 text='\n'.join(lines)+'\n';(R/'TECHNICAL_REPORT_SUMMARY.md').write_text(text);(R/'TECHNICAL_REPORT.md').write_text(text+'\n详细原始数据、实际算法合同和全部限制以上述链接为准。\n')
 fail=['# FAILURE_LEDGER','','所有失败保留，不以新的阈值回写历史。','']
 for q in failure:fail.append('- '+q['case']+' / '+q['arm']+'：'+json.dumps(clean(q),ensure_ascii=False)+'；证据 `arms/'+q['arm']+'/metrics/'+q['case']+'_CANDIDATES.json`。')
 (R/'FAILURE_LEDGER.md').write_text('\n'.join(fail)+'\n');(R/'RESULT_INDEX.md').write_text('# RESULT_INDEX\n\n全部绝对路径和完整恢复状态见 [metrics/RESULT_INDEX.json](metrics/RESULT_INDEX.json)。全部路线保留原始毫米Mesh、FINAL.pt优化器/RNG及最终参数，不上传大检查点。\n');print('REPORTS_WRITTEN',len(gt),len(bmetrics),flush=True)
if __name__=='__main__':main()
