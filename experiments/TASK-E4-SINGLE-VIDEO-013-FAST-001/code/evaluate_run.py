"""Only after all44 predictions freeze: same-camera scores, independent Ring, SE3."""
from common import *
from native_score import evaluate
from dense_audit014 import dense_face_distance,self_intersections
from safe_geometry import points
import shutil,subprocess,concurrent.futures
import open3d as o3d
OLD13=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013'
PY='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python'
BLENDER='/home/liu/blender/blender-5.0.1-linux-x64/blender'
TAGS=['S0','S8','S16','S32']

def case_native(n):
 rows=[];per=[];geom=[];rg=np.load(R/'inputs'/n/'RING.npz');rs=scene(rg['V'],rg['F']);initial=np.load(R/'inputs'/n/'INITIAL.npz');IV,IF=initial['V'],initial['F_solid'];sd0=dense_face_distance(rs,IV,IF,rg['V'],64,rg['F']);penetration0=max(0.,-float(sd0.min()));init_mesh=trimesh.Trimesh(IV,IF,process=False);cm=trimesh.collision.CollisionManager();cm.add_object('Ring',trimesh.Trimesh(rg['V'],rg['F'],process=False));edges=np.unique(np.sort(np.r_[IF[:,[0,1]],IF[:,[1,2]],IF[:,[2,0]]],axis=1),axis=0);sp0=rs.compute_signed_distance(o3d.core.Tensor(points(IV,IF,edges).astype(np.float32)),nsamples=3,nthreads=2).numpy();meta=getcase(n)
 for tag in TAGS:
  path=R/'arms'/tag/'local_results'/n/'FINAL.npz';out=R/'metrics/native'/(n+'_'+tag+'.json');out.parent.mkdir(exist_ok=True)
  if out.exists():d=load(out)
  else:d=evaluate(n,path,True,tag);save(out.relative_to(R),d)
  members=set(load(R/'config/VIEW_SELECTION.json')[n][tag]);rr=d['per_view']
  for v in rr:v['used_for_this_model_update']=v['view']in members;v['metric_frame']='common frozen single-video camera pool, beforeSE3';v['S0_historical_exact_cache']=tag=='S0'
  rec=dict(case=n,label=tag,path=str(path),training_views_N=len(members),FIT_IoU=d['mean']['FIT']['IoU'],HOLDOUT_IoU=d['mean'].get('UPDATE_HOLDOUT',{}).get('IoU'),FIT=d['mean']['FIT'],HOLDOUT=d['mean'].get('UPDATE_HOLDOUT',{}))
  for role,prefix in [('FIT','FIT'),('UPDATE_HOLDOUT','HOLDOUT')]:
   depth=[x for x in rr if x['role']==role and x.get('fixed_depth_N',0)>0];N=sum(x['fixed_depth_N']for x in depth);H=sum(x['depth_hit_N']for x in depth);cost=sum(x['fixed_depth_cost']*x['fixed_depth_N']for x in depth);err=sum(x['depth_MAE_mm']*x['depth_hit_N']for x in depth if x['depth_MAE_mm']is not None);rec.update({prefix+'_HERO_N':N,prefix+'_HERO_hits':H,prefix+'_HERO_hit_rate':H/N if N else None,prefix+'_HERO_fixed_cost':cost/N if N else None,prefix+'_HERO_active_MAE_mm':err/H if H else None})
  rows.append(rec);per+=rr;z=np.load(path);V,F=z['V'],z['F_solid'];sd=dense_face_distance(rs,V,F,rg['V'],64,rg['F']);pen=max(0.,-float(sd.min()));sp=rs.compute_signed_distance(o3d.core.Tensor(points(V,F,edges).astype(np.float32)),nsamples=3,nthreads=2).numpy();tm=trimesh.Trimesh(V,F,process=False);si=self_intersections(V,F);geom.append(dict(case=n,label=tag,Ring_initial_dense_penetration_mm=penetration0,Ring_dense_penetration_mm=pen,Ring_added_dense_penetration_mm=max(0.,pen-penetration0),dense_nonworsening=bool(pen<=penetration0+1e-5),old_sparse_nonworsening_vs_initial=bool((sp>=np.minimum(sp0,0)-1e-5).all()),Ring_FCL=bool(cm.in_collision_single(tm)),Ring_initial_FCL=bool(cm.in_collision_single(init_mesh)),self_Open3D_N=si['intersections'],vertices=len(V),faces=len(F),watertight=bool(tm.is_watertight),winding_consistent=bool(tm.is_winding_consistent),components=len(tm.split(only_watertight=False)),max_displacement_from_initial_mm=float(np.linalg.norm(V-IV,axis=1).max()),roughness_dihedral_deg=stats(np.degrees(tm.face_adjacency_angles)),evaluation_only_dense_check=True,no_deletion_or_postprocessing=True));print('NATIVE_DENSE',n,tag,pen,flush=True)
  folder=R/'local_results/dense_ring';folder.mkdir(exist_ok=True);np.savez_compressed(folder/(n+'_'+tag+'_FACE_SIGNED.npz'),signed_distance_mm=sd,source_path=str(path),divisions=64,used_for_optimization=False)
 return rows,per,geom

