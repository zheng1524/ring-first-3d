from common import *
from evaluate import *
import open3d as o3d
from scipy.stats import qmc

def depth_metrics(name,arm,step,path):
 a=np.load(path);rt=scene(a['V'],a['F']);rr=np.load(R/'inputs'/name/'RING.npz');rs=scene(rr['V'],rr['F']);rows=[]
 for v in getcase(name)['views']:
  cid=v['id'];o=np.load(R/'depth_observations'/(cid+'.npz'));ray=np.c_[o['uv'],np.ones(len(o['uv']))]@np.linalg.inv(o['K']).T;X=(ray*o['z'][:,None])@o['T'][:3,:3].T+o['T'][:3,3];_,_,z=pointcast(rt,X,o['K'],o['T']);_,_,rz=pointcast(rs,X,o['K'],o['T']);hit=np.isfinite(z)&(z>0)&(z<rz-.05);err=z-o['z'];r=abs(err)/.5;cost=np.where(hit,np.minimum(np.where(r<1,.5*r*r,r-.5),9.5),9.5);pairs=o['pairs'];good=hit[pairs[:,0]]&hit[pairs[:,1]];delta=(z[pairs[:,0]]-z[pairs[:,1]])-(o['z'][pairs[:,0]]-o['z'][pairs[:,1]]);dr=abs(delta)/.5;pcost=np.where(good,np.minimum(np.where(dr<1,.5*dr*dr,dr-.5),9.5),9.5)
  rows.append(dict(case=name,arm=arm,step=step,source=cid,role=v['role'],depth_kind='IDEAL_GT_DEPTH_UPPER_BOUND'if name.startswith('virtual')else'HERO_NATIVE',fixed_N=len(z),hit_N=int(hit.sum()),miss_N=int((~hit).sum()),hit_rate=float(hit.mean()),conditional_error_mm=stats(err[hit]),fixed_denominator_Huber_cost=float(cost.mean()),weighted_cost=float(np.average(cost,weights=o['boundary_weight'])),weight_sum=float(o['boundary_weight'].sum()),weight_effective_N=float(o['boundary_weight'].sum()**2/(o['boundary_weight']**2).sum()),pair_N=len(pairs),pair_hit_N=int(good.sum()),pair_delta_error_mm=stats(delta[good]),pair_fixed_cost=float(pcost.mean())if len(pairs)else None))
 return rows

