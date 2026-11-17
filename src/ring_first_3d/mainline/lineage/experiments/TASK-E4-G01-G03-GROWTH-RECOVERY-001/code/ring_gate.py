"""Current-state bidirectional collision non-worsening; initial is diagnostic only."""
import numpy as np
from ring_collision_gate import signed,samples,area
from ring_first_3d.multisurface.geometry import scene,closest

def metrics_accept(before,after,tolerance):
    bad=[]
    for direction in ['body','ring']:
        for key,eps in [('max_mm',tolerance['depth_mm']),('area_mm2',tolerance['area_mm2']),('energy_mm4',tolerance['energy_mm4'])]:
            name=direction+'_'+key
            if after[name]>before[name]+eps:bad.append(name)
    return bad

class CurrentRingGate:
    def __init__(self,current,ring):
        self.ring=ring;self.engine=scene(ring['V'],ring['F']);self.cad=samples(ring['V'],ring['F']);self.cad_area=area(ring['V'],ring['F'])
        repeats=[signed(self.engine,samples(current['V'],current['F_solid']))for _ in range(3)]
        repeat=max(float(abs(x-repeats[0]).max())for x in repeats)
        epsilon=max(4*repeat,4*np.finfo(np.float32).eps*float(max(1.,abs(np.r_[current['V'],ring['V']]).max())))
        self.depth_epsilon=epsilon;self.reference=self.measure(current)
        total=area(current['V'],current['F_solid']).sum()+self.cad_area.sum();p=max(self.reference['body_max_mm'],self.reference['ring_max_mm'])
        self.tolerance=dict(depth_mm=epsilon,area_mm2=float(total*epsilon),energy_mm4=float(total*(2*p*epsilon+epsilon**2)))
        self.calibration=dict(repeat_queries=3,repeat_variability_mm=repeat,float32_ULP_multiple=4,tolerances=self.tolerance)
    def measure(self,body):
        P=samples(body['V'],body['F_solid']);d=np.maximum(0,-signed(self.engine,P));q=np.maximum(0,-signed(scene(body['V'],body['F_solid']),self.cad));A=area(body['V'],body['F_solid'])
        _,_,fi=closest(self.engine,P.reshape(-1,3));local=np.zeros(len(self.ring['F']))
        np.maximum.at(local,fi,d.reshape(-1))
        return dict(body_max_mm=float(d.max()),ring_max_mm=float(q.max()),body_area_mm2=float((A*(d>self.depth_epsilon).mean(1)).sum()),ring_area_mm2=float((self.cad_area*(q>self.depth_epsilon).mean(1)).sum()),
            body_energy_mm4=float((A*(d*d).mean(1)).sum()),ring_energy_mm4=float((self.cad_area*(q*q).mean(1)).sum()),body_local_max_mm=local,ring_local_max_mm=q.max(1),body_penetration=d,ring_penetration=q)
    def check(self,candidate,current=None):
        before=self.reference if current is None else self.measure(current);after=self.measure(candidate);bad=metrics_accept(before,after,self.tolerance)
        for k in ['body_local_max_mm','ring_local_max_mm']:
            if (after[k]>before[k]+self.depth_epsilon).any():bad.append(k)
        return not bad,dict(reasons=bad,tolerance=self.tolerance,before={k:v for k,v in before.items()if np.isscalar(v)},after={k:v for k,v in after.items()if np.isscalar(v)},
            delta={k:after[k]-before[k]for k in before if np.isscalar(before[k])}),after
