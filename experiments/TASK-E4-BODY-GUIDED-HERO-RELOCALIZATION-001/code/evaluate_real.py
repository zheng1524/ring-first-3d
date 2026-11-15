"""Independent evaluation after ALL real numeric candidates freeze; no selection feedback."""
from validate_pose import *
import ast
P18=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018'
f=REPO/'experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/evaluate020.py';node=next(n for n in ast.parse(f.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='visibility_query');exec(compile(ast.Module(body=[node],type_ignores=[]),str(f),'exec'),globals())
ARMS=['A0','A1','A2-E','A2-U']

def corrected(X,C,t):
 p=(X-C[:3,3])@C[:3,:3];A=np.c_[np.ones(len(p)),p[:,:2]/p[:,2:]];return C[:3,3]+(X-C[:3,3])*(1+(A@t)/p[:,2])[:,None]
def source(rec):
 o=dict(np.load(rec['obs']));m=dict(np.load(rec['mesh']));return dict(rec=rec,id=rec['id'],o=o,m=m,ii=np.linspace(0,len(o['X'])-1,min(1024,len(o['X'])),dtype=int))
def arm_source(s,arm,theta):
 rec=s['rec'];o=s['o'];C=np.array(rec['C']);H=np.eye(4);X=o['X'];V=s['m']['V'];z=o['z'];available=True
 if arm=='A1':
  t=theta[s['id']];X=corrected(X,C,t);V=corrected(V,C,t);z=(X-C[:3,3])@C[:3,2]
 elif arm.startswith('A2'):
  b='Body-'+arm[-1];f=R/'local_results'/rec['group']/b/rec['id']/'CANDIDATES_FROZEN.json';r=load(f);available=r['chosen']is not None
  if available:H=np.array(r['chosen']['H']);X=transform(X,H);V=transform(V,H);C=H@C
 grid=np.full(tuple(o['native_shape']),np.nan);uv=o['uv'].astype(int);grid[uv[:,1],uv[:,0]]=z
 return s|dict(C=C,X=X,V=V,grid=grid,available=available,H=H,arm=arm)
def relation(a,b,ring):
 X=a['X'][a['ii']];N=len(X)
 if a['available']and b['available']:q=visibility_query(X,b['C'],b['o']['K'],b['grid'],ring)
 else:q={k:np.zeros(N,bool)for k in ['known','cad_occluded','target_Ring_order_unreliable','supported','front','behind']};q['dz']=np.full(N,np.nan)
 known=q['known'];e=q['dz'][known];pen=np.where(known,np.minimum(abs(q['dz']),10.),10.);return dict(source=a['id'],target=b['id'],fixed_N=N,available_source=a['available'],available_target=b['available'],known_N=int(known.sum()),support_N=int(q['supported'].sum()),front_proxy_N=int(q['front'].sum()),deeper_N=int(q['behind'].sum()),CAD_occluded_N=int(q['cad_occluded'].sum()),bad_target_CAD_N=int(q['target_Ring_order_unreliable'].sum()),UNKNOWN_N=int((~known&~q['cad_occluded']).sum()),effective_error_mm=stats(e),fixed_10mm_penalty_sum=float(pen.sum())),e,q

def main():
 freeze=load(R/'provenance/ALL_REAL_PREDICTIONS_FROZEN.json');assert len(freeze['results'])==150
 for x in freeze['results']:assert sha(x['result']['path'])==x['result']['sha256']
 refs={x['source']:x['references']for x in load(R/'config/BACKGROUND_REFERENCE_PLAN.json')};allrec=load(R/'config/REAL_SOURCES.json');validation=[];flat=[];summ=[];pairs=[];projection=[];source_quality=[];hold_identity=[]
 for g in ['G03','G05','G01','G06']:
  ss=[source(s)for s in allrec if s['group']==g];rv=dict(np.load(R/'inputs'/g/'RING.npz'));ring=scene(rv['V'],rv['F']);a1=np.load(R/'local_results/A1_LEGACY_REPLAY/runs'/g/'B1/FINAL.npz');theta={str(i):t for i,t in zip(a1['source_ids'],a1['theta'])}
  body_scenes={b:scene(np.load(R/'local_results'/g/(b+'.npz'))['V'],np.load(R/'local_results'/g/(b+'.npz'))['F'])for b in ['Body-E','Body-U']}
  for s in ss:
   for b in ['Body-E','Body-U']:
    f=R/'local_results'/g/b/s['id']/'CANDIDATES_FROZEN.json';v=validate(s['rec'],load(f),refs[s['id']]);ai=np.load(s['rec']['view_cache'])['anchor_index'];dd=body_scenes[b].compute_distance(o3d.core.Tensor(s['o']['X'][ai].astype(np.float32))).numpy();v.update(original_anchor_Body_nn_mm=stats(dd),old_1mm_distance_only_gate_N=int((dd<=1.).sum()),fixed_region_anchor_N=len(ai));validation.append(v);flat.append(dict(group=g,source=s['id'],Body=b,status=v['status'],reasons=v.get('reasons',[]),accepted=v['accepted_H']is not None,numerical=v['numerical'],native_N=v['fixed_native_N'],region_N=v.get('Region_N'),old_1mm_distance_only_gate_N=v['old_1mm_distance_only_gate_N'],fixed_region_anchor_N=len(ai),original_Body_nn_MAE_mm=v['original_anchor_Body_nn_mm']['MAE'],region_MAE_mm=v.get('region_MAE_mm'),initial_region_MAE_mm=v.get('old_world_region_MAE_mm'),Ring_boundary_before_px=v['baseline_Ring']['boundary']['MAE'],Ring_boundary_after_px=v.get('derived_Ring',{}).get('boundary',{}).get('MAE'),SIFT_HOLDOUT_N=v['baseline_SIFT']['N'],SIFT_HOLDOUT_before_px=v['baseline_SIFT']['MAE'],SIFT_HOLDOUT_after_px=v.get('derived_SIFT',{}).get('MAE'),own_projection_drift_px=v.get('own_image_projection_max_px'),max_edge_change_mm=v.get('edge_length_max_change_mm'),Ring_min_before_mm=v.get('original_source_Ring_min_mm'),Ring_min_after_mm=v.get('derived_source_Ring_min_mm'),accepted_H=v['accepted_H']))
  save('metrics/'+g+'_VALIDATION.json',[x for x in validation if x.get('group')==g]);print('VALIDATED',g,flush=True)
  meta=load(P18/'inputs'/g/'ALL_VIEW_META.json');held=[];viewcache=[]
  for v in meta['views']:
   if v['role']=='FIT':continue
   p=P18/'holdout/hero'/v['id'];obs=p/'OBS_TRUSTED.npz';me=p/'TRUSTED_HERO.npz'
   if obs.exists()and me.exists():
    o=dict(np.load(obs));rec=dict(id='HOLDOUT__'+v['id'],group=g,video=v.get('video','004'),C=o['T']);t=source(dict(rec,obs=str(obs),mesh=str(me)));t=arm_source(t,'A0',{});held.append(t)
   cache=P18/'holdout'/g/(v['id']+'.npz')
   if not cache.exists():cache=P18/'inputs'/g/(v['id']+'.npz')
   if cache.exists():
    a=dict(np.load(cache));rgbsha=hashlib.sha256(a['RGB'].tobytes()).hexdigest();duplicate=[s['id']for s in ss if s['rec']['RGB_content_SHA']==rgbsha];v=dict(v,duplicate_current_FIT_RGB_sources=duplicate);hold_identity.append(dict(group=g,view=v['id'],RGB_content_SHA=rgbsha,duplicate_current_FIT_RGB_sources=duplicate,ancestor_Body_U_holdout_not_guaranteed=True));viewcache.append((v,a,cast(ring,a['K'],a['T'],*a['labels'].shape)))
  baseline_queries={}
  for arm in ARMS:
   aaa=[arm_source(s,arm,theta)for s in ss]
   for mode in ['same_video','cross_video','photo','independent_HERO_HOLDOUT']:
    rows=[];errors=[]
    for a in aaa:
     for b in held if mode=='independent_HERO_HOLDOUT'else aaa:
      if a['id']==b['id']:continue
      va=a['rec']['video'];vb=b['rec']['video'];kind='photo'if 'PHOTO'in[va,vb]else'same_video'if va==vb else'cross_video'
      if mode!='independent_HERO_HOLDOUT'and mode!=kind:continue
      row,e,q=relation(a,b,ring);key=(mode,a['id'],b['id'])
      if arm=='A0':baseline_queries[key]=q
      baseq=baseline_queries[key];common=q['known']&baseq['known'];row.update(common_known_A0_N=int(common.sum()),new_known_A0_N=int((q['known']&~baseq['known']).sum()),lost_known_A0_N=int((~q['known']&baseq['known']).sum()),common_A0_error_mm=stats(baseq['dz'][common]),common_derived_error_mm=stats(q['dz'][common]));row.update(group=g,arm=arm,comparison=mode);pairs.append(row);rows.append(row);errors.extend(e)
    if rows:
     N=sum(x['fixed_N']for x in rows);known=sum(x['known_N']for x in rows);summ.append(dict(group=g,arm=arm,comparison=mode,source_N=len(aaa),target_N=len(held)if mode=='independent_HERO_HOLDOUT'else len(aaa),ordered_pairs=len(rows),fixed_N=N,known_N=known,known_fraction=known/N,**{k+'_fraction':sum(x[k]for x in rows)/N for k in ['support_N','front_proxy_N','deeper_N','CAD_occluded_N','bad_target_CAD_N','UNKNOWN_N']},effective_error_mm=stats(errors),fixed_10mm_penalty_mm=sum(x['fixed_10mm_penalty_sum']for x in rows)/N,normal_occlusion_not_error=True,absolute_accuracy='NOT_EVALUABLE',numeric_proposals_not_all_validated=arm.startswith('A2')))
   for a in aaa:
    F=a['m']['F'];V=a['V'];used=np.unique(F);area=trimesh.triangles.area(V[F]);orig=trimesh.triangles.area(a['m']['V'][F]);edges=np.unique(np.sort(np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],axis=1),axis=0);l=np.linalg.norm(V[edges[:,0]]-V[edges[:,1]],axis=1);l0=np.linalg.norm(a['m']['V'][edges[:,0]]-a['m']['V'][edges[:,1]],axis=1);source_quality.append(dict(group=g,arm=arm,source=a['id'],available=a['available'],faces_N=len(F),retained_face_ratio=1.,original_area_mm2=float(orig.sum()),derived_area_mm2=float(area.sum())if a['available']else None,edge_change_mm=stats(l-l0)if a['available']else stats([]),no_face_deletion=True,original_pixel_identity=True))
    # Partial native patch into protected real RGB views. Fixed foreground denominator.
    if a['available']:mesh=scene(V,F)
    for v,cache,rz in viewcache:
     target=cache['labels']==1;pred=np.zeros_like(target)
     if a['available']:z=cast(mesh,cache['K'],cache['T'],*target.shape);pred=np.isfinite(z)&(z<rz-.05)
     inter=int((pred&target).sum());pn=int(pred.sum());tn=int(target.sum());projection.append(dict(group=g,arm=arm,source=a['id'],view=v['id'],role=v['role'],duplicate_current_FIT_RGB_sources=v.get('duplicate_current_FIT_RGB_sources',[]),available=a['available'],target_foreground_N=tn,predicted_N=pn,intersection_N=inter,partial_patch_IoU=inter/max(1,int((pred|target).sum()))if a['available']else None,fixed_foreground_coverage=inter/max(1,tn)if a['available']else None,precision=inter/max(1,pn)if a['available']else None,boundary_px=boundary_stats(pred,target),interpretation='partial HERO patch projection, not complete-body reconstruction'))
   print('EVALUATED',g,arm,flush=True)
  save('metrics/'+g+'_PROGRESS.json',dict(completed=True,held_native_sources=len(held),protected_views=len(viewcache)))
 save('metrics/HOLDOUT_IDENTITY_AUDIT.json',hold_identity);save('metrics/VALIDATION.json',validation);table('metrics/VALIDATION.csv',flat);save('metrics/COMPARISON.json',summ);table('metrics/COMPARISON.csv',summ);save('metrics/PER_PAIR.json',pairs);table('metrics/PER_PAIR.csv',pairs);save('metrics/PARTIAL_HERO_REPROJECTION.json',projection);table('metrics/PARTIAL_HERO_REPROJECTION.csv',projection);save('metrics/SOURCE_SHAPE_RETENTION.json',source_quality);table('metrics/SOURCE_SHAPE_RETENTION.csv',source_quality);save('provenance/INDEPENDENT_EVALUATION_COMPLETED.json',dict(epoch=time.time(),predictions_frozen=asset(R/'provenance/ALL_REAL_PREDICTIONS_FROZEN.json'),cases=4,real_GT_used=False));print('ALL_EVALUATED',flush=True)
if __name__=='__main__':main()
