"""FIT-only added deadzone gradient check, not a new optimization experiment."""
from ba021 import *
def main():
 cid=next(v['id']for v in load(R/'config/VIEWS.json')if v['video']=='005'and v['role']=='FIT');obj=BA('CROSS',[cid],'B3');hist=load(R/'config/HISTORICAL_CANDIDATES.json');H=tensor(next(x['T']for x in hist if x['tag']=='HISTORICAL_FULL_RoMa'),torch.float64);q=tensor([.03,-.02,.01,.01,.02,-.01],torch.float64).requires_grad_(True);C=canonical(obj.transform(q,H)@obj.ring.data[cid]['T']);segments=obj.ring.curves.segments(C.detach().cpu().numpy(),obj.ring.data[cid]['K'].cpu().numpy());original=obj.ring.curves.segments;obj.ring.curves.segments=lambda *args,**kwargs:segments;parts=obj.ring.term(obj.transform(q,H),cid,True);rows=[]
 for name in ['Ieps','Oeps']:
  g=torch.autograd.grad(parts[name],q,retain_graph=True)[0]
  for i in [0,4]:
   eps=1e-5;a=q.detach().clone();b=q.detach().clone();a[i]+=eps;b[i]-=eps
   with torch.no_grad():fa=obj.ring.term(obj.transform(a,H),cid,True)[name];fb=obj.ring.term(obj.transform(b,H),cid,True)[name]
   fd=float((fa-fb)/(2*eps));ad=float(g[i]);err=abs(fd-ad)/max(abs(fd),abs(ad),1e-8);rows.append(dict(channel=name,pose_parameter=i,AD=ad,FD=fd,relative_error=err,passed=err<1e-3))
 d=tensor([0.,.5,1.,1.5,3.],torch.float64).requires_grad_(True);f=hub((d-1).clamp_min(0)/3);g=torch.autograd.grad(f.sum(),d)[0];ok=bool((f[:3]==0).all()and(g[:3]==0).all()and(g[3:]>0).all());save('metrics/RING_TOLERANCE_GRADIENT_TEST.json',dict(actual_FIT_CAD_checks=rows,controlled_distance_px=d.detach().cpu().numpy(),controlled_loss=f.detach().cpu().numpy(),controlled_gradient=g.detach().cpu().numpy(),deadzone_control_passed=ok,all_passed=ok and all(a['passed']for a in rows),source=asset(Path(__file__)),no_HOLDOUT_HERO_body=True));print('TOLERANCE021',ok and all(a['passed']for a in rows),rows,flush=True);assert ok and all(a['passed']for a in rows)
if __name__=='__main__':main()
