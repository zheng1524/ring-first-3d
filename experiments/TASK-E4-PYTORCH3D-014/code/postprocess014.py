"""Independent evaluation only after all predictions, method and metric scale freeze."""
from common import *
import shutil,subprocess,concurrent.futures,traceback
from score014 import evaluate
from safe_geometry import dense_face_distance,self_intersections
import open3d as o3d
OLD13=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013'
PY='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python'
BLENDER='/home/liu/blender/blender-5.0.1-linux-x64/blender'

def prediction_index():
 result=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name']
  for tag in ['FINAL011','FINAL012','FINAL013']:result.append(dict(case=n,label=tag,path=str(OLD13/'local_results/metric'/n/(tag+'.npz')),route='frozen historical evaluation control, not prediction fallback'))
  for root in sorted((R/'arms').iterdir()):
   if root.name=='PREFLIGHT':continue
   p=root/'local_results'/n/'FINAL.npz'
   if p.exists():result.append(dict(case=n,label='FINAL014'if root.name=='FINAL_014'else root.name,path=str(p),route='014 independent optimizer output from authorized inherited initialization'))
 return result

def native(m):
 n,tag,p=m['case'],m['label'],Path(m['path']);file=R/'metrics/native'/ (n+'_'+tag+'.json');file.parent.mkdir(exist_ok=True)
 if file.exists():d=load(file)
 else:d=evaluate(n,p,True,tag);save(file.relative_to(R),d)
 train=[]
 if tag in ['FINAL011','FINAL012','FINAL013']:train=[v['id']for c in load(R/'config/CASE_LOCK.json')if c['name']==n for v in c['views']if v['role']=='FIT']
 else:
  arm='FINAL_014'if tag=='FINAL014'else tag;train=[v['id']for v in load(R/'arms'/arm/'inputs'/n/'CASE.json')['views']if v['role']=='FIT']
 for row in d['per_view']:row['used_for_this_model_update']=row['view']in train;row['denominator']='fixed native observation pool; common FIT vs protected HOLDOUT, update membership separate'
 summary=dict(m,FIT_IoU=d['mean']['FIT']['IoU'],HOLDOUT_IoU=d['mean'].get('UPDATE_HOLDOUT',{}).get('IoU'),training_views_N=len(train),common_FIT_N=sum(v['role']=='FIT'for v in d['per_view']),HOLDOUT_N=sum(v['role']!='FIT'for v in d['per_view']),FIT=d['mean']['FIT'],HOLDOUT=d['mean'].get('UPDATE_HOLDOUT',{}))
 for role,prefix in [('FIT','FIT'),('UPDATE_HOLDOUT','HOLDOUT')]:
  dr=[v for v in d['per_view']if v['role']==role and v.get('fixed_depth_N',0)>0];NN=sum(v['fixed_depth_N']for v in dr);hits=sum(v['depth_hit_N']for v in dr);cost=sum(v['fixed_depth_N']*v['fixed_depth_cost']for v in dr);mae=sum(v['depth_hit_N']*v['depth_MAE_mm']for v in dr if v['depth_MAE_mm']is not None)
  summary.update({prefix+'_HERO_fixed_N':NN,prefix+'_HERO_hit_N':hits,prefix+'_HERO_hit_rate':hits/NN if NN else None,prefix+'_HERO_fixed_cost':cost/NN if NN else None,prefix+'_HERO_MAE_active_mm':mae/hits if hits else None})
 # Frozen camera/Mask/CAD first-ray evidence, not hidden-surface truth.
 z=np.load(p);V,F=z['V'],z['F'];P=V[F].mean(1);rt=scene(V,F);rr=np.load(R/'inputs'/n/'RING.npz');rs=scene(rr['V'],rr['F']);support=np.zeros(len(F),bool)
 for v in getcase(n)['views']:
  if v['id']not in train:continue
  a=np.load(R/'inputs'/n/(v['id']+'.npz'));cam=(P-a['T'][:3,3])@a['T'][:3,:3];pix=cam@a['K'].T;uv=pix[:,:2]/pix[:,2:];rays=np.c_[np.broadcast_to(a['T'][:3,3],P.shape),(P-a['T'][:3,3])/np.maximum(cam[:,2,None],1e-12)].astype(np.float32);first=rt.cast_rays(o3d.core.Tensor(rays),nthreads=2)['t_hit'].numpy();cad=rs.cast_rays(o3d.core.Tensor(rays),nthreads=2)['t_hit'].numpy();inside=(cam[:,2]>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360);ij=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);support|=inside&(a['labels'][ij[:,1],ij[:,0]]==1)&(cam[:,2]<cad)&(abs(cam[:,2]-first)<.05)
 depth_support=np.zeros(len(F),bool)
 for cid in train:
  p=R/'depth_observations'/(cid+'.npz')
  if not p.exists():continue
  a=np.load(p);ray=np.c_[a['uv'],np.ones(len(a['uv']))]@np.linalg.inv(a['K']).T;T=a['T'];rays=np.c_[np.broadcast_to(T[:3,3],ray.shape),ray@T[:3,:3].T].astype(np.float32);hit=rt.cast_rays(o3d.core.Tensor(rays),nthreads=2);zz=hit['t_hit'].numpy();fid=hit['primitive_ids'].numpy().astype(int);rz=rs.cast_rays(o3d.core.Tensor(rays),nthreads=2)['t_hit'].numpy();good=(fid<len(F))&np.isfinite(zz)&(zz<rz-.05)&(abs(zz-a['z'])<=.5)&(a['boundary_weight']>=.5);depth_support[fid[good]]=True
 area=trimesh.triangles.area(V[F]);summary.update(contour_supported_area_fraction=float(area[support].sum()/area.sum()),sampled_HERO_supported_area_fraction=float(area[depth_support].sum()/area.sum()),evidence_note='sparse sameview HERO tolerance0.5mm; absence of sampled support is UNKNOWN, not false surface')
 out=R/'local_results/native_eval'/n;out.mkdir(parents=True,exist_ok=True);np.savez_compressed(out/(tag+'_FACE_EVIDENCE.npz'),face_supported=support,sampled_HERO_supported=depth_support,definition='FIT camera+Mask+first-ray/sparse HERO proxies, not physicalGT');return summary,d['per_view']

