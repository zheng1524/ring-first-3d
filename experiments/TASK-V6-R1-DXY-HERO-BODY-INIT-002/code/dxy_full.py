"""Full frozen DXY observations plus an explicitly non-metric pixel-only outlet.

Only task-local files are written. Candidate profiles and rejected fits remain
in evidence but are never promoted to supervision.
"""
from pathlib import Path
import sys, json, gzip, hashlib, subprocess, dataclasses, time, argparse, traceback
import numpy as np
import cv2
T=Path(__file__).resolve().parents[1]
OLD=T.parents[2]/'TASK-V6-R1-BODY-INIT-001/experiments/TASK-V6-R1-DXY-HERO-BODY-INIT-001'
DXY=Path('/home/liu/new-polyp-dxy');COMMIT='75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95'
sys.path.insert(0,str(DXY/'src'))
from dxy_mid import diagnostics, pipeline as official_pipeline, _engine as engine
from dxy_mid._engine.observable_boundary import observable_P
from dxy_mid._engine.exact_v2 import geometry
from dxy_mid._engine import geometry_competition
from dxy_mid._engine.contracts import BoundaryResult

def clean(v):
 if isinstance(v,np.ndarray):return clean(v.tolist())
 if isinstance(v,np.generic):return clean(v.item())
 if dataclasses.is_dataclass(v):return clean(dataclasses.asdict(v))
 if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
 if isinstance(v,(list,tuple,set)):return [clean(x) for x in v]
 if isinstance(v,Path):return str(v)
 if isinstance(v,float) and not np.isfinite(v):return None
 return v

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);assert T in p.resolve().parents;p.parent.mkdir(parents=True,exist_ok=True)
 q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(clean(v),ensure_ascii=False,indent=2)+'\n');q.replace(p)
def asset(p):return dict(path=str(p),sha256=sha(p))
def curve(c,n=361):
 if c is None:return np.empty((0,2))
 a=np.linspace(0,2*np.pi,n);return np.array(c['center_px'])+np.c_[np.cos(a),np.sin(a)]@np.array(c['basis_px']).T

def pixel_only(image,labels,source_id):
 # Ring is intentionally not made valid. Native P depends only on actual local
 # label adjacency. The radius/extent below are image-derived solver bounds,
 # never Ring measurements or metric scale.
 f=engine.FrameInput(image,labels,5.,source_id,'','')
 P,checks=observable_P(f);P=np.asarray(P).reshape(-1,2)
 out=dict(status='NO_CURVE',official_measurement_valid=False,selected=None,candidates=[],P=P,Q=np.empty((0,2)),X=np.array([x['q'] for x in checks if not x['accepted_P']]).reshape(-1,2),boundary_records=checks,failures=[],reason='insufficient_observable_P')
 if len(P)<20:return out
 center=(P.min(0)+P.max(0))/2;extent=float(np.max(np.ptp(P,axis=0)));rr=max(extent/2,1.)
 body=dict(name='PIXEL_OBSERVED_P',points_local=P,geom_center_local=center,extent=extent,rr_native=rr,crop_offset=np.zeros(2),trusted=P)
 b=BoundaryResult([body],P,out['X'],np.empty((0,2)),np.zeros(labels.shape,bool),dict(coordinate_system='native_image_px'))
 cs,failures=geometry(f,None,b,stem=source_id);out['failures']=failures
 records=[]
 for i,c in enumerate(cs):
  records.append(dict(record_id=f'pixel:{i}:{c.shape}',body=c.name,shape=c.shape,center_px=c.center_native,basis_px=c.basis_native,valid=bool(c.fit['valid']),reason=c.fit['reason'],quality=c.quality,selected=False,diagnostic_profile=False,supervision_eligible=bool(c.fit['valid'])))
 good=[r for r in records if r['valid'] and np.isfinite(np.asarray(r['basis_px'])).all()]
 if good:
  # Same rule for all frames; penalize ellipse flexibility by a tiny fixed cost.
  selected=min(good,key=lambda r:float(r['quality']['norm_residual_all'])+(.005 if r['shape']=='ellipse' else 0.))
  selected['selected']=True;out.update(status='PIXEL_ONLY',selected={k:selected[k] for k in ['record_id','center_px','basis_px','shape']},reason='observable_P_native_fit_without_valid_Ring')
  out['selected']['weight']=.2
 out['candidates']=records;out['bounds']=dict(center_px=center,extent_px=extent,rr_proxy_px=rr,source='observable_P_bbox_not_Ring')
 return out

