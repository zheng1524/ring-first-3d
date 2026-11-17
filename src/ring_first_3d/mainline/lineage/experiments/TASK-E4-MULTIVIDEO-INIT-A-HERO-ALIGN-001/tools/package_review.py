"""Read-only publication from accepted Runner snapshots and frozen world Meshes."""
from pathlib import Path
import json,csv,shutil,hashlib,subprocess
import numpy as np
from scipy.spatial.transform import Rotation
from ring_first_3d.policy.contracts import load_task,verify_task
from ring_first_3d.policy.artifacts import read_state,check_artifacts
from ring_first_3d.synthetic.io import fetch
root=Path.cwd();td=root/'experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001';run=td/'runs/INIT_A_002';task=load_task(td/'TASK.yaml');state=read_state(run);assert state['accepted'];assert verify_task(task)['freeze_sha256']==state['freeze_sha256'];check_artifacts(run,state)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['TECHNICAL_REPORT.md','RESULT_CARD.md','metrics.json','failures.json','evidence.png']:
 assert not(td/n).exists();shutil.copyfile(run/n,td/n)
shutil.copytree(run/'visualization',td/'visualization');vis=td/'visualization';evidence=td/'evidence';evidence.mkdir()
for n in ['FREEZE.json','RUN_MANIFEST.json']:shutil.copyfile(run/n,evidence/('ORIGINAL_'+n))
shutil.copyfile('/tmp/inita-historical-905-data-verification.json',evidence/'HISTORICAL_905_DATA_VERIFICATION.json')
for folder in sorted((run/'attempts').iterdir()):
 dest=evidence/'attempts'/folder.name;dest.mkdir(parents=True)
 for p in folder.iterdir():
  if p.is_file()and p.suffix in {'.json','.txt','.csv','.md'}:shutil.copyfile(p,dest/p.name)
old=td/'runs/INIT_A_001'
for p in sorted((old/'attempts').glob('*-inita_regression-*/*')):
 if p.is_file()and p.suffix in {'.txt','.json'}:
  dest=evidence/'PRE_SCIENCE_GATE_FAILURE_001'/p.name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(p,dest)
source=json.loads(Path(task['inita']['assets']['sources']['path']).read_text());body=json.loads((vis/'BODY_SHAPE_METRICS.json').read_text());hero=json.loads((vis/'HERO_METRICS.json').read_text());pred=json.loads(fetch(run,'G1_all_train','BODY_PREDICTIONS_FROZEN.json').read_text());hp=json.loads(fetch(run,'G2_all_hero','ALL_HERO_PREDICTIONS_FROZEN.json').read_text());pb={(p['case'],p['arm']):p for p in pred['records']};B={(p['case'],p['arm']):p for p in body['rows']}
# Small exact model copies preserve observed faces, inferred closing faces and full precision.
for r in body['rows']:
 if r['status']!='NUMERIC':continue
 g,a=r['case'],r['arm'];folder=td/'review_meshes'/g;folder.mkdir(parents=True,exist_ok=True)
 for label,stage,name in [('WORLD','G1_all_train',pb[g,a]['world_mesh_relative']),('ALIGNED','G3_all_evaluate',r['aligned_mesh_relative'])]:
  raw=dict(np.load(fetch(run,stage,name)));copy={k:raw[k]for k in ['V','F','F_solid','inferred_base_faces','boundary_vertex','T']if k in raw};np.savez_compressed(folder/(a+'_'+label+'.npz'),**copy)
  assert np.array_equal(copy['V'],raw['V'])and np.array_equal(copy['F'],raw['F'])

