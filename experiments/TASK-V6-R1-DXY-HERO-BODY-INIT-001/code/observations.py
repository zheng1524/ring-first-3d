"""Fixed original-pixel HERO samples inside trusted triangles, plus native background ROIs."""
from geometry import *
import cv2,importlib
import open3d as o3d
from scipy.ndimage import distance_transform_edt
CFG=read(T/'config.json')
def scene(V,F):
 s=o3d.t.geometry.RaycastingScene();s.add_triangles(o3d.core.Tensor(np.asarray(V,np.float32)),o3d.core.Tensor(np.asarray(F,np.uint32)));return s
def cast(s,r):
 a=s.cast_rays(o3d.core.Tensor(np.asarray(r,np.float32)));return a['t_hit'].numpy(),a['primitive_ids'].numpy().astype(np.int64)
def measure(rgb,labels,radius,source):
 lock=read(snapshot(BASE,'src/ring_first_3d/source_lock.json'))
 ns=dict(np=np,Path=Path,sys=sys,subprocess=subprocess,hashlib=hashlib,importlib=importlib,LOCK=lock,sha256=sha)
 p=snapshot(BASE,'src/ring_first_3d/adapters/dxy.py');tree=ast.parse(p.read_text())
 # QUALITY is a literal tuple, while executable imports remain caller-controlled.
 ns['QUALITY']=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(k,ast.Name)and k.id=='QUALITY'for k in n.targets)))
 definitions(BASE,'src/ring_first_3d/adapters/dxy.py',['verify_dxy','measure_pixels'],ns)
 return ns['measure_pixels'](rgb,labels,inner_diameter_mm=2*(radius-.6),source_id=source,dxy_root='/home/liu/new-polyp-dxy')
