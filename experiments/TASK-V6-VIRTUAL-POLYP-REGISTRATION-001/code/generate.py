"""Generator only. Original static mesh and ray caster; stable material colour extension."""
import cv2
import numpy as np
from scipy.spatial.transform import Rotation
from common import *
from ring_first_3d.sim.scene import synthesize
from ring_first_3d.sim.geometry import transform,se3,cast,scene
from ring_first_3d.contracts.coordinates import project,unproject,validate_c2w,validate_ring
from ring_first_3d.multisurface.geometry import depth_grid_mesh,sample_mesh
from ring_first_3d.multisurface.scene import noise_vectors

def texture(P):
 rng=np.random.default_rng(CFG['texture_seed']);P=np.asarray(P);value=np.zeros(len(P))
 for freq in CFG['texture_frequencies']:
  directions=rng.normal(size=(CFG['texture_modes'],3));directions/=np.linalg.norm(directions,axis=1)[:,None];phases=rng.uniform(0,2*np.pi,len(directions))
  value+=np.sin(P@(directions*freq).T+phases).sum(1)/np.sqrt(len(directions))
 grey=np.clip(132+47*value,30,232);return np.stack([grey,np.clip(grey*.72+20,0,255),np.clip(grey*.78+15,0,255)],1).astype(np.uint8)