# Include actual source, per-view corrections and all geometry, never a GT-aligned HERO input.
(vis/'HERO_PREDICTIONS_AND_TRANSFORMS.json').write_text(json.dumps(hp,indent=2)+'\n')
from ring_first_3d.inita.evaluate import geometry,legacy_namespace
geometry_ns=legacy_namespace(task)
projection=[];diagnostics=[];viewcoverage=[];hflat=[];transforms=[]
for row in source['cases']:
 g=row['case'];initial_model=dict(np.load(row['initial']['path']));initial=initial_model['V'];initial_geo=geometry(initial_model,initial_model,dict(np.load(row['static']['RING.npz']['path'])),geometry_ns);center=initial.mean(0);directions={v:[]for v in ['004','005']};fit_hash={}
 for v in row['FIT']:
  a=np.load(v['cache']['path']);D=a['T'][:3,3]-center;D/=np.linalg.norm(D);directions[v['meta']['video']].append(D);fit_hash[hashlib.sha256(a['RGB'].tobytes()).hexdigest()]=v['meta']['id']
 result=dict(case=g,FIT_counts={v:len(directions[v])for v in directions},world_pose_deployment_certified=False)
 for v,ds in directions.items():
  if ds:result[v+'_direction_max_span_deg']=float(np.rad2deg(np.arccos(np.clip(np.asarray(ds)@np.asarray(ds).T,-1,1))).max())
 if directions['004']and directions['005']:
  distance=np.rad2deg(np.arccos(np.clip(np.asarray(directions['005'])@np.asarray(directions['004']).T,-1,1))).min(1);result['005_nearest004_angle_deg']=dict(mean=float(distance.mean()),median=float(np.median(distance)),maximum=float(distance.max()))
 group=next(gr for gr in source['real_groups']if gr['group']==g);result['HERO_HOLDOUT_in_Body_FIT']=[]
 for v in group['views']:
  if v['role']=='HOLDOUT':
   d=json.loads(Path(v['assets']['dxy']['path']).read_text());match=fit_hash.get(d['RGB_content_SHA'])
   if match:result['HERO_HOLDOUT_in_Body_FIT'].append(dict(id=v['id'],FIT_match=match))
 viewcoverage.append(result)
 for arm in ['A0','A1','A2','A2S']:
  r=B.get((g,arm))
  if r is None:continue
  projection.extend(dict(case=g,arm=arm,**p)for p in r.get('projection',[]))
  p=pb[g,arm]
  if arm=='A0'or p['status']!='NUMERIC':continue
  folder=fetch(run,'G1_all_train',p['world_mesh_relative']).parent/arm;trainfile=folder/'metrics'/(g+'_TRAINING.json');candfile=folder/'metrics'/(g+'_CANDIDATES.json');history=json.loads(trainfile.read_text());candidates=json.loads(candfile.read_text());reasons={}
  for c in candidates:
   for code in c['reasons']:reasons[code]=reasons.get(code,0)+1
  support=folder/'local_results'/(g+'_P0_SUPPORT.npz');unknown=np.load(support)['unknown']if support.is_file()else None
  diag=dict(case=g,arm=arm,training=p.get('training'),iterations_recorded=len(history),accepted=sum(h['accepted']for h in history),last_gradient_norm=history[-1]['gradient_norm']if history else None,first_objective=history[0]['objective']if history else None,last_objective=history[-1]['objective']if history else None,candidate_rejection_counts=reasons,initial_supported_vertices=int((~unknown).sum())if unknown is not None else None,initial_unknown_vertices=int(unknown.sum())if unknown is not None else None,vertex_count=len(initial),raw_parameter_N=len(initial)*3,full_world_geometry=r.get('world_geometry'),causal_claim='Single fixed optimizer/guard run cannot isolate topology, prior, observability and finite-budget contributions. Numerical updates are not proof of head/stalk recovery.')
  chart=json.loads(Path(row['static']['CHART.json']['path']).read_text());diag['step_trust_mm']=chart['tau_mm'];diag['global_displacement_trust_mm']=chart['D_mm'];diag['accepted_path_upper_bound_mm']=diag['accepted']*chart['tau_mm']
  diag['initial_geometry_dense64']=initial_geo;diag['linear_geometry_DOF_before_nonlinear_guards']=len(initial)*3-(int(initial_model['boundary_vertex'].sum())+3*len(np.setdiff1d(np.arange(len(initial)),np.unique(initial_model['F']))))if initial_model['inferred_base_faces'].any()else len(initial)*3
  diagnostics.append(diag);dest=evidence/'training'/g/arm;dest.mkdir(parents=True)
  for f in [trainfile,candfile,folder/'metrics'/(g+'_RUN.json'),folder/'TRAIN_STDOUT.txt']:
   if f.is_file():shutil.copyfile(f,dest/f.name)
