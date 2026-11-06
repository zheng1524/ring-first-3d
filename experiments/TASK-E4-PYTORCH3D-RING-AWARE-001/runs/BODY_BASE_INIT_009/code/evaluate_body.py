from parametric import *
from evaluate import area_samples,distance,pointcast
from scipy.spatial.distance import pdist
from scipy.spatial import cKDTree
import open3d as o3d

def measures(c,V,F,Fsolid,model=None):
 name=c['name'];mesh_=trimesh.Trimesh(V,Fsolid,process=False);rr=np.load(R/'inputs'/name/'RING.npz');ring=trimesh.Trimesh(rr['V'],rr['F'],process=False);rs=scene(rr['V'],rr['F']);rt=scene(V,F);cm=trimesh.collision.CollisionManager();cm.add_object('Ring',ring);intersect=bool(cm.in_collision_single(mesh_));rd=rs.compute_signed_distance(o3d.core.Tensor(np.asarray(V,np.float32)),nsamples=3).numpy();base=load(R/'inputs'/name/'BASE.json');plane=np.array(base['plane'])if base['plane']is not None else None;h=V@plane[:3]+plane[3]if plane is not None else None;per=[];insideRing=0
 if model is not None:insideRing=int((signed_body(rr['V'][::16],np.array(model['p']),model['meta'])<-.001).sum())
 else:
  insideRing=int((scene(V,Fsolid).compute_occupancy(o3d.core.Tensor(rr['V'][::16].astype(np.float32)),nsamples=3).numpy()>.5).sum())
 for v in c['views']:
  a=np.load(R/'inputs'/name/(v['id']+'.npz'));z=cast(rt,a['K'],a['T'],360,640);cz=cast(rs,a['K'],a['T'],360,640);pred=np.isfinite(z)&(z<cz);target=a['labels']==1;known=a['labels']!=2;inter=int((pred&target).sum());FP=int((pred&~target&known).sum());ct=contour(target);cp=contour(pred&known);co=stats(np.r_[cKDTree(cp).query(ct)[0],cKDTree(ct).query(cp)[0]])if len(cp)and len(ct)else stats([]);rec=dict(source=v['id'],role=v['role'],original_Mask_N=int(target.sum()),hit_N=inter,miss_N=int(target.sum()-inter),outside_N=FP,IoU=inter/max(1,int(target.sum())+FP),coverage=inter/max(1,int(target.sum())),outside_per_Mask=FP/max(1,int(target.sum())),contour_px=co,CAD_occluded_N=int((np.isfinite(z)&(z>=cz)).sum()),HERO_status=v['HERO_status'])
  dp=R/'depth_observations'/(v['id']+'.npz')
  if dp.exists():
   o=np.load(dp);ray=np.c_[o['uv'],np.ones(len(o['uv']))]@np.linalg.inv(o['K']).T;X=(ray*o['z'][:,None])@o['T'][:3,:3].T+o['T'][:3,3];_,_,zz=pointcast(rt,X,o['K'],o['T']);_,_,rz=pointcast(rs,X,o['K'],o['T']);hit=np.isfinite(zz)&(zz>0)&(zz<rz-.05);err=zz-o['z'];pair=o['pairs'];good=hit[pair].all(1);delta=(zz[pair[good,0]]-zz[pair[good,1]])-(o['z'][pair[good,0]]-o['z'][pair[good,1]]);cost=np.where(hit,np.minimum(abs(err)/.5,10),10);rec.update(fixed_depth_N=len(hit),depth_hit_N=int(hit.sum()),depth_miss_N=int((~hit).sum()),depth_hit_rate=float(hit.mean())if len(hit)else None,absolute_depth_mm=stats(err[hit]),fixed_censored_absolute_cost=float(cost.mean())if len(hit)else None,fixed_pair_N=len(pair),pair_hit_N=int(good.sum()),relative_depth_mm=stats(delta),fixed_censored_relative_mm=float((abs(delta).sum()+2.5*(~good).sum())/max(1,len(pair))))
  per.append(rec)
 return dict(per_view=per,Ring_collision=intersect,Ring_inside_body_N=insideRing,Ring_max_penetration_mm=max(0.,float(-rd.min())),components=len(mesh_.split(only_watertight=False)),watertight=bool(mesh_.is_watertight),winding_consistent=bool(mesh_.is_winding_consistent),max_adjacent_face_angle_deg=float(np.degrees(mesh_.face_adjacency_angles).max()),roughness_p95_deg=float(np.quantile(np.degrees(mesh_.face_adjacency_angles),.95)),raw_volume_diagnostic_only_mm3=float(mesh_.volume),below_estimated_plane_vertex_N=None if h is None else int((h<-.001).sum()),min_estimated_plane_h_mm=None if h is None else float(h.min()),max_estimated_plane_h_mm=None if h is None else float(h.max()),base_qualification=base['base_status'],contact_status=base['contact_status'],truncate_allowed=base['truncate_allowed'],absolute_height_accuracy='NOT_EVALUABLE',absolute_volume_accuracy='NOT_EVALUABLE')