def pick(ix,n):return np.asarray(ix)[np.linspace(0,len(ix)-1,min(n,len(ix))).astype(int)]if len(ix)else np.asarray(ix)
def frame_data(video,j,C,K,out,role):
 f=video['frames'][j];rgb=cv2.imread(f['RGB_path'])[:,:,::-1];lab=cv2.imread(f['Mask_path'],0);assert rgb.shape[:2]==lab.shape
 assert sha(f['RGB_path'])==f['RGB_SHA256']and sha(f['Mask_path'])==f['Mask_SHA256']
 dfile=out/(f['id']+'_DXY.json')
 receipt=out/(f['id']+'_DXY_CACHE.json');dk=digest([f['RGB_SHA256'],f['Mask_SHA256'],sha(snapshot(BASE,'src/ring_first_3d/adapters/dxy.py')),'75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95'])
 if dfile.exists()and receipt.exists()and read(receipt)['key']==dk:
  asset(dfile,read(receipt)['sha256']);dxy=read(dfile)
 else:
  dxy=measure(rgb,lab,video['ring_radius_mm'],video['case']+':'+f['id']);save(dfile,dxy);save(receipt,dict(key=dk,sha256=sha(dfile)))
 contours,_=cv2.findContours((lab==1).astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
 q=np.concatenate([x[:,0,:]for x in contours])if contours else np.zeros((0,2),int)
 adj=cv2.dilate((lab==2).astype(np.uint8),np.ones((7,7),np.uint8))
 if len(q):q=q[(adj[q[:,1],q[:,0]]==0)&(q[:,0]>1)&(q[:,0]<lab.shape[1]-2)&(q[:,1]>1)&(q[:,1]<lab.shape[0]-2)]
 q=pick(q,CFG['boundary_samples']);yy,xx=np.mgrid[8:lab.shape[0]:CFG['mask_grid_step'],8:lab.shape[1]:CFG['mask_grid_step']];uv=np.c_[xx.ravel(),yy.ravel()];target=lab[uv[:,1],uv[:,0]];keep=target!=2;uv=uv[keep];target=(target[keep]==1).astype(float)
 # Foreground and known background masses each remain fixed and equally weighted.
 w=.5*target/max(target.sum(),1)+.5*(1-target)/max((1-target).sum(),1)
 data=dict(case=video['case'],index=j,id=f['id'],role=role,C=C,K=K,uv=uv,target=target,grid_weight=w,rays=rays(uv,K,C),boundary=q,boundary_rays=rays(q,K,C),DXY=dxy,RGB=f['RGB_path'],Mask=f['Mask_path'],source_frame=f)
 np.savez_compressed(out/(f['id']+'_2D.npz'),**{k:data[k]for k in ['C','K','uv','target','grid_weight','rays','boundary','boundary_rays']})
 return data
def prepare_video(a,v):
 out=T/'runs/observations'/a['group']/v['case'];out.mkdir(parents=True,exist_ok=True)
 c=dict(np.load(v['camera']));K=c['K'];transform=np.array(a['transforms'].get(v['case'],np.eye(4)))
 # Identity here is explicitly a standalone LOCAL coordinate frame, never a joint transform.
 C=transform@c['c2w'];coord='COMMON'if v['case']in a['transforms']else 'VIDEO_LOCAL_UNCONNECTED'
 pool=v['pool'];remaining=[j for j in range(len(v['frames']))if j not in pool];held=pick(remaining,CFG['held_frames_per_video']).tolist()
 fs=[frame_data(v,int(j),C[j],K,out,'FIT'if j in pool else'HOLDOUT')for j in pool+held]
 ss=[];audit=[]
 for source in [s for s in a['sources']if s['case']==v['case']]:
  sid=source['source_id'];dst=out/(source['tag']+'_OBS.npz');meta=dst.with_suffix('.json');source_meta=next(z for z in a['source_metadata']if z['source_id']==sid);sf=v['frames'][source['reference']];key=digest([sha(Path(__file__)),source,source_meta,CFG,v['camera_sha256'],sf['RGB_SHA256'],sf['Mask_SHA256'],transform])
  if dst.exists()and meta.exists()and read(meta)['key']==key:
   rec=read(meta);asset(dst,rec['observations_sha256'])
   for item in rec['source_files']:asset(item['path'],item['sha256'])
   x=dict(np.load(dst));x['meta']=rec;ss.append(x);continue
  asset(source['raw_mesh'],source['raw_mesh_sha256']);asset(source['native_depth'],source['native_sha256']);asset(source['selection'],source['selection_sha256'])
  asset(sf['RGB_path'],sf['RGB_SHA256']);asset(sf['Mask_path'],sf['Mask_SHA256']);asset(source_meta['cad_path'],source_meta['cad_sha256'])
  m=trimesh.load(source['raw_mesh'],process=False);V=np.asarray(m.vertices)@transform[:3,:3].T+transform[:3,3];F=np.asarray(m.faces)
  selection=np.load(source['selection'])['trusted_original_face_id'];trusted=np.zeros(len(F),bool);trusted[selection]=True
  native=np.load(source['native_depth']);D=native['depth_mm'];Kn=native['K_index_native'];j=source['reference'];CC=C[j];f=v['frames'][j];lab=cv2.imread(f['Mask_path'],0);rgb=cv2.imread(f['RGB_path'])
  yy,xx=np.mgrid[:D.shape[0],:D.shape[1]];uv=np.c_[xx.ravel(),yy.ravel()];r=rays(uv,Kn,CC);q=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(Kn).T@K.T;full=q[:,:2]/q[:,2,None];px=np.rint(full).astype(int);inside=(px[:,0]>=0)&(px[:,0]<lab.shape[1])&(px[:,1]>=0)&(px[:,1]<lab.shape[0]);px=np.clip(px,[0,0],[lab.shape[1]-1,lab.shape[0]-1]);labels=lab[px[:,1],px[:,0]]
  valid=inside&np.isfinite(D.ravel())&(D.ravel()>0);eligible=np.flatnonzero(valid&(labels==1)&(xx.ravel()%3==1)&(yy.ravel()%3==1))
  z,fid=cast(scene(V,F),r[eligible]);good=(fid>=0)&(fid<len(F))&np.isfinite(z);good[good]&=trusted[fid[good]];good&=abs(z-D.ravel()[eligible])<.1
  ids=pick(eligible[good],CFG['depth_samples_per_source']);lookup={int(i):int(k)for i,k in zip(eligible,fid)};faceids=np.array([lookup[int(i)]for i in ids],int)
  # Local attachment-neighborhood candidates, never the entire distant background.
  dist=distance_transform_edt(lab!=1)[px[:,1],px[:,0]];rd=distance_transform_edt(lab!=2)[px[:,1],px[:,0]];jump=np.zeros_like(D)
  for axis in [0,1]:
   diff=abs(np.diff(D,axis=axis));sl=[slice(None)]*2;sr=sl.copy();sl[axis]=slice(None,-1);sr[axis]=slice(1,None);jump[tuple(sl)]=np.maximum(jump[tuple(sl)],diff);jump[tuple(sr)]=np.maximum(jump[tuple(sr)],diff)
  bgok=valid&(labels==0)&(rd>3)&(dist>=5)&(dist<=60)&(jump.ravel()<=.75)&(rgb[px[:,1],px[:,0]].min(1)<245)
  bgids=pick(np.flatnonzero(bgok),CFG['background_samples_per_source']);X=corrected_points(r[ids],D.ravel()[ids],0.);bg=corrected_points(r[bgids],D.ravel()[bgids],0.)
  cadpath=next(z['cad_path']for z in a['source_metadata']if z['source_id']==sid);cad=np.load(cadpath);cadscene=scene(cad['V'],cad['F']);cad_z,_=cast(cadscene,r[ids]);bgcad,_=cast(cadscene,r[bgids]);bgvalid=D.ravel()[bgids]<bgcad-.05;bgids=bgids[bgvalid];bg=bg[bgvalid]
  x=dict(rays=r[ids],D=D.ravel()[ids],uv=uv[ids],native_pixel_id=ids,original_face_id=faceids,raw_X=X,bg_X=bg,bg_pixel_id=bgids,bg_distance_px=dist[bgids],C=CC,K=Kn,RGB_uv=full[ids],cad_z=cad_z)
  np.savez_compressed(dst,**x);rec=dict(key=key,observations_sha256=sha(dst),source=source,source_id=sid,case=v['case'],reference=j,raw_target=source['target'],support=source['support'],coordinate_frame=coord,selected_N=len(ids),candidate_N=len(eligible),trusted_candidate_N=int(good.sum()),trusted_total_faces=len(selection),background_N=len(bgids),foreground_only_bias=True,native_K=Kn,source_files=[asset(source['native_depth']),asset(source['raw_mesh']),asset(source['selection']),asset(cadpath),asset(sf['RGB_path']),asset(sf['Mask_path'])]);save(meta,rec);x['meta']=rec;ss.append(x)
 save(out/'INDEX.json',dict(case=v['case'],coordinate_frame=coord,transform=transform,frames=[dict(id=f['id'],index=f['index'],role=f['role'],DXY_available=f['DXY']['available'],RGB=asset(f['RGB']),Mask=asset(f['Mask']),DXY=asset(out/(f['id']+'_DXY.json')),observations_2D=asset(out/(f['id']+'_2D.npz')))for f in fs],sources=[s['meta']for s in ss],camera=asset(v['camera'],v['camera_sha256'])))
 print('OBS',v['case'],len(fs),len(ss),sum(len(s['D'])for s in ss),flush=True)
 return dict(case=v['case'],coordinate_frame=coord,frames=fs,sources=ss,transform=transform,video=v)
