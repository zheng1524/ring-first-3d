"""Fixed image queries and geometric segment distances, native pixel-center units."""
from renderer import *
def mask_segments(mask,known):
    # Linear 0.5 marching-squares boundary, with foreground-disconnected saddle rule.
    a=mask.astype(int);bits=a[:-1,:-1]+2*a[:-1,1:]+4*a[1:,1:]+8*a[1:,:-1]
    points=np.array([[.5,0],[1,.5],[.5,1],[0,.5]])
    lut={1:[(0,3)],2:[(0,1)],3:[(1,3)],4:[(1,2)],5:[(0,3),(1,2)],6:[(0,2)],7:[(2,3)],8:[(2,3)],9:[(0,2)],10:[(0,1),(2,3)],11:[(1,2)],12:[(1,3)],13:[(0,1)],14:[(0,3)]}
    seg=[]
    for y,x in zip(*np.nonzero((bits>0)&(bits<15))):
        if not known[y:y+2,x:x+2].all():continue
        for i,j in lut[int(bits[y,x])]:seg.append(points[[i,j]]+[x,y])
    return np.asarray(seg,float).reshape(-1,2,2)
def distance_segments(Q,S):
    if not len(S):return np.full(len(Q),100.)
    A=S[:,0];D=S[:,1]-A;den=np.maximum((D*D).sum(1),1e-18);out=[]
    for X in np.array_split(Q,max(1,int(np.ceil(len(Q)/256)))):
        V=X[:,None]-A;u=np.clip(np.einsum('ijk,jk->ij',V,D)/den,0,1)
        out.extend(np.sqrt(((V-u[:,:,None]*D)**2).sum(2)).min(1))
    return np.array(out)
def surface_segments(renderer,V,F,cid):
    d=renderer.data[cid];m=trimesh.Trimesh(V,F,process=False);ef=m.faces_unique_edges.ravel();order=np.argsort(ef,kind='stable');adj=np.repeat(np.arange(len(F)),3)[order].reshape(-1,2)
    front=np.einsum('ij,ij->i',m.face_normals,d['T'][:3,3]-m.triangles_center)>0;sel=np.flatnonzero(front[adj[:,0]]!=front[adj[:,1]])
    faces=np.where(front[adj[sel,0]],adj[sel,0],adj[sel,1]);edges=V[m.edges_unique[sel]];P=edges.mean(1);uv,z=vis.project_camera(P,d['K'],d['T']);px=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);ok=(z>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360)&d['known'][px[:,1],px[:,0]]
    probe=P+.005*(m.triangles_center[faces]-P);puv,pz=vis.project_camera(probe,d['K'],d['T']);hit,_=cast(scene(V,F),puv,d['K'],d['T']);cad,_=cast(renderer.cad,uv,d['K'],d['T']);ok&=(abs(hit-pz)<.003)&(z<cad)
    points,_=vis.project_camera(edges[ok].reshape(-1,3),d['K'],d['T'])
    return points.reshape(-1,2,2)
class FixedResidual:
    def __init__(self,renderer):
        self.renderer=renderer;self.rows={};self.slices={};self.meta=[];start=0
        for cid in protocol()['fit_views']:
            d=renderer.data[cid];S=mask_segments(d['target'],d['known']);boundary=S.mean(1)
            yy,xx=np.mgrid[0:360:4,0:640:4];grid=np.c_[xx.ravel(),yy.ravel()];near=distance_segments(grid,S)<=12;grid=grid[near&d['known'][grid[:,1],grid[:,0]]]
            Q=np.r_[boundary,grid];dist=distance_segments(Q,S);sgn=np.r_[np.ones(len(boundary)),np.where(d['target'][grid[:,1],grid[:,0]],-1,1)];target=dist*sgn;target[:len(boundary)]=0
            self.rows[cid]=(Q,target);self.slices[cid]=slice(start,start+len(Q));start+=len(Q)
            self.meta.append(dict(view=cid,fixed_rows=len(Q),target_boundary_rows=len(boundary),fixed_grid_rows=len(grid),known_pixels=int(d['known'].sum()),unknown_Ring_pixels=int(d['unknown'].sum()),foreground_pixels=int((d['target']&d['known']).sum()),background_pixels=int((~d['target']&d['known']).sum()),noise_px=.5,source_weight='1/sqrt(N_source), each view equal total weight'))
        self.N=start
    def evaluate(self,V,F):
        rt=scene(V,F);out=[];info=[]
        for cid,(Q,target)in self.rows.items():
            d=self.renderer.data[cid];S=surface_segments(self.renderer,V,F,cid);dist=distance_segments(Q,S);z,_=cast(rt,Q,d['K'],d['T']);cz,_=cast(self.renderer.cad,Q,d['K'],d['T']);inside=np.isfinite(z)&(z<cz);signed_dist=dist*np.where(inside,-1,1)
            out.extend((signed_dist-target)/(.5*np.sqrt(len(Q))))
            info.append(dict(view=cid,geometric_segments=len(S),fixed_rows=len(Q)))
        return np.array(out),info
def objective(body,renderer,q,corrected=False):
    V,F=body.mesh(q);m=trimesh.Trimesh(V,F,process=False)
    if not m.is_watertight or m.volume<=0 or len(m.split(only_watertight=False))!=1:return 10.,[]
    rt=scene(V,F);per=[]
    for cid in protocol()['fit_views']:
        d=renderer.data[cid];r=renderer.silhouette(V,F,cid)
        if len(r['P'])<10:return 10.,[]
        co=mask_segments(d['target'],d['known']).reshape(-1,2)if corrected else d['contour'];tree=cKDTree(co)
        a=tree.query(r['uv'])[0];b=cKDTree(r['uv']).query(co)[0]
        huber=lambda x:np.where(abs(x)<2,.5*x*x,2*abs(x)-2)
        ch=.5*(huber(a).mean()+huber(b).mean())/9;pred=renderer.project(rt,cid)[0];target=d['target'];known=d['known'];fg=target&known;bg=~target&known
        xor=.5*((pred^target)&fg).sum()/max(1,fg.sum())+.5*((pred^target)&bg).sum()/max(1,bg.sum())
        per.append(dict(view=cid,loss=float(ch+.2*xor),contour_loss=float(ch),fixed_XOR=float(xor)))
    return float(np.mean([x['loss']for x in per])),per
def subpixel_metrics(renderer,V,F,cid):
    d=renderer.data[cid];S=surface_segments(renderer,V,F,cid);T=mask_segments(d['target'],d['known']);dist=np.r_[distance_segments(S.mean(1),T),distance_segments(T.mean(1),S)]
    met,pred=renderer.metrics(scene(V,F),cid);target=d['target'];known=d['known'];met.update(subpixel_contour_px=stats(dist),FN=int((~pred&target&known).sum()),foreground_denominator=int((target&known).sum()),background_denominator=int((~target&known).sum()),unknown_N=int((~known).sum()),outside_prediction_ratio=float((pred&~target&known).sum()/max(1,(pred&known).sum())))
    return met
