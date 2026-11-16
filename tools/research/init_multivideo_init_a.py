"""Freeze exact historical source, 013 Mesh lineage, views and existing HERO assets."""
from _bootstrap import ROOT
from policy import make_task
from pathlib import Path
import json,subprocess,datetime,shutil,yaml
import numpy as np
from ring_first_3d.contracts.identities import sha256
from ring_first_3d.policy.inita_contracts import TASK_ID,LEGACY,BASELINE,INIT_STAGES,MODULE_FILES

def main():
 td=ROOT/'experiments'/TASK_ID
 if(td/'TASK.yaml').exists():raise FileExistsError('Never overwrite frozen protocol')
 inp=td/'inputs';inp.mkdir(parents=True);code=td/'legacy015';code.mkdir()
 prefix='experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/code/'
 names=subprocess.check_output(['git','ls-tree','-r','--name-only',LEGACY,prefix],text=True).splitlines();locked=[]
 for name in names:
  if not name.endswith('.py'):continue
  raw=subprocess.check_output(['git','show',LEGACY+':'+name]);p=code/Path(name).name;p.write_bytes(raw);locked.append(dict(path=str(p),sha256=sha256(p),git_path=name,commit=LEGACY))
 def rec(p):p=Path(p).resolve();return dict(path=str(p),sha256=sha256(p))
 (inp/'CODE_LOCK.json').write_text(json.dumps(dict(commit=LEGACY,files=locked),indent=2)+'\n')
 hist=Path('/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-MULTIVIEW-INIT-STALK-015');p14=hist.parent/'TASK-E4-PYTORCH3D-014';cases=json.loads((hist/'config/CASE_LOCK.json').read_text());selection=json.loads((hist/'config/VIEW_SELECTION.json').read_text());rows=[];assets=[]
 prior=Path('/home/liu/ring_first_3d_multisurface_stress/experiments/TASK-E4-MULTISURFACE-STRESS-AND-REAL-PILOT-001/inputs/REAL_SOURCES.json');real=json.loads(prior.read_text());realby={g['group']:g for g in real['groups']};heldSHA={v['assets']['source_RGB']['sha256']for g in real['groups']for v in g['views']if v['role']=='HOLDOUT'}
 for c in cases:
  g=c['name'];src=hist/'inputs'/g;initial=src/'INITIAL.npz';start=hist/'initializations'/g/'Init-A.npz';a=np.load(initial);b=np.load(start);assert all(np.array_equal(a[k],b[k])for k in ['V','F','F_solid','inferred_base_faces']);assert 'FREE_VERTEX_013/inputs/'in str(initial.resolve());master=json.loads((p14/'inputs'/g/'CASE.json').read_text());old=json.loads((src/'CASE.json').read_text());oldby={r['id']:r for r in old['views']};chosen=[];held=[]
  for cid in selection[g]['FIT']:
   v=oldby[cid]
   if v['video']!='004':continue
   path=src/(cid+'.npz');chosen.append(dict(meta=v,cache=rec(path),sides=rec(src/(cid+'_SIDES.npz')),selection='EXACT_015_004_FIT'))
  for cid in selection[g]['HOLDOUT']:
   v=oldby[cid];held.append(dict(meta=v,cache=rec(src/(cid+'.npz')),sides=rec(src/(cid+'_SIDES.npz'))))
  pool=[v for v in master['views']if v['video']=='005'and v['role']=='FIT'and not v.get('is_photo',False)and(p14/'inputs'/g/(v['id']+'_SIDES.npz')).is_file()and v.get('RGB_sha')not in heldSHA];taken=[];center=a['V'].mean(0)
  if pool:
   dirs=np.array([np.asarray(v['T'])[:3,3]-center for v in pool]);dirs/=np.linalg.norm(dirs,axis=1)[:,None];taken=[0]
   while len(taken)<min(8,len(pool)):
    score=[-1 if i in taken else min(np.arccos(np.clip(dirs[i]@dirs[j],-1,1))for j in taken)for i in range(len(pool))];taken.append(int(np.argmax(score)))
   for i in taken:
    v=pool[i];chosen.append(dict(meta=v,cache=rec(p14/'inputs'/g/(v['id']+'.npz')),sides=rec(p14/'inputs'/g/(v['id']+'_SIDES.npz')),selection='005_ANGULAR_FARTHEST_POINT_NO_GT'))
  for v in master['views']:
   if v['video']=='005'and v['role']!='FIT'and(p14/'inputs'/g/(v['id']+'_SIDES.npz')).is_file()and v['id']not in {r['meta']['id']for r in held}:held.append(dict(meta=v,cache=rec(p14/'inputs'/g/(v['id']+'.npz')),sides=rec(p14/'inputs'/g/(v['id']+'_SIDES.npz'))))
  assert {v['meta']['id']for v in chosen}.isdisjoint(v['meta']['id']for v in held)
  static={k:rec(src/k)for k in ['INITIAL.npz','RING.npz','NORMALIZATION.json','BASE_SELECTION.json','CHART.json']};depth={v['meta']['id']:rec(hist/'depth_observations'/(v['meta']['id']+'.npz'))for v in chosen if(hist/'depth_observations'/(v['meta']['id']+'.npz')).is_file()};a0=rec(hist/'arms/Init-A/local_results'/g/'FINAL.npz');gt=rec(hist/'evaluation_only'/g/'ORIGINAL_BLENDER_GT_MM.npz');legacyhero=[dict(id=v['id'],video=v['video'],raw=[rec(p)for p in v['HERO_sources']if Path(p).is_file()])for v in master['views']if v['role']=='FIT'and v.get('HERO_sources')]
  row=dict(case=g,morphology=c['morphology'],ring=c['ring'],initial=rec(start),resolved013_initial=rec(initial),static=static,A0=a0,GT=gt,FIT=chosen,HOLDOUT=held,depth=depth,meta=master,legacy_HERO_inventory=legacyhero,legacy_aligned_directory=str(hist/'local_results/aligned'/g),status='READY'if any(v['meta']['video']=='004'for v in chosen)and any(v['meta']['video']=='005'for v in chosen)else'NOT_EVALUABLE_MISSING_004_OR_005')
  rows.append(row);assets.extend(list(static.values())+[rec(start),a0,gt]);assets.extend(depth.values());assets.extend(r for v in chosen+held for r in [v['cache'],v['sides']]);assets.extend(r for v in legacyhero for r in v['raw'])
 # Extend the already audited modern adapter uniformly to G06 if its sources exist.
 oldrepo=Path('/home/liu/polyp_research/ring-first-3d/experiments');maxroot=oldrepo/'TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001';repair=oldrepo/'TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001';inf=json.loads((maxroot/'metrics/HERO_INFERENCE_RESULTS.json').read_text())
 for c in cases:
  g=c['name']
  if g not in realby:
   vs=[]
   for vid in ['004','005']:
    opts=[r for r in inf if r.get('group')==g and r.get('success')and('_v'+vid+'_'in r['id']or'video'+vid+'_'in r['id'])]
    for i,r in enumerate(opts[:3]):
     dp=repair/'provenance/dxy_records'/('MAX__'+r['id']+'.json')
     if not dp.is_file():continue
     d=json.loads(dp.read_text());aa={k:rec(r[k])for k in ['native','pack','points','mesh']};aa.update(raw_mesh=rec(Path(r['native']).parent/'RAW_NATIVE_MESH.npz'),dxy=rec(dp));aa.update({k:rec(d[k]['path'])for k in ['cache','source_RGB','source_Mask']});vs.append(dict(id=r['id'],group=g,video=vid,role='FIT'if i<2 else'HOLDOUT',K=r['K'],C=r['C'],unit=r['unit'],depth_definition=r['depth_definition'],source_ids=r['source_ids'],target_RGB_SHA=r['target_SHA'],assets=aa))
   realby[g]=dict(group=g,views=vs,status='SOURCE_BOUND_MODERN_MESH'if len([v for v in vs if v['role']=='FIT'])>=2 else'NOT_EVALUABLE_NO_TWO_SOURCE_BOUND_FULL_MESHES',assets=dict(ring=next(r for r in rows if r['case']==g)['static']['RING.npz']))
  for v in realby[g]['views']:assets.extend(v['assets'].values())
  assets.extend(realby[g]['assets'].values())
 # Hashes bind identity only; GT geometry is not used in selection or preparation.
 dedup={r['path']:r for r in assets};source=dict(cases=rows,real_groups=[realby[c['name']]for c in cases],frozen_assets=list(dedup.values()),Ip_source_review=dict(wrong_half_ellipsoid='G02',missing_long_stalk='G03',source='Actual 013 V/F with original 015 RGB/Mask, no GT selection'),inherited_depth=json.loads((hist/'config/PROTOCOL.json').read_text())['depth'],GT_source_metadata=json.loads((hist/'evaluation_only/GT_SOURCE_LOCK.json').read_text()))
 (inp/'SOURCES.json').write_text(json.dumps(source,indent=2)+'\n');shutil.copyfile('/tmp/INIT_A_ALL_IP_SOURCE_REVIEW.png',inp/'INIT_A_ALL_IP_SOURCE_REVIEW.png');make_task(TASK_ID,td/'TASK.yaml');t=yaml.safe_load((td/'TASK.yaml').read_text());t['schema']=7;t['modules']+=list(MODULE_FILES);t['goal']='Exact 013→015 Init-A: 004-only versus shared 004+005 Mesh, independent scale1 GT shape evaluation and real full HERO localization';t['authorization']['reference']='Explicit user TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001';t['authorization']['stages']=list(INIT_STAGES);t['acceptance']['required_stages']=list(INIT_STAGES);t['split']['GT']=['independent_shape_evaluator_only'];t['split']['access']='inita_train_hero_evaluation_isolation';t['budget']=dict(max_seconds=14400,stage_timeout_seconds=7200,max_attempts_per_stage=2,max_output_bytes=2000000000)
 t['inita']=dict(legacy_commit=LEGACY,parent_commit=BASELINE,initialization='EXACT_013_INPUT_MESH_V_F_SOLID_CAP',arms=['A0','A1','A2'],cases=[c['name']for c in cases],smoke_cases=['G01','G03','G05'],training_budget=dict(max_proposals=80,max_accepted=40,consecutive_rejection_stop=30),GT_alignment_scope='EVALUATION_COPIES_ONLY_SCALE1',HERO_uses_GT_aligned_Body=False,train_uses_GT=False,camera_parameters='004_FIXED; optionally_one_shared_005_SE3; no_per_frame',shared_trigger=dict(delta_FIT_IoU=.10,absolute_005_FIT_IoU=.5),shared_005_bounds_deg_mm=[90.,3.],shared_005_starts_deg=[0.,90.,-90.,180.],shared_005_nfev=40,mesh_projection_adapter='Apparent-contour ellipse of actual frozen Mesh; ray hits actual faces, never ellipsoid replacement',occupancy_Sobol_power=17,occupancy_seed=20261108,shape_samples_per_direction=8192,HERO_frame_prior_deg_mm=[.3,.1],HERO_Body_tolerance_mm=.5,assets=dict(sources=rec(inp/'SOURCES.json'),code_lock=rec(inp/'CODE_LOCK.json'),Ip_source_review=rec(inp/'INIT_A_ALL_IP_SOURCE_REVIEW.png')))
 (td/'TASK.yaml').write_text(yaml.safe_dump(t,sort_keys=False,allow_unicode=True));(td/'TASK_FREEZE.json').write_text(json.dumps(dict(task_sha256=sha256(td/'TASK.yaml'),source_sha256=sha256(inp/'SOURCES.json'),UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),no_GT_selection=True),indent=2)+'\n');print(td/'TASK.yaml');print([(r['case'],r['status'],len(r['FIT']),len(r['HOLDOUT']))for r in rows]);print('HERO',[(g['group'],sum(v['role']=='FIT'for v in g['views']))for g in source['real_groups']])
if __name__=='__main__':main()