for g in hero['groups']:
 if g['status']!='NUMERIC':
  for method in ['M0','BODY_A0','BODY_A1','BODY_A2','ICP']:hflat.append(dict(case=g['case'],method=method,status=g['status'],reason=g.get('reason'),absolute_GT_accuracy='NOT_EVALUABLE'))
  continue
 for m in g['methods']:
  if m['status']!='NUMERIC':hflat.append(dict(case=g['case'],method=m['method'],status=m['status'],reason=m.get('reason')));continue
  holds=m['HOLDOUT'];hflat.append(dict(case=g['case'],method=m['method'],status=m['status'],FIT_views=m['FIT_views'],HOLDOUT_views=m['HOLDOUT_views'],video_count=len(g['videos']),within_target_N=m['within_video']['target_N'],within_MAE_mm=m['within_video']['MAE'],within_P95_mm=m['within_video']['p95'],cross_target_N=m['cross_video']['target_N'],cross_MAE_mm=m['cross_video']['MAE'],cross_P95_mm=m['cross_video']['p95'],body_correspondence_rate=m['correspondence']['body_rate'],pair_correspondence_rate=m['correspondence']['pair_rate'],HOLDOUT_mean_IoU=float(np.mean([h['mask_IoU']for h in holds]))if holds else None,HOLDOUT_mean_recall=float(np.mean([h['mask_recall']for h in holds]))if holds else None,source_vertex_N=m['all_source_vertices'],source_face_N=m['all_source_faces'],maximum_motion_mm=max(mm['maximum_motion_mm']for mm in m['motions']),edge_change_max_mm=max(mm['edge_change_max_mm']for mm in m['motions']),absolute_GT_accuracy='NOT_EVALUABLE'))
for g in hp['groups']:
 for m in g.get('records',[]):
  if m['status']!='NUMERIC':continue
  for cid,T in m['corrections'].items():
   T=np.asarray(T);transforms.append(dict(case=g['case'],method=m['method'],id=cid,rotation_magnitude_deg=float(np.rad2deg(np.linalg.norm(Rotation.from_matrix(T[:3,:3]).as_rotvec()))),translation_magnitude_mm=float(np.linalg.norm(T[:3,3])),matrix=T.tolist(),GT_based=False))
def csvwrite(path,rows):
 if not rows:return
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with path.open('w',newline='')as f:
  w=csv.DictWriter(f,keys,lineterminator='\n');w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False)if isinstance(v,(dict,list))else v for k,v in r.items()}for r in rows)
for name,rows in [('WORLD_MASK_PROJECTION',projection),('OPTIMIZATION_DIAGNOSTICS',diagnostics),('VIEW_COMPLEMENTARITY_AND_ISOLATION',viewcoverage),('HERO_ALL11_METRICS',hflat),('HERO_CORRECTIONS',transforms)]:
 (vis/(name+'.json')).write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n');csvwrite(vis/(name+'.csv'),rows)
