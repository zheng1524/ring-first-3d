"""CPU-only chart geometry test; not an optimizer or Phase B prediction."""
from common import *
from publish import arm_case
import subprocess
if os.environ.get('E4_CONTROL_CHILD')!='1':
 root=arm_case('NUMERIC_CONTROL','G03',R/'arms/Init-A/local_results/G03/FINAL.npz','B');env=dict(os.environ,E4_RUN_DIR=str(root),E4_CONTROL_CHILD='1');subprocess.run([sys.executable,'-B',__file__],env=env,check=True)
else:
 import p3d
 p3d.device=p3d.torch.device('cpu')
 from stalk import *
 c=Case('G03');ch=FreeVertices(c);obj=MultiObjective(c,ch);q=torch.zeros((ch.N,3),device=device,dtype=torch.float64)
 for cid in c.fit:obj.contour(ch.vertices(q),cid)
 seed=make_seed(c,c.V,obj);save('inputs/G03/STALK_SEED.json',seed);assert seed['status']=='RESIDUAL_ASSOCIATION_PROXY';ch=StalkChart(c);z=torch.zeros(ch.parameter_shape,device=device,dtype=torch.float64,requires_grad=True);v=ch.vertices(z);err=float((v-tensor(c.V,torch.float64)).abs().max());rows=[]
 for i in range(11):
  q=z.detach().clone();q[3*ch.N+i]=.001;dv=ch.vertices(q).detach()-v.detach();rows.append(dict(parameter=i,max_vertex_mm=float(dv.norm(dim=1).max()),outside_patch_displacement_mm=float(dv[ch.s==0].norm(dim=1).max())if(ch.s==0).any()else 0.))
 loss=(v*tensor(np.arange(ch.N*3).reshape(ch.N,3)/1000.,torch.float64)).sum();loss.backward();record=dict(identity_error_mm=err,rows=rows,finite_chain_rule=bool(torch.isfinite(z.grad).all()),real_camera_loss_test='deferred to all-case actual Phase B probe',optimizer_updates=0,GT_read=False,case='G03',not_a_selected_Phase_B_initializer=True);save('metrics/CENTERLINE_NUMERIC_CONTROL.json',record);assert err<1e-10 and all(r['max_vertex_mm']>0 and r['outside_patch_displacement_mm']<1e-10 for r in rows)and record['finite_chain_rule'];print('CENTERLINE_NUMERIC_CONTROL_PASS',err,flush=True)
