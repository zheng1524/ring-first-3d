"""All prediction poses frozen first; body, protected views and HERO are evaluation only."""
from common import *
from ring020 import RingRenderer,tensor,torch
from objective020 import SymmetricFeatures
from scipy.spatial.transform import Rotation
import features019 as feat
import open3d as o3d
P19=REPO/'experiments/TASK-E4-RING-POLYP-REGISTRATION-019';P18=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018'

def visibility_query(X,T,K,target,ring):
 # Reuse019 projection/ray convention, additionally reject an unreliable target
 # depth already behind CAD. It cannot certify free space in front of itself.
 p=(X-T[:3,3])@T[:3,:3];q=p@K.T
 with np.errstate(divide='ignore',invalid='ignore'):uv=q[:,:2]/q[:,2:]
 safe=np.where(np.isfinite(uv),uv,-1e9);ij=np.floor(safe+.5).astype(int);h,w=target.shape;inside=(p[:,2]>0)&(ij[:,0]>=0)&(ij[:,0]<w)&(ij[:,1]>=0)&(ij[:,1]<h);dep=np.full(len(X),np.nan);dep[inside]=target[ij[inside,1],ij[inside,0]];known=inside&np.isfinite(dep);ids=np.flatnonzero(known);cad=np.full(len(X),np.inf)
 if len(ids):
  ray=np.c_[uv[ids],np.ones(len(ids))]@np.linalg.inv(K).T;rs=np.c_[np.broadcast_to(T[:3,3],ray.shape),ray@T[:3,:3].T].astype(np.float32);cad[ids]=ring.cast_rays(o3d.core.Tensor(rs))['t_hit'].numpy()
 occ=known&(p[:,2]>=cad-.05);bad_target=known&(dep>=cad-.05);known&=~occ&~bad_target;dz=p[:,2]-dep;return dict(known=known,cad_occluded=occ,target_Ring_order_unreliable=bad_target&~occ,supported=known&(abs(dz)<=.5),front=known&(dz<-.5),behind=known&(dz>.5),dz=dz)

def methods():
 rows=[dict(method=k,T=load(R/'results'/(k+'.json'))['T'])for k in ['R0','R1','R2','R3','R3_MASK_ONLY','R3_INNER_OUTER','R4']]
 h=load(R/'config/HISTORICAL_CANDIDATES.json');rows+=[dict(method='HISTORY_LIGHTGLUE',T=next(x['T']for x in h if x['tag']=='HISTORICAL_FULL_LightGlue')),dict(method='019_A5',T=load(P19/'results/CROSS_A5_FINAL.json')['T']),dict(method='NAMED_3D_DIAGNOSTIC_NOT_ADOPTED',T=load(R/'metrics/NAMED_LANDMARK_RIGID_PROPOSAL.json')['T'])];return rows
def contour_stats(a,b):
 p,q=contour(a),contour(b);return stats(np.r_[cKDTree(p).query(q)[0],cKDTree(q).query(p)[0]])if len(p)and len(q)else stats([])

def held_features(vv):
 feat.VIEWS={v['id']:v for v in vv};fit5=[v['id']for v in vv if v['video']=='005'and v['role']=='FIT'];hold4=[v['id']for v in vv if v['video']=='004'and v['role']=='HOLDOUT']
 for n in ['CROSS_HOLDOUT_PNP.json','CROSS_HOLDOUT_EPI.json','NEGATIVE_HOLDOUT_PNP.json','NEGATIVE_HOLDOUT_EPI.json']:
  dest=R/'features'/n
  if not dest.exists():dest.write_bytes((P19/'features'/n).read_bytes())
 if not(R/'features/REVERSE_HOLDOUT_PNP.json').exists():feat.cross(fit5,hold4,dict(np.load(R/'landmarks/INDEPENDENT_005.npz')),'REVERSE_HOLDOUT')
 n=load(R/'config/NEGATIVE_SPLIT.json')
 if not(R/'features/NEGATIVE_REVERSE_HOLDOUT_PNP.json').exists():feat.cross(n['target_fit'],n['target_holdout'],dict(np.load(R/'landmarks/NEGATIVE_LATE_004.npz')),'NEGATIVE_REVERSE_HOLDOUT')

