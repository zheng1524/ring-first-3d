from ring020 import *

def main():
 allv=load(R/'config/VIEWS.json');ids=['G01_005_raw00057','G01_005_raw00459','G01_005_raw00745'];rr=RingRenderer(ids);base=np.asarray(next(x['T']for x in load(R/'config/HISTORICAL_CANDIDATES.json')if x['tag']=='HISTORICAL_FULL_RoMa'));scale=tensor(load(R/'config/PROTOCOL.json')['pose_scale'],torch.float64);out=[]
 for cid in ids:
  q=torch.zeros(6,device=device,dtype=torch.float64,requires_grad=True);H=exp_se3(q*scale)@tensor(base,torch.float64);L,aux,segs=rr.losses(H,cid);grads={k:torch.autograd.grad(v,q,retain_graph=True)[0].detach().cpu().numpy()for k,v in L.items()};check={}
  for key in ['I','O','C']:
   fd=[]
   for j in range(6):
    a=[]
    for sign in [-1,1]:
     z=torch.zeros_like(q);z[j]=sign*.001;ls,_,_=rr.losses(exp_se3(z*scale)@tensor(base,torch.float64),cid,selection=segs);a.append(float(ls[key].detach()))
    fd.append((a[1]-a[0])/.002)
   fd=np.array(fd);g=grads[key];rel=float(np.linalg.norm(fd-g)/max(np.linalg.norm(fd),1e-8));check[key]=dict(autograd=g,finite_difference=fd,relative_error=rel,pass_gradient=rel<.03)
  yaw=[];yg=[]
  for ang in [0,20,90,180,270]:
   t=torch.tensor(float(np.deg2rad(ang)),device=device,dtype=torch.float64,requires_grad=True);z=t*0;o=z+1;c=t.cos();s=t.sin();G=torch.stack([torch.stack([c,-s,z,z]),torch.stack([s,c,z,z]),torch.stack([z,z,o,z]),torch.stack([z,z,z,o])]);ls,_,_=rr.losses(G@tensor(base,torch.float64),cid);v=sum(ls.values());yaw.append(float(v.detach()));yg.append(float(torch.autograd.grad(v,t)[0]))
  d=rr.data[cid];C=canonical(tensor(base,torch.float64)@d['T']);segments,aa=rr.curves.segments(C.cpu().numpy(),d['K'].cpu().numpy(),True);dist=[]
  for key in ['inner','outer']:
   l,ad=rr.curves.point_to_segments(aa['contours'][key],np.ones(len(aa['contours'][key])),segments[key],C,d['K'],key);dist.append(dict(key=key,raster_boundary_to_actual_edge_px=ad['distance_px']))
  passed=all(x['pass_gradient']for x in check.values())and all(aux[k]['N']>0 and np.linalg.norm(grads[k])>1e-7 for k in ['I','O','C'])and max(abs(np.array(yg)))<1e-5 and np.ptp(yaw)<1e-4 and all(np.isfinite(g).all()for g in grads.values())and all(a['raster_boundary_to_actual_edge_px']['p95']<2.5 for a in dist)
  out.append(dict(view=cid,loss={k:float(v.detach())for k,v in L.items()},gradient=grads,curve_gradient_checks=check,pure_yaw_values=yaw,pure_yaw_gradient=yg,pure_yaw_range=float(np.ptp(yaw)),CAD_correspondence=dist,aux=aux,passed=passed));print('RING020_GATE',cid,passed,{k:round(v['relative_error'],6)for k,v in check.items()},np.ptp(yaw),flush=True)
 save('metrics/RING_CURVE_PROJECTION_GRADIENT_GATE.json',dict(rows=out,all_passed=all(x['passed']for x in out),source=asset(Path(__file__))));assert all(x['passed']for x in out),'Do not optimize before actual CAD curve gradients/visibility pass'
if __name__=='__main__':main()
