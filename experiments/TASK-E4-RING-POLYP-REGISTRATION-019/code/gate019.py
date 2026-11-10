from objective019 import *
import open3d as o3d

def main():
 views=load(R/'config/VIEWS.json');ids=[v['id']for v in views if v['video']=='005'and v['role']=='FIT'];test=[ids[0],ids[len(ids)//2],ids[-1]];r=FrozenRenderer(test);rows=[];H=tensor(yaw_matrix(270),torch.float64);rs=scene(r.ringV,r.ringF);body=scene(r.V,r.F)
 for cid in test:
  d=r.views[cid];T=(H@d['T']).cpu().numpy();K=d['K'].copy();A=np.diag([.5,.5,1]);A[:2,2]=-.25;K=A@K;oz=cast(body,K,T,180,320);cam=r.camera(d,tensor(T,torch.float64));fr=r.hard(r.body,cameras=cam);z=fr.zbuf[0,...,0].cpu().numpy()*r.scale;ok=np.isfinite(oz)&(z>0);err=abs(oz[ok]-z[ok]);rep=[];loss=[]
  for _ in range(3):
   q=torch.zeros(6,dtype=torch.float64,device=device,requires_grad=True);HH=exp_se3(q)@H;L=r.ring_loss(HH,cid);g=torch.autograd.grad(L,q)[0];rep.append(g.cpu().numpy());loss.append(float(L))
  repeat=float(np.linalg.norm(rep[1]-rep[0])/max(np.linalg.norm(rep[0]),1e-12));different=[]
  for angle in [0,37,90,181,270]:
   with torch.no_grad():different.append(float(r.ring_loss(tensor(yaw_matrix(angle),torch.float64),cid)))
  row=dict(view=cid,O3D_P3D_metric_axial=stats(err),Ring_gradient_finite=bool(np.isfinite(rep).all()),Ring_gradient_repeat_relative=repeat,Ring_pure_yaw_loss_range=float(np.ptp(different)),Ring_yaw_gradient=float(rep[0][5]),gradient=rep[0],passed=bool(len(err)>0 and np.quantile(err,.95)<.003 and np.isfinite(rep).all()and repeat<1e-4 and np.ptp(different)<1e-5 and abs(rep[0][5])<1e-4));rows.append(row)
 save('metrics/PROJECTION_AND_POSE_GRADIENT_GATE.json',dict(rows=rows,all_passed=all(x['passed']for x in rows),official_mesh_raster=True,CAD_physical_yaw_not_used=True));assert all(x['passed']for x in rows),rows;print('019_PROJECTION_RING_YAW_POSE_GRADIENT_GATE_PASS',flush=True)
if __name__=='__main__':main()
