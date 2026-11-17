"""Reuses ExplicitContour bidirectionality; full fresh FIT render before acceptance."""
import numpy as np
import torch
import torch.nn.functional as TF
from scipy.ndimage import binary_dilation,distance_transform_edt,gaussian_filter
from scipy.spatial import cKDTree
from ring_first_3d.synthetic.raster import ray_map
from ring_first_3d.contour_guided.correspondence import target_boundary,explicit_pairs,project_torch

DEFAULT=dict(max_distance_px=40.,mutual_radius_px=0.,normal_cos_min=.5,max_tangent_px=8.)
def strict_mutual(source,target,si,ti):
    if not len(source)or not len(target):return np.zeros(len(si),bool)
    j=cKDTree(target).query(source)[1];i=cKDTree(source).query(target)[1]
    return (j[si]==ti)&(i[ti]==si)
def sdf(mask):return gaussian_filter(distance_transform_edt(~mask)-distance_transform_edt(mask),1.)
def stats(pred,target,known):
    union=((pred|target)&known).sum();iou=float(((pred&target)&known).sum()/max(1,union))
    p,n,_=target_boundary(np.where(pred,1,0),100000);t,_,_=target_boundary(np.where(target,1,0),100000)
    p=p[known[p[:,1].astype(int),p[:,0].astype(int)]];t=t[known[t[:,1].astype(int),t[:,0].astype(int)]]
    a=cKDTree(t).query(p)[0]if len(t)and len(p)else np.array([max(pred.shape)])
    b=cKDTree(p).query(t)[0]if len(t)and len(p)else np.array([max(pred.shape)])
    precision=float((a<=2).mean());recall=float((b<=2).mean())
    return dict(IoU=iou,Boundary_MAE_px=float(np.r_[a,b].mean()),Boundary_Fscore_at2px=2*precision*recall/max(1e-12,precision+recall),R_plus_N=int((target&~pred&known).sum()),R_minus_N=int((pred&~target&known).sum()),target_N=int((target&known).sum()))

class ProjectionGate:
    def __init__(self,views,ring,weights,config=None):
        assert all(v['role']=='FIT'for v in views),'HOLDOUT_LEAK';self.views=views;self.weights=weights;self.cfg=dict(DEFAULT if config is None else config)
        self.ringz={v['id']:ray_map(ring['V'],ring['F'],v['K'],v['C'],v['labels'].shape)['z']for v in views}
        self.initial=None;self.generation=0
    def rebuild(self,body,keep_maps=False):
        self.generation+=1;result={}
        for v in self.views:
            lab=v['labels'];r=ray_map(body['V'],body['F'],v['K'],v['C'],lab.shape);unknown=binary_dilation(lab==2,iterations=3);known=~unknown;target=lab==1
            pred=r['valid']&(r['z']>0)&(r['z']<self.ringz[v['id']]-.05)
            bp,bn,_=target_boundary(np.where(pred,1,0),512);bk=~unknown[bp[:,1].astype(int),bp[:,0].astype(int)];tp,tn,tk=target_boundary(lab,512)
            pairs=explicit_pairs(bp,bn,tp,tn,tk,self.cfg);ix=pairs['source'];ti=pairs['target'];uv=bp[ix].astype(int)
            face=r['face'][uv[:,1],uv[:,0]];bary=r['bary'][uv[:,1],uv[:,0]]
            mutual=strict_mutual(bp,tp,ix,ti);outward=(bn[ix]*tn[ti]).sum(1)>=self.cfg['normal_cos_min']
            keep=pairs['accepted']&mutual&outward&bk[ix]&(face>=0)&np.isfinite(bary).all(1)
            reasons=pairs['reasons'].copy();reasons[pairs['accepted']&~keep]='VISIBILITY_OR_UNKNOWN';reasons[pairs['accepted']&~mutual]='NOT_EXACT_MUTUAL';reasons[pairs['accepted']&~outward]='OUTWARD_NORMAL_CONFLICT'
            pairs.update(accepted=keep,reasons=reasons,face=face,bary=bary,source_uv=bp[ix],target_uv=tp[ti],target_normal=tn[ti],body_normal=bn[ix])
            plus=target&~pred&known
            pairs['growth_candidate']=(pairs['direction']==1)&tk[ti]&plus[tp[ti,1].astype(int),tp[ti,0].astype(int)]&(~unknown[uv[:,1],uv[:,0]])&(pairs['distance']>=6)&(face>=0)&outward&(pairs['tangent']<=np.maximum(8.,.5*pairs['distance']))
            # Growth evidence is never accepted as a long-distance deformation pair.
            s=stats(pred,target,known);s.update(id=v['id'],video=v['video'],role=v['role'],generation=self.generation,candidate_N=len(keep),accepted_N=int(keep.sum()),rejections={z:int((reasons==z).sum())for z in np.unique(reasons)if z!='ACCEPTED'})
            item=dict(pairs=pairs,stats=s,sdf=sdf(target),predicted=pred,target=target,unknown=unknown,R_plus=plus,R_minus=pred&~target&known)
            if keep_maps:item.update(visible_face=r['face'],visible_bary=r['bary'])
            result[v['id']]=item
        return result
    def loss(self,V,F,assignments):
        total=V.sum()*0;per={}
        for v in self.views:
            a=assignments[v['id']];p=a['pairs'];keep=p['accepted'];loss=V.sum()*0
            if keep.any():
                fi=torch.as_tensor(F[p['face'][keep]],device=V.device);bar=torch.as_tensor(p['bary'][keep],dtype=V.dtype,device=V.device);X=(V[fi]*bar[:,:,None]).sum(1);uv=project_torch(X,v['K'],v['C'])
                target=torch.as_tensor(p['target_uv'][keep],dtype=V.dtype,device=V.device);normal=torch.as_tensor(p['target_normal'][keep],dtype=V.dtype,device=V.device)
                nr=((uv-target)*normal).sum(1)/20
                H,W=v['labels'].shape;grid=uv.clone();grid=torch.stack([grid[:,0]*2/(W-1)-1,grid[:,1]*2/(H-1)-1],1)
                S=torch.as_tensor(a['sdf'],device=V.device,dtype=V.dtype)[None,None];val=TF.grid_sample(S,grid[None,None],mode='bilinear',padding_mode='border',align_corners=True)[0,0,0]/20
                h=TF.huber_loss(nr,torch.zeros_like(nr),reduction='none',delta=1.)+.25*TF.huber_loss(val,torch.zeros_like(val),reduction='none',delta=1.)
                di=p['direction'][keep];terms=[h[torch.as_tensor(di==z,device=V.device)].mean()for z in [0,1]if(di==z).any()];loss=sum(terms)/len(terms)
            total=total+self.weights[v['id']]*loss;per[v['id']]=loss
        return total,per
    def regional_score(self,assignments):
        return sum(self.weights[c]*(1-a['stats']['IoU']+.01*a['stats']['Boundary_MAE_px'])for c,a in assignments.items())
    def protect(self,assignments):
        bad=[]
        for cid,base in self.initial.items():
            if base['stats']['IoU']>=.80 and base['stats']['target_N']>0:
                s=assignments[cid]['stats'];old=base['stats']
                if s['IoU']<old['IoU']-.01-1e-12 or s['Boundary_MAE_px']>old['Boundary_MAE_px']+1+1e-12:bad.append(dict(id=cid,initial_IoU=old['IoU'],candidate_IoU=s['IoU'],initial_Boundary_MAE_px=old['Boundary_MAE_px'],candidate_Boundary_MAE_px=s['Boundary_MAE_px']))
        return bad
