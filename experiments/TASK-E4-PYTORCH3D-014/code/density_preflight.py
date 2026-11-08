"""Projection and coarse-prior audit of interpolation-only refinement, no GT."""
from multiview import *
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('case');a=p.parse_args();c=Case(a.case);ch=FreeVertices(c);obj=MultiObjective(c,ch);values=[]
 for scale in [0.,.01]:
  V=tensor((c.V-c.center)/c.scale);W=V+scale*V;m=mesh(W,c.F);pr=obj.prior(m);values.append(dict(affine_scale_delta=scale,prior=relative_total(pr).item(),parts={k:v.item()for k,v in pr.items()}))
 save('metrics/'+a.case+'_DENSITY_CONTROL.json',dict(case=a.case,values=values,reference='same coarse restriction for E0/E1/E2, no GT'))
if __name__=='__main__':main()
