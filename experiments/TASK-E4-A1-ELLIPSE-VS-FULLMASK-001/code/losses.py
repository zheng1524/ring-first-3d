"""The only arm difference is a frozen 2-D target: DXY ellipse or original mask."""
from common import *
from scipy.ndimage import map_coordinates
def robust(x):return x*np.sqrt(2/(np.sqrt(1+x*x)+1))
def ellipse_projection(p,R0,K,T):
    c,Q,a=decode(p,R0);center=(c-T[:3,3])@T[:3,:3];A=T[:3,:3].T@Q@np.diag(1/a**2)@Q.T@T[:3,:3]
    v=A@center;H=np.outer(v,v)-(center@v-1)*A;Ki=np.linalg.inv(K);F=Ki.T@H@Ki;S=F[:2,:2];b=F[:2,2]
    uv=-np.linalg.solve(S,b);value=float(uv@S@uv+2*b@uv+F[2,2]);M=-S/value;ev,U=np.linalg.eigh(M)
    if np.any(ev<=0)or not np.isfinite(uv).all():raise ValueError('projection is not a finite front-facing ellipse')
    axes=1/np.sqrt(ev);theta=np.arange(128)*2*np.pi/128;curve=uv+np.c_[np.cos(theta),np.sin(theta)]@(U@np.diag(axes)).T
    return uv,M,axes,curve
def signed_distance(uv,center,M,axes):
    x=uv[:,0]-center[0];y=uv[:,1]-center[1];mx=M[0,0]*x+M[0,1]*y;my=M[1,0]*x+M[1,1]*y
    return(x*mx+y*my-1)/np.maximum(2*np.sqrt(mx*mx+my*my),1/max(axes))
def field_sample(field,uv):
    h,w=field.shape;clipped=np.clip(uv,[0,0],[w-1,h-1]);v=map_coordinates(field,[clipped[:,1],clipped[:,0]],order=1,mode='nearest');return v
def distance_field_sample(field,uv):
    h,w=field.shape;return field_sample(field,uv)+np.linalg.norm(uv-np.clip(uv,[0,0],[w-1,h-1]),axis=1)
def target_data(mask,labels,cad,T,K):
    """All source foreground pixels remain positive; only Ring is unknown."""
    mask=mask.astype(bool);ring=labels==2;boundary=contour(mask);adj=cv2.dilate(ring.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    if len(boundary):boundary=boundary[~adj[boundary[:,1].astype(int),boundary[:,0].astype(int)]]
    bmap=np.ones(mask.shape,np.uint8)
    if len(boundary):bmap[boundary[:,1].astype(int),boundary[:,0].astype(int)]=0
    dt=cv2.distanceTransform(bmap,cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    # Area pooling uses EVERY original pixel; the model is quadratured at fixed
    # 4x4 cell centers. Fine contour pixels remain in the reverse contour term.
    fraction=mask.reshape(90,4,160,4).mean((1,3));unknown=ring.reshape(90,4,160,4).mean((1,3));u,v=np.meshgrid(np.arange(160)*4+1.5,np.arange(90)*4+1.5);grid=np.c_[u.ravel(),v.ravel()]
    known=1-unknown.ravel();fg=fraction.ravel();pixmass=.5*fg/max(fg.sum(),1)+.5*(1-fg)/max((1-fg).sum(),1);pixmass*=known
    # CAD cache is exact fixed-camera first depth at grid centers.
    rays=vis.camera_rays(grid,K,T)
    return dict(mask=mask,ring=ring,boundary=boundary,dt=dt,grid=grid,region=fg,region_weights=pixmass,grid_rays=rays,grid_CAD=cad)
def cad_visibility(p,R0,rays,cad):
    A,B,C,d=ray_components(p,R0,rays);t=-B/A-np.sqrt(np.maximum(d,0))/A
    # Closest-ray depth is used only as a soft silhouette visibility proxy for
    # rays outside the body; never as an observed or predicted first depth.
    return np.where(np.isfinite(cad),expit((cad-t+.05)/.05),1.)
def two_d_parts(p,R0,target,K,T,ring_scene):
    center,M,axes,curve=ellipse_projection(p,R0,K,T);cad_curve=cast(ring_scene,curve,K,T)[0];rays=vis.camera_rays(curve,K,T)
    visible=cad_visibility(p,R0,rays,cad_curve)*(1-field_sample(target['ring'].astype(float),curve))
    forward=robust(distance_field_sample(target['dt'],curve)/3)*np.sqrt(visible/(3*len(curve)))
    q=target['boundary'];reverse=robust(signed_distance(q,center,M,axes)/3)/np.sqrt(3*max(1,len(q)))
    distance=signed_distance(target['grid'],center,M,axes);prob=expit(-distance/1.5);visib=cad_visibility(p,R0,target['grid_rays'],target['grid_CAD']);region=robust((prob-target['region'])/.1)*np.sqrt(visib*target['region_weights']/3)
    return [forward,reverse,region]
def depth_parts(p,R0,rays,pairs,delta):
    z=first_depth(p,R0,rays);good=np.isfinite(z[pairs]).all(1);r=np.zeros(len(pairs));r[good]=(z[pairs[good,0]]-z[pairs[good,1]]-delta[good])/.25
    A,B,C,disc=ray_components(p,R0,rays);qmin=C-B*B/A
    # A common differentiable ray/body feasibility penalty; no fake depth on
    # missing rays, and no discrete hit count enters the optimizer.
    feasibility=np.logaddexp(0,qmin/.01)*.01/.1
    return[robust(r)/np.sqrt(max(1,len(r))),robust(feasibility)*np.sqrt(.1/max(1,len(feasibility)))],z
