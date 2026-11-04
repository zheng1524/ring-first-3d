from inputs import *
from renderer import tensor
from scipy.spatial import cKDTree
import torch

class Data:
    def __init__(self,scene):
        self.scene=scene;self.ids=protocol()['scenes'][scene]['P2'];self.views={};weights=[];sets=[]
        u,v=np.meshgrid(np.arange(320),np.arange(180));uv=np.c_[u.ravel(),v.ravel()]
        for cid in self.ids:
            s=source(cid);K=vis.scaled_intrinsics(s['K'],(640,360),(320,180));labels=s['labels'][np.arange(180)[:,None]*2+1,np.arange(320)[None,:]*2+1];target=labels==1
            cz=cast(ringscene(scene),uv,K,s['T'])[0].reshape(180,320);ring=(labels==2)|np.isfinite(cz);unknown=cv2.dilate(ring.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool);known=~unknown
            # One fixed UNKNOWN mask is applied to both sides, never derived
            # from the evolving prediction or used as a background label.
            fg=target&known;bg=~target&known;w=fg*.5/max(1,fg.sum())+bg*.5/max(1,bg.sum());inside=cv2.distanceTransform(target.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE);outside=cv2.distanceTransform((~target).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE);sdf=np.clip(outside-inside,-20,20)/5
            o=obs(cid);self.views[cid]=dict(s=s,o=o,K=K,target=tensor(target),known=tensor(known),weight=tensor(w),sdf=tensor(sdf),unknown=unknown,known_np=known,target_np=target,cad=cz,rays=vis.camera_rays(o['uv'],o['Kn'],s['T']))
            weights.append(1. if GATE[cid]['qualification']=='CONDITIONAL_USABLE'else .25);sets.append({x['sha256']for x in CC[cid].get('HERO_input_views',[])if x.get('sha256')})
        raw=np.array([w/(1+sum(len(sets[i]&sets[j])/max(1,len(sets[i]|sets[j]))for j in range(len(sets))if i!=j))for i,w in enumerate(weights)]);self.weights=dict(zip(self.ids,raw/raw.sum()))
    def freeze(self):
        rows=[]
        for cid,d in self.views.items():
            path=R/'inputs'/(cid+'_FIXED_MASK.npz')
            if not path.exists():np.savez_compressed(path,target=d['target_np'],known=d['known_np'],unknown=d['unknown'],K=d['K'],c2w=d['s']['T'],cad_depth_mm=d['cad'])
            else:
                frozen=np.load(path);assert np.array_equal(frozen['known'],d['known_np'])and np.array_equal(frozen['target'],d['target_np'])and np.array_equal(frozen['K'],d['K'])
            rows.append(dict(source=cid,known_N=int(d['known_np'].sum()),foreground_N=int((d['known_np']&d['target_np']).sum()),unknown_N=int(d['unknown'].sum()),fixed_native_N=512,fixed_pair_N=256,mask=asset(path),qualification=GATE[cid]['qualification'],source_weight=self.weights[cid]))
        save('metrics/'+self.scene+'_FIXED_DENOMINATORS.json',rows)
