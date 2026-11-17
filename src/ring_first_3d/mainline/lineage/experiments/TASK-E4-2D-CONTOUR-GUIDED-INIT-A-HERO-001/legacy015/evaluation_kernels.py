"""Independent fixed-denominator post-freeze evaluation. Failed finals stay absent/NaN."""
from common import *
from evaluate import area_samples,distance,pointcast
import open3d as o3d

def huber(e):
 r=abs(e/.5);return np.minimum(np.where(r<1,.5*r*r,r-.5),9.5)
def geometry(c,z,rs,ring):
 V=z['V'];F=z['F'];Fs=z['F_solid'];m=trimesh.Trimesh(V,Fs,process=False);up=trimesh.Trimesh(V,F,process=False);cm=trimesh.collision.CollisionManager();cm.add_object('Ring',ring);intersect=bool(cm.in_collision_single(m));edges=np.unique(np.sort(np.r_[Fs[:,[0,1]],Fs[:,[1,2]],Fs[:,[2,0]]],axis=1),axis=0);samples=np.r_[V,V[Fs].mean(1),V[edges].mean(1)];sd=rs.compute_signed_distance(o3d.core.Tensor(samples.astype(np.float32)),nsamples=3).numpy();rt=scene(V,F);base=load(R/'inputs'/c['name']/'BASE_SELECTION.json');p=base['selected_plane'];height=None if p is None else V@np.array(p)[:3]+p[3];supported=np.zeros(4096,bool);P=area_samples(V,F,4096)
 for v in c['views']:
  if v['role']!='FIT':continue
  a=np.load(R/'inputs'/c['name']/(v['id']+'.npz'));uv,pz,bz=pointcast(rt,P,a['K'],a['T']);_,_,cz=pointcast(rs,P,a['K'],a['T']);inside=(pz>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360);pix=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);supported|=inside&(a['labels'][pix[:,1],pix[:,0]]==1)&(pz<cz)&(abs(pz-bz)<.05)
 internal=np.load(R/'inputs'/c['name']/'BASE_EVIDENCE.npz')['Polyp_internal_XYZ'];ih=None if p is None else internal@np.array(p)[:3]+p[3]
 face_normals=up.face_normals;fold=int((np.einsum('ij,ij->i',face_normals[up.face_adjacency[:,0]],face_normals[up.face_adjacency[:,1]])<-.5).sum())if len(up.face_adjacency)else 0
 rr=ring.vertices[::16];contained=scene(V,Fs).compute_occupancy(o3d.core.Tensor(np.asarray(rr,np.float32)),nsamples=3).numpy()
 return dict(V_N=len(V),observed_F_N=len(F),inferred_cap_F_N=int(z['inferred_base_faces'].sum()),watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),connected_components=len(m.split(only_watertight=False)),nonmanifold_edge_N=int((np.bincount(m.edges_unique_inverse)!=2).sum()),degenerate_F_N=int((m.area_faces<=1e-12).sum()),observed_adjacent_normal_over120deg_N=fold,observed_roughness_p95_deg=float(np.quantile(np.degrees(up.face_adjacency_angles),.95))if len(up.face_adjacency_angles)else None,Ring_surface_collision=intersect,Ring_inside_body_sample_N=int((contained>.5).sum()),Ring_signed_sample_penetration_mm=float(max(0,-sd.min())),Ring_negative_sample_N=int((sd<0).sum()),sampled_surface_support_fraction=float(supported.mean()),sampled_supported_area_mm2=float(up.area*supported.mean()),observed_mesh_area_mm2=float(up.area),base_status=base['base_status'],base_uncertain=base['uncertain_base'],model_height_above_estimated_base_mm=None if height is None else float(height.max()),below_estimated_base_vertex_N=None if height is None else int((height<-.001).sum()),estimated_internal_HERO_height_p95_mm=None if ih is None else float(np.quantile(ih,.95)),raw_solid_volume_diagnostic_mm3=float(m.volume),GT_height_volume_accuracy='NOT_EVALUABLE')

