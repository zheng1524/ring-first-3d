from context import *
import preflight

def main():
 freeze('AUDIT',T/'evidence');launch=read(FULL/'LAUNCH.json');identity=read(FULL/'RUN_IDENTITY.json');config=Path(launch['command'][-1]);assert sha(config)==identity['config_sha256'];cfg=read(config);assert cfg['task']=='TASK-V6-R1-MAINLINE-AND-FULL-RUN-B-001';assert cfg['reuse_old_results']is False;assert sha(cfg['manifest'])==identity['manifest_sha256'];manifest=read(cfg['manifest']);eligible={};states={}
 for v in manifest['videos']:
  p=FULL/'states'/(v['case']+'.json');s=read(p)if p.exists()else {};states[v['case']]=s
  if s.get('status')=='DONE'and s.get('native_success',0)>0 and s.get('renderable',0)>0:
   assert s['group']==v['group'];eligible.setdefault(v['group'],[]).append(s)
 eligible={g:sorted(v,key=lambda x:x['case'])[:2]for g,v in eligible.items()if len(v)>=2};rows=[dict(group=g,A=eligible[g][0],B=eligible[g][1])for g in CFG['group_names']]
 save(T/'config/SELECTION.json',dict(before_registration=True,groups=rows,eligible_groups=sorted(eligible),rule='6 named groups frozen in protocol before matching; not selected by registration scores',progress_reference_only=read(FULL/'PROGRESS.json'),actual_full_config=str(config),actual_config_sha256=sha(config),manifest_sha256=sha(cfg['manifest']),actual_execution=identity['execution_commit'],requested_old_root_progress=read(WORK/'runs/v6_full_run_001/PROGRESS.json')))
 for row in rows:
  g=row['group']
  for side in ['A','B']:
   R=Path(row[side]['run_path']);assert FULL in R.parents
   cc=read(R/'CAMERA_COMPLETE.json');pl=read(R/'PLAN_FROZEN.json');he=read(R/'HERO_COMPLETE.json');assert cc['execution_commit']==pl['execution_commit']==he['execution_commit']==identity['execution_commit'];assert cc['task']==cfg['task'];assert he['completed']>0 and not he['failed']
   for rec in [cc,he]:
    for p,h in rec['outputs'].items():assert sha(p)==h,('UPSTREAM_RECEIPT_DRIFT',p)
  preflight.freeze_group(g)
  p=T/'config'/g/'ASSETS.json';a=read(p)
  for v in a['videos']:
   R=Path(v['run']);front=read(R/'FRONTEND_KERNELS.json');tr=next(r for k,r in front['functions'].items()if k.endswith('track005.main'));assert sha(tr['module_file'])==tr['disk_sha256'];assert sha(V6/'track005.py')==tr['disk_sha256'];v['R1_tracking_receipt']=tr;v['R1_component']=read(R/'COMPONENT.json');v['execution_commit']=identity['execution_commit']
   for name in ['FRONTEND_KERNELS.json','COMPONENT.json','inputs/REFERENCE_RECEIPT.json']:
    file=R/name;a['files'].append(dict(path=str(file),sha256=sha(file),bytes=file.stat().st_size))
   native=[s for s in a['sources']if s['side']==v['side']];plan=read(R/'PLAN_FROZEN.json');assert len(native)==plan['budget']==len(plan['legal']);assert {s['tag']for s in native}=={s['tag']for s in plan['legal']};v['plan_all_targets']=len(plan['all_targets']);v['legal_HERO_targets']=plan['budget'];v['not_legal_targets']=[s['tag']for s in plan['all_targets']if s['tag']not in {q['tag']for q in native}]
   for s in native:
    arr=np.load(Path(s['run'])/'raw'/(s['tag']+'.npz'));assert arr['depth_mm'].shape[-2:]==(352,640);assert s['mesh_sha256']==read(R/'HERO_COMPLETE.json')['outputs'][str(R/'meshes'/(s['tag']+'_Polyp.ply'))]
  a['R1_contract_verified']=True;save(p,a)
 print('R1 AUDIT COMPLETE',len(rows),sum(len(read(T/'config'/r['group']/'ASSETS.json')['sources'])for r in rows),flush=True)
if __name__=='__main__':main()