def main():
 marker=R/'provenance/ALL_PREDICTIONS_FROZEN_BEFORE_GT.json'
 while not marker.exists():time.sleep(10)
 frozen=load(marker);assert all(sha(x['path'])==x['sha256']for x in frozen['files']);cases=load(R/'config/CASE_LOCK.json');native=[];per=[];geo=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
  for a,b,c in pool.map(case_native,[c['name']for c in cases]):native+=a;per+=b;geo+=c
 save('metrics/NATIVE_SUMMARY.json',native);table('metrics/NATIVE_SUMMARY.csv',native);save('metrics/PER_VIEW_METRICS.json',per);table('PER_VIEW_METRICS.csv',per);save('metrics/GEOMETRY_AUDIT.json',geo);table('GEOMETRY_AUDIT.csv',geo)
 with(R/'runtime/BLENDER_GEOMETRY.log').open('w')as f:subprocess.run([BLENDER,'-b','--factory-startup','-t','2','--python',str(R/'code/blender_geometry_checks.py'),'--',str(R)],stdout=f,stderr=subprocess.STDOUT,check=True)
 # First opening of GT identity/geometry in this new experiment.
 save('provenance/GT_ACCESS_START.json',dict(epoch=time.time(),prediction_freeze=asset(marker),GT_used_for_training=False));(R/'evaluation_only').mkdir(exist_ok=True);shutil.copyfile(OLD13/'evaluation_only/GT_SOURCE_LOCK.json',R/'evaluation_only/GT_SOURCE_LOCK.json');shutil.copyfile(OLD13/'metrics/GT_VALIDITY.json',R/'metrics/GT_VALIDITY.json')
 for c in cases:
  n=c['name'];folder=R/'evaluation_only'/n;folder.mkdir(exist_ok=True);p=folder/'ORIGINAL_BLENDER_GT_MM.npz'
  if not p.exists():p.symlink_to(OLD13/'evaluation_only'/n/p.name)
  folder=R/'local_results/metric'/n;folder.mkdir(parents=True,exist_ok=True)
  for tag in TAGS:
   p=folder/(tag+'.npz')
   if not p.exists():p.symlink_to((R/'arms'/tag/'local_results'/n/'FINAL.npz').resolve())
 def worker(n):
  if(R/'metrics/eval_case'/(n+'_BLENDER_GEOMETRIC_METRICS.json')).exists():return
  with(R/'runtime'/('RIGID_'+n+'.log')).open('w')as f:subprocess.run([PY,'-B',str(R/'code/best_eval.py'),'--case',n],stdout=f,stderr=subprocess.STDOUT,check=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(worker,[c['name']for c in cases]))
 rows=[];T=[]
 for c in cases:n=c['name'];rows+=load(R/'metrics/eval_case'/(n+'_BLENDER_GEOMETRIC_METRICS.json'));T+=load(R/'metrics/eval_case'/(n+'_BLENDER_RIGID_ALIGNMENT.json'))
 save('metrics/BLENDER_METRICS.json',rows);table('BLENDER_METRICS.csv',rows);save('metrics/BLENDER_TRANSFORMS.json',T);save('provenance/EVALUATION_COMPLETE.json',dict(epoch=time.time(),models=len(rows),predictions_unchanged=all(sha(x['path'])==x['sha256']for x in frozen['files']),no_configuration_selection_using_GT=True));print('EVALUATION_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
