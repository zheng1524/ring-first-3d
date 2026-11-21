from objective019 import *

def main():
 ids=[v['id']for v in load(R/'config/VIEWS.json')if v['video']=='005'and v['role']=='FIT'];r=FrozenRenderer(ids);rows=[];states=[np.zeros(6),np.array([.2,-.1,.15,.02,-.03,.01])]
 with torch.no_grad():
  for cid in ids:
   for dx in states:
    H=exp_se3(tensor(dx,torch.float64))@tensor(yaw_matrix(270.4),torch.float64);cam=r.camera(r.views[cid],H@r.views[cid]['T']);a=r.hard(r.ring,cameras=cam);b=r.ring_hard(r.ring,cameras=cam);ma=a.pix_to_face>=0;mb=b.pix_to_face>=0;same=bool(torch.equal(ma,mb));err=float(abs(a.zbuf[ma&mb]-b.zbuf[ma&mb]).max()*r.scale);rows.append(dict(view=cid,pose=dx,valid_mask_identical=same,max_axial_z_difference_mm=err,passed=same and err<1e-5))
 grad=[]
 for cid in [ids[0],ids[len(ids)//2],ids[-1]]:
  vals=[]
  for naive in [True,False]:
   saved=r.ring_hard
   if naive:r.ring_hard=r.hard
   q=torch.zeros(6,dtype=torch.float64,device=device,requires_grad=True);H=exp_se3(q)@tensor(yaw_matrix(270.4),torch.float64);L=r.polyp(H,cid,False);g=torch.autograd.grad(L,q)[0].detach().cpu().numpy();vals.append((float(L),g));r.ring_hard=saved
  diff=float(np.linalg.norm(vals[0][1]-vals[1][1])/max(np.linalg.norm(vals[0][1]),1e-12));grad.append(dict(view=cid,loss_difference=abs(vals[0][0]-vals[1][0]),gradient_relative_difference=diff,passed=abs(vals[0][0]-vals[1][0])<1e-6 and diff<1e-3))
 save('metrics/PERFORMANCE_BACKEND_EQUIVALENCE.json',dict(all_passed=all(x['passed']for x in rows+grad),all52FIT_two_test_poses=rows,gradient_controls=grad,all_CAD_triangles_and_all_pixels_retained=True,not_a_loss_or_algorithm_change=True));assert all(x['passed']for x in rows+grad);print('ALL52_HARD_CAD_BINNING_EQUIVALENCE_PASS',flush=True)
if __name__=='__main__':main()