def body_ring_eval():
 vv=load(R/'config/VIEWS.json');targets=[v for v in vv if v['video']=='005'];held_features(vv);a=np.load(R/'inputs/G01/BODY018.npz');ring=np.load(R/'inputs/G01/RING.npz');body=scene(a['V'],a['F']);cad=scene(ring['V'],ring['F']);rr=RingRenderer([v['id']for v in targets]);per=[];sift=[];summary=[]
 for method in methods():
  tag=method['method'];H=np.asarray(method['T']);folder=R/'evaluation'/tag;folder.mkdir(parents=True,exist_ok=True)
  for v in targets:
   d=np.load(v['cache']);C=H@d['T'];z=cast(body,d['K'],C,360,640);rz=cast(cad,d['K'],C,360,640);pred=np.isfinite(z)&(z<rz);target=d['labels']==1;union=(pred|target).sum();known=d['labels']!=1;ringpred=np.isfinite(rz)&known;ringtarget=d['labels']==2
   with torch.no_grad():loss,aux,_=rr.losses(tensor(H,torch.float64),v['id'])
   x=dict(method=tag,view=v['id'],role=v['role'],IoU=float((pred&target).sum()/max(1,union)),contour_px=contour_stats(pred,target),foreground_coverage=float((pred&target).sum()/max(1,target.sum())),extra_fraction=float((pred&~target).sum()/max(1,pred.sum())),Ring_known_IoU=float((ringpred&ringtarget).sum()/max(1,(ringpred|ringtarget).sum())),Ring_M=float(loss['M']),Inner_px=aux['I'].get('distance_px',stats([])),Mid_px=aux['C']['distance_px'],Outer_px=aux['O'].get('distance_px',stats([])),Inner_N=aux['I']['N'],Outer_N=aux['O']['N'],Mid_dual_N=aux['C']['dual'],Mid_single_N=aux['C']['single'],Mid_unknown_N=aux['C']['unknown']);per.append(x);np.savez_compressed(folder/(v['id']+'.npz'),pred=pred,body_z_mm=z,Ring_z_mm=rz)
  fwd=np.eye(4);delta=H@np.linalg.inv(np.asarray(load(R/'results/R0.json')['T']));r=dict(method=tag,T=H,Ring_center_mm=float(np.linalg.norm(H[:3,3])),Ring_normal_tilt_deg=float(np.degrees(np.arccos(np.clip(abs(H[2,2]),-1,1)))),correction_from_RoMa_translation_mm=float(np.linalg.norm(delta[:3,3])),correction_from_RoMa_rotation_deg=float(np.degrees(Rotation.from_matrix(delta[:3,:3]).magnitude())),scale_singular_values=np.linalg.svd(H[:3,:3],compute_uv=False))
  for role in ['FIT','HOLDOUT']:
   rows=[x for x in per if x['method']==tag and x['role']==role];r[role+'_N']=len(rows);r[role+'_IoU']=float(np.mean([x['IoU']for x in rows]));r[role+'_worst_IoU']=min(x['IoU']for x in rows)
   for key in ['Inner_px','Mid_px','Outer_px','contour_px']:r[role+'_'+key+'_MAE']=float(np.mean([x[key]['MAE']for x in rows if x[key]['N']]))
   for key in ['Ring_M','Ring_known_IoU']:r[role+'_'+key]=float(np.mean([x[key]for x in rows]))
   sf=SymmetricFeatures('CROSS',held=role=='HOLDOUT')
   with torch.no_grad():F,E,report=sf.evaluate(tensor(H,torch.float64),details=True)
   sift.append(dict(method=tag,role=role,normalized_symmetric_F=float(F),normalized_E=float(E),**report))
  summary.append(r);print('EVAL020',tag,r['FIT_IoU'],r['HOLDOUT_IoU'],flush=True)
 save('metrics/REGISTRATION_COMPARISON.json',summary);table('metrics/REGISTRATION_COMPARISON.csv',summary);save('metrics/ALL005_FRAME_METRICS.json',per);table('metrics/ALL005_FRAME_METRICS.csv',per);save('metrics/SYMMETRIC_SIFT_EVALUATION.json',sift);table('metrics/SYMMETRIC_SIFT_EVALUATION.csv',sift)

