"""Projection and coarse-prior audit of interpolation-only refinement, no GT."""
from multiview import *
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('case');a=p.parse_args();c=Case(a.case);ch=FreeVertices(c);obj=MultiObjective(c,ch);values=[]
 for scale in [0.,.01]:
  V=tensor((c.V-c.center)/c.scale);W=V+scale*V;m=mesh(W,c.F);pr=obj.prior(m);values.append(dict(affine_scale_delta=scale,prior=relative_total(pr).item(),parts={k:v.item()for k,v in pr.items()}))
 with torch.no_grad():
  cid=c.fit[0];fr=c.fragments(c.base,cid);loss,alpha,w,*_=c.aware(fr,cid,True);t=c.views[cid]['target'];probe=dict(view=cid,initial_RingAware_soft_MSE=float(loss),foreground_alpha_mean=float((alpha*t).sum()/t.sum().clamp_min(1)),soft_alpha_sum=float(alpha.sum()),note='soft face-union can vary with tessellation even at identical physical shape; not geometric improvement')
 save('metrics/'+a.case+'_DENSITY_CONTROL.json',dict(case=a.case,values=values,soft_projection_probe=probe,reference='same coarse restriction for E0/E1/E2, no GT'))
if __name__=='__main__':main()
