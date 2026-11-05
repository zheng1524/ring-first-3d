from common import *
class Renderer:
    def __init__(self,root=R):
        a=np.load(root/'inputs/RING_CAD.npz');self.cad=scene(a['V'],a['F']);self.views=load(root/'inputs/CAMERAS.json');self.rays={};self.data={}
        for c in self.views:
            K=np.array(c['K_pixel_center']);T=np.array(c['c2w_mm']);u,v=np.meshgrid(np.arange(c['width']),np.arange(c['height']));uv=np.c_[u.ravel(),v.ravel()];cz,_=cast(self.cad,uv,K,T);path=root/'inputs'/('TARGET__'+c['id']+'.png');rgb=np.asarray(Image.open(path).convert('RGB'));target=(rgb[:,:,0]>128)&(rgb[:,:,0]>rgb[:,:,1]);ring=rgb[:,:,1]>128;unknown=cv2.dilate((ring|np.isfinite(cz).reshape(target.shape)).astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool);known=~unknown;co=contour(target);co=co[known[co[:,1].astype(int),co[:,0].astype(int)]]
            self.data[c['id']]=dict(c=c,K=K,T=T,uv=uv,cz=cz,target=target,unknown=unknown,known=known,contour=co,tree=cKDTree(co),target_rgb=rgb)
    def project(self,rt,cid):
        d=self.data[cid];z,face=cast(rt,d['uv'],d['K'],d['T']);pred=(np.isfinite(z)&(z<d['cz'])).reshape(d['target'].shape);return pred,z.reshape(pred.shape),face.reshape(pred.shape)
    def metrics(self,rt,cid):
        d=self.data[cid];pred,z,f=self.project(rt,cid);target=d['target'];known=d['known'];a=contour(pred);a=a[known[a[:,1].astype(int),a[:,0].astype(int)]];b=d['contour'];dist=np.r_[d['tree'].query(a)[0],cKDTree(a).query(b)[0]]if len(a)else np.array([100.]);inter=int((pred&target&known).sum());union=int(((pred|target)&known).sum());fullI=int((pred&target).sum())/max(1,(pred|target).sum())
        return dict(view=cid,role=d['c']['role'],IoU=inter/max(1,union),full_IoU=fullI,contour_px=stats(dist),Mask_N=int(target.sum()),fixed_known_Mask_N=int((target&known).sum()),hit=int((pred&target).sum()),FP=int((pred&~target&known).sum()),known_N=int(known.sum())),pred
    def silhouette(self,V,F,cid):
        """Visible actual edge positions, verified by a front-face interior ray probe."""
        d=self.data[cid];m=trimesh.Trimesh(V,F,process=False);ef=m.faces_unique_edges.ravel();order=np.argsort(ef,kind='stable');adj=np.repeat(np.arange(len(F)),3)[order].reshape(-1,2);front=np.einsum('ij,ij->i',m.face_normals,d['T'][:3,3]-m.triangles_center)>0;sel=np.flatnonzero(front[adj[:,0]]!=front[adj[:,1]]);faces=np.where(front[adj[sel,0]],adj[sel,0],adj[sel,1]);P=V[m.edges_unique[sel]].mean(1);uv,z=vis.project_camera(P,d['K'],d['T']);px=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);good=(z>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360)&d['known'][px[:,1],px[:,0]]
        probe=P+.005*(m.triangles_center[faces]-P);puv,pz=vis.project_camera(probe,d['K'],d['T']);hit,_=cast(scene(V,F),puv,d['K'],d['T']);cad,_=cast(self.cad,uv,d['K'],d['T']);good&=(abs(hit-pz)<.003)&(z<cad)
        return dict(P=P[good],uv=uv[good],faces=faces[good],normal=m.face_normals[faces[good]],source=cid)
