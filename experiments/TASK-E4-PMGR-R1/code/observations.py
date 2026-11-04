"""Actual visible triangle edges drive bidirectional 2D contour ICP and LM."""
from inputs import *
from scipy.spatial import cKDTree
from geometry import Model
def project_jac(P,JP,K,T):
    cam=(P-T[:3,3])@T[:3,:3];hom=cam@K.T;uv=hom[:,:2]/hom[:,2,None];D=(K[None,:2,:]*hom[:,2,None,None]-hom[:,:2,None]*K[None,2,None,:])/hom[:,2,None,None]**2
    Jcam=np.einsum('ij,njk->nik',T[:3,:3].T,JP);return uv,np.einsum('nij,njk->nik',D,Jcam)
class Observations:
    def __init__(self,scene,model):
        self.scene=scene;self.model=model;self.ids=protocol()['scenes'][scene]['P2'];self.targets={};self.data={cid:obs(cid)for cid in self.ids};self.contour_log={}
        for cid in self.ids:
            s=source(cid);boundary=contour(s['labels']==1);adj=cv2.dilate((s['labels']==2).astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool);boundary=boundary[~adj[boundary[:,1].astype(int),boundary[:,0].astype(int)]];self.targets[cid]=dict(boundary=boundary,tree=cKDTree(boundary),s=s)
        sets=[{v['sha256']for v in CC[c].get('HERO_input_views',[])if v.get('sha256')}for c in self.ids];raw=[]
        for i,c in enumerate(self.ids):raw.append((1. if GATE[c]['qualification']=='CONDITIONAL_USABLE'else .25)/(1+sum(len(sets[i]&sets[j])/max(1,len(sets[i]|sets[j]))for j in range(len(sets))if i!=j)))
        self.weights={c:w/sum(raw)for c,w in zip(self.ids,raw)}
    def silhouette(self,V,J,cid,rt):
        s=source(cid);mesh=trimesh.Trimesh(V,self.model.F,process=False);adj=mesh.face_adjacency;edges=mesh.face_adjacency_edges;front=np.einsum('ij,ij->i',mesh.face_normals,s['T'][:3,3]-mesh.triangles_center)>0;keep=front[adj[:,0]]!=front[adj[:,1]];e=edges[keep];faces=np.where(front[adj[keep,0]],adj[keep,0],adj[keep,1]);uv,z=vis.project_camera(V,s['K'],s['T']);counts=np.clip(np.ceil(np.linalg.norm(uv[e[:,1]]-uv[e[:,0]],axis=1)/3).astype(int),1,128);ee=[];tt=[];ff=[]
        for edge,face,n in zip(e,faces,counts):ee.extend([edge]*n);tt.extend((np.arange(n)+.5)/n);ff.extend([face]*n)
        e=np.array(ee);t=np.array(tt);faces=np.array(ff);P=V[e[:,0]]*(1-t[:,None])+V[e[:,1]]*t[:,None];JP=J[e[:,0]]*(1-t[:,None,None])+J[e[:,1]]*t[:,None,None];xy,JJ=project_jac(P,JP,s['K'],s['T']);_,z=vis.project_camera(P,s['K'],s['T']);inside=(z>0)&np.isfinite(xy).all(1)&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);px=np.clip(np.rint(np.nan_to_num(xy)).astype(int),[0,0],[639,359]);inside&=s['labels'][px[:,1],px[:,0]]!=2
        Ptest=P*.999+mesh.triangles_center[faces]*.001;testuv,testz=vis.project_camera(Ptest,s['K'],s['T']);rz=cast(rt,testuv,s['K'],s['T'])[0];cad=cast(ringscene(self.scene),xy,s['K'],s['T'])[0]
        # The point is known to lie on its front-facing triangle. Visibility
        # asks whether a CLOSER triangle exists; a float32 miss of the known
        # silhouette edge is not evidence that the triangle point disappears.
        inside&=~(np.isfinite(rz)&(rz<testz-.01));inside&=z<=cad+.05
        return dict(uv=xy[inside],J=JJ[inside],P=P[inside],JP=JP[inside],edges=e[inside],fraction=t[inside],faces=faces[inside])
    def linearize(self,q,ids=None,detail=False):
        ids=self.ids if ids is None else ids;V,JV=self.model.vertices(q,True);F=self.model.F;rt=mesh_scene(V,F);rr=[];jj=[];ww=[];types=[];per=[];mapping={}
        normw=sum(self.weights[c]for c in ids)
        for cid in ids:
            o=self.data[cid];s=source(cid);target=self.targets[cid];sil=self.silhouette(V,JV,cid,rt);pred=sil['uv'];boundary=target['boundary']
            if len(pred)<8:raise ValueError('VISIBLE_CONTOUR_INSUFFICIENT:'+cid)
            df,ix=target['tree'].query(pred);dr,ir=cKDTree(pred).query(boundary);targetuv=boundary[ix];rF=(pred-targetuv)/3;rR=(pred[ir]-boundary)/3;Jf=sil['J']/3;Jr=sil['J'][ir]/3;wv=self.weights[cid]/normw
            rr.extend([rF.ravel(),rR.ravel()]);jj.extend([Jf.reshape(-1,len(q)),Jr.reshape(-1,len(q))]);ww.extend([np.full(rF.size,wv*.5/max(1,rF.size)),np.full(rR.size,wv*.5/max(1,rR.size))]);types.extend([np.zeros(rF.size,int),np.zeros(rR.size,int)])
            rays=vis.camera_rays(o['uv'],o['Kn'],s['T']);hit=rt.cast_rays(o3d.core.Tensor(rays.astype(np.float32)));rawz=hit['t_hit'].numpy();fid=hit['primitive_ids'].numpy().astype(int);safe=np.clip(fid,0,len(F)-1);tri=V[F[safe]];normal=mesh_normals(V,F)[safe];den=(normal*rays[:,3:]).sum(1);den_safe=np.where(abs(den)>1e-12,den,1);z=np.einsum('ij,ij->i',normal,tri[:,0]-rays[:,:3])/den_safe;valid=np.isfinite(rawz)&(z>0)&(z<=o['cad']+.05);Pinter=rays[:,:3]+z[:,None]*rays[:,3:];w=barycentric(tri,Pinter);JP=(JV[F[safe]]*w[:,:,None,None]).sum(1);Jz=np.einsum('ij,ijk->ik',normal,JP)/den_safe[:,None];pair=o['pairs'];good=valid[pair].all(1);p=pair[good];rd=(z[p[:,0]]-z[p[:,1]]-o['delta'][good])/.25;jd=(Jz[p[:,0]]-Jz[p[:,1]])/.25
            rr.append(rd);jj.append(jd);ww.append(np.full(len(rd),wv/len(pair)));types.append(np.zeros(len(rd),int))
            cp=rt.compute_closest_points(o3d.core.Tensor(o['X'].astype(np.float32)));fi=cp['primitive_ids'].numpy().astype(int);P=trimesh.triangles.closest_point(V[F[fi]],o['X']);b=barycentric(V[F[fi]],P);JP=(JV[F[fi]]*b[:,:,None,None]).sum(1);pu,pz=vis.project_camera(P,s['K'],s['T']);visz=cast(rt,pu,s['K'],s['T'])[0];cad=cast(ringscene(self.scene),pu,s['K'],s['T'])[0];front=np.einsum('ij,ij->i',mesh_normals(V,F)[fi],s['T'][:3,3]-P)>0;hv=front&(pz>0)&~(np.isfinite(visz)&(visz<pz-.05))&(pz<=cad+.05);dist=np.linalg.norm(P-o['X'],axis=1);n=(P-o['X'])/np.maximum(dist[:,None],1e-12);hd=4*np.tanh(dist[hv]/2);hj=2*(1-np.tanh(dist[hv]/2)**2)[:,None]*np.einsum('ij,ijk->ik',n[hv],JP[hv]);rr.append(hd);jj.append(hj);ww.append(np.full(len(hd),wv*.1/len(o['X'])));types.append(np.ones(len(hd),int))
            per.append(dict(source=cid,contour_mean_px=float(np.r_[df,dr].mean()),contour_p95_px=float(np.quantile(np.r_[df,dr],.95)),predicted_boundary_N=len(pred),observed_boundary_N=len(boundary),depth_hit_N=int(valid.sum()),depth_fixed_N=len(valid),relative_depth=stats(rd*.25),H_visible_N=int(hv.sum()),H_distance_mm=stats(dist[hv])))
            if detail:mapping[cid]=dict(**sil,target_uv=targetuv,contour_error_px=df,observed_boundary=boundary,reverse_indices=ir)
        # Generic priors; no class or per-scene parameters. P0 centre/rotation/
        # log-axis changes are free, with small declared soft regularization.
        d=q-self.model.reference if len(q)==9 else q[:9]-self.model.reference;scales=np.r_[np.full(3,10.),np.full(3,.5),np.full(3,.3)];rpose=d/scales;Jpose=np.zeros((9,len(q)));Jpose[:,:9]=np.diag(1/scales);rr.append(rpose);jj.append(Jpose);ww.append(np.full(9,.002/9));types.append(np.ones(9,int))
        if len(q)>9:
            freq=np.sqrt(self.model.frequency[:len(q)-9]/max(self.model.frequency[0],1e-10));rs=q[9:]*freq;js=np.zeros((len(rs),len(q)));js[:,9:]=np.diag(freq);rr.append(rs);jj.append(js);ww.append(np.full(len(rs),.02/32));types.append(np.ones(len(rs),int))
        r=np.concatenate(rr);J=np.vstack(jj);mass=np.concatenate(ww);kind=np.concatenate(types);robust=kind==0;rho=np.where(robust,np.sqrt(1+r*r)-1,.5*r*r);influence=np.where(robust,1/np.sqrt(1+r*r),1.);E=float((mass*rho).sum());g=J.T@(mass*influence*r);H=J.T@((mass*influence)[:,None]*J)
        return dict(E=E,g=g,H=H,V=V,JV=JV,per_view=per,mapping=mapping,r=r,J=J,mass=mass)
def mesh_normals(V,F):
    t=V[F];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15)
def barycentric(tri,P):
    a=tri[:,1]-tri[:,0];b=tri[:,2]-tri[:,0];c=P-tri[:,0];aa=(a*a).sum(1);ab=(a*b).sum(1);bb=(b*b).sum(1);ca=(c*a).sum(1);cb=(c*b).sum(1);den=aa*bb-ab*ab;u=(bb*ca-ab*cb)/den;v=(aa*cb-ab*ca)/den;return np.c_[1-u-v,u,v]
