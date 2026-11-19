from common import *
import shutil
from scipy.ndimage import distance_transform_edt
ROOT=R
def old_samples(r):
 cid=r['view_id'];a=np.load(ROOT/'hero_fit'/cid/'OBS_FULL.npz');d=np.load(r['cache']);K=a['K'];uv=a['uv'];p=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T@d['K'].T;p=np.floor(p[:,:2]/p[:,2:]+.5).astype(int);dt=distance_transform_edt(d['labels']==1)[p[:,1],p[:,0]];ix=np.flatnonzero(dt>=5);ix=ix[np.linspace(0,len(ix)-1,min(256,len(ix))).astype(int)]if len(ix)else ix;U=uv[ix];z=a['z'][ix];pairs=[];rng=np.random.default_rng(20261110)
 if len(ix):
  tree=cKDTree(U);full=np.load(ROOT/'hero_fit'/cid/'HERO_native.npz')['depth_mm'];seen=set()
  for sc in [4,16,48]:
   count=0
   for i in rng.permutation(len(ix)):
    angle=rng.uniform(0,2*np.pi);_,j=tree.query(U[i]+sc*np.array([np.cos(angle),np.sin(angle)]));j=int(j);pair=tuple(sorted([int(i),j]));gap=np.linalg.norm(U[i]-U[j])
    if pair in seen or not(max(2,.5*sc)<=gap<=2*sc):continue
    line=np.rint(np.linspace(U[i],U[j],int(np.ceil(gap))+1)).astype(int);q=np.c_[line,np.ones(len(line))]@np.linalg.inv(K).T@d['K'].T;q=np.floor(q[:,:2]/q[:,2:]+.5).astype(int);zz=full[line[:,1],line[:,0]]
    if not(d['labels'][q[:,1],q[:,0]]==1).all()or not(np.isfinite(zz)&(zz>0)).all()or (len(zz)>1 and abs(np.diff(zz)).max()>.75):continue
    seen.add(pair);pairs.append(pair);count+=1
    if count>=64:break
 np.savez_compressed(ROOT/'depth_observations'/(cid+'.npz'),uv=U,z=z,weight=np.ones(len(ix)),boundary_weight=np.ones(len(ix)),pairs=np.asarray(pairs,int).reshape(-1,2),pair_weight=np.ones(len(pairs)),K=K,T=a['T'],pixel_id=a['pixel_id'][ix],native_shape=a['native_shape'])
