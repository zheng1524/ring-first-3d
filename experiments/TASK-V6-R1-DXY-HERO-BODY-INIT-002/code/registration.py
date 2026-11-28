"""Qualify frozen M4 relationships without matching, triangulation or solving transforms."""
import ast,hashlib,json,math,sys,csv,subprocess
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
T=Path(__file__).resolve().parents[1];ROOT=T.parents[1]
W=ROOT.parent
OLD=W/'TASK-V6-R1-BODY-INIT-001/experiments/TASK-V6-R1-DXY-HERO-BODY-INIT-001'
M4=W/'TASK-V6-R1-M4-002/experiments/TASK-V6-R1-M4-REGISTRATION-MAINLINE-002'
BASE='80d00ad3530abfd782e27a2c1981a272bf9739e7';KERNEL='efa0adfb09f23f355d3d55180f2becfb1036f35c'
POLICY=dict(min_held_tracks=8,min_target_frames_per_side=2,max_bidirectional_median_px=6.,max_child_ring_MAE_increase_px=1.,tail_warning_P95_px=30.,se3_atol=1e-7,composition_atol=1e-8)
def read(p):return json.loads(Path(p).read_text())
def clean(x):
 if isinstance(x,(np.ndarray,np.generic)):return clean(x.tolist())
 if isinstance(x,Path):return str(x)
 if isinstance(x,dict):return {k:clean(v)for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v)for v in x]
 if isinstance(x,float)and not np.isfinite(x):return None
 return x
def save(p,x):
 p=Path(p);assert T in p.resolve().parents;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def asset(p,expected=None):
 h=sha(p)
 if expected is not None:assert h==expected,('INPUT_DRIFT',str(p))
 return dict(path=str(p),sha256=h)
def verify(records):
 for r in records:asset(r['path'],r['sha256'])
def finite(v):return isinstance(v,(int,float))and math.isfinite(v)
def qualify(methods,prediction,input_valid):
 reasons=[];warnings=[];missing=[]
 if not input_valid:missing.append('INPUT_OR_TRANSFORM_UNVERIFIABLE')
 if 'CONFLICT'in str(prediction.get('quality','')).upper()or prediction.get('candidate_only',False):reasons.append('EXISTING_CONFLICT_OR_CANDIDATE_ONLY')
 try:
  m=methods['M4'];b=m['bidir'];d=b['denominators']
  if not(d.get('evidence_sufficient')is True and d.get('two_sided_DLT_tracks',0)>=8 and d.get('target_frames_A',0)>=2 and d.get('target_frames_B',0)>=2):missing.append('HELD_SUPPORT_INSUFFICIENT')
  for name in ['A_to_B','B_to_A']:
   median=b[name].get('conditional_median');p95=b[name].get('conditional_P95')
   if not finite(median):missing.append(name+'_MEDIAN_MISSING')
   elif median>6.:reasons.append(name+'_MEDIAN_EXCEEDS_6PX')
   if finite(p95)and p95>30.:warnings.append(name+'_P95_EXCEEDS_30PX')
  r=m['ring']['by_side']['B'].get('conditional_MAE');r0=methods['M0']['ring']['by_side']['B'].get('conditional_MAE')
  if not(finite(r)and finite(r0)):missing.append('CHILD_RING_MAE_MISSING')
  elif r-r0>1.:reasons.append('CHILD_RING_MAE_INCREASE_EXCEEDS_1PX')
 except (KeyError,TypeError):missing.append('REQUIRED_EVALUATION_MISSING')
 return dict(status='INCONCLUSIVE_REGISTRATION'if missing else'FAIL_REGISTRATION'if reasons else'PASS_FOR_JOINT',reasons=reasons+missing,warnings=warnings)
def valid_T(t):
 if t is None:return False
 t=np.asarray(t);return t.shape==(4,4)and np.isfinite(t).all()and np.allclose(t[3],[0,0,0,1],atol=1e-7)and np.allclose(t[:3,:3].T@t[:3,:3],np.eye(3),atol=1e-7)and abs(np.linalg.det(t[:3,:3])-1)<1e-7

def functions(path,names,ns,commit,rel,locks):
 raw=Path(path).read_bytes();frozen=subprocess.check_output(['git','show',commit+':'+rel],cwd=ROOT);assert raw==frozen,('CODE_DRIFT',path)
 tree=ast.parse(raw);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names];assert {n.name for n in nodes}==set(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns);locks.append(dict(**asset(path),commit=commit,repository_path=rel,functions=names))
