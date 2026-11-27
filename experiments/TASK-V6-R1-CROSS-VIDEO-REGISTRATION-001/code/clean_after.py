"""Apply frozen T first, then call original classifier with shared fixed CAD."""
from context import *
from clean2 import mapping,verify_clean_identity
from ring_first_3d.mainline.native.cleaning import classify_native
from ring_first_3d.v6_raw.trusted_restore import trusted_subset,stats
from ring_first_3d.sim.geometry import transform
from ring_first_3d.multisurface.geometry import sample_mesh
import trimesh,tempfile,traceback

def one(source,ordinal,out,T0):
 resource();verify_clean_identity();dest=out/'clean'/(source['side']+'__'+source['tag']);dest.mkdir(parents=True,exist_ok=False);freeze('CLEAN_AFTER_REGISTRATION',dest,[out/'PREDICTION_FREEZE.json']);info=mapping(source);V,F=info['V'],info['F'];TV=np.eye(4)if source['side']=='A'else T0;world=transform(V,TV);payload=dict(info['payload']);payload['raw']=dict(payload['raw'],V=world);payload['native']=dict(payload['native'],reference_pose_mm=TV@payload['native']['reference_pose_mm']);scratch=T/'runtime/scratch';scratch.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(dir=scratch,prefix='registered_clean_')as tmp:
  tmp=Path(tmp);mesh=tmp/'INPUT_WORLD.ply';trimesh.Trimesh(world,F,process=False).export(mesh);payload['original_mesh_path']=str(mesh);rec=classify_native(tmp,source['cad_path'],mapped_input=payload);e=dict(np.load(tmp/'FACE_EVIDENCE.npz'))
 state=e['state'];sub=trusted_subset(world,F,state);assert np.array_equal(e['original_face_id'],np.arange(len(F)))and np.array_equal(e['F'],F);assert np.array_equal(sub['V'],world)and np.array_equal(sub['F'],F[state==0]);assert np.array_equal(e['V'],world)
 np.savez_compressed(dest/'FACE_SELECTION.npz',state=state,reason_bits=e['reason_bits'],original_face_id=e['original_face_id'],trusted_original_face_id=sub['original_face_id'],working_uv=info['uv'],native_pixel_id=info['raw']['native_pixel_id']);_,ids,bary=sample_mesh(V,F,CFG['surface_samples_per_source'],20261127+ordinal);np.savez_compressed(dest/'RAW_DOMAIN.npz',original_face_id=ids,bary=bary);tri=V[F];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
 # Existing R1 single-video clean is only a post-freeze diagnostic; never consumed by registration.
 upstream=FULL/'clean'/source['case']/source['tag'];comparison={'status':'NOT_FOUND'}
 if (upstream/'COMPLETE.json').exists():
  old=read(upstream/'COMPLETE.json');assert old['raw_mesh_sha256']==source['mesh_sha256']and old['native_sha256']==source['native_sha256'];assert old['filter']=='F[state==0]';oldp=upstream/'FACE_EVIDENCE.npz';assert sha(oldp)==old['retained_hashes'][str(oldp)];oldstate=np.load(oldp)['state'];comparison=dict(status='COMPARED_AFTER_PREDICTION',changed_faces=int((oldstate!=state).sum()),old_trusted_faces=int((oldstate==0).sum()),path=str(oldp),sha256=sha(oldp),cause='shared CAD stays fixed while B geometry/camera transforms; float32 classifier input follows original implementation')
 record=dict(source=source,origin='NEW_POST_REGISTRATION',status='COMPLETE',classification=rec,raw=stats(V,F),trusted=stats(V,F[state==0]),raw_area_mm2=float(area.sum()),trusted_area_mm2=float(area[state==0].sum()),excluded_area_mm2=float(area[state!=0].sum()),raw_faces=len(F),trusted_faces=int((state==0).sum()),selection_path=str(dest/'FACE_SELECTION.npz'),selection_sha256=sha(dest/'FACE_SELECTION.npz'),raw_domain=str(dest/'RAW_DOMAIN.npz'),T_local_to_global=TV,registration_method='M5',classification_coordinate_frame='shared A metric frame, fixed CAD_A',common_faces_additional_coordinate_change_mm=0.,upstream_single_video_clean_comparison=comparison)
 assert sha(info['meshpath'])==source['mesh_sha256']and sha(info['nativepath'])==source['native_sha256'];save(dest/'COMPLETE.json',record);print('CLEAN AFTER',source['case'],source['tag'],int((state==0).sum()),'/',len(F),flush=True);return record

def main():
 for row in read(T/'config/SELECTION.json')['groups']:
  out=RUN/'real'/row['group'];asset=read(T/'config'/row['group']/'ASSETS.json');pred=read(out/'PREDICTIONS.json');before=sha(out/'PREDICTIONS.json');assert before==read(out/'PREDICTION_FREEZE.json')['predictions_sha256'];T0=pred['M5']['T'];index=[]
  for i,source in enumerate(asset['sources']):
   try:
    if T0 is None:raise ValueError('M5_NO_TRANSFORM_CLEAN_NOT_RUN')
    rec=one(source,i,out,np.array(T0))
   except Exception as e:rec=dict(source=source,status='MISSING',origin='NOT_COMPLETED',error=repr(e),traceback=traceback.format_exc());print('CLEAN FAILURE',source['case'],source['tag'],repr(e),flush=True)
   index.append(rec);save(out/'CLEAN_INDEX.json',index)
  assert before==sha(out/'PREDICTIONS.json');save(out/'CLEAN_TRANSFORM_UNCHANGED.json',dict(prediction_sha256=before,unchanged=True))
if __name__=='__main__':main()
