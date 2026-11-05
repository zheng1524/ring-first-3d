from inputs import *
from field import project_jacobian
from scipy.spatial import cKDTree
FFD=Path('/home/liu/ring_first_3d_e4_ffd/experiments/TASK-E4-PMGR-FFD-002')
class Data:
    def __init__(self):
        p=protocol();self.fit=p['fit'];self.validation=p['validation'];self.ids=self.fit+self.validation;self.views={}
        u,v=np.meshgrid(np.arange(320),np.arange(180));uv=np.c_[u.ravel(),v.ravel()]
        for cid in self.ids:
            s=source(cid);d=dict(np.load(FFD/'inputs'/(cid+'_FIXED_MASK.npz')));d.update(s=s,o=obs(cid),uv=uv)
            assert np.allclose(d['c2w'],s['T'])
            t=d['target'];inside=cv2.distanceTransform(t.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE);outside=cv2.distanceTransform((~t).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
            d['sd']=outside-inside;d['weight']=.5*(t&d['known'])/max(1,(t&d['known']).sum())+.5*((~t)&d['known'])/max(1,((~t)&d['known']).sum())
            co=contour(t);co=co[d['known'][co[:,1].astype(int),co[:,0].astype(int)]];d['contour']=co;d['tree']=cKDTree(co);self.views[cid]=d
        sets=[{a['sha256']for a in CC[cid].get('HERO_input_views',[])if a.get('sha256')}for cid in self.fit]
        ww=np.array([1/(1+sum(len(a&b)/max(1,len(a|b))for j,b in enumerate(sets)if i!=j))for i,a in enumerate(sets)]);self.weights=dict(zip(self.fit,ww/ww.sum()))
    def mask(self,rt,cid):
        d=self.views[cid];z,f=cast(rt,d['uv'],d['K'],d['c2w']);return (np.isfinite(z)&(z>0)&(z<=d['cad_depth_mm'].ravel())).reshape(180,320)
    def mask_metrics(self,rt,cid):
        d=self.views[cid];a=self.mask(rt,cid);b=d['target'];k=d['known'];pa=contour(a);pb=d['contour'];pa=pa[k[pa[:,1].astype(int),pa[:,0].astype(int)]]
        ds=np.r_[d['tree'].query(pa)[0],cKDTree(pa).query(pb)[0]]if len(pa)else np.array([100.])
        # Fixed image-grid objective: each class has fixed mass; cap distance at 20px.
        err=a!=b;loss=float(np.sum(d['weight']*err*(1+np.minimum(abs(d['sd']),20)/5)))
        return dict(source=cid,role='FIT'if cid in self.fit else'UPDATE_HOLDOUT',qualification=GATE[cid]['qualification'],known_N=int(k.sum()),Mask_N=int((b&k).sum()),Mask_hit_N=int((a&b&k).sum()),Mask_miss_N=int((~a&b&k).sum()),FP_N=int((a&~b&k).sum()),IoU=float((a&b&k).sum()/max(1,((a|b)&k).sum())),contour_px=stats(ds),contour_median_px=float(np.median(ds)),fixed_Mask_loss=loss),a
    def contour_rows(self,V,F,grid,phi):
        """Two-way visible silhouette correspondences; original face identity retained."""
        mesh=trimesh.Trimesh(V,F,process=False);grad=grid.gradient(phi);P=(V[mesh.edges_unique[:,0]]+V[mesh.edges_unique[:,1]])/2
        # Each mesh edge has exactly two adjacent faces on the closed starting body.
        ef=mesh.faces_unique_edges.ravel();ff=np.repeat(np.arange(len(F)),3);order=np.argsort(ef,kind='stable');adj=ff[order].reshape(-1,2)
        assert np.array_equal(np.sort(ef)[::2],np.arange(len(P)))
        rt=mesh_scene(V,F);out=[]
        for cid in self.fit:
            d=self.views[cid];T=d['c2w'];view=T[:3,3]-mesh.triangles_center;front=np.einsum('ij,ij->i',mesh.face_normals,view)>0
            sel=np.flatnonzero(front[adj[:,0]]!=front[adj[:,1]]);pp=P[sel];uv,z=vis.project_camera(pp,d['K'],T);px=np.rint(uv).astype(int)
            good=(z>0)&(px[:,0]>=0)&(px[:,0]<320)&(px[:,1]>=0)&(px[:,1]<180);px=np.clip(px,[0,0],[319,179]);good&=d['known'][px[:,1],px[:,0]]
            hit,_=cast(rt,uv,d['K'],T);cad,_=cast(getattr(self,'cad_rt',ringscene('G01_004')),uv,d['K'],T);good&=(abs(hit-z)<.2)&(z<cad)
            sel=sel[good];pp=pp[good];uv=uv[good]
            if not len(pp):continue
            di,idx=d['tree'].query(uv);a=list(zip(range(len(pp)),idx,di,['PRED_TO_OBS']*len(pp)))
            di,idx=cKDTree(uv).query(d['contour'][::2]);a+=list(zip(idx,np.arange(len(d['contour']))[::2],di,['OBS_TO_PRED']*len(idx)))
            for j,k,dist,direction in a:
                target=d['contour'][k];line=np.linspace(uv[j],target,max(2,int(np.ceil(dist))+1));pix=np.clip(np.rint(line).astype(int),[0,0],[319,179])
                if dist>20 or not d['known'][pix[:,1],pix[:,0]].all():continue
                B,_=grid.basis(pp[j:j+1]);g=np.asarray(B@grad)[0];gn=np.linalg.norm(g);n=g/max(gn,1e-12);w=project_jacobian(pp[j:j+1],d['K'],T)[0]@n
                if np.linalg.norm(w)<1.:continue
                r=uv[j]-target;v=float(-r@w/(w@w));sd=float(d['sd'][tuple(np.clip(np.rint(uv[j]).astype(int),[0,0],[319,179])[::-1])])
                # Prevent nearest-contour tangential mismatches reversing the actual inside/outside correction.
                if abs(sd)>1.5 and sd*v>0:continue
                out.append(dict(source=cid,face_id=int(adj[sel[j],np.flatnonzero(front[adj[sel[j]]])[0]]),P=pp[j],normal=n,grad_norm=gn,uv=uv[j],target_uv=target,w=w,residual=r,normal_velocity_mm=v,distance_px=float(dist),direction=direction,sd_px=sd))
        return out
