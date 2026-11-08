"""Independent symmetric body-only SE(3) evaluation, no learned/prediction parameters.
96 fixed proper rotation seeds. One selected pose serves all geometric metrics.
"""
from common import *
from evaluate import area_samples,distance,occupied,pointcast
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist
from scipy.stats import qmc
import itertools,open3d as o3d
EVAL_LABEL='After Ring-based Metric Recovery and Best 6-DoF Rigid Alignment'
def frames():
 out=[]
 for order in itertools.permutations(range(3)):
  for s in itertools.product([-1.,1.],repeat=3):
   A=np.eye(3)[:,order]@np.diag(s)
   if np.linalg.det(A)>.5:out.append(A)
 u=qmc.Sobol(3,scramble=True,seed=20261108).random_base2(7)[:72];q=np.c_[np.sqrt(1-u[:,0])*np.sin(2*np.pi*u[:,1]),np.sqrt(1-u[:,0])*np.cos(2*np.pi*u[:,1]),np.sqrt(u[:,0])*np.sin(2*np.pi*u[:,2]),np.sqrt(u[:,0])*np.cos(2*np.pi*u[:,2])];return out+list(Rotation.from_quat(q).as_matrix())
def pca(P):
 w,Q=np.linalg.eigh(np.cov(P.T));Q=Q[:,np.argsort(w)[::-1]]
 if np.linalg.det(Q)<0:Q[:,-1]*=-1
 return Q
def apply(P,T):return P@T[:3,:3].T+T[:3,3]
def rigid(A,B):
 ca=A.mean(0);cb=B.mean(0);U,s,V=np.linalg.svd((A-ca).T@(B-cb));rot=V.T@np.diag([1.,1.,np.linalg.det(V.T@U.T)])@U.T;T=np.eye(4);T[:3,:3]=rot;T[:3,3]=cb-rot@ca;return T
def interpolate(T,U,a):
 D=U[:3,:3]@T[:3,:3].T;R=Rotation.from_rotvec(a*Rotation.from_matrix(D).as_rotvec()).as_matrix()@T[:3,:3];W=np.eye(4);W[:3,:3]=R;W[:3,3]=(1-a)*T[:3,3]+a*U[:3,3];return W
def align(V,F,GV,GF,D):
 P=area_samples(V,F,2048);G=area_samples(GV,GF,2048);pr=scene(V,F);gr=scene(GV,GF);A=pca(P);B=pca(G);pc=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(P));gc=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(G));starts=[]
 def score(T,P=P,G=G):
  dp=distance(gr,apply(P,T));Y=(G-T[:3,3])@T[:3,:3];dg=distance(pr,Y);return float(.5*(dp.mean()+dg.mean())),float(dp.mean()),float(dg.mean())
 for i,S in enumerate(frames()):
  rot=B@S@A.T;T=np.eye(4);T[:3,:3]=rot;T[:3,3]=G.mean(0)-rot@P.mean(0)
  for ratio in [.5,.25]:
   result=o3d.pipelines.registration.registration_icp(pc,gc,ratio*D,T,o3d.pipelines.registration.TransformationEstimationPointToPoint(with_scaling=False),o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=30));T=result.transformation.copy()
  val,dp,dg=score(T);starts.append(dict(start=i,coarse_score_mm=val,coarse_T=T,pred_to_GT=dp,GT_to_pred=dg))
 # Genuine two-direction closest-surface correspondences in the optimization,
 # rather than ranking a one-direction ICP by a symmetric score.
 P=area_samples(V,F,8192);G=area_samples(GV,GF,8192);refined=[]
 for rec in sorted(starts,key=lambda x:x['coarse_score_mm'])[:8]:
  T=rec['coarse_T'].copy();old=score(T,P,G)[0];hist=[old]
  for it in range(50):
   X=apply(P,T);cp=gr.compute_closest_points(o3d.core.Tensor(X.astype(np.float32)))['points'].numpy().astype(float);Y=(G-T[:3,3])@T[:3,:3];back=pr.compute_closest_points(o3d.core.Tensor(Y.astype(np.float32)))['points'].numpy().astype(float);U=rigid(np.r_[P,back],np.r_[cp,G]);accepted=False
   for a in [1.,.5,.25,.125,.0625]:
    W=interpolate(T,U,a);val=score(W,P,G)[0]
    if val<=old+1e-8:T=W;old=val;accepted=True;break
   hist.append(old)
   if not accepted:break
  val,dp,dg=score(T,P,G);refined.append(dict(start=rec['start'],score_mm=val,pred_to_GT_mm=dp,GT_to_pred_mm=dg,T=T,history=hist,iterations=len(hist)-1))
 refined.sort(key=lambda x:x['score_mm']);best=refined[0];second=next((x for x in refined[1:]if np.linalg.norm(Rotation.from_matrix(x['T'][:3,:3]@best['T'][:3,:3].T).as_rotvec())>np.radians(1)or np.linalg.norm(x['T'][:3,3]-best['T'][:3,3])>.1),refined[1]);return best['T'],dict(starts=starts,refined=refined,best=best,second=second,score_gap_mm=second['score_mm']-best['score_mm'],globally_optimal_certified=False,scale_fixed=1.,correspondences='equal direction mass bidirectional closest surface, rigidKabsch +monotoneSE3 backtracking')