# Physical-case paired comparison, never pool experimental arms as independent samples.
paired=[]
for g in task['inita']['cases']:
 a=B.get((g,'A1'));b=B.get((g,'A2'))
 if not a or not b or a['status']!='NUMERIC'or b['status']!='NUMERIC':continue
 row=dict(case=g,conditional_occupancy_IoU_A1=a['conditional_occupancy_IoU'],conditional_occupancy_IoU_A2=b['conditional_occupancy_IoU'],conditional_IoU_delta=b['conditional_occupancy_IoU']-a['conditional_occupancy_IoU'],Chamfer_A1_mm=a['Chamfer_MAE_mm'],Chamfer_A2_mm=b['Chamfer_MAE_mm'],Chamfer_delta_mm=b['Chamfer_MAE_mm']-a['Chamfer_MAE_mm'],strict_IoU_both_valid=a['IoU_3D']is not None and b['IoU_3D']is not None)
 for arm,r in [('A1',a),('A2',b)]:
  for video in ['004','005']:
   for role in ['FIT','HOLDOUT']:
    vals=[p['IoU']for p in r['projection']if p['video']==video and p['role']==role];row[arm+'_'+video+'_'+role+'_IoU']=float(np.mean(vals))if vals else None
 h1=next((r for r in hflat if r['case']==g and r['method']=='BODY_A1'and r['status']=='NUMERIC'),None);h2=next((r for r in hflat if r['case']==g and r['method']=='BODY_A2'and r['status']=='NUMERIC'),None)
 if h1 and h2:
  for field in ['within_MAE_mm','cross_MAE_mm','HOLDOUT_mean_IoU','body_correspondence_rate']:
   row['HERO_'+field+'_A1']=h1.get(field);row['HERO_'+field+'_A2']=h2.get(field);row['HERO_'+field+'_delta']=h2[field]-h1[field]if h1.get(field)is not None and h2.get(field)is not None else None
 paired.append(row)