def official_arrays(obs):
 if obs.boundary is None:return None
 d=obs.selected['data'];records=obs.boundary['original_boundary']['records'];Q=d['Q']
 return dict(P=np.asarray(d['P']).reshape(-1,2),Q=np.array([q['q'] for q in Q]).reshape(-1,2),X=np.array([r['q'] for r in records if r['class_']=='X']).reshape(-1,2),Q_normals=np.array([q['n'] for q in Q]).reshape(-1,2),Q_lo=np.array([q['lo'] for q in Q]),Q_hi=np.array([q['hi'] for q in Q]),P_global_indices=np.array(d['P_global_indices'],int),Q_global_indices=np.array([q['global_index'] for q in Q],int),X_global_indices=np.array([r['global_index'] for r in records if r['class_']=='X'],int),boundary_points=np.array([r['q'] for r in records]).reshape(-1,2),boundary_global_indices=np.array([r['global_index'] for r in records],int),boundary_contour_ids=np.array([r['contour_id'] for r in records],int),boundary_contour_indices=np.array([r['contour_index'] for r in records],int),boundary_classes=np.array([r['class_'] for r in records]))

def inventory():
 rows=[];audits=[]
 for ap in sorted((OLD/'runs/inputs').glob('*/AUDIT.json')):
  a=read(ap);audits.append(asset(ap))
  for v in a['videos']:
   oldindex=read(OLD/'runs/observations'/a['group']/v['case']/'INDEX.json')
   roles={r['id']:r['role'] for r in oldindex['frames']}
   for j,f in enumerate(v['frames']):
    rows.append(dict(group=a['group'],case=v['case'],index=j,frame_id=f['id'],role=roles.get(f['id'],'UNSELECTED'),source_id=v['case']+':'+f['id'],stem=v['case']+':'+f['id'],RGB=f['RGB_path'],Mask=f['Mask_path'],RGB_sha256=f['RGB_SHA256'],Mask_sha256=f['Mask_SHA256'],native_shape=f['working_shape'],inner_diameter_mm=2*(v['ring_radius_mm']-.6),source_frame=f,camera=asset(v['camera']),audit=asset(ap)))
 assert len(rows)==1700 and len({r['case'] for r in rows})==79
 lock=dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=DXY,text=True).strip(),files=[asset(p) for p in sorted((DXY/'src/dxy_mid').rglob('*.py'))])
 assert lock['commit']==COMMIT
 assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=DXY,text=True).strip(),'Frozen DXY modified'
 save(T/'evidence/DXY_INPUT_INDEX.json',dict(rows=rows,frames=len(rows),videos=79,groups=39,audits=audits,source=lock,roles_are_unchanged=True))
 return rows,lock

def resolve_selected_record(records, selected, body, shape, origin, actual_record_id=None):
 matches=[]
 for record in records:
  if record['body']!=body or record['shape']!=shape or record.get('origin')!=origin or record.get('diagnostic_profile',False):continue
  delta=max(np.max(np.abs(np.asarray(record['center_px'])-selected['center_px'])),np.max(np.abs(np.asarray(record['basis_px'])-selected['basis_px'])))
  if delta<=1e-10:matches.append(record)
 if not matches:raise ValueError('No exact native-parameter candidate identity')
 ids=[r['record_id'] for r in matches]
 if actual_record_id is None:
  if len(matches)!=1:raise ValueError('Ambiguous exact candidates require actual object observation')
  return matches[0],ids
 if actual_record_id not in ids:raise ValueError('Observed object identity disagrees with native parameters')
 return next(r for r in matches if r['record_id']==actual_record_id),ids

def observe_complete(row):
 baseline=[];candidate_objects={};previous=sys.getprofile()
 def capture(frame,event,arg):
  if previous is not None:previous(frame,event,arg)
  if event=='return' and frame.f_code is official_pipeline._measure.__code__:
   baseline.extend(frame.f_locals.get('current',[]))
  elif event=='return' and frame.f_code is geometry_competition.to_candidate.__code__:
   candidate_objects[id(arg)]=frame.f_locals['r']
 try:
  sys.setprofile(capture)
  observed=diagnostics.observe_files(row['RGB'],row['Mask'],inner_diameter_mm=row['inner_diameter_mm'],source_id=row['source_id'],stem=row['stem'])
 finally:sys.setprofile(previous)
 identity=None;c=observed.measurement.candidate
 if c is not None:
  original=candidate_objects.get(id(c))
  if original is not None:
   found=[f"default:{body['data']['name']}:{i}" for body in observed.results['default'] for i,r in enumerate(body['records']) if r is original]
   assert len(found)==1,'Actual selected record object must occur exactly once in default pool'
   identity=found[0]
  else:
   found=[f'default:{q.name}:exact_V2:{i}' for i,q in enumerate(baseline) if q is c]
   assert len(found)==1,'No-Q selected object must occur in actual baseline pool'
   identity=found[0]
 return observed,baseline,identity

