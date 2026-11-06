"""Read-only depth coordinate proof. No camera or pixel remapping edits."""
from common import *
def main():
 src={x['id']:x for x in load('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/provenance/INPUT_ELIGIBILITY.json')['references']};rows=[]
 for c in['real_Ip','real_IIa','real_Is']:
  for v in getcase(c)['views']:
   cid=v['id'];raw=np.load(src[cid]['E1_actual_native']['path']);o=np.load(R/'depth_observations'/(cid+'.npz'));im=np.load(R/'inputs'/c/(cid+'.npz'));T=raw['pose']if'pose'in raw else raw['reference_pose_mm'];s=raw['depth_mm'].shape[0]/360;A=np.diag([1,s,1]);A[1,2]=s*.5-.5;derived=A@im['K'];pe=float(abs(T-o['T']).max());ke=float(abs(derived-o['K']).max());headerr=float(abs(raw['K_index_native']-o['K']).max())if'K_index_native'in raw else None;uv=o['uv'];ze=float(abs(raw['depth_mm'][uv[:,1],uv[:,0]]-o['z']).max());assert pe<1e-10 and ke<1e-9 and ze<3e-5;assert headerr is None or headerr<1e-9
   rows.append(dict(case=c,source=cid,raw_pose_error=pe,derived_native_K_error=ke,raw_header_K_error=headerr,depth_original_error_mm=ze,resize_scale_y=s,pixel_center_shift_y=s*.5-.5,naive_row_scaling_principal_point_error_px=abs(s*im['K'][1,2]-o['K'][1,2]),mapping='u_native center rays: A_y=(sy,sy/2-1/2); RGB_uv=K_RGB inv(K_native) uv_native',no_input_edit=True))
 save('metrics/NATIVE_CAMERA_DEPTH_CONTRACT.json',rows)
if __name__=='__main__':main()
