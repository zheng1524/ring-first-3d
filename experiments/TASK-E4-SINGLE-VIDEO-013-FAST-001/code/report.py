"""Concise complete-group paired results; no model or checkpoint selection."""
from common import *
from collections import Counter
import shutil
TAGS=['S0','S8','S16','S32']
def fmt(x):
 if x is None:return 'NOT_EVALUABLE'
 return f'{x:.5f}'if isinstance(x,(float,np.floating))else str(x)
def md(rows,cols):return '| '+' | '.join(cols)+' |\n| '+' | '.join('---'for _ in cols)+' |\n'+'\n'.join('| '+' | '.join(fmt(r.get(k))for k in cols)+' |'for r in rows)
def main():
 assert(R/'provenance/EVALUATION_COMPLETE.json').exists();cases=load(R/'config/CASE_LOCK.json');names=[c['name']for c in cases];native={(q['case'],q['label']):q for q in load(R/'metrics/NATIVE_SUMMARY.json')};gt={(q['case'],q['label']):q for q in load(R/'metrics/BLENDER_METRICS.json')};geo={(q['case'],q['label']):q for q in load(R/'metrics/GEOMETRY_AUDIT.json')};bv={(q['case'],q['label']):q for q in load(R/'metrics/POST_GEOMETRY_VALIDITY.json')};cover={(q['case'],q['arm']):q for q in load(R/'metrics/VIEW_COVERAGE.json')};rows=[];fail=[];reject=[];logs=[]
 for n in names:
  for tag in TAGS:
   a,b,c=native[n,tag],gt[n,tag],geo[n,tag];root=R/'arms'/tag;run=load(root/'metrics'/(n+'_RUN.json'));hist=load(root/'metrics'/(n+'_TRAINING.json'));trials=load(root/'metrics'/(n+'_CANDIDATES.json'));reason=Counter(y for q in trials for y in q['reasons']);reject.append(dict(case=n,arm=tag,candidate_trials=len(trials),reason_counts=dict(reason)));logs+= [dict(q,arm=tag)for q in hist]
   rr=dict(case=n,type=next(x['morphology']for x in cases if x['name']==n),arm=tag,reference_video=cover[n,tag]['video'],actual_FIT_N=cover[n,tag]['actual_FIT_N'],max_direction_span_deg=cover[n,tag]['max_direction_span_deg'],HERO_source_ids=cover[n,tag]['HERO_source_ids'],HERO_training_fixed_rays=cover[n,tag]['HERO_fixed_rays'],effective_013_depth_coefficient=cover[n,tag]['effective_013_depth_coefficient'],S0_cache_reused=tag=='S0',attempts=run['attempts'],accepted=run['accepted'],run_status=run['status'],seconds=run['seconds'],last_training_loss=hist[-1]['loss']if hist else None,FIT_IoU=a['FIT_IoU'],HOLDOUT_IoU=a['HOLDOUT_IoU'],FIT_Recall=a['FIT']['Recall'],FIT_FP_per_mask=a['FIT']['FP_per_mask'],FIT_boundary_MAE_px=a['FIT']['boundary_MAE_px'],HERO_fixed_N=a['FIT_HERO_N'],HERO_hit_rate=a['FIT_HERO_hit_rate'],HERO_active_MAE_mm=a['FIT_HERO_active_MAE_mm'],HERO_fixed_cost=a['FIT_HERO_fixed_cost'],Chamfer_MAE_mm=b.get('Chamfer_MAE_mm'),Chamfer_p95_mm=b.get('Chamfer_p95_mm'),Dxy_GT_mm=b.get('Dxy_GT_mm'),Dxy_pred_mm=b.get('Dxy_pred_mm'),Dxy_AE_mm=b.get('Dxy_AE_mm'),Dxy_ARE=b.get('Dxy_relative_error'),old_sparse_nonworsening_vs_initial=c['old_sparse_nonworsening_vs_initial'],dense_Ring_penetration_mm=c['Ring_dense_penetration_mm'],dense_added_Ring_penetration_mm=c['Ring_added_dense_penetration_mm'],dense_nonworsening=c['dense_nonworsening'],Ring_FCL=c['Ring_FCL'],self_Open3D_N=c['self_Open3D_N'],self_Blender_N=bv[n,tag]['self_intersections_N'],connected_components=c['components'],watertight=c['watertight'],max_displacement_mm=c['max_displacement_from_initial_mm'],major_rejection=max(reason,key=reason.get)if reason else'NONE')
   rows.append(rr)
   if run['status']!='ACCEPTED_TARGET_REACHED':fail.append(dict(case=n,arm=tag,stage='OPTIMIZATION_STOP',reason=run['status'],accepted=run['accepted'],attempts=run['attempts'],evidence='metrics/REJECTION_COUNTS.csv'))
   if not c['dense_nonworsening']:fail.append(dict(case=n,arm=tag,stage='DENSE_RING',reason='Added penetration above original frozen1e-5mm numeric allowance; sparse acceptance not physical proof',amount_mm=c['Ring_added_dense_penetration_mm'],evidence='GEOMETRY_AUDIT.csv'))
   if bool(c['self_Open3D_N'])or bool(bv[n,tag]['self_intersections_N']):fail.append(dict(case=n,arm=tag,stage='SELF_INTERSECTION',reason='Open3D / Blender independent geometry check, all predictions retained',evidence='metrics/POST_GEOMETRY_VALIDITY.json'))
   if b.get('Chamfer_MAE_mm')is None:fail.append(dict(case=n,arm=tag,stage='GT_EVALUATION',reason=b.get('not_evaluable_reason','NO_VALID_GT'),evidence='BLENDER_METRICS.csv'))
 by={(q['case'],q['arm']):q for q in rows};summary=[];paired=[]
 for tag in TAGS:
  rr=[by[n,tag]for n in names];ee=np.array([q['Dxy_AE_mm']for q in rr if q['Dxy_AE_mm']is not None]);re=np.array([q['Dxy_ARE']for q in rr if q['Dxy_ARE']is not None]);cc=np.array([q['Chamfer_MAE_mm']for q in rr if q['Chamfer_MAE_mm']is not None]);s=dict(arm=tag,target_physical_N=11,numeric_models=11,S0_exact_controls_reused=11 if tag=='S0'else 0,new_optimizations=0 if tag=='S0'else 11,mean_FIT_IoU=float(np.mean([q['FIT_IoU']for q in rr])),mean_HOLDOUT_IoU=float(np.mean([q['HOLDOUT_IoU']for q in rr if q['HOLDOUT_IoU']is not None])),GT_evaluable_N=len(cc),Chamfer_group_mean_mm=float(cc.mean())if len(cc)else None,Dxy_evaluable_N=len(ee),Dxy_MAE_mm=float(ee.mean())if len(ee)else None,Dxy_median_ARE_percent=float(100*np.median(re))if len(re)else None,Dxy_p95_AE_mm=float(np.quantile(ee,.95))if len(ee)else None,Dxy_max_AE_mm=float(ee.max())if len(ee)else None,dense_Ring_worsening_groups=sum(bool(not q['dense_nonworsening'])for q in rr),self_check_flagged_groups=sum(bool(q['self_Open3D_N'])or bool(q['self_Blender_N'])for q in rr));summary.append(s)
  if tag!='S0':
   for n in names:
    old,new=by[n,'S0'],by[n,tag];d=new['Chamfer_MAE_mm']-old['Chamfer_MAE_mm']if new['Chamfer_MAE_mm']is not None and old['Chamfer_MAE_mm']is not None else None;paired.append(dict(case=n,arm=tag,FIT_IoU_change=new['FIT_IoU']-old['FIT_IoU'],HOLDOUT_IoU_change=new['HOLDOUT_IoU']-old['HOLDOUT_IoU']if new['HOLDOUT_IoU']is not None and old['HOLDOUT_IoU']is not None else None,Chamfer_change_mm=d,Dxy_AE_change_mm=new['Dxy_AE_mm']-old['Dxy_AE_mm']if new['Dxy_AE_mm']is not None and old['Dxy_AE_mm']is not None else None,HERO_hit_rate_change=new['HERO_hit_rate']-old['HERO_hit_rate'],depth_coefficient_ratio=new['effective_013_depth_coefficient']/old['effective_013_depth_coefficient']))
 table('CASE_ARM_METRICS.csv',rows);save('metrics/CASE_ARM_METRICS.json',rows);table('SUMMARY.csv',summary);save('metrics/SUMMARY.json',summary);table('PAIRED_VS_S0.csv',paired);save('metrics/PAIRED_VS_S0.json',paired);table('metrics/REJECTION_COUNTS.csv',reject);save('metrics/REJECTION_COUNTS.json',reject);table('metrics/TRAINING_HISTORY.csv',logs);save('metrics/FAILURES.json',fail);table('metrics/FAILURES.csv',fail)
 s32=[q for q in paired if q['arm']=='S32'];gvalid=[q for q in s32 if q['Chamfer_change_mm']is not None];improve=sum(q['Chamfer_change_mm']<0 for q in gvalid);iouup=sum(q['HOLDOUT_IoU_change']is not None and q['HOLDOUT_IoU_change']>0 for q in s32);mixed=sum(q['FIT_IoU_change']>0 and q['Chamfer_change_mm']is not None and q['Chamfer_change_mm']>0 for q in s32)
 audit='''| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 11个独立物理组；44个条件模型不算44例 |
| 本算法独立成功 | S8/S16/S32各11/11由本轮013方法独立执行；S0为11个身份/方法一致的历史对照缓存，单列不冒充新训练 |
| 本算法失败 | 优化停滞、Ring、自交和GT不可评价逐病例/逐臂列出；数值输出不代表几何正确，缺失指标NaN |
| 历史测量值回退 | 0；不读取旧照片直径、历史测量S0/V2或其他路线补填失败。显式S0为用户指定的同方法控制 |
| 失败组及具体原因 | [FAILURE_LEDGER](FAILURE_LEDGER.md)、[逐臂失败表](metrics/FAILURES.csv)、[原始日志索引](RESULT_INDEX.md) |
| 最终统计样本 | 每臂目标11；GT/Dxy实际可评价N见SUMMARY，共同成功组配对见PAIRED_VS_S0，病例不剔除 |
| 是否使用 GT 选择算法 | 否；013方法固定，不选最佳视角数/checkpoint；全44预测与Ring尺度冻结后读取GT |
'''
 wide=[dict(case=n,**{t+'_IoU':by[n,t]['HOLDOUT_IoU']for t in TAGS},**{t+'_CDmm':by[n,t]['Chamfer_MAE_mm']for t in TAGS})for n in names]
 report=f'''# 单视频增加视角是否有效：快速013方法消融

11组完成S0/S8/S16/S32。S0复用经身份与参数核验的013原视角完整训练缓存，33个新增条件实际执行相同013预算。本轮未使用第二视频，未生成新Mask/相机/HERO，未追加可选D2。

S32相对S0：留出IoU提高{iouup}/11；Chamfer下降{improve}/{len(gvalid)}个可评价病例；FIT IoU提高但Chamfer恶化{mixed}/11。结论必须结合下表与实际Mesh；这不是最终收敛或绝对测量精度认证。不能用单张图片或平均IoU代替三维评价。

{audit}

## 主要结果

{md(summary,['arm','target_physical_N','new_optimizations','S0_exact_controls_reused','mean_FIT_IoU','mean_HOLDOUT_IoU','GT_evaluable_N','Chamfer_group_mean_mm','Dxy_median_ARE_percent','Dxy_MAE_mm','Dxy_p95_AE_mm','Dxy_max_AE_mm','dense_Ring_worsening_groups'])}

{md(wide,['case']+[t+'_IoU'for t in TAGS]+[t+'_CDmm'for t in TAGS])}

## 方法和可解释范围

013 A3/O3N/1D、lr.02、8级回缩和旧几何保护原样保留。800候选/300接受/连续拒绝80停止，最后接受状态；接受次数不等于实际有效毫米位移。先跑全组S8，再S16，再S32，不根据结果换病例。原9例精确011 FINAL；G10/G11继承013已有配方等效初始化。新视角按相机方向嵌套最远采样，S8/16/32指包含原参考的目标总数。原始参考均保留，实际数量和跨度见VIEW_COVERAGE.csv。

计算适配仅逐视角反向累加，并复用同一视角同一几何的重复光栅结果。与原013目标的零更新比较、显存和源diff已保留，未改变任何损失系数、优化器候选/接受规则或采样分辨率；详见CODE_REUSE_AUDIT与provenance。额外恢复/日志代码不改优化方法。

保留013真实归一化：深度项按总FIT视角数除，而非HERO来源数。HERO来源和原生像素/点对固定，但加入无深度Mask会降低深度相对总权重，实际系数逐臂列在CASE_ARM_METRICS。故本轮结论是原013配置下的单视频增视角效果，不是完全分离了深度权重的纯视角因果实验，未偷偷引入014归一化。未新增跨视角深度配准或梯度。

## 失败主要在哪里

1. 观察覆盖：更多帧不等于更多方向；对照每组跨度曲线和输入Ring投影，所有异常帧保留、不靠旧Gate拒绝病例。
2. 监督取舍：结合FP/FN、固定HERO命中率/误差/未命中代价；2D变好而3D变差必须记录，深度稀释也是解释限制。
3. 可行更新：实际拒绝原因及毫米位移见CASE_ARM_METRICS和REJECTION_COUNTS，不把低接受率直接归因于形状表达能力。
4. Ring真实性：旧稀疏检查只为复现013，最终另用014的64阶三角面CAD签名查询、FCL、Open3D和Blender检查，不回写学习过程、不删面制造PASS；已有碰撞与新增碰撞分开。

## GT和评价

**After Ring-based Metric Recovery and Best 6-DoF Rigid Alignment**。Ring唯一公制尺度锁定、实际恢复系数接近1且不重复缩放。复用013/014相同96正旋转初值、top8双向最近曲面刚性优化；单个模型同一个T用于Chamfer和Dxy，无尺度、镜像或非刚性。全部新旧条件统一重算本轮同视频相机评价池和同一GT程序，GT只在全44预测冻结后读取，不用于训练、停止或选方法。这是姿态排除后的形状评价，不是端到端相机或测量精度。

HOLDOUT只指本轮Mesh更新未用，上游相机/分割/初始化可能见过这些图像。主IoU继承忽略观测Ring的定义，另报全像素IoU和Ring前方冲突；原生固定分母、深度命中率和未命中代价均保留。作者基底不可靠的量保持NOT_EVALUABLE，Dxy仅作为独立三维评估，不改DXY主线。

完整失败、输入质量和逐病例原始量见CSV及图片。完成后停止，等待人工审核，不推广、不追加新损失。
''';(R/'TECHNICAL_REPORT.md').write_text(report)
 public=[dict(q,evidence=f"[{q.get('evidence','')} ]({q.get('evidence','')})")for q in fail];(R/'FAILURE_LEDGER.md').write_text('# 完整失败与停止记录\n\n'+audit+'\n\n'+md(public,['case','arm','stage','reason','evidence']))
 # Raw model geometry, no smoothing, all arms peers rather than a chosen winner.
 for n in names:
  folder=R/'meshes'/n;folder.mkdir(exist_ok=True)
  for t in TAGS:
   src=R/'arms'/t/'local_results'/n/'FINAL.npz';dst=folder/(t+'_mm.npz');shutil.copyfile(src,dst);a=np.load(src);trimesh.Trimesh(a['V'],a['F_solid'],process=False).export(folder/(t+'_mm.ply'))
 index=[asset(p)for p in sorted((R/'arms').glob('*/local_results/*/*'))if p.is_file()and p.suffix in ['.pt','.npz','.ply']];save('provenance/LOCAL_ARTIFACT_INDEX.json',dict(files=index,full_checkpoints_logs_and_original_models_local=True,S0_cached_symlinks_readonly=True))
 (R/'RESULT_INDEX.md').write_text('# 结果索引\n\n'+ '\n'.join('- ['+name+'](figures/'+name+')'for name in ['Fig1_All_Groups_Native_Contours.png','Fig2_All_Groups_Actual_Meshes.png','Fig3_View_Count_2D_3D.png','Fig4_Blender_Best_Rigid_Comparison.png'])+'\n\n[逐臂指标](CASE_ARM_METRICS.csv) / [共同组配对](PAIRED_VS_S0.csv) / [逐视角原生指标](PER_VIEW_METRICS.csv) / [Ring几何](GEOMETRY_AUDIT.csv) / [Blender指标](BLENDER_METRICS.csv)。\n\n'+ '\n'.join('- '+n+': [轮廓对比](figures/details/'+n+'_FIT_HOLDOUT_Contours.png) / [世界毫米六视图](figures/details/'+n+'_World_Six_Views.png)'for n in names)+'\n\n原始模型meshes/Gxx/S*_mm.npz及PLY，均为mm。arms/<arm>/local_results/Gxx/保存初始化、接受/候选检查点、最终模型、机制梯度与拒绝示例；arms/<arm>/metrics及runtime保存完整日志。绝对路径、SHA和字节数见provenance/LOCAL_ARTIFACT_INDEX.json。大checkpoint/输入视频/HERO保留本地，不能将只加载V或参数称完整续训。\n')
 (R/'REPRODUCE.md').write_text('''# 复现

环境复用 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python，Blender /home/liu/blender/blender-5.0.1-linux-x64/blender。需要恢复013/014冻结资产到相同绝对路径并核验SHA；不是仅clone代码即可拥有视频/HERO数据。

1. 新隔离副本中准备code/config，prepare.py选择视角并建立只读链接；不覆盖本次冻结目录。INPUTS_FROZEN及TRAINING_PROTOCOL_FREEZE记录时间和SHA。
2. E4_RUN_DIR=<newroot>/arms/S0 python -B code/preflight.py；E4_RUN_DIR=<newroot>/arms/S32 python -B code/preflight.py --memory-only。均无optimizer.step，原比较失败不改容差。
3. python -B code/driver.py 串行S8/S16/S32；S0仅用核验过的同方法完整缓存，不是失败回退。预算800候选/300接受/80停滞。中断后driver从完整.pt的参数/Adam/RNG/迭代及日志恢复；CUDA不宣称位级重现。
4. python -B code/evaluate_run.py 等待全部预测和Ring尺度冻结，再完成原生/密集几何/Blender评价。GT在显式门禁后读取，相机不动，所有模型一个尺度和一个最佳SE3。
5. python -B code/report.py 生成表格；python -B code/figures.py 生成真实Mesh/Mask和六方向图。

原013稀疏guard不可当真实无穿透认证；dense_audit014仅评价导入，不能在此复现实验中切换为新的优化拒绝规则。可选D2未运行，不能把它混作主消融。全部结果冻结后禁止直接继续优化，需要新授权和隔离运行。
''')
 print('REPORT_COMPLETE',len(rows),'S32CDbetter',improve,'holdoutbetter',iouup,flush=True)
if __name__=='__main__':main()
