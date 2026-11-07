"""Publish repaired C and run unchanged 011 recipe for new groups only.
These are recipe-equivalent new initializations, never mislabeled historic 011.
"""
from common import *
import shutil
from scipy.ndimage import distance_transform_edt
MASTER=Path(__file__).resolve().parents[1]
def main():
 f=MASTER/'initialization';out=MASTER/'initialization_011';out.mkdir(exist_ok=True);old=MASTER.parent/'CAP_REPAIR_STABLE_011'
 for d in ['inputs','depth_observations','code','config','metrics','assets_index','local_results']:(out/d).mkdir(exist_ok=True)
 for p in (old/'code').glob('*.py'):
  if p.name in ['common.py']:continue
  shutil.copyfile(p,out/'code'/p.name)
 shutil.copyfile(MASTER/'code/common.py',out/'code/common.py')
 cfg=load(old/'config/PROTOCOL.json');cfg['cases']=['G10','G11'];save(out/'config/PROTOCOL.json',cfg);save(out/'config/CASE_LOCK.json',load(f/'config/CASE_LOCK.json'))
 for c in load(f/'config/CASE_LOCK.json'):
  n=c['name'];shutil.copytree(f/'inputs'/n,out/'inputs'/n,dirs_exist_ok=True);model=load(f/'local_results'/n/'C_SELECTED.json');z=dict(np.load(f/'local_results'/n/'C_SELECTED.npz'));V=z['V'];bound=np.zeros(len(V),bool)
  if z['inferred_base_faces'].any():bound[np.unique(z['F_solid'][z['inferred_base_faces']])]=True;bound[-1]=False
  z['boundary_vertex']=bound;np.savez_compressed(out/'inputs'/n/'INITIAL.npz',**z);save(out/'inputs'/n/'C_INITIAL_MODEL.json',model);base=load(f/'inputs'/n/'BASE.json');plane=base['plane']if base['plane']is not None else [0.,0.,1.,0.];save(out/'inputs'/n/'BASE_SELECTION.json',dict(base,selected_plane=plane,uncertain_base=base['base_status']!='RELIABLE',directed_plane_source='same original Polyp-positive RANSAC base, no reorientation for model'))
  save(out/'inputs'/n/'NORMALIZATION.json',dict(center=V.mean(0),scale_mm=c['R_mid_mm']-c['wire_mm'],source='known Ring inner radius only'))
  for v in c['views']:
   p=f/'depth_observations'/(v['id']+'.npz')
   if not p.exists():continue
   obs=dict(np.load(p));a=np.load(f/'inputs'/n/(v['id']+'.npz'));lab=a['labels'];q=np.c_[obs['uv'],np.ones(len(obs['uv']))]@np.linalg.inv(obs['K']).T@a['K'].T;px=np.rint(q[:,:2]/q[:,2:]).astype(int);db=distance_transform_edt(lab!=0);dr=distance_transform_edt(lab!=2);w=.1+.9*(1-np.exp(-(np.minimum(db[px[:,1],px[:,0]],dr[px[:,1],px[:,0]])/8)**2));uvn=obs['uv'];reliable=w>=.5;tree=cKDTree(uvn);rng=np.random.default_rng(20261106);pairs=[];scales=[];seen=set();dense=np.load(f/'inputs'/n/(v['id']+'_DEPTH.npz'))['depth_mm']
   for scale in [4,16,48]:
    count=0
    for i in rng.permutation(np.flatnonzero(reliable)):
     angle=rng.uniform(0,2*np.pi);_,j=tree.query(uvn[i]+scale*np.array([np.cos(angle),np.sin(angle)]));j=int(j);gap=np.linalg.norm(uvn[i]-uvn[j]);key=tuple(sorted([int(i),j]))
     if not reliable[j]or key in seen or not(max(2,.5*scale)<=gap<=2*scale):continue
     line=np.rint(np.linspace(uvn[i],uvn[j],int(np.ceil(gap))+1)).astype(int);q=np.c_[line,np.ones(len(line))]@np.linalg.inv(obs['K']).T@a['K'].T;pix=np.rint(q[:,:2]/q[:,2:]).astype(int);zz=dense[line[:,1],line[:,0]]
     if not(lab[pix[:,1],pix[:,0]]==1).all()or not(np.isfinite(zz)&(zz>0)).all()or np.max(abs(np.diff(zz)))>.5:continue
     pairs.append(key);scales.append(scale);seen.add(key);count+=1
     if count>=128:break
   pairs=np.asarray(pairs,int).reshape(-1,2);np.savez_compressed(out/'depth_observations'/p.name,**{**obs,'boundary_weight':w,'pairs':pairs,'pair_scale_px':scales,'pair_weight':np.sqrt(w[pairs[:,0]]*w[pairs[:,1]])if len(pairs)else np.empty(0)})
 save(out/'metrics/PREFLIGHT.json',dict(passed=True,scope='input publication only; complete geometry still inspected by unchanged011 guard every candidate',GT_read=False))
 files=[asset(p)for d in ['inputs','code','config','depth_observations']for p in sorted((out/d).rglob('*'))if p.is_file()];save(out/'assets_index/PREOPT_FREEZE.json',dict(files=files,epoch=time.time(),GT_read=False));print('NEW_011_RECIPE_READY')
def publish_final():
 f=MASTER/'initialization_011';meta=load(MASTER/'config/CASE_LOCK.json')
 for c in meta:
  n=c['name']
  if n not in ['G10','G11']:continue
  shutil.copytree(f/'inputs'/n,MASTER/'inputs'/n,dirs_exist_ok=True);a=dict(np.load(f/'local_results'/n/'FINAL.npz'));np.savez_compressed(MASTER/'inputs'/n/'INITIAL.npz',**a);shutil.copyfile(f/'inputs'/n/'INITIAL.npz',MASTER/'inputs'/n/'C_011.npz');c['initialization']='new independent 009+011 recipe-equivalent FINAL, not historic011';save(MASTER/'inputs'/n/'CASE.json',c)
  for p in (f/'depth_observations').glob(n+'*.npz'):shutil.copyfile(p,MASTER/'depth_observations'/p.name)
 save(MASTER/'config/CASE_LOCK.json',meta);print('NEW_FINAL_INITIALIZATIONS_PUBLISHED')
if __name__=='__main__':
 import sys
 publish_final()if '--publish-final'in sys.argv else main()