def geometric_audit(models):
 rows=[]
 for m in models:
  n,tag=m['case'],m['label'];z=np.load(m['path']);V,F=z['V'],z['F_solid'];rr=np.load(R/'inputs'/n/'RING.npz');rs=scene(rr['V'],rr['F']);sd=dense_face_distance(rs,V,F,rr['V'],64,rr['F']);initial=np.load(R/'inputs'/n/'INITIAL.npz');s0=dense_face_distance(rs,initial['V'],initial['F_solid'],rr['V'],64,rr['F']);penetration=max(0.,-float(sd.min()));before=max(0.,-float(s0.min()));tm=trimesh.Trimesh(V,F,process=False);cm=trimesh.collision.CollisionManager();cm.add_object('Ring',trimesh.Trimesh(rr['V'],rr['F'],process=False));edges=np.sort(np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],axis=1);_,counts=np.unique(edges,axis=0,return_counts=True);si=self_intersections(V,F);base=load(R/'inputs'/n/'BASE_SELECTION.json')['selected_plane'];base=np.asarray(base);h=V@base[:3]+base[3];row=dict(case=n,label=tag,vertices=len(V),triangles=len(F),Ring_surface_collision=cm.in_collision_single(tm),Ring_max_material_penetration_mm=penetration,INITIAL011_penetration_mm=before,new_penetration_vs011_mm=max(0.,penetration-before),Ring_worsening_within_epsilon=penetration<=before+1e-5,Ring_epsilon_mm=1e-5,self_intersections_Open3D=si['intersections'],watertight=tm.is_watertight,winding_consistent=tm.is_winding_consistent,nonmanifold_edges_N=int((counts>2).sum()),open_solid_edges_N=int((counts<2).sum()),connected_components=len(tm.split(only_watertight=False)),degenerate_faces_N=int((tm.area_faces<1e-14).sum()),inferred_cap_faces_N=int(z['inferred_base_faces'].sum()),base_illegal_vertices_N=int((h<-1e-7).sum())if z['inferred_base_faces'].any()else None,minimum_base_height_mm=float(h.min()),surface_area_mm2=float(tm.area),conditional_closed_volume_mm3=float(abs(tm.volume))if tm.is_watertight else None,GT_read=False);rows.append(row);print('GEOMETRY64',n,tag,penetration,si['intersections'],flush=True)
  body=trimesh.Trimesh(V,z['F'],process=False);theta=body.face_adjacency_angles;ee=body.face_adjacency_edges;length=np.linalg.norm(V[ee[:,0]]-V[ee[:,1]],axis=1);row.update(body_normal_variation_per_mm=float((length*theta).sum()/max(body.area,1e-20)),body_dihedral_p95_deg=float(np.degrees(np.quantile(theta,.95)))if len(theta)else None,body_dihedral_max_deg=float(np.degrees(theta.max()))if len(theta)else None,roughness_note='area-normalized integrated normal variation, geometric proxy not calibrated anatomical truth; cap excluded')
 table('metrics/POST_GEOMETRY_AUDIT.csv',rows);save('metrics/POST_GEOMETRY_AUDIT.json',rows)

