"""Sparse common-point Jacobian blocks and explicit Schur information audit (not a BA solver)."""
from geometry021 import *
from scipy.linalg import block_diag
from scipy.spatial.transform import Rotation
from ba021 import CommonPoints,tensor,torch,exp_se3
def skew_np(x):return np.array([[0,-x[2],x[1]],[x[2],0,-x[0]],[-x[1],x[0],0]])
def spectrum(A):
 e,V=np.linalg.eigh((A+A.T)/2);tol=max(e.max(),1e-20)*1e-8;rank=int((e>tol).sum());return dict(eigenvalues=e,numerical_rank=rank,relative_rank_tolerance=1e-8,condition_full=float(e[-1]/e[0])if e[0]>tol else None,eigenvectors_columns=V)

def main():
 wait_freeze();rows=[];pointrows=[];gradient=[];scale=np.array(load(R/'config/PROTOCOL.json')['pose_scale']);rv=np.load(R/'inputs/G01/RING.npz');cad=scene(rv['V'],rv['F'])
 for arm in ['B1','B2','B3','SENS_B2_LightGlue','SENS_B2_020R2','NEG_B1','NEG_B2','NEG_B3']:
  a=load(R/'results'/(arm+'.json'));H=np.array(a['T']);X=np.array(a['X']);tracks=load(R/'observations'/(a['scope']+'_COMMON_TRACKS.json'));Kp=len(X);A=np.zeros((6,6));B=[np.zeros((6,3))for _ in X];D=[np.zeros((3,3))for _ in X];gt=np.zeros(6);gx=[np.zeros(3)for _ in X];sidegx=[np.zeros((Kp,3)),np.zeros((Kp,3))];pervideo=[[],[]];jrows=[]
  for t in tracks:
   k=t['track']
   for o in t['observations']:
    side=o['side'];C=np.asarray(o['native_C']);C=H@C if side else C;K=np.asarray(o['K']);P=(X[k]-C[:3,3])@C[:3,:3];u=P@K.T;uv=u[:2]/u[2];r=(uv-o['uv'])/3;norm=np.linalg.norm(r);rw=min(1.,1/max(norm,1e-20));w=o['weight']*t['track_weight'];jp=(K[:2]*u[2]-u[:2,None]*K[2])/u[2]**2;JX=jp@C[:3,:3].T/3;JT=np.c_[-jp@C[:3,:3].T,jp@C[:3,:3].T@skew_np(X[k])]/3 if side else np.zeros((2,6));JT=JT*scale[None];A+=w*rw*JT.T@JT;B[k]+=w*rw*JT.T@JX;D[k]+=w*rw*JX.T@JX;gt+=w*rw*JT.T@r;gx[k]+=w*rw*JX.T@r;sidegx[side][k]+=w*rw*JX.T@r;pervideo[side].append(float(np.linalg.norm(uv-o['uv'])))
  S=A.copy();effective=gt.copy()
  for k in range(Kp):S-=B[k]@np.linalg.pinv(D[k],rcond=1e-10)@B[k].T;effective-=B[k]@np.linalg.pinv(D[k],rcond=1e-10)@gx[k]
  x0=np.asarray(a['X0']);disp=np.linalg.norm(X-x0,axis=1);initialsd=cad.compute_signed_distance(o3d.core.Tensor(x0.astype(np.float32)),nsamples=11).numpy();finalsd=cad.compute_signed_distance(o3d.core.Tensor(X.astype(np.float32)),nsamples=11).numpy();sv=np.linalg.svd(X-X.mean(0),compute_uv=False);COV=np.linalg.pinv(S,rcond=1e-8);covstd=np.sqrt(np.maximum(np.diag(COV),0))*scale;cos=float(np.sum(sidegx[0]*sidegx[1])/max(np.linalg.norm(sidegx[0])*np.linalg.norm(sidegx[1]),1e-20));row=dict(arm=arm,landmarks_N=Kp,observations_N=sum(len(t['observations'])for t in tracks),fixed_X_pose_information=spectrum(A),Schur_eliminated_point_pose_information=spectrum(S),Schur_to_fixed_trace_ratio=float(np.trace(S)/max(np.trace(A),1e-20)),common_point_spatial_singular_values_mm=sv,point_displacement_mm=stats(disp),effective_pose_gradient_after_point_elimination=effective,conditional_std_proxy_mm_rad=covstd,unit_noise_covariance_not_calibrated=True,prior_not_in_geometric_information=True,video004_reprojection_px=stats(pervideo[0]),video005_reprojection_px=stats(pervideo[1]),point_gradient_video_cosine=cos,point_gradient_video_cosine_not_equal_pose_conflict=True)
  rows.append(row);W=np.array([t['whitener']for t in tracks]);white=np.einsum('kij,kj->ki',W,X-x0)
  for k,t in enumerate(tracks):pointrows.append(dict(arm=arm,track=k,X0=x0[k],X_final=X[k],displacement_mm=float(disp[k]),whitened_displacement=float(np.linalg.norm(white[k])),initial_Ring_signed_mm=float(initialsd[k]),final_Ring_signed_mm=float(finalsd[k]),point_information_spectrum=spectrum(D[k]),gradient004=sidegx[0][k],gradient005=sidegx[1][k],observations=len(t['observations'])))
  # Audit the original independent fixed-004/fixed-005 gradient conflict at this endpoint.
  if a['scope']=='CROSS':
   cp=CommonPoints('CROSS');q=torch.zeros(6,dtype=torch.float64,device='cuda',requires_grad=True);HH=exp_se3(q*tensor(scale,torch.float64))@tensor(H,torch.float64);old=[];vv={v['id']:v for v in load(R/'config/VIEWS.json')}
   for side in [0,1]:
    vals=[]
    for t in tracks:
     xx=t['X004_independent']if side==1 else t['X005_independent'];parts=[]
     for o in t['observations']:
      if o['side']!=side:continue
      C=tensor(o['native_C'],torch.float64);xp=tensor(xx,torch.float64)
      if side:C=HH@C
      else:xp=HH[:3,:3]@xp+HH[:3,3]
      p=(xp-C[:3,3])@C[:3,:3];uv=p@tensor(o['K'],torch.float64).T;r=(uv[:2]/uv[2]-tensor(o['uv'],torch.float64)).norm()/3;parts.append(torch.where(r<1,.5*r*r,r-.5)*o['weight']*2)
     vals.append(torch.stack(parts).sum()*t['track_weight'])
    L=torch.stack(vals).sum();old.append(torch.autograd.grad(L,q,retain_graph=True)[0].detach().cpu().numpy())
   gradient.append(dict(arm=arm,independent_anchor_gradient004_to005=old[1],independent_anchor_gradient005_to004=old[0],cosine=float(np.dot(old[0],old[1])/max(np.linalg.norm(old[0])*np.linalg.norm(old[1]),1e-20)),definition='same18 named tracks, separately frozen independent triangulations; not old020 complete PnP pool',joint_004_005_point_gradient_cosine=cos,warning='common X couples observations; opposing point gradients can be equilibrium. Do not label direct004 pose gradient=0 as solved conflict.'))
  print('SCHUR021',arm,row['Schur_eliminated_point_pose_information']['numerical_rank'],flush=True)
 save('metrics/BA_IDENTIFIABILITY.json',rows);table('metrics/BA_IDENTIFIABILITY.csv',rows);save('metrics/COMMON_POINT_MOVEMENT.json',pointrows);table('metrics/COMMON_POINT_MOVEMENT.csv',pointrows);save('metrics/FIXED_ANCHOR_GRADIENT_CONFLICT.json',gradient);table('metrics/FIXED_ANCHOR_GRADIENT_CONFLICT.csv',gradient)
 compare=[]
 for n in ['SENS_B2_LightGlue','SENS_B2_020R2']:
  D=np.array(load(R/'results'/f'{n}.json')['T'])@np.linalg.inv(np.array(load(R/'results/B2.json')['T']));compare.append(dict(run=n,translation_from_main_B2_mm=float(np.linalg.norm(D[:3,3])),rotation_from_main_B2_deg=float(np.degrees(Rotation.from_matrix(D[:3,:3]).magnitude())),not_used_for_selection=True))
 save('metrics/INITIALIZATION_SENSITIVITY.json',compare);table('metrics/INITIALIZATION_SENSITIVITY.csv',compare);save('runtime/IDENTIFIABILITY_COMPLETE.json',dict(epoch=time.time()));print('IDENTIFIABILITY021_COMPLETE',flush=True)
if __name__=='__main__':main()
