from common import *
from evaluate import pointcast
from ring_sides import sample
from scipy.ndimage import distance_transform_edt
import open3d as o3d
PREV=R.parent/'PROGRESSIVE_HERO_001'
def main():
 cfg=load(R/'config/PROTOCOL.json');src={x['id']:x for x in load('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/provenance/INPUT_ELIGIBILITY.json')['references']};rows=[];pairrows=[];sources=[]
 for name in cfg['cases']:
  c=getcase(name);root=R/'inputs'/name
  if name in['virtual_Ip','virtual_Is']:
   sc=load(R/'config'/(name+'_SCENE.json'))
   for v,cam in zip(c['views'],sc['cameras']):
    rgb=np.array(Image.open(root/(v['id']+'_LABEL.png')).convert('RGB'));lab=np.zeros(rgb.shape[:2],np.uint8);lab[(rgb[:,:,0]>128)&(rgb[:,:,0]>rgb[:,:,1])]=1;lab[rgb[:,:,1]>128]=2;np.savez_compressed(root/(v['id']+'.npz'),RGB=rgb,labels=lab,K=cam['K_pixel_center'],T=cam['c2w_mm'])
  if name.startswith('virtual'):
   gt=OLD/'audit_only/NATIVE_CAD_GT.npz'if name=='virtual_IIa'else R/'audit_only'/name/'GT.npz';g=np.load(gt);grt=scene(g['V'],g['F']);sources.append(asset(gt))
  rr=np.load(root/'RING.npz');rs=scene(rr['V'],rr['F'])
  for v in c['views']:
   cid=v['id'];a=dict(np.load(root/(cid+'.npz')));lab=a['labels'];K=a['K'];T=a['T']
   if not(root/(cid+'_SIDES.npz')).exists():
    sec,cl,band=sample(lab);np.savez_compressed(root/(cid+'_SIDES.npz'),classes=cl,band=band);save('metrics/sides/'+cid+'.json',sec)
   op=R/'depth_observations'/(cid+'.npz')
   if name.startswith('virtual'):
    dense=cast(grt,K,T,360,640);Kn=K
    if not op.exists():
     inner=cv2.erode((lab==1).astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool);y,x=np.where(inner);ix=np.linspace(0,len(x)-1,min(512,len(x))).astype(int);uv=np.c_[x[ix],y[ix]];z=dense[uv[:,1],uv[:,0]];X=(np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T*z[:,None])@T[:3,:3].T+T[:3,3];_,_,cz=pointcast(rs,X,K,T);good=np.isfinite(z)&(z>0)&(z<cz-.05);np.savez_compressed(op,uv=uv[good],pixel_id=(uv[:,1]*640+uv[:,0])[good],z=z[good],K=K,T=T,weight=np.ones(good.sum()),native_shape=[360,640])
   else:
    rawpath=src[cid]['E1_actual_native']['path'];raw=np.load(rawpath);dense=raw['depth_mm'];sources.append(asset(rawpath))
   o=dict(np.load(op));uv=o['uv'];Kn=o['K'];mapped=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(Kn).T@K.T;mapped=mapped[:,:2]/mapped[:,2:];px=np.clip(np.rint(mapped).astype(int),[0,0],[639,359]);db=distance_transform_edt(lab!=0);dr=distance_transform_edt(lab!=2)if(lab==2).any()else np.full(lab.shape,np.inf);d=np.minimum(db[px[:,1],px[:,0]],dr[px[:,1],px[:,0]]);weights=.1+.9*(1-np.exp(-(d/8.)**2));assert(lab[px[:,1],px[:,0]]==1).all();assert np.allclose(o['z'],dense[uv[:,1],uv[:,0]],rtol=0,atol=3e-5)
   reliable=weights>=.5;tree=cKDTree(uv);rng=np.random.default_rng(20261106);pairs=[];scales=[];seen=set()
   for scale in cfg['relative_depth']['scales_native_px']:
    added=0
    for i in rng.permutation(np.where(reliable)[0]):
     angle=rng.uniform(0,2*np.pi);target=uv[i]+scale*np.array([np.cos(angle),np.sin(angle)]);_,j=tree.query(target);j=int(j);separation=np.linalg.norm(uv[i]-uv[j]);key=tuple(sorted([int(i),j]))
     if not reliable[j]or key in seen or not(max(2,scale*.5)<=separation<=scale*2):continue
     line=np.rint(np.linspace(uv[i],uv[j],int(np.ceil(separation))+1)).astype(int);hh=np.c_[line,np.ones(len(line))]@np.linalg.inv(Kn).T@K.T;pp=np.rint(hh[:,:2]/hh[:,2:]).astype(int);zz=dense[line[:,1],line[:,0]]
     if not(lab[pp[:,1],pp[:,0]]==1).all()or not(np.isfinite(zz)&(zz>0)).all()or np.max(abs(np.diff(zz)))>.5:continue
     pairs.append(key);scales.append(scale);seen.add(key);added+=1
     if added>=128:break
   pairs=np.asarray(pairs,int).reshape(-1,2);pw=np.sqrt(weights[pairs[:,0]]*weights[pairs[:,1]])if len(pairs)else np.empty(0)
   np.savez_compressed(op,**{**o,'weight':np.ones(len(uv)),'boundary_weight':weights,'distance_background_px':db[px[:,1],px[:,0]],'distance_ring_px':dr[px[:,1],px[:,0]],'RGB_uv':mapped,'pairs':pairs,'pair_scale_px':scales,'pair_weight':pw})
   for i in range(len(uv)):rows.append(dict(case=name,source=cid,role=v['role'],depth_kind='IDEAL_GT_DEPTH_UPPER_BOUND'if name.startswith('virtual')else'HERO_NATIVE',pixel_id=int(o['pixel_id'][i]),native_u=int(uv[i,0]),native_v=int(uv[i,1]),z_mm=float(o['z'][i]),distance_Background_px=float(db[px[i,1],px[i,0]]),distance_Ring_px=float(dr[px[i,1],px[i,0]]),boundary_weight=float(weights[i]),same_E1_E2_E3_ID=True))
   for (i,j),s,w in zip(pairs,scales,pw):pairrows.append(dict(case=name,source=cid,i=int(i),j=int(j),pixel_id_i=int(o['pixel_id'][i]),pixel_id_j=int(o['pixel_id'][j]),scale_native_px=s,weight=w,delta_observed_mm=float(o['z'][i]-o['z'][j])))
   print(name,cid,'N',len(uv),'pairs',len(pairs),'weight',weights.min(),np.median(weights),weights.max(),flush=True)
 table('metrics/OBSERVATION_ID_WEIGHT_AUDIT.csv',rows);table('metrics/FIXED_RELATIVE_PAIRS.csv',pairrows);save('assets_index/DEPTH_GENERATION_SOURCES.json',sources);save('assets_index/INPUTS_FROZEN.json',[asset(p)for folder in['inputs','depth_observations','config']for p in sorted((R/folder).rglob('*'))if p.is_file()]);print('OBSERVATIONS_FROZEN')
if __name__=='__main__':main()