def feret(V,n):
 n=np.asarray(n,float);n/=np.linalg.norm(n);a=np.eye(3)[np.argmin(abs(n))];u=np.cross(n,a);u/=np.linalg.norm(u);v=np.cross(n,u);P=np.c_[V@u,V@v];h=P[ConvexHull(P).vertices];return float(np.sqrt(pdist(h,'sqeuclidean').max()))
def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--case');args=ap.parse_args();prefix='metrics/eval_case/'+args.case+'_'if args.case else 'metrics/'
 for a in load(R/'assets_index/SCALE_LOCK_BEFORE_GT.json')['files']:assert sha(a['path'])==a['sha256']
 sources={x['case']:x for x in load(R/'evaluation_only/GT_SOURCE_LOCK.json')};scales={x['case']:x for x in load(R/'metrics/RING_SCALE_VALIDATION.json')};native={(x['case'],x['label']):x for x in load(R/'metrics/NATIVE_SUMMARY.json')};rows=[];transforms=[];validity={x['case']:x for x in load(R/'metrics/GT_VALIDITY.json')}
 for c in load(R/'config/CASE_LOCK.json'):
  if args.case and c['name']!=args.case:continue
  n=c['name'];src=sources[n];gtpath=R/'evaluation_only'/n/'ORIGINAL_BLENDER_GT_MM.npz'
  for tag in ['FINAL011','FINAL012','FINAL013']:
   row=dict(case=n,type=c['morphology'],label=tag,target_groups=11,evaluation=EVAL_LABEL,GT_used_for_training=False,scale_changed_by_registration=False,IoU_3D=None,IoU_3D_status='NOT_EVALUABLE',Dxy_AE_mm=None,Dxy_relative_error=None,Chamfer_MAE_mm=None,height_max_AE_mm=None,H95_AE_mm=None,GT_source_status=src['status']);nn=native.get((n,tag),{});row.update(FIT_2D_IoU_original_cameras=nn.get('FIT_IoU'),HOLDOUT_2D_IoU_original_cameras=nn.get('HOLDOUT_IoU'))
   path=R/'local_results/metric'/n/(tag+'.npz')
   if not gtpath.exists()or not path.exists():row['not_evaluable_reason']=src.get('reason','NO_SOURCE');rows.append(row);continue
   out=R/'local_results/aligned'/n;out.mkdir(parents=True,exist_ok=True);cache=R/'metrics/alignment'/(n+'_'+tag+'_STARTS.json');aligned=out/(tag+'.npz');z=np.load(path);g=np.load(gtpath);V,F,Fs=z['V'],z['F'],z['F_solid'];GV,GF=g['V'],g['F']
   if aligned.exists()and cache.exists():T=np.load(aligned)['T'];trials=load(cache)
   else:
    T,trials=align(V,F,GV,GF,scales[n]['diameter_true_mm']);save(cache,trials)
   assert np.linalg.det(T[:3,:3])>.999999 and np.allclose(T[:3,:3].T@T[:3,:3],np.eye(3),atol=1e-8);AV=apply(V,T);np.savez_compressed(aligned,V=AV,F=F,F_solid=Fs,inferred_base_faces=z['inferred_base_faces'],T=T);trimesh.Trimesh(AV,Fs,process=False).export(out/(tag+'_mm.ply'));transforms.append(dict(case=n,label=tag,T=T,R=T[:3,:3],t_mm=T[:3,3],det_R=np.linalg.det(T[:3,:3]),scale=1.,best_score=trials['best']['score_mm'],second_score=trials['second']['score_mm'],second_T=trials['second']['T'],score_gap=trials['score_gap_mm'],evaluation=EVAL_LABEL))
   pr=scene(AV,F);gr=scene(GV,GF);P=area_samples(AV,F,8192);G=area_samples(GV,GF,8192);dp=distance(gr,P);dg=distance(pr,G);st=stats(np.r_[dp,dg]);row.update(Chamfer_MAE_mm=st['MAE'],Chamfer_median_mm=st['median'],Chamfer_p95_mm=st['p95'],Chamfer_max_mm=st['maximum'],prediction_to_GT_mm=stats(dp),GT_to_prediction_mm=stats(dg),not_evaluable_reason='',prediction_visible_eligible_faces=len(F),inferred_cap_faces=int(z['inferred_base_faces'].sum()))
   ev=R/'local_results/native_eval'/n/(tag+'_FACE_EVIDENCE.npz')
   if ev.exists():
    evidence=np.load(ev)['face_supported'];fid=pr.compute_closest_points(o3d.core.Tensor(P.astype(np.float32)))['primitive_ids'].numpy().astype(int);support=evidence[np.clip(fid,0,len(evidence)-1)];row.update(observation_supported_proxy_to_GT_mm=stats(dp[support]),unobserved_or_unverified_back_to_GT_mm=stats(dp[~support]),supported_surface_sample_N=int(support.sum()),unverified_surface_sample_N=int((~support).sum()))
   capfaces=Fs[z['inferred_base_faces']]
   if len(capfaces):row['inferred_bottom_to_GT_mm']=stats(distance(gr,area_samples(AV,capfaces,1024)))
   rr=np.load(R/'inputs'/n/'RING.npz');ringrt=scene(rr['V'],rr['F']);GT_ring=(GV-T[:3,3])@T[:3,:3];GT_samples_ring=(G-T[:3,3])@T[:3,:3];g_original=scene(GT_ring,GF);gsupport=np.zeros(len(G),bool)
   for v in c['views']:
    if v['role']!='FIT':continue
    a=np.load(R/'inputs'/n/(v['id']+'.npz'));uv,zz,rz=pointcast(ringrt,GT_samples_ring,a['K'],a['T']);_,_,gz=pointcast(g_original,GT_samples_ring,a['K'],a['T']);inside=(zz>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360);ix=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);gsupport|=inside&(a['labels'][ix[:,1],ix[:,0]]==1)&(zz<rz)&(abs(zz-gz)<.05)
   row.update(GT_supported_under_best_pose_to_prediction_mm=stats(dg[gsupport]),GT_unverified_under_best_pose_to_prediction_mm=stats(dg[~gsupport]),GT_best_pose_supported_sample_N=int(gsupport.sum()),surface_evidence='Frozen FIT cameras/Mask/CAD + first-ray visibility; evidence proxy not anatomical truth. No subset used for pose ranking.')
   for tol in [.1,.25,.5,1.]:
    precision=float((dp<=tol).mean());recall=float((dg<=tol).mean());row['surface_precision_'+str(tol)+'mm']=precision;row['surface_recall_'+str(tol)+'mm']=recall;row['surface_Fscore_'+str(tol)+'mm']=2*precision*recall/max(1e-20,precision+recall)
   row['surface_overlap_proxy_0.5mm']=row['surface_Fscore_0.5mm'];row['surface_proxy_definition']='toleranceFscore; NOT solidIoU, works for open/selfintersectingGT';base=src.get('author_base')
   if base is not None:
    normal=np.asarray(base['normal'],float);normal/=np.linalg.norm(normal);offset=float(base['offset_mm']);h=AV@normal+offset;gh=GV@normal+offset;dx,gx=feret(AV,normal),feret(GV,normal);H,GH=float(h.max()),float(gh.max());h95=float(np.quantile(P@normal+offset,.95));g95=float(np.quantile(G@normal+offset,.95));row.update(Dxy_GT_mm=gx,Dxy_pred_mm=dx,Dxy_AE_mm=abs(dx-gx),Dxy_relative_error=abs(dx-gx)/gx,height_max_GT_mm=GH,height_max_pred_mm=H,height_max_AE_mm=abs(H-GH),height_max_relative_error=abs(H-GH)/max(1e-20,abs(GH)),H95_GT_mm=g95,H95_pred_mm=h95,H95_AE_mm=abs(h95-g95),H95_relative_error=abs(h95-g95)/max(1e-20,abs(g95)),lowest_point_vs_author_base_mm=float(h.min()),prediction_top_to_bottom_span_mm=float(np.ptp(h)),GT_top_to_bottom_span_mm=float(np.ptp(gh)),base_status=base['qualification'],base_evidence=base['evidence'])
   elif src.get('author_reference_axis') is not None:
    normal=np.asarray(src['author_reference_axis'],float);normal/=np.linalg.norm(normal);dx,gx=feret(AV,normal),feret(GV,normal);row.update(Dxy_GT_mm=gx,Dxy_pred_mm=dx,Dxy_AE_mm=abs(dx-gx),Dxy_relative_error=abs(dx-gx)/gx,base_status='NOT_EVALUABLE_NO_AUTHORED_BASE',height_not_evaluable_reason=src.get('height_reason'),prediction_top_to_bottom_span_mm=float(np.ptp(AV@normal)),GT_top_to_bottom_span_mm=float(np.ptp(GV@normal)),Dxy_reference='conditional nativeauthorXY projection, no anatomicalbase claim',lowest_point_vs_author_base_mm=None)
   pm=trimesh.Trimesh(AV,Fs,process=False);gm=trimesh.Trimesh(GV,GF,process=False);pv=next((x for x in load(R/'metrics/POST_GEOMETRY_VALIDITY.json')if x['case']==n and x['label']==tag),{});valid=pm.is_watertight and gm.is_watertight and pm.is_winding_consistent and gm.is_winding_consistent and pv.get('self_intersections_N',-1)==0 and validity[n].get('GT_self_intersections_N',-1)==0;row.update(pred_watertight=bool(pm.is_watertight),GT_watertight=bool(gm.is_watertight),pred_self_N=pv.get('self_intersections_N'),GT_self_N=validity[n].get('GT_self_intersections_N'))
   if valid:
    lo=np.minimum(AV.min(0),GV.min(0));hi=np.maximum(AV.max(0),GV.max(0));Q=lo+(hi-lo)*qmc.Sobol(3,scramble=True,seed=20261108).random_base2(17);op=occupied(scene(AV,Fs),Q);og=occupied(gr,Q);inter=int((op&og).sum());union=int((op|og).sum());iou=inter/max(1,union);row.update(conditional_occupancy_IoU=iou,occupancy_N=len(Q),occupancy_intersection_N=inter,occupancy_union_N=union,occupancy_note='Sobol sampled occupancy estimate; inferredbase conditional')
    if not z['inferred_base_faces'].any()and src.get('GT_geometry_complete',False):row.update(IoU_3D=iou,IoU_3D_status='VALID_SOLID_SAMPLED_ESTIMATE')
    else:row['IoU_3D_status']='NOT_EVALUABLE_STRICT_INFERRED_OR_UNCERTAIN_BASE'
   else:row['IoU_3D_status']='NOT_EVALUABLE_ENTITY_VALIDITY'
   rows.append(row);save(prefix+'BLENDER_GEOMETRIC_METRICS_PARTIAL.json',rows);print('BEST_RIGID',n,tag,'chamfer',row['Chamfer_MAE_mm'],'Dxy',row['Dxy_AE_mm'],flush=True)
 save(prefix+'BLENDER_GEOMETRIC_METRICS.json',rows);table(prefix+'BLENDER_GEOMETRIC_METRICS.csv',rows);save(prefix+'BLENDER_RIGID_ALIGNMENT.json',transforms);table(prefix+'BLENDER_RIGID_ALIGNMENT.csv',transforms)
if __name__=='__main__':main()
