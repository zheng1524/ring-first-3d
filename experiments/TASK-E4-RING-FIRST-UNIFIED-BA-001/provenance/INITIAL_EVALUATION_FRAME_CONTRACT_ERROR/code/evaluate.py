"""Independent images/features after main camera freeze; no GT or HERO used here."""
from joint_ba import *
from stage_a import ray_scene
import open3d as o3d

def contour(mask):
 cs,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE);return np.concatenate([c[:,0]for c in cs]).astype(float)if cs else np.empty((0,2))
def contour_stats(a,b):
 p,q=contour(a),contour(b);return stats(np.r_[cKDTree(p).query(q)[0],cKDTree(q).query(p)[0]])if len(p)and len(q)else stats([])
def cast(scene,C,K,h=360,w=640):
 y,x=np.mgrid[:h,:w];r=np.c_[x.ravel(),y.ravel(),np.ones(h*w)]@np.linalg.inv(K).T;z=scene.cast_rays(o3d.core.Tensor(np.c_[np.broadcast_to(C[:3,3],r.shape),r@C[:3,:3].T].astype(np.float32)))['t_hit'].numpy().reshape(h,w);return z

def getresults():
 out={}
 for g in GROUPS:
  for m in METHODS:
   final=N/'results'/g/m/'FINAL.json';decision=final.parent/'NOT_RUN_FINAL_DECISION.json'
   if final.exists():out[g,m]=load(decision if m=='B4'and decision.exists()else final)
 return out
def getpose(results,g,m,cid):
 r=results.get((g,m),{});ps=r.get('poses');return None if not ps or cid not in ps else np.array(ps[cid])
def skew_np(t):x,y,z=t;return np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
def epi(a,b,Ka,Kb,u,v):
 D=np.linalg.inv(b)@a;F=np.linalg.inv(Kb).T@skew_np(D[:3,3])@D[:3,:3]@np.linalg.inv(Ka);p=np.r_[u,1];q=np.r_[v,1];fp=F@p;fq=F.T@q;return float(q@fp/max(np.sqrt(np.sum(fp[:2]**2+fq[:2]**2)),1e-15))