(vis/'FINAL_PAIRED_ANSWERS.json').write_text(json.dumps(paired,indent=2)+'\n');csvwrite(vis/'FINAL_PAIRED_ANSWERS.csv',paired)
summary=dict(task_id=task['task_id'],implementation_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),target_physical_cases=11,paired_body_cases=len(paired),strict_IoU_pair_cases=sum(r['strict_IoU_both_valid']for r in paired),conditional_IoU_A2_better_cases=sum(r['conditional_IoU_delta']>0 for r in paired),Chamfer_A2_better_cases=sum(r['Chamfer_delta_mm']<0 for r in paired),mean_conditional_IoU_delta=float(np.mean([r['conditional_IoU_delta']for r in paired]))if paired else None,mean_Chamfer_delta_mm=float(np.mean([r['Chamfer_delta_mm']for r in paired]))if paired else None,HERO_numeric_groups=sum(g['status']=='NUMERIC'for g in hero['groups']),HERO_two_video_groups=sum(g['status']=='NUMERIC'and len(g['videos'])==2 for g in hero['groups']),HERO_cross_A2_better_cases=sum(r.get('HERO_cross_MAE_mm_delta',0)<0 for r in paired if r.get('HERO_cross_MAE_mm_delta')is not None),HERO_cross_paired_cases=sum(r.get('HERO_cross_MAE_mm_delta')is not None for r in paired),GT_used_for_training=False,GT_aligned_HERO=False,historical_measurement_fallback=0)
summary['strict_IoU_A2_better_cases']=sum(r['strict_IoU_both_valid'] and r['conditional_IoU_delta']>0 for r in paired)
strict_pairs=[r for r in paired if r['strict_IoU_both_valid']];summary['mean_strict_IoU_delta']=float(np.mean([r['conditional_IoU_delta']for r in strict_pairs]))if strict_pairs else None
(td/'SCIENTIFIC_RESULT.json').write_text(json.dumps(summary,indent=2)+'\n')
report=td/'TECHNICAL_REPORT.md';text=report.read_text();text+='\n## 最终共同样本回答与实际优化证据\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\n[全部11组HERO方法CSV](visualization/HERO_ALL11_METRICS.csv) · [同病例A1/A2完整配对](visualization/FINAL_PAIRED_ANSWERS.csv) · [004/005 FIT/HOLDOUT逐帧投影](visualization/WORLD_MASK_PROJECTION.csv) · [实际优化/拒绝/可动顶点支持](visualization/OPTIMIZATION_DIAGNOSTICS.json) · [005互补视角与留出隔离](visualization/VIEW_COMPLEMENTARITY_AND_ISOLATION.json) · [实际共享与帧残余修正](visualization/HERO_PREDICTIONS_AND_TRANSFORMS.json)。\n\n135维之类额外结构未加入：每个初始网格仍为原N×3顶点自由度，并保留原基底约束/保护。若新增视角仍不能恢复头柄，本轮仅由实际支持区、梯度、接受/拒绝和真实三维形变诊断；没有足够对照将原因唯一归结为拓扑、先验或优化失败。\n\n原INIT_A_001在科学开始前回归门禁失败；校验顺序修复后新INIT_A_002重新执行原35项与全部130项回归，未绕过门禁。原失败与源码版本证据完整保留。GT仅作用评价副本。\n';text=text.replace('135维之类额外结构未加入：','没有新增主体结构：');report.write_text(text)
p=vis/'index.html';text=p.read_text().replace('</html>','<p><a href="FINAL_PAIRED_ANSWERS.csv">最终A1/A2共同样本回答</a> · <a href="HERO_ALL11_METRICS.csv">全部11组HERO含无效结果</a> · <a href="OPTIMIZATION_DIAGNOSTICS.json">优化失败诊断</a> · <a href="VIEW_COMPLEMENTARITY_AND_ISOLATION.json">互补方向/隔离</a></p></html>');p.write_text(text)
# Failure facts remain task-local unreviewed scientific/engineering evidence.
registry=[]
for fid,cat,symptom,path in [('FM-INIT-A-G08-001','incomplete_evaluation','G08 lacks004; A1/A2 cannot be evaluated as defined','visualization/BODY_SHAPE_METRICS.json'),('FM-INIT-A-ENTITY-001','scientific_negative','Strict solid IoU validity is not guaranteed; conditional occupancy is not a replacement for strict IoU','visualization/BODY_SHAPE_METRICS.json'),('FM-INIT-A-HERO-SOURCES-001','incomplete_evaluation','Not all physical groups have >=2 source-bound complete HERO Meshes; unavailable targets remain NaN','visualization/HERO_ALL11_METRICS.json'),('FM-INIT-A-GATE-001','code_error','Guarded regression initially checked GT metadata before rejecting corrupted source binding','ENGINEERING_FIXES.md')]:
 p=td/path;registry.append(dict(id=fid,category=cat,modules=['IA01','IA02','IA03'],symptom=symptom,cause='Source availability or observed scientific limitation; gate ordering cause confirmed separately in ENGINEERING_FIXES'if cat!='code_error'else'YAML key sorting changed asset-check order inside trusted worker guard',cause_status='observed_only'if cat!='code_error'else'confirmed',repair='Keep all targets, valid/invalid metrics and actual Mesh evidence; no GT tuning, prediction fallback or automatic permanent promotion',regression=['130 inherited and new source/initialization/scope/isolation tests'],evidence=[dict(path=str(p.relative_to(root)),sha256=sha(p))],rule_status='candidate',review=dict(status='unreviewed',reviewer=None,evidence=None)))
(td/'FAILURE_REGISTRY.json').write_text(json.dumps(dict(schema=1,failures=registry),indent=2)+'\n');manifest=dict(schema='multivideo-inita-delivery-1',task_id=task['task_id'],implementation_commit=summary['implementation_commit'],runner_freeze_sha256=state['freeze_sha256'],runner_accepted=True,scientific_acceptance='AWAITING_HUMAN_REVIEW',local_original_run=str(run),spent_seconds=state['spent_seconds'],budget=task['budget'],summary=summary);files=sorted(p for p in td.rglob('*')if p.is_file()and'runs'not in p.relative_to(td).parts and p!=td/'RUN_MANIFEST.json');manifest['artifacts']={str(p.relative_to(td)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in files};(td/'RUN_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(summary,indent=2))