def main():
 freeze=load(R/'assets_index/PREDICTIONS_FROZEN.json')
 for a in freeze['files']:assert sha(a['path'])==a['sha256']
 rows=[];allper=[];stability=[];selections=[];stage=[]
 for c in load(R/'config/CASE_LOCK.json'):
  name=c['name'];folder=R/'local_results'/name;a=np.load(R/'inputs'/name/'INITIAL.npz');variants=[('A',a['V'],a['F'],a['F'],None)]
  for tag in['B','C']:
   model=load(folder/(tag+'_SELECTED.json'));z=np.load(folder/(tag+'_SELECTED.npz'));variants.append((tag,z['V'],z['F'],z['F_solid'],model))
  for tag,V,F,Fsolid,model in variants:
   rec=measures(c,V,F,Fsolid,model);rec.update(case=name,type=c['morphology'],arm=tag,selection_status='FROZEN_BASELINE'if model is None else model['selection_status'],family='ellipsoid_baseline'if model is None else model['meta']['family'],parameter_N=9 if model is None else len(model['p']),candidate_parameters=None if model is None else model['p']);rows.append(rec)
   for x in rec['per_view']:allper.append(dict(case=name,arm=tag,**x))
   fit=[x for x in rec['per_view']if x['role']=='FIT'];hold=[x for x in rec['per_view']if x['role']!='FIT'];r={k:v for k,v in rec.items()if k not in['per_view','candidate_parameters']};r['FIT_IoU']=float(np.mean([x['IoU']for x in fit]));r['HOLDOUT_IoU']=float(np.mean([x['IoU']for x in hold]));r['FIT_coverage']=float(np.mean([x['coverage']for x in fit]));r['HOLDOUT_coverage']=float(np.mean([x['coverage']for x in hold]));rec.update({k:r[k]for k in['FIT_IoU','HOLDOUT_IoU','FIT_coverage','HOLDOUT_coverage']});selections.append(r)
  fits=[load(folder/f'B_seed{s}_DEPTH.json')for s in[0,1,2]];centers=np.array([m['p'][:3]for m in fits]);axes=np.array([np.exp(m['p'][6:9])for m in fits]);pairdist=[];rotation=[]
  for i,j in[(0,1),(0,2),(1,2)]:
   vi,fi,_,_=body(np.array(fits[i]['p']),fits[i]['meta']);vj,fj,_,_=body(np.array(fits[j]['p']),fits[j]['meta']);err=np.r_[distance(scene(vj,fj),area_samples(vi,fi)),distance(scene(vi,fi),area_samples(vj,fj))];pairdist.append(dict(i=i,j=j,center_distance_mm=float(np.linalg.norm(centers[i]-centers[j])),surface_difference_mm=stats(err)));qi=decode_ellipsoid(np.array(fits[i]['p']),np.array(fits[i]['meta']['Q0']))[1];qj=decode_ellipsoid(np.array(fits[j]['p']),np.array(fits[j]['meta']['Q0']))[1];rotation.append(float(np.degrees(Rotation.from_matrix(qi.T@qj).magnitude())))
  stability.append(dict(case=name,type=c['morphology'],starts=3,center_max_pairwise_mm=float(max(pdist(centers))),semiaxes_spread_mm=np.ptp(axes,axis=0),rotation_max_deg=max(rotation),surface_pairs=pairdist,solver_success_N=sum(x['success']for x in fits),finite_model_N=len(fits),selection_eligible_N=sum(x['diagnostics']['selection_eligible']for x in fits)))
  for p in sorted(folder.glob('*.json')):
   m=load(p)
   if'phase'not in m:continue
   stage.append(dict(case=name,tag=p.stem,phase=m['phase'],family=m['meta']['family'],parameter_N=len(m['p']),parameters=m['p'],objective=m['objective'],initial_objective=m['initial_objective'],nfev=m['nfev'],actual_forward_calls=m['actual_forward_calls'],seconds=m['seconds'],success=m['success'],termination=m['termination']))
  print('EVALUATED',name,flush=True)
 save('metrics/CASE_MODEL_RESULTS.json',rows);table('metrics/CASE_MODEL_SUMMARY.csv',selections);save('metrics/CASE_MODEL_SUMMARY.json',selections);table('metrics/PER_VIEW_METRICS.csv',allper);save('metrics/PER_VIEW_METRICS.json',allper);save('metrics/MULTISTART_STABILITY.json',stability);table('metrics/MULTISTART_STABILITY.csv',stability);table('metrics/STAGE_PARAMETERS.csv',stage);save('metrics/STAGE_PARAMETERS.json',stage)
if __name__=='__main__':main()