def run_frame(row,lock):
 out=T/'runs/dxy'/row['case']/row['frame_id'];out.mkdir(parents=True,exist_ok=True)
 key=hashlib.sha256(json.dumps([row,lock,sha(__file__)],sort_keys=True).encode()).hexdigest()
 receipt=out/'COMPLETE.json'
 if receipt.exists():
  old=read(receipt)
  if old['key']==key and all(Path(x['path']).exists() and sha(x['path'])==x['sha256'] for x in old['files']):return read(out/'FRAME.json')
 assert sha(row['RGB'])==row['RGB_sha256'] and sha(row['Mask'])==row['Mask_sha256']
 start=time.time();obs,baseline,actual_record_id=observe_complete(row)
 diagnostics.export_observation(obs,out/'official')
 m=obs.measurement;selected=None;equivalent=[];selection_identity=dict(record_id=None,equivalent_record_ids=[],method='no_selected_curve');arrays=official_arrays(obs);records=diagnostics.candidate_records(obs)
 for rec in records:
  rec['record_id']=f"default:{rec['body']}:{rec['index']}";theta=rec['angle_rad'];rec['center_px']=[rec['cx'],rec['cy']];rec['basis_px']=(np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])@np.diag([rec['radius_1_px'],rec['radius_2_px']])).tolist()
  rec['supervision_eligible']=not rec['diagnostic_profile'] and not rec['current_reasons'];rec['selected']=False
  body=next(b for b in obs.results['default'] if b['data']['name']==rec['body']);original=body['records'][rec['index']];rec['sampling_trace']=original.get('trace',[])
 # Official no-Q branch directly uses actual exact-V2 candidates and has no
 # competition records. Preserve that real baseline pool, not invented seeds.
 for i,c in enumerate(baseline):
  if obs.results is None or not any(b['branch']=='no_Q_exact_V2' and b['data']['name']==c.name for b in obs.results['default']):continue
  records.append(dict(record_id=f'default:{c.name}:exact_V2:{i}',body=c.name,shape=c.shape,center_px=c.center_native,basis_px=c.basis_native,origin='actual_no_Q_exact_V2',quality=c.quality,fit=c.fit,selected=False,diagnostic_profile=False,supervision_eligible=bool(c.fit['valid'])))
 status='OFFICIAL' if m.candidate is not None else 'NO_CURVE';quality=m.audit['quality_class'];pixel=None
 if m.candidate is not None:
  c=m.candidate;weight=.8 if m.audit['strict_stable'] else .5 if m.audit['normal_Gate_pass'] else .25
  if m.audit.get('P_zero_occlusion_inference'):weight=min(weight,.15)
  selected=dict(center_px=c.center_native,basis_px=c.basis_native,shape=c.shape,weight=weight)
  actual=next(r for r in records if r['record_id']==actual_record_id)
  chosen,equivalent=resolve_selected_record(records,selected,c.name,c.shape,actual.get('origin'),actual_record_id)
  chosen['selected']=True;selected['record_id']=chosen['record_id']
  selection_identity=dict(record_id=chosen['record_id'],equivalent_record_ids=equivalent,method='observed_actual_record_object',absolute_tolerance_px=1e-10)
 else:
  pixel=pixel_only(obs.native_image,obs.original_labels,row['source_id']);status=pixel['status'];quality='pixel_observed_P_uncertain' if pixel['selected'] else 'pixel_fit_failure';selected=pixel['selected'];records+=pixel['candidates']
  if selected is not None:
   equivalent=[selected['record_id']];selection_identity=dict(record_id=selected['record_id'],equivalent_record_ids=equivalent,method='actual_pixel_V2_selection_record')
  br=pixel['boundary_records'];Pidx=[i for i,r in enumerate(br) if r['accepted_P']];Xidx=[i for i,r in enumerate(br) if not r['accepted_P']]
  arrays=dict(P=pixel['P'],Q=pixel['Q'],X=pixel['X'],Q_normals=np.empty((0,2)),Q_lo=np.empty(0),Q_hi=np.empty(0),P_global_indices=np.array(Pidx,int),Q_global_indices=np.empty(0,int),X_global_indices=np.array(Xidx,int),boundary_points=np.array([r['q'] for r in br]).reshape(-1,2),boundary_global_indices=np.arange(len(br)),boundary_contour_ids=np.array([r['contour_id'] for r in br],int),boundary_contour_indices=np.array([r['contour_index'] for r in br],int),boundary_classes=np.array(['P' if r['accepted_P'] else 'X' for r in br]))
 if arrays is None:arrays={k:np.empty((0,2)) for k in ['P','Q','X','Q_normals']};arrays.update({k:np.empty(0) for k in ['Q_lo','Q_hi','P_global_indices','Q_global_indices','X_global_indices']})
 arrays['selected_curve']=curve(selected);np.savez_compressed(out/'CURVES.npz',**arrays)
 process=dict(selection_identity=selection_identity,actual_baseline_candidates=baseline,default_candidate_pool=records,selection=None if obs.selected is None else {k:obs.selected[k] for k in ['actual_sampled_P_indices','actual_sampled_Q_indices','plan','reason','branch'] if k in obs.selected},variant_summary=m.variants,pixel_branch=pixel,checks=obs.checks)
 with gzip.open(out/'PROCESS.json.gz','wt',encoding='utf8') as f:json.dump(clean(process),f,ensure_ascii=False)
 result={**row,'status':status,'quality':quality,'selected':selected,'selected_record_id':selected['record_id'] if selected else None,'official_measurement_valid':bool(m.audit['measurement_eligible']),'official_ring_valid':bool(m.ring.valid),'official_reason':m.ring.reason,'official_audit':m.audit,'candidate_count':len(records),'profile_count':sum(r.get('diagnostic_profile',False) for r in records),'P_count':len(arrays['P']),'Q_count':len(arrays['Q']),'X_count':len(arrays['X']),'arrays':asset(out/'CURVES.npz'),'process':asset(out/'PROCESS.json.gz'),'seconds':time.time()-start,'cache_key':key,'DXY_commit':COMMIT,'PIXEL_ONLY_has_no_mm_output':True,'selection_identity':selection_identity,'selected_record_equivalent_ids':equivalent,'execution_wrapper_sha256':sha(__file__),'metadata_revalidation_wrapper_sha256':sha(__file__),'numeric_cache_reused':False}
 save(out/'FRAME.json',result);save(receipt,dict(key=key,files=[asset(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='COMPLETE.json']))
 return result

def load_frame(case,frame_id):
 p=T/'runs/dxy'/case/frame_id/'FRAME.json';r=read(p)
 for item in read(p.parent/'COMPLETE.json')['files']:assert sha(item['path'])==item['sha256']
 a=dict(np.load(r['arrays']['path']));r['data']=a;return r

def main():
 arg=argparse.ArgumentParser();arg.add_argument('--workers',type=int,default=2);arg.add_argument('--limit',type=int);arg.add_argument('--case');arg.add_argument('--frame');arg.add_argument('--summary-only',action='store_true');args=arg.parse_args()
 rows,lock=inventory();work=[r for r in rows if (not args.case or args.case==r['case']) and(not args.frame or args.frame==r['frame_id'])];work=work[:args.limit] if args.limit else work
 if not args.summary_only:
  import concurrent.futures
  with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
   futures={pool.submit(run_frame,r,lock):r for r in work}
   for i,f in enumerate(concurrent.futures.as_completed(futures)):
    row=futures[f]
    try:r=f.result();print(i+1,row['case'],row['frame_id'],r['status'],round(r['seconds'],2),flush=True)
    except Exception as e:
     save(T/'runs/dxy'/row['case']/row['frame_id']/'FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc(),row=row));print('FAIL',row['case'],row['frame_id'],repr(e),flush=True)
 records=[];failures=[]
 for row in rows:
  path=T/'runs/dxy'/row['case']/row['frame_id']/'FRAME.json'
  if path.exists():
   r=read(path);records.append({k:r[k] for k in ['group','case','index','frame_id','role','status','quality','selected_record_id','official_measurement_valid','official_ring_valid','candidate_count','P_count','Q_count','X_count']}|dict(path=str(path),sha256=sha(path)))
  else:failures.append(dict(case=row['case'],frame_id=row['frame_id'],reason='not_completed'))
 from collections import Counter
 save(T/'evidence/DXY_FRAME_INDEX.json',dict(frames=1700,completed=len(records),statuses=dict(Counter(r['status'] for r in records)),roles=dict(Counter(r['role'] for r in records)),rows=records,failures=failures,inputs=asset(T/'evidence/DXY_INPUT_INDEX.json'),DXY_commit=COMMIT))
 print('SUMMARY',len(records),dict(Counter(r['status'] for r in records)),len(failures),flush=True)
if __name__=='__main__':main()
