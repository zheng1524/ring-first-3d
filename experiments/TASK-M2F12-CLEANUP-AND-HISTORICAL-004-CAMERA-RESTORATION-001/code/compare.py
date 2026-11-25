"""Post-freeze, unpaired common CAD scorer and fixed 5-group/10-video tables."""
import sys,json,csv,ast,collections,datetime
from pathlib import Path
import numpy as np,cv2
from scipy.spatial.transform import Rotation
from scipy.ndimage import binary_erosion,distance_transform_edt
from historical_io import W,E,sha,common,load
HERE=Path(__file__).resolve().parent;T=HERE.parent;B=W/'runs/m2f12_historical004'
def read(p):return json.loads(Path(p).read_text())
def save(p,d):
 def clean(x):
  if isinstance(x,dict):return{k:clean(v)for k,v in x.items()}
  if isinstance(x,(list,tuple)):return[clean(v)for v in x]
  if hasattr(x,'tolist'):return clean(x.tolist())
  if isinstance(x,float)and not np.isfinite(x):return None
  return x
 Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(clean(d),indent=2))
def table(p,rows):
 fields=list(dict.fromkeys(k for r in rows for k in r));p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w')as f:
  w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def median(xs):
 xs=[x for x in xs if x is not None and np.isfinite(x)];return float(np.median(xs))if xs else None
def steps(poses):
 out=[]
 for a,b in zip(poses[:-1],poses[1:]):
  if a is None or b is None:continue
  a,b=np.array(a),np.array(b)
  if not np.isfinite(a).all()or not np.isfinite(b).all():continue
  out.append(dict(center_step_mm=float(np.linalg.norm(a[:3,3]-b[:3,3])),rotation_step_deg=float(np.degrees(Rotation.from_matrix(a[:3,:3].T@b[:3,:3]).magnitude()))))
 return out
