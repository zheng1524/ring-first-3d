"""Only new geometry: an explicit pixel affine and identity-traced nearest sampler.
Projection, unprojection, native K and CAD all call inherited functions.
"""
from common import *

def make_crop(s):
    c=config();h,w=s['depth'].shape;y,x=np.nonzero((s['native_labels']==1)|(s['native_labels']==2));assert len(x)
    bbox=np.array([x.min(),y.min(),x.max()+1,y.max()+1],int);bw,bh=bbox[2:]-bbox[:2];margin=max(c['crop']['minimum_margin_native_px'],int(np.ceil(c['crop']['fraction_margin_each_side']*max(bw,bh))))
    expanded=bbox+[-margin,-margin,margin,margin];ew,eh=expanded[2:]-expanded[:2];k=int(np.ceil(max(ew/4,eh/3)));cw,ch=4*k,3*k
    x0,y0=np.floor((expanded[:2]+expanded[2:]-[cw,ch])/2).astype(int);a=320/cw
    # Crop/Padding in a virtual 4:3 source rectangle, followed by one isotropic scale.
    A=np.array([[a,0,a*(.5-x0)-.5],[0,a,a*(.5-y0)-.5],[0,0,1.]],float);Ai=np.linalg.inv(A);Kp=A@s['Kn']
    vv,uu=np.mgrid[0:240,0:320];uvout=np.c_[uu.ravel(),vv.ravel()];uvsrc=affine_uv(uvout,Ai);pix=np.floor(uvsrc+.5).astype(int)
    inside=(pix[:,0]>=0)&(pix[:,0]<w)&(pix[:,1]>=0)&(pix[:,1]<h);j=np.flatnonzero(inside);p=pix[j];labels=np.zeros(240*320,np.uint8);labels[j]=s['native_labels'][p[:,1],p[:,0]]
    z=np.zeros(240*320,float);z[j]=s['depth'][p[:,1],p[:,0]];valid=inside&(labels==1)&np.isfinite(z)&(z>0);depth=np.where(valid,z,0).reshape(240,320).astype(np.float32)
    rgb=np.zeros((240*320,3),np.uint8);rgb[j]=s['native_RGB'][p[:,1],p[:,0]];source_ids=np.full(240*320,-1,np.int64);source_ids[j]=p[:,1]*w+p[:,0]
    # 0 BG, 1 legal Polyp, 2 Ring, 3 Unknown Polyp, 4 virtual padding.
    semantic=np.zeros(240*320,np.uint8);semantic[labels==2]=2;semantic[(labels==1)&~valid]=3;semantic[valid]=1;semantic[~inside]=4
    v,u=np.nonzero(valid.reshape(240,320));Xout=unproject(depth[v,u].astype(float),s['T'],np.c_[u,v],Kp)
    return dict(A=A,A_inverse=Ai,K_crop=Kp,source_bbox=bbox,expanded_bbox=expanded,crop_bbox=np.array([x0,y0,x0+cw,y0+ch]),scale=float(a),padding_native=[max(0,-x0),max(0,-y0),max(0,x0+cw-w),max(0,y0+ch-h)],letterbox_output_px=[0,0,0,0],labels=labels.reshape(240,320),depth_mm=depth,valid=valid.reshape(240,320),semantics=semantic.reshape(240,320),RGB=rgb.reshape(240,320,3),source_ids=source_ids.reshape(240,320),nearest_source_uv=pix.reshape(240,320,2),inverse_continuous_native_uv=uvsrc.reshape(240,320,2),output_uv=np.c_[u,v],output_X_mm=Xout)

def ridge_proxy(valid):
    # Uncalibrated local medial-ridge proxy; all candidates retained, no size filtering.
    dt=cv2.distanceTransform(valid.astype(np.uint8),cv2.DIST_L2,5);ridge=valid&(dt>=cv2.dilate(dt,np.ones((3,3),np.uint8))-1e-6);return dt,ridge