def view_metrics(c,z,rt,rs):
 V=z['V'];F=z['F'];records=[]
 for v in c['views']:
  a=np.load(R/'inputs'/c['name']/(v['id']+'.npz'));depth=cast(rt,a['K'],a['T'],360,640);cad=cast(rs,a['K'],a['T'],360,640);pred=np.isfinite(depth)&(depth<cad);target=a['labels']==1;known=a['labels']!=2;intersection=int((pred&target).sum());FP=int((pred&~target&known).sum());q=contour(pred&known);qq=contour(target);errs=np.r_[cKDTree(q).query(qq)[0],cKDTree(qq).query(q)[0]]if len(q)and len(qq)else[];row=dict(source=v['id'],role=v['role'],Mask_N=int(target.sum()),Mask_hit_N=intersection,Mask_miss_N=int(target.sum()-intersection),Mask_outside_N=FP,IoU=intersection/max(1,int(target.sum())+FP),Mask_coverage=intersection/max(1,int(target.sum())),outside_per_Mask=FP/max(1,int(target.sum())),contour_px=stats(errs),CAD_occluded_N=int((np.isfinite(depth)&(depth>=cad)).sum()),predicted_in_front_of_observed_Ring_N=int((pred&(a['labels']==2)).sum()))
  path=R/'depth_observations'/(v['id']+'.npz')
  if path.exists():
   o=np.load(path);ray=np.c_[o['uv'],np.ones(len(o['uv']))]@np.linalg.inv(o['K']).T;rays=np.c_[np.broadcast_to(o['T'][:3,3],ray.shape),ray@o['T'][:3,:3].T].astype(np.float32);hits=rt.cast_rays(o3d.core.Tensor(rays));zh=hits['t_hit'].numpy();fid=hits['primitive_ids'].numpy().astype(int);cz=rs.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();valid=(fid<len(F))&np.isfinite(zh)&(zh>0)&(zh<cz-.05);tri=(V[F[np.clip(fid,0,len(F)-1)]]-o['T'][:3,3])@o['T'][:3,:3];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);cos=abs((n*ray).sum(1))/np.maximum(np.linalg.norm(n,axis=1)*np.linalg.norm(ray,axis=1),1e-30);active=valid&(cos>.001)&(np.linalg.norm(n,axis=1)>2e-14);err=np.where(active,zh-o['z'],0.);cost=np.where(active,huber(err),9.5);w=o['boundary_weight'];pairs=o['pairs'];good=active[pairs].all(1);delta=(np.where(active,zh,0)[pairs[:,0]]-np.where(active,zh,0)[pairs[:,1]])-(o['z'][pairs[:,0]]-o['z'][pairs[:,1]]);rcost=np.where(good,huber(delta),9.5);pw=o['pair_weight'];row.update(HERO_status='NATIVE_FIXED_ORIGINAL',fixed_depth_N=len(active),depth_hit_N=int(active.sum()),depth_miss_N=int((~active).sum()),depth_hit_rate=float(active.mean()),absolute_depth_mm=stats(err[active]),raw_fixed_depth_cost=float(cost.mean()),boundary_weighted_depth_cost=float(cost@w/w.sum()),weight_sum=float(w.sum()),fixed_pair_N=len(pairs),pair_hit_N=int(good.sum()),pair_miss_N=int((~good).sum()),relative_depth_mm=stats(delta[good]),raw_fixed_relative_cost=float(rcost.mean())if len(pairs)else None,weighted_relative_cost=float(rcost@pw/pw.sum())if len(pairs)and pw.sum()>0 else None)
  else:row.update(HERO_status='NO_NATIVE_DEPTH_NO_FILL',fixed_depth_N=0,depth_hit_rate=None,raw_fixed_depth_cost=None)
  records.append(row)
 return records