def kernels():
 sys.path.insert(0,str(ROOT/'src'))
 from ring_first_3d.sim.geometry import transform
 ns=dict(np=np,Path=Path,cKDTree=cKDTree,transform=transform,CFG=dict(min_held_tracks=8),read=read,sha=sha,verify=verify);locks=[]
 rel='experiments/TASK-V6-R1-M4-REGISTRATION-MAINLINE-002/code/'
 functions(M4/'code/context.py',['verify_registration'],ns,BASE,rel+'context.py',locks)
 functions(M4/'code/connections.py',['pair_view'],ns,BASE,rel+'connections.py',locks)
 functions(M4/'code/run.py',['pair_asset','evaluate_edges'],ns,BASE,rel+'run.py',locks)
 mrel='experiments/TASK-V6-REGISTRATION-NOISE-AND-RAW-CLEAN-002/code/metrics2.py'
 functions(M4/'runtime/pinned'/KERNEL/mrel,['summarize','bidirectional','ring_pixels'],ns,KERNEL,mrel,locks)
 # ring_pixels imports this exact project implementation.
 for rel in ['src/ring_first_3d/mainline/native/ring_cad.py','src/ring_first_3d/sim/geometry.py']:
  p=ROOT/rel;raw=subprocess.check_output(['git','show',BASE+':'+rel],cwd=ROOT);assert p.read_bytes()==raw;locks.append(dict(**asset(p),commit=BASE,repository_path=rel))
 return ns,locks