def generate():
 assert not RUN.exists(),'Run exists; never overwrite observations'
 public=RUN/'public';private=RUN/'private'
 for p in [public/'images',public/'observations',public/'meshes',public/'conditions',private]:p.mkdir(parents=True,exist_ok=True)
 src=read(T/'inputs/VIEW_SOURCES.json');views=src['selected']+src['HOLDOUT'];gt=dict(np.load(T/'inputs/virtual_GT.npz'));ring=dict(np.load(T/'inputs/canonical_ring.npz'));V,F=gt['V'],gt['F'];RV,RF=ring['V'],ring['F'];validate_ring(RV,10)
 records=[];truth={};audit=[];masks={};depths={}
 for row in views:
  cid=row['view_id'];C=np.array(row['Camera_to_Ring']);K=np.array(row['K']);validate_c2w(C)
  obs,b,rg=synthesize(V,F,RV,RF,K,C);rgb=np.full_like(obs['RGB'],[104,65,61]);valid=obs['labels']==1;rgb[valid]=texture(b['points'][valid]);rgb[obs['labels']==2]=[24,24,24]
  # Keep the original labels/depth exactly, changing appearance only.
  obs['RGB']=rgb;np.savez_compressed(public/'observations'/(cid+'.npz'),**obs,K=K)
  cv2.imwrite(str(public/'images'/(cid+'.png')),rgb[:,:,::-1]);cv2.imwrite(str(public/'images'/(cid+'_labels.png')),obs['labels'])
  mesh,info=depth_grid_mesh(obs['depth_axial_mm'],obs['labels'],K,CFG['stride'],CFG['edge_limit_mm']);np.savez_compressed(public/'meshes'/(cid+'.npz'),**mesh)
  q=mesh['uv'].astype(int);err=np.max(np.linalg.norm(transform(mesh['V'],C)-b['points'][q[:,1],q[:,0]],axis=1));assert err<.001
  records.append(dict(id=cid,video=row['video'],role=row['role'],K=K,synthetic_trajectory_source=row['source_id'],proxy=CFG['proxy']))
  truth[cid]=dict(C=C,K=K,video=row['video'],role=row['role']);masks[cid]=obs['labels'];depths[cid]=obs['depth_axial_mm'];audit.append(dict(id=cid,**info,unproject_max_mm=err,RGB_sha256=sha(public/'images'/(cid+'.png')),mesh_sha256=sha(public/'meshes'/(cid+'.npz'))))
  print('RENDER',cid,row['role'],len(mesh['F']),flush=True)
 save(public/'FRAMES.json',records)
 D=np.eye(4);D[:3,:3]=Rotation.from_euler('z',30,degrees=True).as_matrix()@Rotation.from_euler('y',3,degrees=True).as_matrix();D[:3,3]=[.3,0,0]
 injection={};contract=[]
 for cond in cases():
  bias=np.eye(4) if cond=='V0' else D;noise={v:np.zeros((sum(r['video']==v for r in records),6))for v in ['004','005']}
  if cond.startswith('V2'):
   seed=int(cond.split('_')[1]);noise=noise_vectors({'x':{'sigma':{'004':[0,0],'005':[CFG['sigma_rotation_deg'],CFG['sigma_translation_mm']]}}},records,seed)['x']
  frames=[];counts={'004':0,'005':0};injection[cond]={}
  for r in records:
   cid=r['id'];v=r['video'];C=np.array(truth[cid]['C']);d=np.eye(4) if v=='004' else bias;q=noise[v][counts[v]];counts[v]+=1;N=se3(np.r_[np.deg2rad(q[:3]),q[3:]]);estimated=d@C@N
   frames.append(dict(id=cid,video=v,role=r['role'],C=estimated));injection[cond][cid]=dict(D=d,N=N,true_C=C)
   if cond in ['V0','V1']:
    mesh=np.load(public/'meshes'/(cid+'.npz'));P=transform(mesh['V'][::97],C);uv,z=project(P,r['K'],C);newuv,newz=project(transform(P,d),r['K'],estimated);record=dict(condition=cond,id=cid,projection_max_px=np.max(abs(uv-newuv)),axial_Z_max_mm=np.max(abs(z-newz)));assert record['projection_max_px']<1e-8 and record['axial_Z_max_mm']<1e-8;contract.append(record)
  save(public/'conditions'/(cond+'.json'),dict(frames=frames,ring={'004':dict(center=[0,0,0],normal=[0,0,1],radius_mm=5.6,wire_mm=.6),'005':dict(center=bias[:3,3],normal=bias[:3,2],radius_mm=5.6,wire_mm=.6)},measurement_error_family='per_frame_camera'if cond.startswith('V2')else'coordinate_change'))
  # Full video relative poses invariant for pure coordinate transforms.
  if cond in ['V0','V1']:
   for video in ['004','005']:
    seq=[r for r in frames if r['video']==video];ref=seq[0]
    for rr in seq:
     before=np.linalg.inv(truth[ref['id']]['C'])@truth[rr['id']]['C'];after=np.linalg.inv(ref['C'])@rr['C'];assert np.max(abs(before-after))<1e-8
 save(private/'TRUTH.json',dict(frames=truth,injections=injection));save(T/'evidence/GENERATION_AUDIT.json',dict(views=audit,contracts=contract,material='Object/world locked deterministic texture; constant background',original_geometric_generator=True,shape_sha256=sha(T/'inputs/virtual_GT.npz'),ring_sha256=sha(T/'inputs/canonical_ring.npz')))
 # Fixed GT sample target masks, independent of predictions/methods.
 P,face,bary=sample_mesh(V,F,CFG['GT_samples'],CFG['GT_seed']);vis={};sceneGT=scene(V,F);sceneRing=scene(RV,RF)
 for r in records:
  cid=r['id'];C=truth[cid]['C'];K=r['K'];pc=(P-C[:3,3])@C[:3,:3];uv=pc@np.array(K).T;uv=uv[:,:2]/uv[:,2:];inside=(pc[:,2]>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360);ix=np.flatnonzero(inside);visible=np.zeros(len(P),bool)
  z,_,_=cast(sceneGT,uv[ix],K,C);rz,_,_=cast(sceneRing,uv[ix],K,C);visible[ix]=(abs(z-pc[ix,2])<.001)&(z<rz);vis[cid]=visible
 maskvid={v:np.any([vis[r['id']]for r in records if r['video']==v and r['role']=='FIT'],axis=0)for v in ['004','005']}
 np.savez_compressed(private/'GT_TARGETS.npz',P=P,face=face,bary=bary,visible004=maskvid['004'],visible005=maskvid['005'],**{k:v for k,v in vis.items()})
 save(T/'evidence/FIXED_DOMAIN.json',dict(total=len(P),union=int((maskvid['004']|maskvid['005']).sum()),overlap=int((maskvid['004']&maskvid['005']).sum()),only004=int((maskvid['004']&~maskvid['005']).sum()),only005=int((maskvid['005']&~maskvid['004']).sum()),frames=records))
 save(RUN/'GENERATION_FREEZE.json',dict(config_sha256=sha(T/'config.json'),sources=freeze((T/'code').glob('*.py')),public=freeze(p for p in public.rglob('*')if p.is_file()),private=freeze(p for p in private.rglob('*')if p.is_file())))
if __name__=='__main__':generate()
