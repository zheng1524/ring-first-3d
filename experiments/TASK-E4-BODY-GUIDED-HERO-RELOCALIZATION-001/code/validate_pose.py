"""Frozen-candidate validation, not used by the optimizer or candidate ranking."""
from resection import *

def boundary_stats(pred,target):
 p=contour(pred);q=contour(target)
 if not len(p)or not len(q):return dict(N=0,MAE=None,median=None,p95=None,maximum=None)
 return stats(np.r_[cKDTree(p).query(q)[0],cKDTree(q).query(p)[0]])
def ring_metrics(V,F,C,K,labels):
 h,w=labels.shape;rt=scene(V,F);z=cast(rt,K,C,h,w);pred=np.isfinite(z);target=labels==2;known=labels!=1;pp=pred&known;union=(pp|target).sum();cc=cv2.findContours(pp.astype(np.uint8),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE);observed=cv2.findContours(target.astype(np.uint8),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
 def pieces(item):
  contours,hierarchy=item;out={'inner':[],'outer':[]}
  if hierarchy is not None:
   for c,hh in zip(contours,hierarchy[0]):out['inner'if hh[3]>=0 else'outer'].append(c[:,0])
  return {k:np.concatenate(v)if v else np.empty((0,2))for k,v in out.items()}
 pc=pieces(cc);tc=pieces(observed);curve={}
 for k in pc:
  curve[k]=stats(np.r_[cKDTree(pc[k]).query(tc[k])[0],cKDTree(tc[k]).query(pc[k])[0]])if len(pc[k])and len(tc[k])else dict(N=0,MAE=None,median=None,p95=None,maximum=None)
 return dict(IoU=float((pp&target).sum()/max(1,union)),boundary=boundary_stats(pp,target),inner=curve['inner'],outer=curve['outer'],source_ring_pixels=int(target.sum()),known_canvas_pixels=int(known.sum()),data_identity='same Ring observation as fit; independent full CAD raster operator, no unseen-pixel claim')

def held_sift(C,K,refs):
 errors=[];rows=[]
 for v in refs:
  a=np.load(v['match']);ii=a['HOLDOUT_index'];e=abs(sampson(fundamental(C,K,np.array(v['ref_C']),np.array(v['ref_K'])),a['p'][ii],a['q'][ii]));errors.extend(e);rows.append(dict(reference=v['reference'],fixed_N=len(ii),errors=stats(e),baseline_mm=float(np.linalg.norm(C[:3,3]-np.array(v['ref_C'])[:3,3]))))
 return dict(**stats(errors),per_reference=rows,selection='all frozen mutual-descriptor holdout IDs, no pose-based filtering',independent_of_pose_optimization=True)

def validate(rec,record,refs):
 a=np.load(rec['view_cache']);o=np.load(rec['obs']);m=np.load(rec['mesh']);rv=np.load(rec.get('ring_path',str(R/'inputs'/rec['group']/'RING.npz')));C0=np.array(rec['C']);K=np.array(rec['K']);baseline=ring_metrics(rv['V'],rv['F'],C0,K,a['labels']);bg0=held_sift(C0,K,refs);chosen=record['chosen'];reasons=[]
 if chosen is None:return dict(source=rec['id'],group=rec['group'],Body=record['Body'],status='NO_NUMERICAL_CANDIDATE',accepted_H=None,baseline_Ring=baseline,baseline_SIFT=bg0,fixed_native_N=len(o['X']),numerical=False)
 C=np.array(chosen['C']);H=np.array(chosen['H']);r=ring_metrics(rv['V'],rv['F'],C,K,a['labels']);bg=held_sift(C,K,refs);X=transform(o['X'],H);uv0,z0=project(o['X'],C0,K);uv1,z1=project(X,C,K);delta=np.linalg.norm(uv1-uv0,axis=1);cad=rayquery(scene(rv['V'],rv['F']),C,K,uv1)['t_hit'];oldcad=rayquery(scene(rv['V'],rv['F']),C0,K,uv0)['t_hit'];ring=scene(rv['V'],rv['F']);used=np.unique(m['F']);sd0=ring.compute_signed_distance(o3d.core.Tensor(m['V'][used].astype(np.float32)),nsamples=3).numpy();newV=transform(m['V'],H);sd=ring.compute_signed_distance(o3d.core.Tensor(newV[used].astype(np.float32)),nsamples=3).numpy();edges=np.unique(np.sort(np.r_[m['F'][:,[0,1]],m['F'][:,[1,2]],m['F'][:,[2,0]]],axis=1),axis=0);l0=np.linalg.norm(m['V'][edges[:,0]]-m['V'][edges[:,1]],axis=1);l1=np.linalg.norm(newV[edges[:,0]]-newV[edges[:,1]],axis=1);info=chosen['information'];rank=info['rank'];cond=info['condition']
 if rank<6 or cond is None or cond>CFG['information_condition_limit']:reasons.append('INSUFFICIENT_INDEPENDENT_INFORMATION')
 if bg['N']<CFG['independent_min_sift_holdout']:reasons.append('INSUFFICIENT_BACKGROUND_HOLDOUT')
 elif bg['MAE']>CFG['independent_sift_max_MAE_px']or(bg0['MAE']is not None and bg['MAE']>bg0['MAE']+CFG['independent_sift_max_worsening_px']):reasons.append('BACKGROUND_HOLDOUT_CONFLICT')
 if r['boundary']['MAE']is None or baseline['boundary']['MAE']is None:reasons.append('INSUFFICIENT_RING_OBSERVATION')
 elif r['boundary']['MAE']>baseline['boundary']['MAE']+CFG['independent_ring_max_worsening_px']:reasons.append('RING_RASTER_WORSENING')
 if record['ambiguous_alternatives']:reasons.append('DIRECTION_OR_REGION_AMBIGUITY')
 if chosen['region_MAE_mm']>CFG['region_max_MAE_mm']:reasons.append('BODY_REGION_GEOMETRY_UNEXPLAINED')
 if float(sd.min())<min(float(sd0.min()),0)-.05:reasons.append('NEW_OR_WORSENED_HERO_RING_PENETRATION')
 if any(x['baseline_mm']<CFG['sift_baseline_floor_mm']for x in bg['per_reference']if x['fixed_N']):reasons.append('DEGENERATE_BACKGROUND_BASELINE')
 if delta.max()>1e-4 or np.max(abs(l0-l1))>1e-6:reasons.append('PROJECTION_OR_RIGID_SHAPE_CONTRACT')
 status='CONDITIONAL_CONSTRAINT_SUPPORTED'if not reasons else'UNKNOWN'if any(x in reasons for x in ['INSUFFICIENT_INDEPENDENT_INFORMATION','INSUFFICIENT_BACKGROUND_HOLDOUT','DIRECTION_OR_REGION_AMBIGUITY'])else'INDEPENDENT_CONFLICT_OR_UNEXPLAINED'
 return dict(source=rec['id'],group=rec['group'],Body=record['Body'],status=status,reasons=reasons,accepted_H=H if not reasons else None,numerical_H=H,numerical_C=C,numerical=True,fixed_native_N=len(X),Region_N=chosen['region_N'],region_MAE_mm=chosen['region_MAE_mm'],old_world_region_MAE_mm=chosen['initial_region_MAE_mm'],independent_information=info,baseline_Ring=baseline,derived_Ring=r,baseline_SIFT=bg0,derived_SIFT=bg,original_CAD_occluded_N=int((z0>=oldcad-.05).sum()),derived_CAD_occluded_N=int((z1>=cad-.05).sum()),own_image_projection_max_px=float(delta.max()),edge_length_max_change_mm=float(abs(l0-l1).max()),relative_edge_max_change=float(np.max(abs(l0-l1)/np.maximum(l0,1e-12))),original_source_Ring_min_mm=float(sd0.min()),derived_source_Ring_min_mm=float(sd.min()),retained_native_faces_N=len(m['F']),retained_native_face_ratio=1.,local_curvature_retention='exact SE3 invariant; no smoothing/remeshing; same topology',source_local_camera_points_max_mm=float(np.max(np.linalg.norm((X-C[:3,3])@C[:3,:3]-(o['X']-C0[:3,3])@C0[:3,:3],axis=1))),absolute_real_pose_accuracy='NOT_EVALUABLE')