def main():
 import open3d as o3d
 scenes={};frame_rows=[];rows=[];detail={};source_receipts=[]
 for diam in [5,10]:
  p=W/f'runs/m2f5_unified/cad/R{diam}.npz';a=np.load(p);s=o3d.t.geometry.RaycastingScene(nthreads=2);s.add_triangles(o3d.core.Tensor(a['V'].astype(np.float32)),o3d.core.Tensor(a['F'].astype(np.uint32)));scenes[diam]=s;source_receipts.append(dict(path=str(p),sha256=sha(p)))
 def ring(C,K,lab,diam):
  C=np.array(C);K=np.array(K);h,w=lab.shape;y,x=np.mgrid[:h,:w];dirs=np.c_[x.ravel(),y.ravel(),np.ones(h*w)]@np.linalg.inv(K).T@C[:3,:3].T;rays=np.c_[np.broadcast_to(C[:3,3],dirs.shape),dirs].astype(np.float32);z=scenes[diam].cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy().reshape(h,w);pred=np.isfinite(z)&(z>0);obs=lab==2;edge=obs&~binary_erosion(obs);boundary=pred&~binary_erosion(pred)
  dist=distance_transform_edt(~pred)if pred.any()else np.full((h,w),np.nan);bd=distance_transform_edt(~boundary)if boundary.any()else np.full((h,w),np.nan)
  return dict(common_ring_observed_pixels=int(obs.sum()),common_ring_support_2px=float((dist[obs]<=2).mean())if obs.any()else None,common_ring_boundary_MAE_px=float(bd[edge].mean())if edge.any()and boundary.any()else None,common_ring_boundary_p95_px=float(np.quantile(bd[edge],.95))if edge.any()and boundary.any()else None,common_ring_IoU_diagnostic=float((pred&obs).sum()/max(1,(pred|obs).sum())))
 oldcsv=list(csv.DictReader((T/'evidence/V6_VIDEO_METRICS.csv').open()));old={(x['group_id'],x['video_id']):x for x in oldcsv}
 heroes={(x['case'],x['route']):x for x in read(B/'HERO_LIMITED/RESULTS.json')}if(B/'HERO_LIMITED/RESULTS.json').exists()else{}
 for registry in read(T/'evidence/INPUT_REGISTRY.json'):
  case=registry['case'];diam=int(registry['ring_inner_mm']);R=B/'H004_RAW_BASELINE'/case
  for route in ['H004_RAW_BASELINE','V6']:
   rec=dict(group=registry['group'],video=registry['video_id'],route=route,raw_sha256=registry['raw_sha256'],status='NOT_EVALUABLE',requested_cameras=16 if route=='H004_RAW_BASELINE'else None,numeric_cameras=0,own_qualified_cameras=0,legal_target_count=0,legal_support_links=0,landmarks=0,common_independent_RGB_status='NOT_EVALUABLE_V6_AND_NATIVE_FITTING_EXCLUSION_UNCERTIFIED',absolute_pose_GT='NOT_EVALUABLE',paired_same_input=False)
   cams=[];krows=[];poses=[];extra={}
   if route=='H004_RAW_BASELINE':
    for st in ['prepare','seed','recover']:
     p=R/f'STAGE_{st}.json'
     if p.exists():
      s=read(p);rec[st+'_seconds']=s['seconds'];rec[st+'_status']=s['status']
      if s['status']=='FAILED':rec['failure']=s['error']
    if(R/'metrics/SEED_EVALUATION.json').exists():
     se=read(R/'metrics/SEED_EVALUATION.json');g,h=se['geometry'],se['heldout'];ac=read(R/'config.json')['acceptance']
     rec.update(seed_numeric=len(g['registered']),seed_points=g['candidate_points'],seed_positive_fraction=g['positive_fraction'],seed_held_track_count=h['target_heldout_tracks'],seed_held_testable=h['testable_tracks'],seed_independent_RGB_n=h['error_px']['n'],seed_independent_RGB_MAE_px=h['error_px']['MAE'],seed_independent_RGB_p95_px=h['error_px']['p95'],seed_held_positive_fraction=h['positive_track_fraction'],seed_max_rotation_step_deg=g['largest_rotation_step_deg'],seed_basic_pass=bool(len(g['registered'])>=ac['min_registered']and g['reference8']and h['testable_tracks']>=ac['min_test_tracks']and h['error_px']['MAE']is not None and h['error_px']['MAE']<=ac['max_holdout_MAE_px']and g['positive_fraction']>=ac['min_positive_fraction']and g['largest_rotation_step_deg']<=ac['max_rotation_step_deg']),full_9_initialization_reliability='NOT_RUN')
    if(R/'registration/CAMERAS.json').exists():
     cams=read(R/'registration/CAMERAS.json');sm=read(R/'metrics/RECOVERY_SUMMARY.json');su=read(R/'selection/SUPPORTS.json');legal={x['target']for x in su if x['support_N']==3};supportids={y['id']for x in su for y in x['selected']};rec.update(status='COMPLETED',numeric_cameras=sm['numeric'],own_qualified_cameras=sm['qualified'],legal_target_count=sm['legal_targets'],legal_support_links=sm['legal_support_links'],landmarks=sm['landmarks'],own_gate='original MAX qualification on native RF/PnP; conditional map-held')
     rec['RGB_registered_numeric']=sum(v.get('numeric_status')=='NUMERIC_RGB_REGISTERED_CONDITIONAL'for v in cams);rec['ring_only_yaw_unresolved']=sum(v.get('numeric_status')=='RING_ONLY_YAW_UNRESOLVED'for v in cams)
     rec['candidate_sources']=json.dumps(dict(collections.Counter(v.get('candidate_source','FAILED')for v in cams)));rec['qualification_failures']=json.dumps(dict(collections.Counter(reason for v in cams for reason in v.get('qualification_reasons',[]))))
     seedP=np.load(R/'predictions/C_F980_0.npz')['c2w'];delta=[dict(rotation=float(np.degrees(Rotation.from_matrix(seedP[v['index'],:3,:3].T@np.array(v['C'])[:3,:3]).magnitude())),center=float(np.linalg.norm(seedP[v['index'],:3,3]-np.array(v['C'])[:3,3])))for v in cams if v['C']is not None and np.isfinite(seedP[v['index']]).all()];rec['native_vs_seed_rotation_median_deg']=median([d['rotation']for d in delta]);rec['native_vs_seed_center_median_mm']=median([d['center']for d in delta])
     rec['native_mapheld_MAE_median_px']=median([v.get('RGB_evaluation',{}).get('FEATURE_HELD',{}).get('MAE')for v in cams]);rec['native_mapheld_p95_median_px']=median([v.get('RGB_evaluation',{}).get('FEATURE_HELD',{}).get('p95')for v in cams]);rec['native_mapheld_positive_median']=median([v.get('RGB_evaluation',{}).get('FEATURE_HELD_positive_fraction')for v in cams]);rec['native_mapheld_independent']=False
     for v in cams:
      a=np.load(v['cache']);krows.append(dict(id=v['id'],raw_frame=v['raw_frame'],C=v['C'],K=v['K'],labels=a['labels'],RGB=a['RGB'],own_qualified=v['formal'],target_eligible=v['id']in legal,support_eligible=v['id']in supportids,native_mapheld=v.get('RGB_evaluation',{}).get('FEATURE_HELD',{}),native_positive=v.get('RGB_evaluation',{}).get('FEATURE_HELD_positive_fraction')))
     lm=read(R/'landmarks/BUILD_AUDIT.json');accepted=[x for x in lm['tracks']if x['qualified']];rec.update(landmark_background=sum(x['category']=='background'for x in accepted),landmark_polyp=sum(x['category']=='polyp'for x in accepted),landmark_mixed=sum(x['category']=='mixed'for x in accepted),landmark_attempted=len(lm['tracks']),landmark_reprojection_max_median_px=median([max(x['reprojection_px'])for x in accepted]),landmark_parallax_median_deg=median([x['parallax_deg']for x in accepted]))
     cells={(s['view'],int(s['uv'][0]//80),int(s['uv'][1]//60))for a in accepted for s in a['sources']};rec['landmark_views_covered']=len({x[0]for x in cells});rec['landmark_view_grid_cells']=len(cells);rec['landmark_positive_min']=min((x['positive_depth_fraction']for x in accepted),default=None)
     c=common(R);load('geometry_safe',R,diam/2+.6);ev=load('evaluate_real',R,diam/2+.6);tr=np.load(R/'observations/tracks.npz');P=np.array([v['C']if v['C']is not None else np.full((4,4),np.nan)for v in cams]);held=np.flatnonzero(~tr['train_track']&tr['holdout_eligible']);post=ev.holdout(P,np.array(cams[0]['K']),tr['xy'],held,tr['category']);save(R/'metrics/FINAL_LK_DIAGNOSTIC.json',post);rec.update(final_LK_diagnostic_MAE_px=post['error_px']['MAE'],final_LK_diagnostic_p95_px=post['error_px']['p95'],final_LK_diagnostic_n=post['error_px']['n'],final_LK_diagnostic_positive=post['positive_track_fraction'],final_LK_independent=False)
   else:
    states=registry['V6_states'];V=Path(states[-1]['path']).parent;val=read(V/'metrics/local_validation.json');v=next(v for v in val['versions']if v['version']==val['primary']);cam=np.load(V/f"predictions/local005_camera_{val['primary']}.npz");L=read(V/'inputs/ledger005.json');cs=[c for c in read(V/'inputs/MVS_supported_cases.json')if len(c['sources'])==3];legal={x['reference']for x in cs};supportids={i for x in cs for i in x['sources']};rec.update(status='COMPLETED_READONLY',requested_cameras=len(L),numeric_cameras=int(np.isfinite(cam['c2w']).all((1,2)).sum()),own_qualified_cameras=sum(x['status']=='VALIDATED'for x in v['per_frame']),legal_target_count=len(legal),legal_support_links=sum(len(x['sources'])for x in cs),landmarks=len(cam['points']),own_gate='V6 final attempt VALIDATED; supported Target need not be VALIDATED',V6_code_commit=states[-1]['code_commit'],V6_attempts=len(states))
    for i,(a,q)in enumerate(zip(L,v['per_frame'])):
     krows.append(dict(id=a['id'],raw_frame=a['raw_frame'],C=cam['c2w'][i],K=a['K'],labels=cv2.imread(a['Mask_path'],0),RGB=cv2.cvtColor(cv2.imread(a['RGB_path']),cv2.COLOR_BGR2RGB),own_qualified=q['status']=='VALIDATED',target_eligible=i in legal,support_eligible=i in supportids,native_mapheld=q.get('held_reprojection'),native_positive=q.get('held_positive_fraction')))
    rec['own_held_diagnostic_MAE_median_px']=median([x['held_reprojection']['MAE']for x in v['per_frame']]);rec['own_held_diagnostic_p95_median_px']=median([x['held_reprojection']['p95']for x in v['per_frame']]);rec['own_held_observations']=sum(x['held_reprojection']['n']for x in v['per_frame']);rec['own_positive_median']=median([x.get('held_positive_fraction')for x in v['per_frame']]);rec['own_held_status']='V6 claims leave-one-view-out held tracks; not common certified test'
    for k,value in old[(registry['group'],registry['video_id'])].items():
     if k not in ['group_id','video_id']:rec['M2F10_full_'+k]=value
    spans=[]
    for state in states:
     trace=[json.loads(line)for line in (Path(state['path']).parent/'RUN_TRACE.jsonl').read_text().splitlines()];ts=[datetime.datetime.fromisoformat(x['utc'])for x in trace if x.get('utc')];spans.append((max(ts)-min(ts)).total_seconds())
    rec['V6_elapsed_all_attempts_including_HERO_seconds']=sum(spans)
   local=[]
   for v in krows:
    C=v['C'];poses.append(C);rr=dict(case=case,route=route,id=v['id'],raw_frame=v['raw_frame'],own_qualified=v['own_qualified'],target_eligible=v['target_eligible'],support_eligible=v['support_eligible'],numeric=C is not None and np.isfinite(C).all())
    if rr['numeric']:rr.update(ring(C,v['K'],v['labels'],diam))
    frame_rows.append(rr);local.append(rr)
   jumps=steps(poses);rec.update(max_rotation_step_deg=max((x['rotation_step_deg']for x in jumps),default=None),max_center_step_mm=max((x['center_step_mm']for x in jumps),default=None),rotation_jumps_gt30deg=sum(x['rotation_step_deg']>30 for x in jumps),qualified_targets=sum(x['target_eligible']and x['own_qualified']for x in local),qualified_supports=sum(x['support_eligible']and x['own_qualified']for x in local))
   for k in ['common_ring_support_2px','common_ring_boundary_MAE_px','common_ring_boundary_p95_px','common_ring_IoU_diagnostic']:rec[k+'_median']=median([x.get(k)for x in local])
   hero=heroes.get((case,route if route!='V6'else'V6_LIMITED_DIAGNOSTIC'),{});rec['limited_HERO_status']=hero.get('status','NOT_RUN');rec['limited_HERO_budget']=1
   if hero.get('ring'):
    for k,v in hero['ring'].items():rec['limited_HERO_ring_'+k]=v
    for k in ['target_coverage','RGB_MAE_0_255','RGB_p95_0_255']:rec['limited_HERO_A_to_B_'+k]=hero['a_to_b'][k]
   rows.append(rec);detail[case+'/'+route]=dict(camera_steps=jumps,frames=local)
 table(T/'evidence/COMPARISON_LONG.csv',rows);wide=[]
 keys=['status','numeric_cameras','own_qualified_cameras','qualified_targets','qualified_supports','legal_target_count','landmarks','common_ring_support_2px_median','common_ring_boundary_MAE_px_median','max_rotation_step_deg','limited_HERO_status','limited_HERO_ring_MAE_mm','limited_HERO_ring_ratio_median','limited_HERO_ring_coverage','limited_HERO_A_to_B_target_coverage','limited_HERO_A_to_B_RGB_MAE_0_255']
 for registry in read(T/'evidence/INPUT_REGISTRY.json'):
  d=dict(group=registry['group'],video=registry['video_id'],raw_sha256=registry['raw_sha256'])
  for route in ['H004_RAW_BASELINE','V6']:
   r=next(x for x in rows if x['route']==route and x['group']==d['group']and x['video']==d['video'])
   d.update({route+'_'+k:r.get(k)for k in keys})
   if route=='H004_RAW_BASELINE':d.update(H004_seed_basic_pass=r.get('seed_basic_pass'),H004_seed_independent_RGB_MAE_px=r.get('seed_independent_RGB_MAE_px'),H004_final_LK_diagnostic_MAE_px=r.get('final_LK_diagnostic_MAE_px'))
  d.update(common_independent_RGB='NOT_EVALUABLE',pose_GT='NOT_EVALUABLE',paired_same_input=False,H004_PLUS='NOT_RUN_NO_RELIABLE_CAUSAL_BASIS');wide.append(d)
 table(T/'COMPARISON.csv',wide);table(T/'evidence/CAMERA_COMMON_EVALUATION.csv',frame_rows);save(T/'evidence/CAMERA_STEPS.json',detail)
 save(T/'evidence/COMPARISON_PROTOCOL.json',dict(groups=5,videos=10,rows=len(rows),common_scorer='same CAD first-hit + observed-mask support; visible-boundary identity uncertified so boundary diagnostic',common_RGB='NOT_EVALUABLE: no shared fit-excluded identity set',same_frame_diagnostic='NOT_PAIRED_NOT_RUN; native frame schedules differ',yaw='H004 reference8 arbitrary yaw; V6 independent per-video gauge; no trajectory alignment used to modify predictions',denominator_policy='all ten videos retained; no failures dropped; null metric is not zero',source_receipts=source_receipts))
 print('COMPARISON',len(rows),'rows',len(frame_rows),'camera records',flush=True)
if __name__=='__main__':main()