def main():
 cfg=load(R/'config/PROTOCOL.json');geom=load(R/'metrics/ALL_GEOMETRY.json');checks=load(R/'metrics/BLENDER_CHECKS.json');exact=[];depth=[];shape=[];sections=[];end=[];weights=[]
 for name in cfg['cases']:
  init=np.load(R/'inputs'/name/'INITIAL.npz');ring=np.load(R/'inputs'/name/'RING.npz');rscene=scene(ring['V'],ring['F']);g=None
  if name.startswith('virtual'):
   p=OLD/'audit_only/NATIVE_CAD_GT.npz'if name=='virtual_IIa'else R/'audit_only'/name/'GT.npz';g=np.load(p);grt=scene(g['V'],g['F']);gps=area_samples(g['V'],g['F']);zbase=float(g['V'][:,2].min());hgt=float(g['V'][:,2].max()-zbase);gm=trimesh.Trimesh(g['V'],g['F'],process=False);gc=next(x for x in checks if x['case']==name and x['arm']=='GT');GTsolid=bool(gm.is_watertight and gm.is_winding_consistent and gc['self_pair_N']==0);regions=np.where(gps[:,2]<zbase+.15*hgt,'base',np.where(gps[:,2]>zbase+.66*hgt,'top','side'))
  for v in getcase(name)['views']:
   o=np.load(R/'depth_observations'/(v['id']+'.npz'));w=o['boundary_weight'];weights.append(dict(case=name,source=v['id'],role=v['role'],N=len(w),weight_sum=float(w.sum()),min=float(w.min()),median=float(np.median(w)),p95=float(np.quantile(w,.95)),near_boundary_N=int((np.minimum(o['distance_background_px'],o['distance_ring_px'])<=8).sum()),weight_below_half_N=int((w<.5).sum()),pair_N=len(o['pairs'])))
  states=[('P0',0,R/'inputs'/name/'INITIAL.npz')]+[(a,s,R/'local_results'/name/a/('STEP_%04d.npz'%s))for a in cfg['arms']for s in[50,100,200,300]]
  for arm,step,path in states:
   a=np.load(path);V,F=a['V'],a['F'];m=trimesh.Trimesh(V,F,process=False);rec=next(x for x in checks if(x['case'],x['arm'],x['step'])==(name,arm,step));confirmed=[]
   for i,j in rec['self_pairs']:
    cm=trimesh.collision.CollisionManager();cm.add_object('one',trimesh.Trimesh(V[F[i]],[[0,1,2]],process=False));yes=cm.in_collision_single(trimesh.Trimesh(V[F[j]],[[0,1,2]],process=False));
    if yes:confirmed.append([i,j])
   sd=rscene.compute_signed_distance(o3d.core.Tensor(V.astype(np.float32)),nsamples=3).numpy();solid=bool(m.is_watertight and m.is_winding_consistent and len(m.split(only_watertight=False))==1 and not rec['self_pair_N'] and m.area_faces.min()>1e-12);row=dict(case=name,arm=arm,step=step,Ring_pair_N=rec['Ring_pair_N'],self_candidate_N=rec['self_pair_N'],self_FCL_confirmed_checked_N=len(confirmed),self_all_checked=not rec['self_pairs_truncated'],self_confirmed_pairs=confirmed,Ring_penetration_max_mm=max(0,float(-sd.min())),solid_geometry_valid=solid,geometry_gate=solid and not rec['Ring_pair_N'] and float(sd.min())>=-.001);exact.append(row)
   gg=next(x for x in geom if(x['case'],x['arm'],x['step'])==(name,arm,step));domain=load(R/'metrics'/(name+'_VOLUME_DOMAIN.json'));outside_gt=bool(g is not None and ((g['V']<np.array(domain['lo']))|(g['V']>np.array(domain['hi']))).any());gg['GT_outside_integration_domain']=outside_gt;gg['geometry_gate']=row['geometry_gate'];gg['solid_geometry_valid']=solid;gg['absolute_solid_volume_error_mm3']=gg.get('volume_error_abs_mm3')if solid and g is not None and GTsolid else None;gg['GT_difference_volume_mm3']=gg.get('symmetric_difference_mm3')if solid and g is not None and GTsolid and not outside_gt and gg.get('outside_integration_domain_vertices',0)==0 else None;gg['occupancy_proxy_only']=not solid
   dd=depth_metrics(name,arm,step,path);depth+=dd
   if g is not None:
    rt=scene(V,F);err=distance(rt,gps)
    for region in['top','side','base']:shape.append(dict(case=name,arm=arm,step=step,region=region,GT_surface_error_mm=stats(err[regions==region]),maximum_height_mm=float(V[:,2].max()-zbase),GT_maximum_height_mm=hgt,height_error_mm=float(V[:,2].max()-zbase-hgt),minimum_z_mm=float(V[:,2].min()),full_GEOMETRY_GT=True))
    if step in[0,300]:
     for z in np.linspace(zbase,zbase+hgt,25)[1:-1]:
      vals=[]
      for mesh_ in[m,trimesh.Trimesh(g['V'],g['F'],process=False)]:
       from section_audit import section_area
       area,status=section_area(mesh_.vertices,mesh_.faces,z)
       vals.append(area)
      sections.append(dict(case=name,arm=arm,z_mm=float(z),prediction_section_area_mm2=vals[0]if solid else None,prediction_raw_proxy_area_mm2=vals[0],GT_section_area_mm2=vals[1],prediction_solid_valid=solid))
   pp=list(csv.DictReader((R/'metrics'/f'{name}_PER_VIEW.csv').open()));pp=[p for p in pp if p['arm']==arm and int(p['step'])==step];rr=dict(case=name,arm=arm,step=step,volume_mm3=gg['volume_mm3'],volume_ratio_P0=gg['volume_ratio_P0'],Ring_collision=gg['Ring_collision'],Ring_penetration_max_mm=row['Ring_penetration_max_mm'],self_FCL_N=len(confirmed),geometry_gate=row['geometry_gate'],solid_geometry_valid=solid,Chamfer_MAE_mm=gg.get('Chamfer_mm',{}).get('MAE'),Chamfer_p95_mm=gg.get('Chamfer_mm',{}).get('p95'),Chamfer_max_mm=gg.get('Chamfer_mm',{}).get('maximum'),GT_difference_volume_mm3=gg['GT_difference_volume_mm3'],GT_difference_occupancy_proxy_mm3=gg.get('symmetric_difference_mm3'),absolute_solid_volume_error_mm3=gg['absolute_solid_volume_error_mm3'],roughness_p95_deg=gg['roughness_normal_angle_deg']['p95'])
   for role in['fit','holdout']:
    pv=[x for x in pp if(x['role']=='FIT')==(role=='fit')];dv=[x for x in dd if(x['role']=='FIT')==(role=='fit')];rr[role+'_IoU']=float(np.mean([float(x['full_Mask_IoU'])for x in pv]));rr[role+'_coverage']=float(np.mean([float(x['coverage'])for x in pv]));rr[role+'_depth_MAE_mm']=float(np.mean([x['conditional_error_mm']['MAE']for x in dv if x['conditional_error_mm']['MAE']is not None]));rr[role+'_depth_hit_rate']=sum(x['hit_N']for x in dv)/sum(x['fixed_N']for x in dv);rr[role+'_fixed_depth_cost']=float(np.mean([x['fixed_denominator_Huber_cost']for x in dv]))
   end.append(rr)
  print('EXTRA_DONE',name,flush=True)
 table('metrics/DEPTH_EVALUATION.csv',depth);save('metrics/DEPTH_EVALUATION.json',depth);table('metrics/VIRTUAL_SHAPE.csv',shape);table('metrics/CROSS_SECTIONS.csv',sections);save('metrics/SHAPE.json',shape);save('metrics/SECTIONS.json',sections);table('metrics/WEIGHTS_SUMMARY.csv',weights);save('metrics/EXACT_GEOMETRY.json',exact);save('metrics/SUMMARY.json',end);table('metrics/SUMMARY.csv',end);save('metrics/ENDPOINTS.json',[x for x in end if x['step']in[0,300]]);table('metrics/ENDPOINTS.csv',[x for x in end if x['step']in[0,300]]);save('metrics/ALL_GEOMETRY_WITH_VALIDITY.json',geom)
if __name__=='__main__':main()
