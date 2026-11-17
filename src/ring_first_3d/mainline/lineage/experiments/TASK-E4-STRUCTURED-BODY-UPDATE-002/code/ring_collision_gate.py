"""Detached non-worsening collision predicate; fixed material and CAD probes."""
import numpy as np
import open3d as o3d
from ring_first_3d.multisurface.geometry import scene

BARY=np.array([[1,0,0],[0,1,0],[0,0,1],[1/3]*3,[.5,.5,0],[0,.5,.5],[.5,0,.5]],float)
def samples(V,F):return np.einsum('ki,nij->nkj',BARY,V[F])
def signed(s,P):return s.compute_signed_distance(o3d.core.Tensor(np.asarray(P,np.float32).reshape(-1,3)),nsamples=3,nthreads=2).numpy().astype(float).reshape(np.shape(P)[:-1])
def area(V,F):q=V[F];return np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)*.5

class RingCollisionGate:
    def __init__(self,initial,ring):
        self.initial=initial;self.ring=ring;self.rs=scene(ring['V'],ring['F']);self.face_lookup={tuple(f):i for i,f in enumerate(initial['F_solid'])}
        self.source_samples=samples(initial['V'],initial['F_solid']);self.cad_samples=samples(ring['V'],ring['F']);self.area=area(initial['V'],initial['F_solid']);self.cad_area=area(ring['V'],ring['F'])
        ds=[signed(self.rs,self.source_samples)for _ in range(3)];self.initial_body=np.maximum(0,-ds[0]);self.initial_ring=np.maximum(0,-signed(scene(initial['V'],initial['F_solid']),self.cad_samples))
        # Repeat-query variability plus float32 coordinate ULP, fixed before updates.
        noise=max(float(abs(x-ds[0]).max())for x in ds);ulp=np.finfo(np.float32).eps*max(1.,float(abs(np.r_[initial['V'],ring['V']]).max()))
        self.epsilon=max(4*noise,4*ulp);self.calibration=dict(repeat_queries=3,repeat_max_mm=noise,float32_coordinate_ulp_mm=ulp,epsilon_mm=self.epsilon)
    def measure(self,body):
        sd=signed(self.rs,samples(body['V'],body['F_solid']));rd=signed(scene(body['V'],body['F_solid']),self.cad_samples);p=np.maximum(0,-sd);q=np.maximum(0,-rd);A=area(body['V'],body['F_solid'])
        return dict(body_penetration=p,ring_penetration=q,body_area=A,body_max_mm=float(p.max()),ring_max_mm=float(q.max()),body_area_mm2=float((A*(p>self.epsilon).mean(1)).sum()),ring_area_mm2=float((self.cad_area*(q>self.epsilon).mean(1)).sum()),body_energy_mm4=float((A*(p*p).mean(1)).sum()),ring_energy_mm4=float((self.cad_area*(q*q).mean(1)).sum()))
    def check(self,body,current,sweep=None):
        m=self.measure(body);old=self.measure(current);current_lookup={tuple(f):i for i,f in enumerate(current['F_solid'])};bad=[];regions=[]
        for j,f in enumerate(body['F_solid']):
            key=tuple(f);i=self.face_lookup.get(key);k=current_lookup.get(key)
            if i is not None:
                ceiling=self.initial_body[i]
                if k is not None:ceiling=np.minimum(ceiling,old['body_penetration'][k])
                if (m['body_penetration'][j]>ceiling+self.epsilon).any():bad.append(j)
            elif sweep is not None:
                # First transition strip has explicit parent attachment provenance.
                first=int(np.sum(sweep.keep));root=first<=j<first+len(sweep.loop)+sweep.angles
                parents=[self.face_lookup.get(tuple(sweep_template_face))for sweep_template_face in self.initial['F'][sweep.parent_faces]]
                source=max([self.initial_body[x].max()for x in parents if x is not None]or[0.]) if root else 0.
                current_parent=[current_lookup.get(tuple(f))for f in self.initial['F'][sweep.parent_faces]]
                source=min(source,max([old['body_penetration'][x].max()for x in current_parent if x is not None]or[source])) if root else 0.
                ceiling=np.full(7,source)
                if k is not None:ceiling=np.minimum(ceiling,old['body_penetration'][k])
                if (m['body_penetration'][j]>ceiling+self.epsilon).any():bad.append(j)
                regions.append(dict(face=j,root=bool(root),parent_faces=sweep.parent_faces.tolist(),ceiling_mm=float(source)))
            else:
                if m['body_penetration'][j].max()>self.epsilon:bad.append(j)
        reverse_bad=np.flatnonzero((m['ring_penetration']>np.minimum(self.initial_ring,old['ring_penetration'])+self.epsilon).any(1))
        ok=not bad and not len(reverse_bad)
        summary={k:v for k,v in m.items()if not isinstance(v,np.ndarray)}
        summary.update(accepted=ok,epsilon_mm=self.epsilon,body_worsened_face_ids=bad,ring_worsened_region_ids=reverse_bad.tolist(),new_surface_provenance=regions)
        return ok,summary,m