def main():
 for a in load(R/'assets_index/PREDICTIONS_FROZEN.json')['files']:assert sha(a['path'])==a['sha256'],a['path']
 summaries=[];views=[];details=[];failures=[];primary=[]
 for c in load(R/'config/CASE_LOCK.json'):
  name=c['name'];rr=np.load(R/'inputs'/name/'RING.npz');rs=scene(rr['V'],rr['F']);ring=trimesh.Trimesh(rr['V'],rr['F'],process=False);variants=[('B','STATIC_B',0,R/'inputs'/name/'B_UNCUT.npz',False)]
  for route in['P','S']:
   run=load(R/'metrics'/(name+'_'+route+'_RUN.json'));primary.append(dict(case=name,route=route,status=run['status'],optimizer_steps=run['optimizer_steps'],accepted_steps=run['accepted_steps'],final_300_path=str(R/'local_results'/name/route/'FINAL.npz')if run['status']=='COMPLETED'else None,final_Mask_IoU=None,GT_accuracy='NOT_EVALUABLE'))
   for step in load(R/'config/PROTOCOL.json')['checkpoints']:
    p=R/'local_results'/name/route/('STEP_%04d.npz'%step)
    if p.exists():variants.append((route,'CHECKPOINT',step,p,False))
   if run['status']=='COMPLETED':variants.append((route,'FINAL',300,R/'local_results'/name/route/'FINAL.npz',False))
   else:
    for label in['LAST_SAFE','UNSAFE_CANDIDATE']:
     p=R/'local_results'/name/route/(label+'.npz')
     if p.exists():variants.append((route,label,int(np.load(p)['step']),p,True))
    init=np.load(R/'inputs'/name/(route+'_INITIAL.npz'));unsafe=R/'local_results'/name/route/'UNSAFE_CANDIDATE.npz';last=R/'local_results'/name/route/'LAST_SAFE.npz';inf=dict(case=name,route=route,status=run['status'],steps=run['optimizer_steps'],accepted=run['accepted_steps'],final_300_NaN=True)
    if unsafe.exists()and last.exists():
     u=np.load(unsafe);last=np.load(last);volume0=trimesh.Trimesh(init['V'],init['F_solid'],process=False).volume;vol=trimesh.Trimesh(u['V'],u['F_solid'],process=False).volume;delta=np.linalg.norm(u['V']-last['V'],axis=1);inf.update(max_candidate_step_mm=float(delta.max()),candidate_volume_ratio=float(vol/volume0),nonfinite_N=int((~np.isfinite(u['V'])).sum()),reasons=[s for ok,s in[(delta.max()>2,'SINGLE_STEP_OVER_2MM'),(not .1<=vol/volume0<=10,'VOLUME_EMERGENCY_RANGE'),(not np.isfinite(u['V']).all(),'NONFINITE_GEOMETRY')]if ok])
    failures.append(inf)
  for route,label,step,path,diagnostic in variants:
   z=dict(np.load(path));z.setdefault('F_solid',z['F']);z.setdefault('inferred_base_faces',np.zeros(len(z['F']),bool));rt=scene(z['V'],z['F']);g=geometry(c,z,rs,ring);per=view_metrics(c,z,rt,rs);fit=[x for x in per if x['role']=='FIT'];hold=[x for x in per if x['role']!='FIT'];rec=dict(case=name,type=c['morphology'],route=route,label=label,step=step,diagnostic_only=diagnostic,path=str(path),FIT_IoU=float(np.mean([x['IoU']for x in fit])),HOLDOUT_IoU=float(np.mean([x['IoU']for x in hold])),FIT_Mask_coverage=float(np.mean([x['Mask_coverage']for x in fit])),HOLDOUT_Mask_coverage=float(np.mean([x['Mask_coverage']for x in hold])),**g)
   for prefix,subset in[('FIT',fit),('HOLDOUT',hold)]:
    dd=[x for x in subset if x.get('fixed_depth_N',0)>0];N=sum(x['fixed_depth_N']for x in dd);rec[prefix+'_fixed_depth_N']=N;rec[prefix+'_depth_hit_N']=sum(x['depth_hit_N']for x in dd);rec[prefix+'_depth_hit_rate']=sum(x['depth_hit_N']for x in dd)/N if N else None;rec[prefix+'_raw_fixed_depth_cost']=sum(x['raw_fixed_depth_cost']*x['fixed_depth_N']for x in dd)/N if N else None
   if route in['P','S']:
    init=np.load(R/'inputs'/name/(route+'_INITIAL.npz'));disp=np.linalg.norm(z['V']-init['V'],axis=1);norm0=trimesh.Trimesh(init['V'],init['F'],process=False).vertex_normals;signed=np.einsum('ij,ij->i',z['V']-init['V'],norm0);rec.update(initial_material_vertex_displacement_mm=stats(disp),outward_material_displacement_N=int((signed>.01).sum()),inward_material_displacement_N=int((signed<-.01).sum()),volume_ratio_own_initial=float(g['raw_solid_volume_diagnostic_mm3']/trimesh.Trimesh(init['V'],init['F_solid'],process=False).volume))
   summaries.append(rec);details.append(dict(**rec,per_view=per));views.extend(dict(case=name,route=route,label=label,step=step,diagnostic_only=diagnostic,**x)for x in per)
   if label=='FINAL':
    for p in primary:
     if p['case']==name and p['route']==route:p.update(final_Mask_IoU=rec['HOLDOUT_IoU'],FIT_fixed_depth_cost=rec['FIT_raw_fixed_depth_cost'],final_CAD_collision=rec['Ring_surface_collision'])
  print('EVALUATED',name,flush=True)
 save('metrics/ALL_STAGE_RESULTS.json',details);table('metrics/ALL_STAGE_SUMMARY.csv',summaries);save('metrics/ALL_STAGE_SUMMARY.json',summaries);table('metrics/PER_VIEW_METRICS.csv',views);save('metrics/PER_VIEW_METRICS.json',views);save('metrics/FAILURE_DIAGNOSIS.json',failures);table('metrics/FAILURE_DIAGNOSIS.csv',failures);save('metrics/FINAL_300_FIXED_DENOMINATOR.json',primary);table('metrics/FINAL_300_FIXED_DENOMINATOR.csv',primary)
 pairs=[]
 for n in load(R/'config/PROTOCOL.json')['cases']:
  x=[a for a in summaries if a['case']==n and a['label']=='FINAL'];p=next((a for a in x if a['route']=='P'),None);s=next((a for a in x if a['route']=='S'),None);pairs.append(dict(case=n,P_completed=p is not None,S_completed=s is not None,paired_final_eligible=p is not None and s is not None,HOLDOUT_IoU_P_minus_S=p['HOLDOUT_IoU']-s['HOLDOUT_IoU']if p and s else None,FIT_fixed_depth_cost_P_minus_S=p['FIT_raw_fixed_depth_cost']-s['FIT_raw_fixed_depth_cost']if p and s else None))
 save('metrics/PAIRED_FINAL_COMPARISON.json',pairs);table('metrics/PAIRED_FINAL_COMPARISON.csv',pairs)
if __name__=='__main__':main()
