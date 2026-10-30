"""One single-scene optimization around official MonoSDF, no new renderer."""
from pathlib import Path
import sys,os,time,json,traceback,ast,hashlib
R=Path(__file__).resolve().parents[1]
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['MPLCONFIGDIR']=str(R/'runtime/mpl')
sys.path[:0]=[str(R/'runtime/python'),str(R/'runtime/monosdf_official/code')]
from audit import load,save,sha,normal,extract,vis
import numpy as np,cv2,torch
from PIL import Image

def main():
 result=dict(arm='S',scene='G01_005',official_repo_commit='12513009cd20a08b35ddc2c55a7e42da2c7baf43',status='INITIALIZING',optimizer_steps=0,GT_used=False,CPU_fallback=False)
 folder=R/'local_results/sdf_scene';folder.mkdir(parents=True,exist_ok=True)
 assert not (R/'provenance/SDF_RUN_RESULT.json').exists(),'single optimization already attempted'
 q=load(R/'config/sdf_minimal.json');scale=q['scene_scale_mm_per_network_unit'];start=time.monotonic()
 try:
  assert torch.cuda.is_available();torch.set_num_threads(2);torch.manual_seed(q['seed']);np.random.seed(q['seed'])
  # The executed official MLP, ray sampler, rendering and density are unchanged.
  # Defer only the unused grid CUDA import so an MLP run needs no nvcc.
  network=R/'runtime/monosdf_official/code/model/network.py';original=network.read_text();line='from hashencoder.hashgrid import _hash_encode, HashEncoder\n'
  assert original.count(line)==1
  modified=original.replace(line,'')
  anchor='class ImplicitNetworkGrid(nn.Module):'
  a,b=modified.split(anchor,1);b=b.replace('        super().__init__()','        from hashencoder.hashgrid import _hash_encode, HashEncoder\n        super().__init__()',1)
  network.write_text(a+anchor+b)
  import difflib
  patch=''.join(difflib.unified_diff(original.splitlines(True),network.read_text().splitlines(True),fromfile='official/network.py',tofile='local/network.py'))
  (R/'provenance/MONOSDF_LAZY_IMPORT.patch').write_text(patch)
  from model.network import MonoSDFNetwork
  from model.loss import MonoSDFLoss
  from pyhocon import ConfigFactory
  registry=load(R/'provenance/INPUT_ELIGIBILITY.json')['references'];sources=[];files=[]
  for cid in q['input_ids']:
   c=next(x for x in registry if x['id']==cid);p=np.load(c['pack']);rgb=np.asarray(Image.open(c['RGB']).convert('RGB'))/255.;mask=np.asarray(Image.open(c['Mask']));z=p['depth_mm'];weight=np.ones_like(z)
   points=np.load(c['source_points']);uv=points['uv']if'uv'in points else points['source_uv'];cl=np.load(c['cleaned_flags']['path'])['clean_removed'];weight[uv[:,1],uv[:,0]]=np.where(cl,.25,1.)
   fg=(mask==1)&np.isfinite(z)&(z>0);bg=(cv2.dilate((mask==1).astype(np.uint8),np.ones((41,41),np.uint8))>0)&(mask==0)
   K4=np.eye(4);K4[:3,:3]=p['K'];pose=p['pose'].copy();pose[:3,3]/=scale
   sources.append(dict(id=cid,c=c,z=z,rgb=rgb,mask=mask,weight=weight,fg=np.argwhere(fg),bg=np.argwhere(bg),K=p['K'],pose_mm=p['pose'],input=dict(intrinsics=torch.tensor(K4[None],dtype=torch.float32,device='cuda'),pose=torch.tensor(pose[None],dtype=torch.float32,device='cuda'))))
   files +=[Path(c[k])for k in ['RGB','Mask','pack','source_points']]+[Path(c['cleaned_flags']['path'])]
  executed=[R/'code/sdf_run.py',R/'config/sdf_minimal.json',network,*sorted((R/'runtime/monosdf_official/code/model').glob('*.py')),*sorted((R/'runtime/monosdf_official/code/utils').glob('*.py'))]
  save('provenance/SDF_BEFORE_OPTIMIZATION_FREEZE.json',dict(time=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),files=[dict(path=str(p),sha256=sha(p))for p in dict.fromkeys(files+executed)],inputs=q['input_ids'],targets_excluded_from_fitting=q['target_ids_evaluation_only'],GT_ACCESS='DENY',official_executed_MLP_and_renderer_unchanged=True,patch='inactive-grid import deferred only'))
  torch.cuda.reset_peak_memory_stats();model=MonoSDFNetwork(ConfigFactory.from_dict(q['model'])).cuda();model.train();optimizer=torch.optim.Adam(model.parameters(),lr=q['learning_rate']);rng=np.random.default_rng(q['seed']);steps=[];opt_start=time.monotonic()
  for step in range(q['optimization_max_steps']):
   if time.monotonic()-opt_start>q['optimization_max_seconds']:break
   s=sources[step%len(sources)];fg=s['fg'][rng.integers(len(s['fg']),size=q['foreground_rays'])];bg=s['bg'][rng.integers(len(s['bg']),size=q['background_rays'])];yx=np.r_[fg,bg];uv=yx[:,::-1].copy();n=len(fg)
   inp=dict(s['input'],uv=torch.tensor(uv[None],dtype=torch.float32,device='cuda'));out=model(inp,torch.tensor([step%len(sources)],device='cuda'))
   expected_rgb=torch.tensor(s['rgb'][yx[:n,0],yx[:n,1]],dtype=torch.float32,device='cuda');expected_z=torch.tensor(s['z'][yx[:n,0],yx[:n,1]]/scale,dtype=torch.float32,device='cuda')
   w=torch.tensor(s['weight'][yx[:n,0],yx[:n,1]],dtype=torch.float32,device='cuda');lrgb=abs(out['rgb_values'][:n]-expected_rgb).mean();ldepth=(w*torch.nn.functional.smooth_l1_loss(out['depth_values'][:n,0],expected_z,reduction='none',beta=q['depth_huber_beta_mm']/scale)).mean()
   acc=out['weights'].sum(-1).clamp(1e-5,1-1e-5);truth=torch.cat([torch.ones(n,device='cuda'),torch.zeros(len(bg),device='cuda')]);lsil=torch.nn.functional.binary_cross_entropy(acc,truth);leik=MonoSDFLoss.get_eikonal_loss(None,out['grad_theta']);loss=lrgb+.1*lsil+ldepth+.1*leik
   if not torch.isfinite(loss):raise FloatingPointError('nonfinite loss')
   optimizer.zero_grad(set_to_none=True);loss.backward();optimizer.step();result['optimizer_steps']=step+1
   row=dict(step=step+1,loss=float(loss.detach()),rgb=float(lrgb.detach()),depth=float(ldepth.detach()),silhouette=float(lsil.detach()),eikonal=float(leik.detach()),seconds=time.monotonic()-opt_start);steps.append(row)
   if step%25==0:print('SDF',row,flush=True)
  torch.cuda.synchronize();result.update(optimization_seconds=time.monotonic()-opt_start,peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated(),peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved(),parameters=sum(p.numel()for p in model.parameters()),stop_reason='STEP_LIMIT'if result['optimizer_steps']==q['optimization_max_steps']else'TIME_LIMIT')
  torch.save(model.state_dict(),folder/'model.pt');save('metrics/SDF_LOSS_TRACE.json',steps)
  # Freeze trained output before any holdout RGB/Mask read. Extract only afterward.
  save('provenance/SDF_MODEL_FROZEN.json',dict(model=str(folder/'model.pt'),sha256=sha(folder/'model.pt'),config_SHA256=sha(R/'config/sdf_minimal.json'),steps=result['optimizer_steps'],GT_used=False,holdout_images_read=False))
  model.eval();from skimage.measure import marching_cubes
  N=q['surface_grid_resolution'];lo,hi=q['surface_grid_bounds_mm'];lin=np.linspace(lo,hi,N);xx,yy,zz=np.meshgrid(lin,lin,lin,indexing='ij');grid=np.stack([xx,yy,zz],-1).reshape(-1,3);values=[]
  with torch.no_grad():
   for st in range(0,len(grid),8192):values.append(model.implicit_network.get_sdf_vals(torch.tensor(grid[st:st+8192]/scale,dtype=torch.float32,device='cuda')).cpu().numpy().reshape(-1))
  field=np.concatenate(values).reshape(N,N,N);P,F,_,_=marching_cubes(field,0,spacing=((hi-lo)/(N-1),)*3);P=P+lo
  def support(P):
   known=np.zeros(len(P),bool);best=np.full(len(P),np.inf);C=np.full((len(P),3),.55)
   for s in sources:
    uv,z=vis.project_camera(P,s['K'],s['pose_mm']);xy=np.rint(np.nan_to_num(uv,nan=-1e6)).astype(int);valid=(z>0)&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);ids=np.flatnonzero(valid);x,y=xy[ids].T;err=abs(s['z'][y,x]-z[ids]);ok=(s['mask'][y,x]==1)&np.isfinite(err)&(err<=q['support_depth_tolerance_mm']);take=ids[ok];known[take]=True;replace=ok&(err<best[ids]);ids=ids[replace];best[ids]=err[replace];C[ids]=s['rgb'][xy[ids,1],xy[ids,0]]
   return known,C
  point_supported,C=support(P);face_supported,_=support(P[F].mean(1));supported_faces=F[face_supported];selected=np.unique(supported_faces);area=np.linalg.norm(np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]),axis=1)/2
  np.savez_compressed(folder/'surface.npz',XYZ_mm=P,RGB=C,faces=F,point_observed_support=point_supported,face_observed_support=face_supported,face_prior_or_unknown=~face_supported,source_input_ids=q['input_ids'],unit='mm',depth_type='SDF zero-level set; HERO-supported domain separately labelled')
  import trimesh
  trimesh.Trimesh(P,F,vertex_colors=np.rint(C*255).astype(np.uint8),process=False).export(folder/'raw_zero_level_set.ply')
  trimesh.Trimesh(P,supported_faces,vertex_colors=np.rint(C*255).astype(np.uint8),process=False).export(folder/'observed_supported_open_mesh.ply')
  result.update(status='SMOKE_PASS_UNCERTIFIED_GEOMETRY',zero_level_vertices=len(P),zero_level_faces=len(F),supported_faces=int(face_supported.sum()),supported_vertex_N=len(selected),zero_level_area_mm2=float(area.sum()),observed_support_area_mm2=float(area[face_supported].sum()),prior_or_unknown_area_mm2=float(area[~face_supported].sum()),output=str(folder/'surface.npz'),output_SHA256=sha(folder/'surface.npz'),support_is_conditional_on_HERO_and_camera=True)
 except Exception:
  result.update(status='FAILED',error=traceback.format_exc());print(result['error'],flush=True)
 result['total_seconds']=time.monotonic()-start;save('provenance/SDF_RUN_RESULT.json',result);print('SDF_RESULT',result,flush=True)
if __name__=='__main__':main()