def camera_metrics():
 for g in GROUPS:checkfreeze('provenance/'+g+'_MAIN_POSES_FROZEN.json')
 results=getresults();views=load(N/'config/VIEWS.json');vd={v['id']:v for v in views};tracks=load(N/'config/TRACKS.json');by=collections.defaultdict(list)
 for t in tracks:
  for o in t['observations']:by[o['view']].append((t,o))
 ring={g:ray_scene(next(v['ring_path']for v in views if v['group']==g))[0]for g in GROUPS};rows=[];features={};localimages=N/'local_results/IMAGE_AUDIT';localimages.mkdir(exist_ok=True)
 for v in views:
  d=np.load(v['cache']);K=np.array(v['K']);obs,ar=qualified(v);lab=d['labels'];rgb=load(N/'inputs'/v['id']/'RGB_GEOMETRY.json')
  for method in ['B0','B1','B2','B3']:
   r=results[v['group'],method];C=getpose(results,v['group'],method,v['id']);rec=dict(group=v['group'],video=v['video'],id=v['id'],role=v['role'],method=method,status=r['status'],C=C,physical_unit='mm',pixel_grid='640x360 integercenter',direct_GT_accuracy='NOT_EVALUABLE',actual_pixels=lab.size)
   if C is None:rec.update(Ring_IoU=None);rows.append(rec);continue
   cr=curves(C,K);rz=cast(ring[v['group']],C,K);known=lab!=1;pred=np.isfinite(rz)&known;target=lab==2;inter=int((pred&target).sum());union=int((pred|target).sum());R0=np.array(v['T']);dc=np.linalg.norm(C[:3,3]-R0[:3,3]);dr=np.degrees(Rotation.from_matrix(C[:3,:3]@R0[:3,:3].T).magnitude());rec.update(Ring_IoU=inter/max(1,union),Ring_intersection_N=inter,Ring_union_N=union,Ring_known_N=int(known.sum()),Ring_contour_px=contour_stats(pred,target),center_change_mm=float(dc),rotation_change_deg=float(dr),scale_singular_values=np.linalg.svd(C[:3,:3],compute_uv=False),minimum_Ring_depth_mm=float(((cr['X'].reshape(-1,3)-C[:3,3])@C[:3,:3])[:,2].min()))
   for key in ['inner','outer']:
    j,t,dd=nearest(obs[key],cr[key]);rec[key+'_px']=stats(dd);rec[key+'_actual_visible_N']=len(obs[key]);rec[key+'_unknown_N']=len(obs[key+'_unknown']);bins=np.unique(np.floor((j+t)/1024*72).astype(int));rec[key+'_visible_phase_coverage_proxy']=len(bins)/72
   for trackrole in ['TRACK_FIT','TRACK_HELD']:
    err=[];nused=0
    for t,o in by[v['id']]:
     if t['role']!=trackrole:continue
     X=np.array(r.get('X',{}).get(str(t['track_id']),t['X0']));uv,z=projection(X[None],C,K);err.extend(np.linalg.norm(uv-np.array(o['uv']),axis=1));nused+=int(trackrole=='TRACK_FIT'and v['role']=='FIT'and (method!='B2'or t['cross_video']))
    rec[trackrole+'_reprojection_px']=stats(err);rec[trackrole+'_actually_used_N']=nused if method!='B0'else 0
   # Additional existing descriptor-held matches include protected image cameras.
   errs=[];epis=[]
   for m in [m for m in rgb['matches']if m['role']=='FEATURE_HELD']:
    X=np.array(m['X']);
    if v['group']=='G01'and v['video']=='005':
     H21=np.array(load(P/'results/B3.json')['T']);H0=np.array(load(N/'config/H0.json')['G01_005_to004']);D=H0@np.linalg.inv(H21);X=X@D[:3,:3].T+D[:3,3]
    uv,z=projection(X[None],C,K);errs.extend(np.linalg.norm(uv-np.array(m['uv']),axis=1));ref=vd[m['descriptor_source']];Cr=getpose(results,ref['group'],method,ref['id'])
    if Cr is None:continue
    sid=ref['id']
    if sid not in features:features[sid]=np.load(N/'features'/(sid+'.npz'))['xy']
    u=features[sid][m['source_feature_id']];epis.append(epi(Cr,C,np.array(ref['K']),K,u,m['uv']))
   rec['descriptor_HELD_reprojection_px']=stats(errs);rec['descriptor_HELD_epipolar_px']=stats(epis);rec['HOLDOUT_local_fit']=False;rows.append(rec)
   if v['id']==next(x['id']for x in views if x['group']==v['group']and x['role']=='FIT'):np.savez_compressed(localimages/(v['group']+'_'+method+'.npz'),RGB=d['RGB'],labels=lab,ring_pred=np.isfinite(rz),inner=cr['inner'],outer=cr['outer'],inner_obs=obs['inner'],outer_obs=obs['outer'],unknown=np.r_[obs['inner_unknown'],obs['outer_unknown']])
  print('CAMERA_EVAL',v['id'],flush=True)
 save('metrics/PER_VIEW_CAMERA_GEOMETRY.json',rows);table('metrics/PER_VIEW_CAMERA_GEOMETRY.csv',rows);summ=[]
 for g in GROUPS:
  for method in ['B0','B1','B2','B3']:
   for role in ['FIT','HOLDOUT']:
    allr=[r for r in rows if r['group']==g and r['method']==method and r['role']==role];rr=[r for r in allr if r.get('Ring_IoU')is not None];x=dict(group=g,method=method,role=role,target_N=len(allr),numeric_N=len(rr))
    for key in ['Ring_IoU','center_change_mm','rotation_change_deg']:x[key]=float(np.mean([r[key]for r in rr]))if rr else None
    for key in ['inner_px','outer_px','TRACK_FIT_reprojection_px','TRACK_HELD_reprojection_px','descriptor_HELD_reprojection_px','descriptor_HELD_epipolar_px']:
     vals=[r[key]['MAE']for r in rr if r[key]['N']];x[key+'_MAE_macro']=float(np.mean(vals))if vals else None;x[key+'_observations_N']=sum(r[key]['N']for r in rr)
    summ.append(x)
 save('metrics/FOUR_GROUP_POSE_SCORECARD.json',summ);table('FOUR_GROUP_POSE_SCORECARD.csv',summ);print('CAMERA_METRICS_COMPLETE',flush=True)
if __name__=='__main__':camera_metrics()
