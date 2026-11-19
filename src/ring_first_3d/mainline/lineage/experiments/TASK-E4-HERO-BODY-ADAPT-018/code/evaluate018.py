from hero_objective018 import *
from gate018 import configure
from safe_geometry import dense_face_distance,self_intersections
import hero_objective018 as hm
import shutil,open3d as o3d
ROOT=Path(__file__).resolve().parents[1]
def iou(a,b):return float((a&b).sum()/max(1,(a|b).sum()))
def main():
 frozen=load(ROOT/'provenance/ALL_OPTIMIZED_PREDICTIONS_FROZEN.json');assert frozen['all_formal_arms_attempted'];records=[];perview=[];quality=[]
 for group in ['G06','G05','G01','G03']:
  source=ROOT/'inputs'/group;folder=R/'inputs'/group;folder.mkdir(parents=True,exist_ok=True);meta=load(source/'ALL_VIEW_META.json')
  for p in source.iterdir():
   if p.name=='CASE.json':continue
   if p.is_file()and not(folder/p.name).exists():(folder/p.name).symlink_to(p.resolve())
  for p in(ROOT/'holdout'/group).glob('*.npz'):
   if not(folder/p.name).exists():(folder/p.name).symlink_to(p.resolve())
  save('inputs/'+group+'/CASE.json',meta);c=Case(group);configure(c);ch=FreeVertices(c);ch.total_trust_D=1.;held=[v['id']for v in meta['views']if v['role']!='FIT'];fit=list(c.fit);sources={};full_sources={}
  for role,ids in [('FIT',fit),('HOLDOUT',held)]:
   if role=='HOLDOUT':
    alias=R/'held_alias';alias.mkdir(exist_ok=True);p=alias/'hero_fit'
    if not p.exists():p.symlink_to(ROOT/'holdout/hero',target_is_directory=True)
    hm.ROOT=alias
   sources[role]=HeroDepth018(c,ch,'TRUSTED',ids);full_sources[role]=HeroDepth018(c,ch,'FULL',ids);hm.ROOT=ROOT
  ring=scene(c.ringV,c.ringF);cad={cid:cast(ring,c.views[cid]['K'],c.views[cid]['T'],360,640)for cid in fit+held};V0=c.V;Fsolid=c.F_solid;tri0=V0[Fsolid];edge0=np.linalg.norm(tri0[:,[1,2,0]]-tri0,axis=2);basearea=trimesh.triangles.area(tri0)
  routes=[dict(arm='B0_FROZEN',kind='STATIC',path=str(ROOT/'inputs'/group/'INITIAL.npz'))]+[dict(arm=a['arm'],kind=a['kind'],path=str(Path(a['path'])/'local_results'/group/'FINAL.npz'))for a in load(ROOT/'config/ARM_PLAN.json')if a['group']==group]
  routes += [dict(arm=a['arm'],kind=a['kind'],path=str(Path(a['path'])/'local_results'/group/'FINAL.npz'),phase='R1_RETAINED_DIAGNOSTIC')for a in load(ROOT/'config/ARM_PLAN_R1_RETAINED.json')if a['group']==group and group=='G06' and (Path(a['path'])/'local_results'/group/'FINAL.npz').exists()]
  for route in routes:
   path=Path(route['path'])
   if not path.exists():records.append(dict(group=group,arm=route['arm'],status='MISSING_FINAL',HERO_MAE_mm=None));continue
   a=np.load(path);q=tensor(a['parameters']if route['kind']!='STATIC'else np.zeros((ch.N,3)),torch.float64);m=ch.mesh(q);V=ch.vertices(q).detach().cpu().numpy();body=scene(V,c.F);out=R/'local_results'/group/route['arm'];out.mkdir(parents=True,exist_ok=True);fits=[];holds=[]
   with torch.no_grad():
    for role,ids in [('FIT',fit),('HOLDOUT',held)]:
     for cid in ids:
      d=c.views[cid];loss,info,data=sources[role].term(m,cid,True);active=data['active'];H=sources[role].obs[cid];res=data['z'][active]-H['z'][active];space=np.linalg.norm(data['world_point'][active]-H['X'][active],axis=1);dz=cast(body,d['K'],d['T'],360,640);pred=np.isfinite(dz)&(dz<cad[cid]);target=d['labels']==1;val=iou(pred,target);(fits if role=='FIT'else holds).append(val);row=dict(group=group,arm=route['arm'],role=role,view=cid,IoU=val,**{k:v for k,v in info.items()if k!='view'},residual=stats(res),spatial_mm=stats(space),miss_fraction=(info['miss_N']+info['Ring_occluded_N'])/info['fixed_N']);fl,fi,fd=full_sources[role].term(m,cid,True);fa=fd['active'];fo=full_sources[role].obs[cid];row.update(FULL_fixed_N=fi['fixed_N'],FULL_active_N=fi['active_N'],FULL_miss_N=fi['miss_N'],FULL_Ring_occluded_N=fi['Ring_occluded_N'],FULL_residual_mm=stats(fd['z'][fa]-fo['z'][fa]),FULL_fixed_denominator_cost=fi['unweighted_loss']);perview.append(row);np.savez_compressed(out/(cid+'_EVAL.npz'),**data,pred=pred,target=target,depth_mesh=dz,cad_depth=cad[cid]);save('metrics/per_view/'+group+'_'+route['arm']+'_'+cid+'.json',row)
   fitrows=[x for x in perview if x['group']==group and x['arm']==route['arm']and x['role']=='FIT'];heldrows=[x for x in perview if x['group']==group and x['arm']==route['arm']and x['role']=='HOLDOUT'];sd=dense_face_distance(ring,V,Fsolid,c.ringV,64,c.ringF);si=self_intersections(V,Fsolid);ar=trimesh.triangles.area(V[Fsolid]);edges=np.linalg.norm(V[Fsolid][:,[1,2,0]]-V[Fsolid],axis=2);disp=np.linalg.norm(V-V0,axis=1);mm=trimesh.Trimesh(V,Fsolid,process=False)
   rec=dict(group=group,arm=route['arm'],status='FROZEN_STATIC'if route['kind']=='STATIC'else'OPTIMIZED_STATE',FIT_IoU=float(np.mean(fits)),HOLDOUT_IoU=float(np.mean(holds)),FIT_fixed_N=sum(x['fixed_N']for x in fitrows),FIT_active_N=sum(x['active_N']for x in fitrows),FIT_missing_N=sum(x['miss_N']for x in fitrows),FIT_Ring_occluded_N=sum(x['Ring_occluded_N']for x in fitrows),FIT_miss_fraction=sum(x['miss_N']+x['Ring_occluded_N']for x in fitrows)/sum(x['fixed_N']for x in fitrows),HERO_MAE_mm=sum(x['residual']['MAE']*x['active_N']for x in fitrows if x['residual']['MAE']is not None)/sum(x['active_N']for x in fitrows)if sum(x['active_N']for x in fitrows)else None,HERO_fixed_denominator_cost=sum(x['unweighted_loss']*x['weight']for x in fitrows),HOLDOUT_HERO_MAE_mm=sum(x['residual']['MAE']*x['active_N']for x in heldrows if x['residual']['MAE']is not None)/sum(x['active_N']for x in heldrows)if sum(x['active_N']for x in heldrows)else None,Ring64_min_mm=float(sd.min()),Ring64_penetrating_faces=int((sd<-.001).sum()),self_intersections=si['intersections'],watertight=bool(mm.is_watertight),winding_consistent=bool(mm.is_winding_consistent),components=len(mm.split(only_watertight=False)),min_area_ratio=float((ar/np.maximum(basearea,1e-20)).min()),max_edge_stretch=float((edges/np.maximum(edge0,1e-20)).max()),max_displacement_mm=float(disp.max()),mean_displacement_mm=float(disp.mean()),GT='NOT_EVALUABLE_NO_PROJECT_GT_USED',path=str(path))
   if route['kind']!='STATIC':rec.update({k:load(ROOT/'arms'/route['arm']/'metrics'/(group+'_RUN.json'))[k]for k in ['attempts','accepted','seconds']})
   else:rec.update(attempts=0,accepted=0,seconds=0)
   rec['FULL_FIT_fixed_N']=sum(x['FULL_fixed_N']for x in fitrows);rec['FULL_FIT_active_N']=sum(x['FULL_active_N']for x in fitrows);rec['FULL_FIT_miss_fraction']=1-rec['FULL_FIT_active_N']/rec['FULL_FIT_fixed_N'];rec['FULL_HERO_MAE_mm']=sum(x['FULL_residual_mm']['MAE']*x['FULL_active_N']for x in fitrows if x['FULL_residual_mm']['MAE']is not None)/rec['FULL_FIT_active_N']if rec['FULL_FIT_active_N']else None;rec['phase']=route.get('phase','MAIN_R2'if route['kind']!='STATIC'else'FROZEN_016_BASELINE');rec['HOLDOUT_fixed_N']=sum(x['fixed_N']for x in heldrows);rec['HOLDOUT_active_N']=sum(x['active_N']for x in heldrows);rec['HOLDOUT_miss_fraction']=1-rec['HOLDOUT_active_N']/rec['HOLDOUT_fixed_N'];rec['residual_metrics_definition']='active-first-hit errors, conditioned on hit; misses separately fixed-denominator cost and explicit N';records.append(rec);save('metrics/'+group+'_'+route['arm']+'_GEOMETRY.json',rec);np.savez_compressed(out/'FINAL_METRIC_GEOMETRY.npz',V=V,F=c.F,F_solid=Fsolid,displacement_mm=disp,Ring64=sd);print('EVAL018',group,route['arm'],'HERO',round(rec['HERO_MAE_mm'],4)if rec['HERO_MAE_mm']is not None else None,'miss',round(rec['FIT_miss_fraction'],3),flush=True)
  del c,ch,sources;torch.cuda.empty_cache()
 save('metrics/COMPARISON.json',records);table('metrics/COMPARISON.csv',records);save('metrics/PER_VIEW.json',perview);table('metrics/PER_VIEW.csv',perview)
if __name__=='__main__':main()
