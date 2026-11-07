"""Independent branchwise check of new term. Does not hide full-objective switches."""
from contour_objective import *
def fixed_branch(cd,V,cid,s):
 d=cd.c.views[cid];T=d['T'];ed=s['eid'];t=tensor(s['t'],torch.float64);P=V[tensor(ed[:,0],torch.int64)]*(1-t)[:,None]+V[tensor(ed[:,1],torch.int64)]*t[:,None];cam=(P-tensor(T[:3,3],torch.float64))@tensor(T[:3,:3],torch.float64);uv=cam@tensor(d['K'].T,torch.float64);uv=uv[:,:2]/uv[:,2:];h,w=d['labels'].shape;grid=torch.stack([2*uv[:,0]/(w-1)-1,2*uv[:,1]/(h-1)-1],1)[None,None];dt,ct=cd.data[cid];fw=tf.grid_sample(dt,grid,align_corners=True,padding_mode='border').reshape(-1);rv=(ct-uv[tensor(s['nn'],torch.int64)]).norm(dim=1)
 def hub(x):x=x/20;return torch.where(x<1,.5*x*x,x-.5)
 return .5*(hub(fw).mean()+hub(rv).mean())
def main():
 guard_optimizer();rows=[]
 for n in ['G03','G01','G02']:
  c=Case(n);ch=FreeVertices(c);cd=ContourDistance(c);q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);V=ch.vertices(q)
  for cid in c.fit:
   L,info=cd(V,cid);snap=cd.last[cid];g=torch.autograd.grad(L,q,retain_graph=True)[0];v=g/g.norm().clamp_min(1e-20);eps=1e-4
   with torch.no_grad():fp=float(fixed_branch(cd,ch.vertices(q+eps*v),cid,snap));fm=float(fixed_branch(cd,ch.vertices(q-eps*v),cid,snap));same=float(fixed_branch(cd,V,cid,snap))
   ad=float((g*v).sum());fd=(fp-fm)/(2*eps);err=abs(fd-ad)/max(1e-8,abs(ad));rows.append(dict(case=n,view=cid,loss=float(L),same_frozen_branch=same,gradient_norm=float(g.norm()),autodiff=ad,FD=fd,relative_error=err,passed=err<.01 and abs(same-float(L))<1e-9,scope='newdistance term fixed visibility/edge/NN branch only; full objective discontinuities separately retained'))
 save('metrics/DISTANCE_GRADIENT_CONTROL.json',dict(passed=all(x['passed']for x in rows),rows=rows));print(rows);assert all(x['passed']for x in rows)
if __name__=='__main__':main()