def main():
 freeze=R/'provenance/ALL_014_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json'
 assert freeze.exists(),'No evaluation before final prediction and scale freeze'
 for a in load(freeze)['files']:assert sha(a['path'])==a['sha256'],a['path']
 models=prediction_index();save('config/EVAL_MODELS.json',models);summary=[];per=[]
 for m in models:
  a,b=native(m);summary.append(a);per+=b;print('NATIVE_EVAL',m['case'],m['label'],flush=True)
 save('metrics/NATIVE_SUMMARY.json',summary);table('metrics/NATIVE_SUMMARY.csv',summary);save('metrics/PER_VIEW_METRICS.json',per);table('PER_VIEW_METRICS.csv',per);geometric_audit(models)
 # Independent Blender BVH geometry check on frozen predictions, no GT loading.
 script=OLD13/'code/blender_geometry_checks.py'
 with(R/'runtime/BLENDER_POST_GEOMETRY.log').open('w')as f:subprocess.run([BLENDER,'-b','--factory-startup','-t','2','--python',str(script),'--',str(R)],stdout=f,stderr=subprocess.STDOUT,check=True)
 # This is the first opening of Blender source metadata/geometry in 014.
 save('provenance/GT_ACCESS_START.json',dict(epoch=time.time(),prediction_freeze=asset(freeze),evaluation_only=True,source='unchanged013 author-identity lock; no GT selection'))
 (R/'evaluation_only').mkdir(exist_ok=True)
 for filename in ['GT_SOURCE_LOCK.json']:
  shutil.copyfile(OLD13/'evaluation_only'/filename,R/'evaluation_only'/filename)
 shutil.copyfile(OLD13/'metrics/GT_VALIDITY.json',R/'metrics/GT_VALIDITY.json')
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];folder=R/'evaluation_only'/n;folder.mkdir(exist_ok=True);source=OLD13/'evaluation_only'/n/'ORIGINAL_BLENDER_GT_MM.npz';dest=folder/source.name
  if source.exists()and not dest.exists():dest.symlink_to(source)
 for m in models:
  n,tag=m['case'],m['label'];folder=R/'local_results/metric'/n;folder.mkdir(parents=True,exist_ok=True);p=folder/(tag+'.npz')
  if not p.exists():p.symlink_to(Path(m['path']).resolve())
  if tag in ['FINAL011','FINAL012','FINAL013']:
   cache=OLD13/'metrics/alignment'/(n+'_'+tag+'_STARTS.json');dest=R/'metrics/alignment'/cache.name;dest.parent.mkdir(exist_ok=True)
   if cache.exists()and not dest.exists():shutil.copyfile(cache,dest)
   aligned=OLD13/'local_results/aligned'/n/(tag+'.npz');dest=R/'local_results/aligned'/n/(tag+'.npz');dest.parent.mkdir(parents=True,exist_ok=True)
   if aligned.exists()and not dest.exists():shutil.copyfile(aligned,dest)
 # Exact 013 align/metric implementation; only stage enumeration is generalized.
 text=(OLD13/'code/best_rigid.py').read_text();text=text.replace(" for a in load(R/'assets_index/SCALE_LOCK_BEFORE_GT.json')['files']:assert sha(a['path'])==a['sha256']", " for a in load(R/'provenance/ALL_014_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json')['files']:assert sha(a['path'])==a['sha256']")
 text=text.replace("for tag in ['FINAL011','FINAL012','FINAL013']:","for tag in [m['label'] for m in load(R/'config/EVAL_MODELS.json') if m['case']==n]:")
 text=text.replace('FIT_2D_IoU_original_cameras','FIT_2D_IoU_fixed014_evaluation_cameras').replace('HOLDOUT_2D_IoU_original_cameras','HOLDOUT_2D_IoU_fixed014_evaluation_cameras')
 evaluator=R/'code/best_rigid014.py';evaluator.write_text(text);save('provenance/EVALUATOR_REUSE.json',dict(original=asset(OLD13/'code/best_rigid.py'),adapted=asset(evaluator),changes=['freeze manifest path','stage enumeration only'],alignment_and_metrics_unchanged=True,old_transform_cache='identical frozen prediction and GT; same 96seeds/top8 symmetric surface algorithm',GT_access_after_freeze=True))
 def worker(n):
  p=R/'metrics/eval_case'/(n+'_BLENDER_GEOMETRIC_METRICS.json')
  if not p.exists():
   with(R/'runtime'/('BEST_SE3_'+n+'.log')).open('w')as f:subprocess.run([PY,'-B',str(evaluator),'--case',n],stdout=f,stderr=subprocess.STDOUT,check=True)
  return n
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(worker,[c['name']for c in load(R/'config/CASE_LOCK.json')]))
 rows=[];Ts=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];rows+=load(R/'metrics/eval_case'/(n+'_BLENDER_GEOMETRIC_METRICS.json'));Ts+=load(R/'metrics/eval_case'/(n+'_BLENDER_RIGID_ALIGNMENT.json'))
 save('metrics/BLENDER_ALIGNMENT_METRICS.json',rows);table('BLENDER_ALIGNMENT_METRICS.csv',rows);save('metrics/BLENDER_RIGID_TRANSFORMS.json',Ts);save('provenance/INDEPENDENT_EVALUATION_COMPLETE.json',dict(epoch=time.time(),models=len(rows),GT_used_for_optimization=False,predictions_still_match_freeze=all(sha(a['path'])==a['sha256']for a in load(freeze)['files'])));print('INDEPENDENT_EVALUATION_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
