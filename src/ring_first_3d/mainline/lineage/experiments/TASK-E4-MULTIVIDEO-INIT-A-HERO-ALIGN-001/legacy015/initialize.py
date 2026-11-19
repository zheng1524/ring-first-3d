"""Actual multi-view initialization. SciPy TRF and 011 cap/shape formulas reused.

Init-B transforms the actual current mesh; Init-C refits its frozen analytic
family. Neither is an ICP, a GT fit, or an independently re-estimated camera.
"""
from parametric import body
from p3d import *
from depth_terms import D2Depth
from scipy.optimize import least_squares
import argparse,open3d as o3d

def robustify(r):return r*np.sqrt(2/(np.sqrt(1+r*r)+1))

class Initializer:
    def __init__(self,n,arm,subset=False):
        self.c=Case(n);self.n=n;self.arm=arm;self.calls=0;self.history=[];self.subset=subset
        if subset:self.c.fit=load(R/'config/VIEW_SELECTION.json')[n]['stability_FIT']
        self.V0=self.c.V.copy();self.center=self.V0.mean(0);self.base=load(R/'inputs'/n/'BASE_SELECTION.json');self.plane=np.array(self.base['selected_plane'],float);self.plane/=np.linalg.norm(self.plane[:3]);self.cap=bool(self.c.inferred.any());self.D=5. if self.c.meta['ring']=='R5'else 10.;self.rs=scene(self.c.ringV,self.c.ringF);self.saved=dict(np.load(R/'inputs'/n/'INITIAL.npz'));self.model=load(R/'inputs'/n/'PARAMETRIC_START.json');normal=self.plane[:3];e=np.eye(3)[np.argmin(abs(normal))];u=np.cross(normal,e);u/=np.linalg.norm(u);self.Q=np.column_stack([u,np.cross(normal,u),normal]);self.anchor=-self.plane[3]*normal
        self.p0=np.zeros(6)if arm=='Init-B'else np.array(self.model['p'],float);V,F,Fs,flag=self.shape(self.p0);self.c.F=F;self.depth=D2Depth(self.c);self.mass={}
        for cid in self.c.fit:
            t=self.c.views[cid]['target'];self.mass[cid]=(.5*t/t.sum().clamp_min(1)+.5*(1-t)/(1-t).sum().clamp_min(1))

    def shape(self,p):
        if self.arm=='Init-C':return body(p,self.model['meta'])
        V=self.V0.copy()
        if self.cap:
            q=(V-self.anchor)@self.Q;xy=q[:,:2].mean(0);cs,sn=np.cos(p[5]),np.sin(p[5]);rot=np.array([[cs,-sn],[sn,cs]]);q[:,:2]=(q[:,:2]-xy)*np.exp(p[2:4])@rot.T+xy+p[:2];q[:,2]*=np.exp(p[4]);V=q@self.Q.T+self.anchor
        else:V=(V-self.center)*np.exp(p[3:6])+self.center+p[:3]
        return V,self.saved['F'],self.saved['F_solid'],self.saved['inferred_base_faces']

    def residual(self,p,record=True):
        self.calls+=1;V,F,Fs,flag=self.shape(p);self.c.F=F;m=mesh((V-self.c.center)/self.c.scale,F);parts=[];rec=dict(silhouette=0.,absolute=0.,relative=0.,CAD=0.)
        with torch.no_grad():
            for cid in self.c.fit:
                fr=self.c.fragments(m,cid);_,alpha,w,*_=self.c.aware(fr,cid,True);r=((alpha-self.c.views[cid]['target'])*torch.sqrt(w*self.mass[cid]/len(self.c.fit))).cpu().numpy().ravel();parts.append(r);rec['silhouette']+=float(r@r)
            self.depth.begin(m)
            for cid,a in self.depth.obs.items():
                zz,active,_,_=self.depth.query(m,cid);z=zz.cpu().numpy();hit=active.cpu().numpy();r=np.where(hit,np.clip(robustify((z-a['z'])/.5),-np.sqrt(19),np.sqrt(19)),np.sqrt(19));w=a['boundary_weight'];r*=np.sqrt(.1*w/max(1e-12,w.sum())/len(self.depth.obs));parts.append(r);rec['absolute']+=float(r@r);pair=a['pairs'];good=hit[pair].all(1);delta=(z[pair[:,0]]-z[pair[:,1]])-(a['z'][pair[:,0]]-a['z'][pair[:,1]]);r=np.where(good,np.clip(robustify(delta/.5),-np.sqrt(19),np.sqrt(19)),np.sqrt(19));pw=a['pair_weight'];r*=np.sqrt(pw/max(1e-12,pw.sum())/len(self.depth.obs));parts.append(r);rec['relative']+=float(r@r)
            tri=V[Fs];P=np.r_[V,tri.mean(1),(tri[:,0]+tri[:,1])/2,(tri[:,1]+tri[:,2])/2,(tri[:,2]+tri[:,0])/2];sd=self.rs.compute_signed_distance(o3d.core.Tensor(P.astype(np.float32)),nsamples=3,nthreads=2).numpy();rp=self.c.ringV[::16];reverse=scene(V,Fs).compute_signed_distance(o3d.core.Tensor(rp.astype(np.float32)),nsamples=3,nthreads=2).numpy();r=np.maximum(0,.005-sd)/.05*np.sqrt(20/len(sd));b=np.maximum(0,.005-reverse)/.05*np.sqrt(20/len(reverse));parts.extend([r,b]);rec['CAD']=float(r@r+b@b);scale=np.ones(len(p));scale[:min(3,len(p))]=10;parts.append(np.sqrt(.005)*(p-self.p0)/scale)
        r=np.concatenate(parts).astype(float);assert np.isfinite(r).all()
        if record:self.history.append(dict(call=self.calls,objective=float(r@r/2),parameters=p.copy(),**rec))
        return r

    def jac(self,p):
        h=np.full(len(p),.002)
        if self.arm=='Init-B':h[:2 if self.cap else 3]=.02
        elif self.model['meta']['family']in['ellipsoid','star']:h[:3]=.02
        else:h[:2]=.02
        J=[]
        for k,s in enumerate(h):
            a=p.copy();b=p.copy();a[k]+=s;b[k]-=s;J.append((self.residual(a,False)-self.residual(b,False))/(2*s))
        return np.stack(J,axis=1)

    def bounds(self):
        p=self.p0;n=len(p)
        if self.arm=='Init-B':
            b=np.r_[self.D/2,self.D/2,.7,.7,.7,.5]if self.cap else np.r_[np.full(3,self.D/2),np.full(3,.7)];return -b,b
        if self.model['meta']['family']in['ellipsoid','star']:return np.r_[p[:3]-self.D,np.full(3,-.8),np.log(np.full(3,.25)),np.full(n-9,-.2)],np.r_[p[:3]+self.D,np.full(3,.8),np.log(np.full(3,20)),np.full(n-9,.2)]
        lo=np.r_[p[:2]-self.D,np.log([.25,.25,.1]),-np.pi];hi=np.r_[p[:2]+self.D,np.log([20,20,20]),np.pi]
        if n>=7:lo=np.r_[lo,.5];hi=np.r_[hi,2.]
        if n>=9:lo=np.r_[lo,[-.25,-.25]];hi=np.r_[hi,[.25,.25]]
        return lo,hi

    def solve(self):
        lo,hi=self.bounds();start=np.clip(self.p0,lo+1e-6,hi-1e-6);r0=self.residual(start);cfg=load(R/'config/PROTOCOL.json')['phase_A'];budget=cfg['stability_TRF_max_nfev'if self.subset else'initializer_TRF_max_nfev'];t=time.time();out=least_squares(self.residual,start,jac=self.jac,bounds=(lo,hi),method='trf',loss='linear',max_nfev=budget,ftol=1e-4,xtol=1e-4,gtol=1e-4,x_scale='jac');V,F,Fs,flag=self.shape(out.x);folder=R/'initializations'/self.n;folder.mkdir(parents=True,exist_ok=True);tag=self.arm+('_SUBSET'if self.subset else'');boundary=np.zeros(len(V),bool)
        if flag.any():boundary[np.unique(Fs[flag])]=True;boundary[np.setdiff1d(np.arange(len(V)),np.unique(F))]=False
        np.savez_compressed(folder/(tag+'.npz'),V=V,F=F,F_solid=Fs,inferred_base_faces=flag,boundary_vertex=boundary,parameters=out.x);trimesh.Trimesh(V,Fs,process=False).export(folder/(tag+'_mm.ply'));save('initializations/'+self.n+'/'+tag+'.json',dict(arm=self.arm,subset=self.subset,p=out.x,initial_p=self.p0,meta=self.model['meta']if self.arm=='Init-C'else dict(family='actual mesh affine6',cap=self.cap),nfev=out.nfev,actual_forward_calls=self.calls,success=bool(out.success),termination=out.message,initial_objective=float(r0@r0/2),objective=float(out.fun@out.fun/2),seconds=time.time()-t,history=self.history,actual_FIT=self.c.fit,GT_read=False));print('INIT_DONE',self.n,tag,out.nfev,flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('case');p.add_argument('arm',choices=['Init-B','Init-C']);p.add_argument('--subset',action='store_true');a=p.parse_args();guard_optimizer();Initializer(a.case,a.arm,a.subset).solve()

if __name__=='__main__':main()