def hero_eval():
 # Exact019 native-source set registered before evaluation; no substitute views.
 import importlib.util
 spec=importlib.util.spec_from_file_location('hero019_readonly',P19/'code/hero_diagnosis019.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
 rows=load(R/'config/HERO_EVALUATION_SOURCES.json');data=[]
 for s in rows:
  assert sha(s['observation']['path'])==s['observation']['sha256'];a=dict(np.load(s['observation']['path']));m=dict(np.load(s['mesh']['path']));grid=np.full(tuple(a['native_shape']),np.nan);grid[a['uv'][:,1],a['uv'][:,0]]=a['z'];data.append(dict(id=s['id'],video=s['video'],role=s['role'],obs=a,grid=grid,mesh=m))
 rv=np.load(R/'inputs/G01/RING.npz');cad=scene(rv['V'],rv['F']);per=[];areas=[]
 for meth in methods():
  H=np.asarray(meth['T']);trans=[]
  for d in data:
   a=d['obs'];G=H if d['video']=='005'else np.eye(4);trans.append(d|dict(X=a['X']@G[:3,:3].T+G[:3,3],C=G@a['T'],G=G))
  for a in trans:
   m=a['mesh'];cent=m['V'][m['F']].mean(1)@a['G'][:3,:3].T+a['G'][:3,3];fa=trimesh.triangles.area(m['V'][m['F']]);support=np.zeros(len(fa),bool);known=np.zeros(len(fa),bool);behind=np.zeros(len(fa),bool)
   for b in trans:
    if a['video']==b['video']:continue
    o=visibility_query(a['X'],b['C'],b['obs']['K'],b['grid'],cad);N=len(a['X']);per.append(dict(method=meth['method'],source=a['id'],target=b['id'],source_role=a['role'],target_role=b['role'],fixed_source_N=N,known_N=int(o['known'].sum()),supported_N=int(o['supported'].sum()),front_proxy_N=int(o['front'].sum()),behind_N=int(o['behind'].sum()),CAD_occluded_N=int(o['cad_occluded'].sum()),target_Ring_order_unreliable_N=int(o['target_Ring_order_unreliable'].sum()),unknown_N=int((~o['known']&~o['cad_occluded']).sum()),known_axial_difference_mm=stats(o['dz'][o['known']]),front_not_physical_error_GT=True,behind_is_not_free_space_conflict=True));q=visibility_query(cent,b['C'],b['obs']['K'],b['grid'],cad);support|=q['supported'];known|=q['known'];behind|=q['behind']
   areas.append(dict(method=meth['method'],source=a['id'],TRUSTED_area_mm2=float(fa.sum()),supported_centroid_area_proxy_mm2=float(fa[support].sum()),unobserved_centroid_area_proxy_mm2=float(fa[~known].sum()),deeper_centroid_area_proxy_mm2=float(fa[behind&~support].sum()),not_unique_union=True,not_certified_complementary_geometry=True))
  print('HERO020',meth['method'],flush=True)
 agg=[]
 for m in methods():
  x=[a for a in per if a['method']==m['method']];N=sum(a['fixed_source_N']for a in x);known=sum(a['known_N']for a in x);agg.append(dict(method=m['method'],source_count=len(data),ordered_cross_source_target_pairs=len(x),fixed_source_target_observation_denominator=N,known_N=known,support_fraction_fixed=sum(a['supported_N']for a in x)/N,front_proxy_fraction_fixed=sum(a['front_proxy_N']for a in x)/N,behind_fraction_fixed=sum(a['behind_N']for a in x)/N,Ring_occluded_fraction_fixed=sum(a['CAD_occluded_N']for a in x)/N,unknown_fraction_fixed=sum(a['unknown_N']for a in x)/N,known_MAE_mm=sum(a['known_axial_difference_mm']['MAE']*a['known_N']for a in x if a['known_N'])/max(1,known),not_unique_surface_samples=True))
 save('metrics/HERO_INDEPENDENT_PER_PAIR.json',per);table('metrics/HERO_INDEPENDENT_PER_PAIR.csv',per);save('metrics/HERO_INDEPENDENT_AGGREGATE.json',agg);table('metrics/HERO_INDEPENDENT_AGGREGATE.csv',agg);save('metrics/HERO_CENTROID_AREA_PROXIES.json',areas);table('metrics/HERO_CENTROID_AREA_PROXIES.csv',areas)

def negative_eval():
 n=load(R/'config/NEGATIVE_SPLIT.json');vv={v['id']:v for v in load(R/'config/VIEWS.json')};ids=n['target_fit']+n['target_holdout'];rr=RingRenderer(ids);a=np.load(R/'inputs/G01/BODY018.npz');rv=np.load(R/'inputs/G01/RING.npz');body=scene(a['V'],a['F']);cad=scene(rv['V'],rv['F']);rows=[];summary=[]
 for tag,H in [('IDENTITY',np.eye(4)),('NEGATIVE_R3',np.asarray(load(R/'results/NEGATIVE_R3.json')['T']))]:
  for cid in ids:
   v=vv[cid];d=np.load(v['cache']);C=H@d['T'];z=cast(body,d['K'],C,360,640);rz=cast(cad,d['K'],C,360,640);pred=np.isfinite(z)&(z<rz);target=d['labels']==1
   with torch.no_grad():ls,aux,_=rr.losses(tensor(H,torch.float64),cid)
   rows.append(dict(method=tag,view=cid,role=v['role'],IoU=float((pred&target).sum()/max(1,(pred|target).sum())),Inner_px=aux['I']['distance_px']['MAE'],Outer_px=aux['O']['distance_px']['MAE'],Mid_px=aux['C']['distance_px']['MAE'],Ring_M=float(ls['M'])))
  rec=dict(method=tag,T=H,translation_mm=float(np.linalg.norm(H[:3,3])),rotation_deg=float(np.degrees(Rotation.from_matrix(H[:3,:3]).magnitude())))
  for role in ['FIT','HOLDOUT']:
   xx=[x for x in rows if x['method']==tag and x['role']==role];rec[role+'_N']=len(xx)
   for k in ['IoU','Inner_px','Outer_px','Mid_px','Ring_M']:rec[role+'_'+k]=float(np.mean([x[k]for x in xx]))
   with torch.no_grad():F,E,r=SymmetricFeatures('NEGATIVE',held=role=='HOLDOUT').evaluate(tensor(H,torch.float64),details=True)
   rec[role+'_SIFT']=r
  summary.append(rec)
 save('metrics/NEGATIVE_CONTROL.json',summary);table('metrics/NEGATIVE_CONTROL.csv',summary);table('metrics/NEGATIVE_PER_VIEW.csv',rows)

def main():
 p=R/'provenance/ALL_POSES_FROZEN_BEFORE_EVALUATION.json'
 while not p.exists():time.sleep(5)
 for a in load(p)['files']:assert sha(a['path'])==a['sha256']
 body_ring_eval();negative_eval();hero_eval();save('runtime/EVALUATION_COMPLETE.json',dict(epoch=time.time(),body_used_only_after_no_body_freeze=True,HOLDOUT_after_all_pose_freeze=True));print('020_INDEPENDENT_EVALUATION_COMPLETE',flush=True)
if __name__=='__main__':main()
