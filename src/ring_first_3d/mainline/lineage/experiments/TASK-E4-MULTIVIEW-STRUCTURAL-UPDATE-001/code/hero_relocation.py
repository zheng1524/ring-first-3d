"""Pixel-identity low-DOF axial corrections after immutable Body freeze.
No camera variables, per-vertex fits, Body replacement or global fusion.
"""
import numpy as np
from scipy.optimize import least_squares
from ring_first_3d.contracts.coordinates import unproject
from ring_first_3d.synthetic.raster import ray_map
from ring_first_3d.multisurface.geometry import scene,closest
from ring_first_3d.stress.real import safe_project
from ring_first_3d.policy.contracts import require


def relocate(data,body,ring,cfg):
    videos=sorted({d['video'] for d in data});nv=len(videos);N=len(data);samples=[];fixed=[]
    for i,d in enumerate(data):
        uv=np.asarray(d['uv'],int);K,C=d['K'],d['C'];pred=ray_map(body['V'],body['F'],K,C,d['labels'].shape)
        rz=ray_map(ring['V'],ring['F'],K,C,d['labels'].shape)['z'];face=pred['face'][uv[:,1],uv[:,0]];bary=pred['bary'][uv[:,1],uv[:,0]]
        zbody=pred['z'][uv[:,1],uv[:,0]];cam=(d['V']-C[:3,3])@C[:3,:3];z=cam[:,2]
        q=np.c_[np.ones(len(z)),(uv[:,0]-K[0,2])/K[0,0],(uv[:,1]-K[1,2])/K[1,1]]
        valid=(face>=0)&(d['labels'][uv[:,1],uv[:,0]]==1)&(zbody<rz[uv[:,1],uv[:,0]]-.05)&(abs(zbody-z)<=cfg['capture_mm'])
        ids=np.flatnonzero(valid);ids=ids[np.linspace(0,len(ids)-1,min(cfg['samples'],len(ids)),dtype=int)] if len(ids) else ids
        samples.append(dict(z=z,Q=q,face=face,bary=bary,zbody=zbody,valid=valid,ids=ids,video=videos.index(d['video'])))
        fixed.append(dict(id=d['id'],source_uv=uv,Body_face=face,Body_bary=bary,Body_depth=zbody,accepted=valid))
    def corrected(p,i):
        s=samples[i];shared=p[s['video']];local=p[nv+4*i:nv+4*(i+1)]
        return s['z']*(1+local[0])+shared+s['Q']@local[1:]
    def fun(p):
        parts=[]
        for i,s in enumerate(samples):
            ix=s['ids'];delta=corrected(p,i)[ix]-s['zbody'][ix]
            dead=np.sign(delta)*np.maximum(abs(delta)-cfg['tolerance_mm'],0)
            parts.append(dead/np.sqrt(max(1,len(ix))*N))
        # Fixed variance prior on frame offset/scale/slope, plus video zero gauge prior.
        parts.append(p[:nv]/cfg['video_offset_bound_mm']*.01)
        local=p[nv:].reshape(N,4);parts.append((local/np.array(cfg['frame_prior'])).ravel()*.05)
        for video in range(nv):parts.append(local[[s['video']==video for s in samples],1].mean(keepdims=True)/cfg['frame_prior'][1]*.1)
        return np.concatenate(parts)
    bound=np.r_[np.full(nv,cfg['video_offset_bound_mm']),np.tile(np.array(cfg['frame_bounds']),N)]
    p=np.zeros(len(bound));history=[]
    # Body/cameras/rays fixed; candidate identities are rebuilt each outer pass to
    # audit consistency and retain all unmatched sources. No lateral surface motion.
    for outer in range(cfg['outer_iterations']):
        fit=least_squares(fun,p,bounds=(-bound,bound),loss='soft_l1',f_scale=.1,max_nfev=cfg['max_nfev'])
        p=fit.x;history.append(dict(outer=outer,parameters=p.tolist(),cost=float(fit.cost),optimizer_success=bool(fit.success),nfev=fit.nfev))
        for d,s in zip(data,samples):
            again=ray_map(body['V'],body['F'],d['K'],d['C'],d['labels'].shape);uv=np.asarray(d['uv'],int)
            require(np.array_equal(s['face'],again['face'][uv[:,1],uv[:,0]]),'PIXEL_IDENTITY','Fixed source rays must keep Face IDs')
    meshes=[];records=[]
    for i,(d,s) in enumerate(zip(data,samples)):
        zz=corrected(p,i);V=unproject(d['uv'],zz,d['K'],d['C']);uv,_=safe_project(V,d['K'],d['C'])
        require(np.max(np.linalg.norm(uv-d['uv'],axis=1))<1e-6,'PIXEL_IDENTITY','No camera/pixel shift')
        F=d['F'];edges=np.unique(np.sort(np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],axis=1),axis=0)
        edge0=np.linalg.norm(d['V'][edges[:,0]]-d['V'][edges[:,1]],axis=1);edge1=np.linalg.norm(V[edges[:,0]]-V[edges[:,1]],axis=1)
        meshes.append(dict(V=V,F=F,uv=d['uv']));records.append(dict(id=d['id'],accepted_N=int(s['valid'].sum()),target_N=len(d['V']),
            axial_change_MAE_mm=float(abs(zz-s['z']).mean()),axial_change_max_mm=float(abs(zz-s['z']).max()),
            edge_relative_change_P95=float(np.quantile(abs(edge1-edge0)/np.maximum(1e-12,edge0),.95)),
            edge_change_max_mm=float(abs(edge1-edge0).max()),source_pixel_error_max_px=float(np.linalg.norm(uv-d['uv'],axis=1).max()),
            all_vertices_retained=True,local_shape_replaced=False))
        fixed[i]['corrected_axial_mm']=zz;fixed[i]['original_axial_mm']=s['z']
    return meshes,fixed,dict(history=history,per_view=records,videos=videos,parameter_model='z_new=(1+s_frame) z + b_video + b_frame + gx_frame normalized_u + gy_frame normalized_v',Body_updated=False,camera_optimized=False)