def main():
 plan=load(ROOT/'config/VIEW_PLAN.json');bindings={x['view_id']:x for x in load(ROOT/'metrics/FRAME_BINDING_AUDIT.json')};rows=[];ready={};arms=[]
 for g in ['G06','G05','G01','G03']:
  rr=[r for r in plan if r['group']==g];ok=True
  for r in rr:
   cid=r['view_id'];root=ROOT/('hero_fit'if r['role']=='FIT'else'holdout/hero')/cid;s=load(root/'SOURCE.json');c=load(root/'CLEANING.json');d=np.load(r['cache']);dep=np.load(s['native']);pose=dep['pose']if'pose'in dep else dep['reference_pose_mm'];p=np.load(s['pack']);identity=np.allclose(pose,d['T'],atol=1e-8)and np.allclose(p['K'],d['K'],atol=1e-8)and np.array_equal(p['labels'],d['labels']);valid=s['success']and c['success']and identity and bindings[cid]['status'].startswith('EXACT_');ok&=valid
   rows.append(dict(group=g,video='004',view_id=cid,role=r['role'],RGB=r['meta']['RGB_source'],Mask=r['meta']['Mask_source'],pose_source=r['meta'].get('pose_source'),RGB_SHA256=r['RGB_SHA256'],Mask_SHA256=r['Mask_SHA256'],pose_cache_SHA256=r['pose_cache_SHA256'],raw_frame_binding=bindings[cid]['status'],HERO_source='REUSED_NATIVE'if s['reused']else'NEW_OFFICIAL_HERO',HERO_native=s['native'],HERO_SHA256=sha(s['native']),HERO_Mesh=s['mesh'],Mesh_SHA256=sha(s['mesh']),source_parents=s['parent_RGB'],label_source=c['label_source'],label_SHA256=sha(root/'FACE_EVIDENCE.npz'),TRUSTED_mesh=str(root/'TRUSTED_HERO.npz'),TRUSTED_mesh_SHA256=sha(root/'TRUSTED_HERO.npz'),trusted_area_mm2=c['trusted_area_mm2'],trusted_observations=c['trusted_native_observations'],input_complete=bool(valid),regenerated=not s['reused'],classified=True,cleaned='017_LABELS_AND_ACTUAL_TRUSTED_FACE_SUBSET',geometry_supervision_eligible=bool(valid),holdout_optimizer_use=False))
   if r['role']=='FIT':old_samples(r)
  ready[g]=dict(ready=bool(ok),FIT=sum(r['role']=='FIT'for r in rr),HOLDOUT=sum(r['role']=='HOLDOUT'for r in rr));assert ok,(g,'INPUT_NOT_COMPLETE')
  seq=[('B1_FULL','FULL'),('B2_TRUSTED','TRUSTED'),('OLD_D2','OLD')]
  if g=='G01':seq=[('SINGLE_TRUSTED','TRUSTED'),('TWO_TRUSTED','TRUSTED')]+seq
  fit=load(ROOT/'config/VIEW_SELECTION_016.json')[g]['BALANCED'];by={r['view_id']:r for r in rr};first=fit[0];second=max([x for x in fit if x!=first],key=lambda x:np.arccos(np.clip(np.dot(by[first]['meta']['direction'],by[x]['meta']['direction']),-1,1)))
  for tag,kind in seq:
   folder=ROOT/'arms'/tag;folder.mkdir(parents=True,exist_ok=True)
   for sub in ['inputs','depth_observations']:
    dest=folder/sub
    if not dest.exists():dest.symlink_to(ROOT/sub,target_is_directory=True)
   for sub in ['config','metrics','local_results','provenance']:(folder/sub).mkdir(exist_ok=True)
   if not(folder/'config/PROTOCOL.json').exists():shutil.copyfile(ROOT/'config/PROTOCOL.json',folder/'config/PROTOCOL.json')
   ids=[first]if tag=='SINGLE_TRUSTED'else[first,second]if tag=='TWO_TRUSTED'else fit
   arms.append(dict(group=g,arm=tag,kind=kind,HERO_views=ids,FIT_silhouette_views=fit,path=str(folder),budget=load(ROOT/'config/PROTOCOL.json')['budget']))
 save('config/GROUP_READY.json',ready);save('config/ARM_PLAN.json',arms);table('VIEW_HERO_COMPLETENESS_MANIFEST.csv',rows);save('VIEW_HERO_COMPLETENESS_MANIFEST.json',rows);save('provenance/PRE_OPTIMIZATION_ASSETS.json',dict(epoch=time.time(),all43_complete=True,groups=ready,manifest=asset(ROOT/'VIEW_HERO_COMPLETENESS_MANIFEST.json'),sources=[asset(ROOT/('hero_fit'if r['role']=='FIT'else'holdout/hero')/r['view_id']/f)for r in plan for f in ['SOURCE.json','CLEANING.json','HERO_native.npz','FACE_EVIDENCE.npz','OBS_FULL.npz','OBS_TRUSTED.npz']],code=[asset(p)for p in sorted((ROOT/'code').glob('*.py'))],GT=False,initialization_ancestry='016 FINAL is frozen inherited result; older HERO parents may have included current holdout images. This round prohibits new holdout access/gradient, not claiming whole-pipeline independence.'))
 print('ALL_GROUPS_READY_43_HERO',len(arms),'formal optimization arms',flush=True)
if __name__=='__main__':main()
