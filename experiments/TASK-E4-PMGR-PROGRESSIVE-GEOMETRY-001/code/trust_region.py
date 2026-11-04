"""Millimetre candidate trust region, triangle checks, reversible updates."""
from inputs import *
from scipy.spatial import cKDTree
def self_intersections(V,F):
    t=V[F];cent=t.mean(1);r=np.linalg.norm(t-cent[:,None],axis=2).max();pairs=cKDTree(cent).query_pairs(2*r,output_type='ndarray')
    if not len(pairs):return dict(intersections=0,coplanar_candidates=0)
    i,j=pairs.T;shared=(F[i,:,None]==F[j,None,:]).any((1,2));box=(t[i].min(1)<=t[j].max(1)+1e-9).all(1)&(t[j].min(1)<=t[i].max(1)+1e-9).all(1);i=i[~shared&box];j=j[~shared&box];A=t[i];B=t[j];found=np.zeros(len(A),bool)
    for a,b in [(A,B),(B,A)]:
        e1=b[:,1]-b[:,0];e2=b[:,2]-b[:,0]
        for k in range(3):
            o=a[:,k];d=a[:,(k+1)%3]-o;p=np.cross(d,e2);det=(e1*p).sum(1);good=abs(det)>1e-10;inv=np.zeros(len(det));inv[good]=1/det[good];s=o-b[:,0];u=(s*p).sum(1)*inv;q=np.cross(s,e1);v=(d*q).sum(1)*inv;tt=(e2*q).sum(1)*inv
            found|=good&(u>1e-7)&(v>1e-7)&(u+v<1-1e-7)&(tt>1e-7)&(tt<1-1e-7)
    # Near-coplanar overlapping AABBs are unresolved warnings, not certified
    # intersections. Conservative candidate rejection includes these warnings.
    na=np.cross(A[:,1]-A[:,0],A[:,2]-A[:,0]);nb=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]);na/=np.maximum(np.linalg.norm(na,axis=1)[:,None],1e-15);nb/=np.maximum(np.linalg.norm(nb,axis=1)[:,None],1e-15)
    cop=(abs((na*nb).sum(1))>1-1e-9)&(abs(((B[:,0]-A[:,0])*na).sum(1))<1e-8)
    return dict(intersections=int(found.sum()),coplanar_candidates=int(cop.sum()))
class Guard:
    def __init__(self,problem,parts):
        self.p=problem;self.V0=problem.b['V'];self.F=problem.F;self.cross0=np.cross(self.V0[self.F[:,1]]-self.V0[self.F[:,0]],self.V0[self.F[:,2]]-self.V0[self.F[:,0]]);self.area0=np.linalg.norm(self.cross0,axis=1);self.base_parts=parts;self.ring0=self.ring(self.V0);self.last_ring=self.ring0;self.base_self=self_intersections(self.V0,self.F)
    def ring(self,V):
        t=V[self.F];P=np.vstack([V,t.mean(1),(t[:,0]+t[:,1])/2,(t[:,1]+t[:,2])/2,(t[:,2]+t[:,0])/2]);d=ringscene(self.p.scene).compute_signed_distance(o3d.core.Tensor(P.astype(np.float32))).numpy();return d
    def check(self,V,old,parts,oldparts,loss,oldloss):
        reasons=[];max_step=float(np.linalg.norm(V-old,axis=1).max());total=float(np.linalg.norm(V-self.V0,axis=1).max())
        if not np.isfinite(V).all()or not np.isfinite(loss):reasons.append('NONFINITE')
        if max_step>self.p.tau+1e-6:reasons.append('STEP_TRUST')
        if total>.25*self.p.diameter:reasons.append('TOTAL_TRUST')
        if loss>oldloss+1e-7:reasons.append('GLOBAL_OBJECTIVE')
        for cid,new,prev,base in zip(self.p.ids,parts,oldparts,self.base_parts):
            if float(new['loss'])>float(prev['loss'])*1.05+.01:reasons.append('VIEW_REGRESSION:'+cid)
            if new['hit']<max(prev['hit'],base['hit'])-.02*512:reasons.append('COVERAGE_LOSS:'+cid)
            if np.isfinite(new['H_MAE'])and np.isfinite(prev['H_MAE'])and new['H_MAE']>prev['H_MAE']+.1:reasons.append('HERO_LOSS:'+cid)
        t=V[self.F];cross=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);ratio=np.linalg.norm(cross,axis=1)/self.area0;dot=(cross*self.cross0).sum(1)
        if ratio.min()<.1:reasons.append('AREA_COLLAPSE')
        if dot.min()<=0:reasons.append('FACE_FOLD')
        rd=self.ring(V)
        # A per-step epsilon alone accumulates penetration. The immutable P0
        # limit must hold simultaneously with the previous accepted state.
        # BOTH lower bounds must hold: their intersection is the maximum,
        # not the minimum. min() would silently keep the looser old-step bound.
        limit=np.maximum(np.minimum(self.last_ring,0),np.minimum(self.ring0,0))-.01
        if np.any(rd<limit):reasons.append('RING_PENETRATION')
        si=dict(intersections=None,coplanar_candidates=None)
        if not reasons:
            si=self_intersections(V,self.F)
            if si['intersections']>self.base_self['intersections']:reasons.append('SELF_INTERSECTION')
            if si['coplanar_candidates']>self.base_self['coplanar_candidates']:reasons.append('COPLANAR_UNRESOLVED')
        return reasons,dict(max_step_mm=max_step,total_displacement_mm=total,min_area_ratio=float(ratio.min()),ring_min_signed_mm=float(rd.min()),ring_inside_N=int((rd<-.01).sum()),**si),rd
