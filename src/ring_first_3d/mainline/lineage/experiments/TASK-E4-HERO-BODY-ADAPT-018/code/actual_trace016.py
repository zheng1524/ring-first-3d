"""Replay recorded accepted/rejected geometry at its actual loss ramp and state."""
from tape import *
import argparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('case');ap.add_argument('snapshot');ap.add_argument('label');a=ap.parse_args();guard_optimizer();c=Case(a.case);ch=FreeVertices(c);ch.total_trust_D=1.;s=np.load(a.snapshot);before=s['before_V'];after=s['after_V']if'after_V'in s else s['V'];q=tensor(before-c.V,torch.float64).detach().requires_grad_(True);obj=MultiObjective(c,ch);obj.attempt=int(s['attempt']);G,per,corr,rec=instrument(c,ch,obj,q);gg=GeometryGuard(c,ch);gg.lastsd=gg.ring_distance(before);gg.lastreverse=gg.reverse(before);why,checks,_=gg.inspect(after,before)
 with torch.no_grad():old,op=obj.compute(q,False);new,np_=obj.compute(tensor(after-c.V,torch.float64),False)
 full=sum(G.values());delta=after-before;rec.update(case=a.case,label=a.label,snapshot=asset(Path(a.snapshot)),actual_attempt=obj.attempt,actual_delta_mm=stats(np.linalg.norm(delta,axis=1)),method=str(s['method'])if'method'in s else'REJECTED_RECORDED_CANDIDATE',actual_geometry_reasons=why,actual_geometry_checks=checks,actual_loss_before=old,actual_loss_after=new,actual_component_change={k:np_[k]-op[k]for k in op},actual_step_dot_current_gradient=float((full*tensor(delta,torch.float64)).sum()),component_dot_actual_step={k:float((g*tensor(delta,torch.float64)).sum())for k,g in G.items()},gradient_is_not_optimizer_displacement=True)
 ramp=.25+.75*min(1.,obj.attempt/40.);coeff=dict(silhouette=1.,missing=.05*ramp,extra=.05*ramp,contour=.01*ramp,absolute=.01,relative=.01,prior=1.)
 rec['weighted_actual_component_change']={k:rec['actual_component_change'][k]*v for k,v in coeff.items()};rec['weighted_component_sum_error']=sum(rec['weighted_actual_component_change'].values())-rec['actual_component_change']['total'];rec['raw_parts_require_coefficients']=True
 if'full_loss_gradient'in s:
  fg=tensor(s['full_loss_gradient'],torch.float64);rec['recomputed_gradient_vs_recorded_relative']=float((full-fg).norm()/fg.norm().clamp_min(1e-30))
 flat={cid+'__'+k:v for cid,p in per.items()for k,v in p.items()};np.savez_compressed(R/'metrics'/(a.case+'_'+a.label+'_ACTUAL_TAPE.npz'),before_V=before,after_V=after,F=c.F,F_solid=c.F_solid,delta=delta,**{k:g.cpu().numpy()for k,g in G.items()},**flat);save('metrics/'+a.case+'_'+a.label+'_ACTUAL_TRACE.json',rec);save('metrics/'+a.case+'_'+a.label+'_ACTUAL_CORRESPONDENCES.json',{cid:v for cid,v in corr.items()});print('ACTUAL_TRACE',a.case,a.label,obj.attempt,why,new-old,flush=True)
if __name__=='__main__':main()
