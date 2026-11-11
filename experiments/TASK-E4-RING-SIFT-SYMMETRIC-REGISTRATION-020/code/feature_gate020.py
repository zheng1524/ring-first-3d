"""Actual FIT-only symmetric projection gradient and unknown-Mid checks."""
from objective020 import *
def main():
 base=np.asarray(next(x['T']for x in load(R/'config/HISTORICAL_CANDIDATES.json')if x['tag']=='HISTORICAL_FULL_RoMa'));sf=SymmetricFeatures('CROSS');scale=tensor(load(R/'config/PROTOCOL.json')['pose_scale'],torch.float64);seed=tensor(base,torch.float64);q=torch.zeros(6,device=device,dtype=torch.float64,requires_grad=True)
 def vals(x):
  H=exp_se3(x*scale)@seed;F,E,_=sf.evaluate(H);F0,_,_=sf.evaluate(H,mode='single');return dict(forward=F0,reverse=2*F-F0,symmetric=F,EPI=E)
 values=vals(q);rows=[]
 for k,v in values.items():
  g=torch.autograd.grad(v,q,retain_graph=True)[0].detach().cpu().numpy();fd=[]
  for j in range(6):
   ss=[]
   for sign in [-1,1]:
    x=torch.zeros_like(q);x[j]=sign*.001
    with torch.no_grad():ss.append(float(vals(x)[k]))
   fd.append((ss[1]-ss[0])/.002)
  rel=float(np.linalg.norm(g-fd)/max(np.linalg.norm(fd),1e-12));rows.append(dict(component=k,gradient=g,finite_difference=fd,relative_error=rel,nonzero=bool(np.linalg.norm(g)>1e-8),passed=bool(rel<.03 and np.isfinite(g).all()and np.linalg.norm(g)>1e-8)))
 cid='G01_v004_raw00152';rr=RingRenderer([cid]);d=rr.data[cid];I=tensor(np.eye(4),torch.float64);L,_,seg=rr.losses(I,cid);before=float(L['C']);e=d['evidence'];unknown_N=int((e['mid_weight']==0).sum());assert unknown_N>0;old=e['mid'].copy();e['mid']=old.copy();e['mid'][e['mid_weight']==0]+=[1000,1000];L,_,_=rr.losses(I,cid,selection=seg);after=float(L['C']);e['mid']=old;unknown_ok=abs(before-after)<1e-12
 save('metrics/SYMMETRIC_PROJECTION_GRADIENT_CHECK.json',dict(rows=rows,unknown_Mid_test_view=cid,unknown_Mid_moved_N=unknown_N,unknown_Mid_zero_weight_loss_before=before,unknown_Mid_zero_weight_loss_after=after,unknown_Mid_no_supervision=unknown_ok,all_passed=all(x['passed']for x in rows)and unknown_ok,FIT_only=True,HOLDOUT=False,body=False,GT=False));print('SYMMETRIC_FEATURE_GATE',[(a['component'],a['relative_error'])for a in rows],unknown_ok,'moved_unknown_N',unknown_N,flush=True);assert all(x['passed']for x in rows)and unknown_ok
if __name__=='__main__':main()
