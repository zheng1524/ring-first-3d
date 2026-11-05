from field import *
from data import Data
from scipy.optimize import lsq_linear
from scipy.spatial import cKDTree

class Evolution:
    def __init__(self,grid,phi0,data):
        self.g=grid;self.phi0=phi0.copy();self.d=data;self.p=protocol();self.initial_mesh=grid.mesh(phi0);self.initial_rt=mesh_scene(*self.initial_mesh);self.initial_volume=volume(*self.initial_mesh)
        self.hero=np.vstack([obs(cid)['X']for cid in data.fit]);self.H,valid=grid.basis(self.hero);hp=self.H@phi0
        eligible=np.concatenate([(obs(cid)['z']<=obs(cid)['cad']+.05)for cid in data.fit]);self.eligible=valid&eligible;self.H=self.H[self.eligible];self.h0=hp[self.eligible]
        self.hero_weight=np.minimum(1.,.5/np.maximum(abs(self.h0),1e-12))
        self.protect=abs(self.h0)<=self.p['protection_band_mm'];self.HP=self.H[self.protect];self.protect_tol=np.maximum(abs(self.h0[self.protect]),self.p['protection_band_mm'])+self.p['protection_slack_mm']
        self.cad=ringmesh('G01_004');self.cad_points=np.vstack([self.cad.vertices,self.cad.triangles_center]);self.C,valid=grid.basis(self.cad_points);assert valid.all()
    def objective(self,phi,V,F):
        rt=mesh_scene(V,F);rows=[self.d.mask_metrics(rt,cid)[0]for cid in self.d.fit];mask=sum(self.d.weights[a['source']]*a['fixed_Mask_loss']for a in rows)
        r=self.H@phi/.5;robust=np.where(abs(r)<=1,.5*r*r,abs(r)-.5);hero=float(np.average(robust,weights=self.hero_weight));corr=phi-self.phi0;band=abs(self.phi0)<1.25
        prior=float(np.mean((corr[band]/.75)**2));gg=np.stack(np.gradient(corr.reshape(self.g.shape),self.g.h),-1);smooth=float(np.mean((gg.reshape(-1,3)[band]**2)))
        total=mask+self.p['HERO_weight']*hero+self.p['prior_weight']*prior+self.p['H1_weight']*smooth
        return dict(total=total,Mask=mask,HERO_proxy=hero,prior=prior,smooth=smooth),rows
    @staticmethod
    def restrict_bounds(B,rhs,lower,upper,low=True):
        # Sufficient box inequality on each trilinear support: convex weighted sum obeys it.
        ind=B.indices;val=np.repeat(rhs,np.diff(B.indptr));nonzero=B.data>1e-10
        if low:np.maximum.at(lower,ind[nonzero],val[nonzero])
        else:np.minimum.at(upper,ind[nonzero],val[nonzero])
    def propose(self,phi,V,F,iteration):
        g=self.g;p=self.p;active=abs(phi)<p['active_band_mm'];boundary=np.zeros(g.shape,bool)
        for k in range(3):
            a=[slice(None)]*3;a[k]=[0,-1];boundary[tuple(a)]=True
        active&=~boundary.ravel();ix=np.flatnonzero(active);N=len(ix);offset=phi-self.phi0
        lo=np.maximum(-p['CFL_field_mm'], -p['total_field_correction_mm']-offset);hi=np.minimum(p['CFL_field_mm'],p['total_field_correction_mm']-offset)
        self.restrict_bounds(self.C,p['CAD_field_margin_mm']-self.C@phi,lo,hi,True)
        hp=self.HP@phi;self.restrict_bounds(self.HP,-self.protect_tol-hp,lo,hi,True);self.restrict_bounds(self.HP,self.protect_tol-hp,lo,hi,False)
        assert (lo<=hi+1e-12).all(),'INFEASIBLE_BOX';assert (lo<=1e-10).all()and(hi>=-1e-10).all(),'CURRENT_FIELD_NOT_FEASIBLE'
        fixed=(hi-lo)<1e-10;active&=~fixed;ix=np.flatnonzero(active);N=len(ix)
        matrices=[];targets=[];blocks=[]
        def add(A,b,weight,label):
            if not len(b):return
            scale=np.sqrt(weight/len(b));matrices.append(A[:,ix]*scale);targets.append(np.asarray(b)*scale);blocks.append(dict(name=label,rows=len(b),weight=weight))
        rows=self.d.contour_rows(V,F,g,phi)
        for cid in self.d.fit:
            for direction in ['PRED_TO_OBS','OBS_TO_PRED']:
                rr=[r for r in rows if r['source']==cid and r['direction']==direction]
                if not rr:continue
                B,_=g.basis(np.array([r['P']for r in rr]));w=np.array([r['w']/r['grad_norm']for r in rr]);r=np.array([r['residual']for r in rr]);hu=np.sqrt(np.minimum(1,p['Huber_px']/np.maximum(np.linalg.norm(r,axis=1),1e-12)))
                for k in range(2):add(sparse.diags(w[:,k]*hu)@B,r[:,k]*hu,self.d.weights[cid]*.5/p['contour_sigma_px']**2,'contour_'+cid+'_'+direction)
        hero=self.H@phi;hw=np.sqrt(self.hero_weight*np.minimum(1,.5/np.maximum(abs(hero),1e-12)));add(sparse.diags(hw)@self.H,-hero*hw,p['HERO_weight']/.5**2,'HERO')
        I=sparse.eye(g.N,format='csr')[ix];add(I,-offset[ix],p['prior_weight']/.75**2,'prior')
        D=g.differences(active)
        for A in D:add(A,-A@offset,p['H1_weight'],'H1')
        cent,Ds=g.centered(active);lap=sum([A.T@A for A in Ds]);local=sparse.eye(g.N,format='csr')[cent]@lap
        add(local,-local@offset,p['bending_weight'],'bending')
        grad=g.gradient(phi)[cent];gn=np.linalg.norm(grad,axis=1);n=grad/np.maximum(gn[:,None],1e-12);E=sum([sparse.diags(n[:,k])@Ds[k]for k in range(3)]);sel=abs(phi[cent])<.5
        add(E[sel],(1-gn)[sel],p['eikonal_weight'],'Eikonal')
        A=sparse.vstack(matrices,format='csr');b=np.concatenate(targets)
        sol=lsq_linear(A,b,bounds=(lo[ix],hi[ix]),method='trf',lsq_solver='lsmr',tol=p['LS_tol'],lsmr_tol=p['LSMR_tol'],max_iter=p['LS_TRF_max_iter'],lsmr_maxiter=p['LSMR_maxiter'])
        delta=np.zeros(g.N);delta[ix]=sol.x
        report=dict(variables=N,rows=A.shape[0],nnz=A.nnz,solver_status=int(sol.status),solver_message=sol.message,optimality=float(sol.optimality),cost=float(sol.cost),iterations=sol.nit,finite=bool(np.isfinite(delta).all()),delta_min_mm=float(delta.min()),delta_max_mm=float(delta.max()),contour_N=len(rows),expansion_proposals=sum(r['normal_velocity_mm']>0 for r in rows),contraction_proposals=sum(r['normal_velocity_mm']<0 for r in rows),blocks=blocks,protected_HERO_N=int(self.protect.sum()),CAD_constraints_N=len(self.cad_points))
        table('metrics/iter_%02d_CORRESPONDENCES.csv'%iteration,rows);np.savez_compressed(R/'local_results'/('iter_%02d_PROPOSAL.npz'%iteration),delta=delta)
        return delta,report,rows
    def cheap_constraints(self,oldphi,newphi,V,F,oldV,oldF):
        p=self.p;reasons=[];m=trimesh.Trimesh(V,F,process=False);vol=m.volume;prev=volume(oldV,oldF)
        if not m.is_watertight or not m.is_winding_consistent or vol<=0:reasons.append('TOPOLOGY_OR_ORIENTATION')
        components=len(m.split(only_watertight=False));
        if components!=1:reasons.append('MULTIPLE_COMPONENTS')
        if not p['volume_lower_ratio']<=vol/self.initial_volume<=p['volume_upper_ratio']:reasons.append('VOLUME_PRIOR')
        if max(vol/prev,prev/vol)>p['per_step_volume_ratio']:reasons.append('STEP_VOLUME')
        oldrt=mesh_scene(oldV,oldF);rt=mesh_scene(V,F);move=np.r_[oldrt.compute_distance(o3d.core.Tensor(V.astype(np.float32))).numpy(),rt.compute_distance(o3d.core.Tensor(oldV.astype(np.float32))).numpy()]
        if move.max()>p['max_surface_step_mm']:reasons.append('TRUE_SURFACE_STEP')
        grad=np.linalg.norm(self.g.gradient(newphi),axis=1);near=abs(newphi)<.5;quant=np.quantile(grad[near],[.01,.5,.99])
        if quant[0]<p['gradient_p01_lower']or quant[2]>p['gradient_p99_upper']:reasons.append('SDF_METRIC_DISTORTION')
        hp=np.abs(self.HP@newphi);cv=self.C@newphi
        if (hp>self.protect_tol+1e-7).any():reasons.append('PROTECTED_HERO')
        if cv.min()<p['CAD_field_margin_mm']-1e-7:reasons.append('CAD_SAMPLED_FIELD')
        return reasons,dict(volume_mm3=vol,volume_ratio=vol/self.initial_volume,components=components,actual_surface_move_mm=stats(move),gradient_quantiles=quant,protected_HERO_abs_mm=stats(hp),CAD_sample_min_field_mm=float(cv.min()))