def main():
 ns,locks=kernels();manifest=read(M4/'evidence/ARCHIVE_MANIFEST.json');oldmanifest=read(OLD/'evidence/ARCHIVE_MANIFEST.json')
 mh={str(M4/x['path']):x['sha256']for x in manifest['files']};oh={str(OLD/x['path']):x['sha256']for x in oldmanifest['files']}
 # Manifests themselves are pinned in the audited commits.
 for root,commit in [(M4,BASE),(OLD,'3b8610075a4959a32097cca83247faaddbf61aa1')]:
  p=root/'evidence/ARCHIVE_MANIFEST.json';rel=str(p.relative_to(root.parent.parent));assert p.read_bytes()==subprocess.check_output(['git','show',commit+':'+rel],cwd=ROOT)
 groups=[];all_edges=[];input_records={};old_count=0;new_count=0
 for auditpath in sorted((OLD/'runs/inputs').glob('*/AUDIT.json')):
  asset(auditpath,oh[str(auditpath)]);a=read(auditpath);g=a['group'];out=T/'runs/registration'/g;inputs=[asset(auditpath,oh[str(auditpath)])]
  for r in a['files']:inputs.append(asset(r['path'],r['sha256']))
  oldpath=Path(a['old_group']['path']);asset(oldpath,a['old_group']['sha256']);oldout=oldpath.parent
  ns['read']=read
  oldasset,reg=ns['verify_registration'](oldout)
  for v in read(oldpath)['videos']:
   assert np.array_equal(v['T_local_to_common'],a['transforms'][v['case']]);old_count+=1
  new_count+=len(a['videos'])-len(read(oldpath)['videos'])
  for name in ['REGISTRATION.json','ASSETS.json','TRANSFORM_FREEZE.json']:
   inputs.append(asset(oldout/name,mh.get(str(oldout/name))))
  edges=[]
  oldeval=oldout/'EDGE_EVALUATION.json'
  cached=read(oldeval)if oldeval.exists()else[]
  if oldeval.exists():inputs.append(asset(oldeval,mh[str(oldeval)]))
  for origin,entries in [('ORIGINAL_62',reg['edges']),('SUPPLEMENT_17',a['supplement_edges'])]:
   for edge in entries:
    folder=Path(edge['folder']);sourceout=folder.parents[1];match=read(sourceout/'MATCH_CACHE.json');verify(match['files']);verify(edge['files']);inputs.extend(match['files']+edge['files']);inputs.append(asset(sourceout/'MATCH_CACHE.json',mh.get(str(sourceout/'MATCH_CACHE.json'),oh.get(str(sourceout/'MATCH_CACHE.json')))))
    # Ensure archive identity protects the supplemental matched/DLT inputs too.
    for rr in match['files']+edge['files']:
     archive_hash=mh.get(rr['path'],oh.get(rr['path']));assert archive_hash is not None,rr['path'];asset(rr['path'],archive_hash)
    ep=(edge['parent'],edge['child']);row=next((r for r in cached if(r['parent'],r['child'])==ep),None)if origin=='ORIGINAL_62'else None
    destination=out/('original'if origin=='ORIGINAL_62'else'supplement')
    if row is None:
     # Exact original evaluate_edges, with only IO adapted for missing supplemental REGISTRATION wrapper.
     native_read=read
     def adapted_read(p):
      return dict(edges=[edge])if Path(p)==sourceout/'REGISTRATION.json'else native_read(p)
     def adapted_save(p,obj):save(destination/Path(p).relative_to(sourceout),obj)
     ns.update(group_out=lambda _:sourceout,read=adapted_read,save=adapted_save)
     ns['evaluate_edges'](g);row=read(destination/'EDGE_EVALUATION.json')[0];mode='NEW_FROZEN_CACHE_EVALUATION'
    else:
     mode='REUSED_HASH_VERIFIED_ORIGINAL_EVALUATION'
     save(destination/'EDGE_EVALUATION.json',row)
    pred=edge['results']['M4'];Ta=a['transforms'].get(ep[0]);Tb=a['transforms'].get(ep[1]);t=pred.get('T');consistent=valid_T(Ta)and valid_T(Tb)and valid_T(t)and np.allclose(np.asarray(Ta)@np.asarray(t),Tb,atol=1e-8,rtol=0)
    verdict=qualify(row['methods'],pred,bool(consistent))
    q=dict(group=g,parent=ep[0],child=ep[1],origin=origin,evaluation_mode=mode,**verdict,composition_consistent=bool(consistent),T_child_to_parent=t,metrics_path=str(destination/'EDGE_EVALUATION.json'),metrics_sha256=sha(destination/'EDGE_EVALUATION.json'),methods=row['methods'],source_edge=dict(**asset(folder/'EDGE.json',oh.get(str(folder/'EDGE.json'),mh.get(str(folder/'EDGE.json'))))),FIT_tracks=edge['FIT_tracks'])
    edges.append(q);all_edges.append(q)
  # Keep every node; only PASS edges establish joint components.
  remaining={v['case']for v in a['videos']};components=[]
  while remaining:
   component={min(remaining)};changed=True
   while changed:
    changed=False
    for edge in edges:
     pair={edge['parent'],edge['child']}
     if edge['status']=='PASS_FOR_JOINT'and pair&component and not pair<=component:component|=pair;changed=True
   remaining-=component
   if len(component)>1:
    videos=sorted(component);anchor=videos[0];left=np.linalg.inv(a['transforms'][anchor]);trans={v:left@np.asarray(a['transforms'][v])for v in videos}
    components.append(dict(name='JOINT'if len(videos)==len(a['videos'])else'JOINT_'+'_'.join(v.rsplit('_',1)[-1]for v in videos),videos=videos,anchor=anchor,T_local_to_joint=trans,coordinate_frame='QUALIFIED_COMPONENT_ANCHOR_LOCAL',all_group_videos=len(videos)==len(a['videos'])))
  singles=[dict(case=v['case'],coordinate_frame='LOCAL',T_local_to_output=np.eye(4),cad_frame='LOCAL',ring_radius_mm=v['ring_radius_mm'],ring_wire_mm=v['ring_wire_mm'],camera=v['camera'],camera_sha256=v['camera_sha256'],joint_components=[c['name']for c in components if v['case']in c['videos']])for v in a['videos']]
  group=dict(group=g,videos=[v['case']for v in a['videos']],edges=edges,joint_components=components,single_routes=singles,joint_not_run_reason=None if components else'NO_QUALIFIED_CONNECTED_PAIR',input_audit=asset(auditpath),input_files=inputs)
  save(out/'QUALIFICATION.json',group);groups.append(group)
  input_records.update({x['path']:x for x in inputs});print(g,[e['status']for e in edges],len(components),flush=True)
 states={s:sum(e['status']==s for e in all_edges)for s in ['PASS_FOR_JOINT','FAIL_REGISTRATION','INCONCLUSIVE_REGISTRATION']}
 result=dict(task='TASK-V6-R1-DXY-HERO-BODY-INIT-002',schema='REGISTRATION_QUALIFICATION_1',policy=POLICY,policy_sha256=hashlib.sha256(json.dumps(POLICY,sort_keys=True).encode()).hexdigest(),source_locks=locks,summary=dict(groups=len(groups),videos=sum(len(g['videos'])for g in groups),old_transforms_exact=old_count,new_videos_checked=new_count,verified_unique_input_files=len(input_records),original_evaluations_reused=sum(e['evaluation_mode']=='REUSED_HASH_VERIFIED_ORIGINAL_EVALUATION'for e in all_edges),supplement_evaluations_computed=sum(e['evaluation_mode']=='NEW_FROZEN_CACHE_EVALUATION'for e in all_edges),edges=len(all_edges),statuses=states,joint_components=sum(len(g['joint_components'])for g in groups)),groups=groups,source_files=list(input_records.values()),held_scope='Used for downstream admission; not an independent end-to-end test',transform_rule='Singles local. Qualified component: inv(old_T_anchor) @ old_T_video; applied identically to cameras, landmarks, surfaces and per-video CAD. No new T solved.')
 save(T/'evidence/REGISTRATION_QUALIFICATION.json',result)
 with open(T/'evidence/REGISTRATION_QUALIFICATION.csv','w',newline='')as f:
  keys=['group','parent','child','origin','status','reasons','warnings','composition_consistent','median_A_to_B','median_B_to_A','child_ring_increase','held_DLT_tracks','metrics_path'];w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader()
  for e in all_edges:
   row={k:e.get(k)for k in keys};m=e['methods'];b=m['M4']['bidir'];row.update(median_A_to_B=b['A_to_B']['conditional_median'],median_B_to_A=b['B_to_A']['conditional_median'],child_ring_increase=(m['M4']['ring']['by_side']['B']['conditional_MAE']-m['M0']['ring']['by_side']['B']['conditional_MAE'])if finite(m['M4']['ring']['by_side']['B']['conditional_MAE'])and finite(m['M0']['ring']['by_side']['B']['conditional_MAE'])else None,held_DLT_tracks=b['denominators']['two_sided_DLT_tracks']);w.writerow(row)
 print(json.dumps(result['summary']),flush=True)
if __name__=='__main__':main()
