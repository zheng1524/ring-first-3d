"""Post-freeze geometry diagnostics; no model, pose fit, GT or input changes."""
from evidence import *
def main():
 allrows=[];ringrows=[];overlaps=[];output_contract=[]
 records=load(R/'provenance/MAP_RUN_RESULT.json')['rows']+load(R/'provenance/MAP_M3_SUPPLEMENT_RESULT.json')['rows'];records={r['mode']:r for r in records if r['status'].startswith('SMOKE_PASS')}
 ms=methods('G01_005')
 for mode,rec in records.items():
  name='Map_'+mode;z=ms[name];folder=R/'local_results/map'/mode;gauge=np.load(folder/'surface.npz')['evaluation_gauge_to_frozen_first_camera'];predposes=[];inputposes=[]
  for i in range(2):
   a=np.load(folder/f'view{i}_official_outputs.npz');P=a['pts3d'][0].reshape(-1,3);T=a['camera_poses'][0];camera=(P-T[:3,3])@T[:3,:3];depth=a['depth_z'][0,...,0].reshape(-1);finite=np.isfinite(P).all(1)&np.isfinite(depth);err=abs(camera[:,2]-depth);polyp=finite&(a['source_Mask'].reshape(-1)==1)&(a['mask'][0,...,0].reshape(-1)>.5);output_contract.append(dict(mode=mode,view=i,finite_point_N=int(finite.sum()),all_pixels_depth_pose_max_m=float(err[finite].max()),valid_Polyp_depth_pose_max_mm=float(err[polyp].max()*1000),valid_Polyp_depth_pose_relative_p95=float(np.quantile(err[polyp]/depth[polyp],.95)),valid_Polyp_depth_z_median_m=float(np.median(depth[polyp])),camera_rotation_det=float(np.linalg.det(T[:3,:3])),valid_output_Polyp_N=rec['views'][i]['valid_Polyp_points'],contract_pass=bool(err[polyp].max()*1000<.001)))
   world=(P@gauge[:3,:3].T+gauge[:3,3])*1000;mask=a['source_Mask'].reshape(-1);valid=finite&(a['mask'][0,...,0].reshape(-1)>.5)&(mask==2);rp=world[valid];signed=cad_scene('R10').compute_signed_distance(o3d.core.Tensor(rp.astype(np.float32)),nthreads=2,nsamples=3).numpy()if len(rp)else np.array([])
   ringrows.append(dict(mode=mode,view=i,input_Ring_pixels=int((mask==2).sum()),predicted_valid_Ring_N=len(rp),absolute_CAD_surface_distance_median_mm=float(np.median(abs(signed)))if len(rp)else None,absolute_CAD_surface_distance_p95_mm=float(np.quantile(abs(signed),.95))if len(rp)else None,inside_CAD_N=int((signed<-.02).sum()),predicted_Ring_partial_extent_mm=np.ptp(rp,axis=0).tolist()if len(rp)else None,meaning='known fixed CAD alignment diagnostic; partial observed Ring, not recovered full diameter'))
   predposes.append(T);inputposes.append(np.asarray(rec['views'][i]['input_pose_m']))
  relpred=np.linalg.inv(predposes[0])@predposes[1];relin=np.linalg.inv(inputposes[0])@inputposes[1];delta=np.linalg.inv(relin)@relpred
  cut=rec['views'][0]['valid_Polyp_points'];F=z['F'];f0=F[(F<cut).all(1)];f1=F[(F>=cut).all(1)];c=CC[load(R/'config/map_minimal.json')['input_ids'][0]];K=np.array(c['K_raw']);pose=np.array(c['c2w_mm']);a=render_triangle(z['P'],f0,z['C'],K,pose,np.eye(4),'R10');b=render_triangle(z['P'],f1,z['C'],K,pose,np.eye(4),'R10');valid=a['valid']&b['valid'];dz=abs(a['z_mm'][valid]-b['z_mm'][valid]);tau=np.maximum(.5,3*a['z_mm'][valid]/min(K[0,0],K[1,1]));conflict=dz>tau
  overlaps.append(dict(mode=mode,common_reference_pixels=int(valid.sum()),conflict_pixels=int(conflict.sum()),conflict_fraction=float(conflict.mean())if len(dz)else None,axial_discrepancy_median_mm=float(np.median(dz))if len(dz)else None,axial_discrepancy_p95_mm=float(np.quantile(dz,.95))if len(dz)else None,threshold='max(0.5mm,3pixel footprints)',relative_pose_rotation_difference_deg=float(np.degrees(np.arccos(np.clip((np.trace(delta[:3,:3])-1)/2,-1,1)))),relative_pose_translation_difference_mm=float(np.linalg.norm(relpred[:3,3]-relin[:3,3])*1000),not_absolute_geometry_accuracy=True))
 for name,z in ms.items():
  if not len(z['P']):allrows.append(dict(method=name,point_N=0,CAD_inside_N=None,maximum_inside_mm=None,status='NO_OBSERVED_SUPPORTED_SURFACE'));continue
  d=cad_scene('R10').compute_signed_distance(o3d.core.Tensor(z['P'].astype(np.float32)),nthreads=2,nsamples=3).numpy();allrows.append(dict(method=name,point_N=len(d),CAD_inside_N=int((d<-.02).sum()),maximum_inside_mm=float(max(0,-d.min())),status='CONDITIONAL_FIXED_CAD_DIAGNOSTIC',tolerance_mm=.02))
 table('metrics/ALL_METHOD_CAD_AUDIT.csv',allrows);table('metrics/MAP_RING_SCALE_ALIGNMENT.csv',ringrows);table('metrics/MAP_OVERLAP_AND_POSE_DIAGNOSTIC.csv',overlaps);table('metrics/MAP_OUTPUT_GEOMETRY_CONTRACT.csv',output_contract)
 print('GEOMETRY_AUDIT',len(allrows),'CAD rows',len(ringrows),'Ring rows',len(output_contract),'output contracts')
if __name__=='__main__':main()
