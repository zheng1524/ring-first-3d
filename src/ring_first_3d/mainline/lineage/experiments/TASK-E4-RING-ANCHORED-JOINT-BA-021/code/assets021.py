"""Read-only four-group camera/native identity checks and bounded other-video inventory."""
from common import *
import collections
P14=REPO/'experiments/TASK-E4-PYTORCH3D-014';P18=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018'
def main():
 rows=[];source=[];scope=load(R/'config/FOUR_GROUP_INPUTS.json');g01={v['id']:v for v in load(R/'config/VIEWS.json')};cameras=[]
 for g in scope:
  V=load(Path(g['bodies']['B0']['path']).parent/'ALL_VIEW_META.json')['views']
  if g['group']=='G01':V=list(g01.values())
  for v in V:
   C=np.asarray(v['T']);K=np.asarray(v['K']);rows.append(dict(group=g['group'],view=v['id'],video=v.get('video',v.get('sid','').split('_')[-1]),role=v['role'],qualification=v.get('qualification','UNSPECIFIED_RETAINED'),rotation_orthogonality_error=float(np.max(abs(C[:3,:3].T@C[:3,:3]-np.eye(3)))),rotation_determinant=float(np.linalg.det(C[:3,:3])),camera_distance_to_Ring_origin_mm=float(np.linalg.norm(C[:3,3])),K_focal_px=K[[0,1],[0,1]],camera_source=v.get('pose_source'),frame_binding=v.get('frame_binding')))
  for s in g['sources']:
   a=np.load(s['observation']['path']);m=np.load(s['mesh']['path']);v=g01[s['id']]if s['id']in g01 else next(x['meta'] for x in g['views']if x['view_id']==s['id']);C=np.asarray(v['T']);K=np.asarray(v['K']);shape=a['native_shape'];A=np.diag([shape[1]/640,shape[0]/360,1.]);A[:2,2]=A.diagonal()[:2]*.5-.5;mapping=np.max(abs(A@K-a['K']));pt=(a['X']-a['T'][:3,3])@a['T'][:3,:3];uv=pt@a['K'].T;uv=uv[:,:2]/uv[:,2:];d=dict(group=g['group'],source=s['id'],origin=s['origin'],original_face_ids_N=len(m['original_face_id']),native_pixel_ID_N=len(a['pixel_id']),camera_to_frozen_cache_max_abs_mm=float(abs(a['T']-C).max()),native_K_mapping_max_abs_px=float(mapping),native_X_reprojection_max_px=float(np.linalg.norm(uv-a['uv'],axis=1).max()),native_axial_Z_difference_max_mm=float(abs(pt[:,2]-a['z']).max()),unmodified_source_geometry=True,observation_asset=s['observation'],mesh_asset=s['mesh']);source.append(d)
  pervideo={}
  for video in sorted({v.get('video',v.get('sid','').split('_')[-1])for v in V}):
   selected=[v for v in V if v.get('video',v.get('sid','').split('_')[-1])==video];C=np.array([np.asarray(v['T'])[:3,3]for v in selected]);directions=C/np.linalg.norm(C,axis=1)[:,None];ang=np.degrees(np.arccos(np.clip(directions@directions.T,-1,1)));pervideo[video]=dict(N=len(C),maximum_direction_separation_deg=float(ang.max()))
  cameras.append(dict(group=g['group'],views_N=len(V),per_native_video=pervideo,native_video_frames='separate Ring-local gauges; no cross-gauge angular pooling',absolute_camera_error='NOT_EVALUABLE_NO_POSE_GT',Ring_reprojection_in='metrics/groups/*_PROJECTIONS.csv',native_and_image_pose_equality_is_integrity_only=True))
 table('metrics/FOUR_GROUP_CAMERA_INTEGRITY.csv',rows);save('metrics/FOUR_GROUP_CAMERA_INTEGRITY.json',rows);save('metrics/FOUR_GROUP_SOURCE_COORDINATE_AUDIT.json',source);table('metrics/FOUR_GROUP_SOURCE_COORDINATE_AUDIT.csv',source);save('metrics/FOUR_GROUP_DIRECTION_COVERAGE.json',cameras)
 assert max(x['camera_to_frozen_cache_max_abs_mm']for x in source)<1e-5
 assert max(x['native_K_mapping_max_abs_px']for x in source)<1e-4
 # Existing asset registries only. No crawling videos, no inference or new poses.
 raw=load(P14/'config/RAW_ASSETS.json');views=load(P14/'config/ALL_VIEWS.json');inventory=[]
 for group in ['G03','G05','G06']:
  sids=sorted({v['sid']for v in views if v['case']==group}|{a['sid']for a in raw if a.get('case')==group and a.get('type')=='video'})
  for sid in sids:
   vs=[v for v in views if v['case']==group and v['sid']==sid];aa=[a for a in raw if a.get('case')==group and a.get('sid')==sid];rgb=[v.get('RGB_source',v.get('RGB_path'))for v in vs];mask=[v.get('Mask_source',v.get('Mask_path'))for v in vs];hero=sorted(set(p for v in vs for p in v.get('HERO_sources',[])if Path(p).exists()));sf=P14/'runtime'/(sid+'_BG_LANDMARKS.npz');count=len(np.load(sf)['X'])if sf.exists()else None
   inventory.append(dict(group=group,sid=sid,role='CURRENT_004_OR_OTHER_VIDEO_ASSET_ONLY',view_records_N=len(vs),readable_RGB_N=sum(bool(p and Path(p).exists())for p in rgb),readable_Mask_N=sum(bool(p and Path(p).exists())for p in mask),frozen_posed_view_N=sum(v.get('T')is not None and v.get('K')is not None for v in vs),existing_NATIVE_HERO_paths=hero,existing_NATIVE_HERO_N=len(hero),existing_same_video_SIFT_landmarks_N=count,SIFT_path=str(sf)if sf.exists()else'MISSING',raw_asset_records=aa,not_new_crossvideo_certification=True,recovery_attempt='014 RAW_ASSETS and ALL_VIEWS, source HERO links and same-video runtime SIFT cache inspected; no missing asset fabricated'))
 save('metrics/OTHER_VIDEO_ASSET_INVENTORY.json',inventory);table('metrics/OTHER_VIDEO_ASSET_INVENTORY.csv',inventory);save('provenance/FOUR_GROUP_INPUT_INTEGRITY_COMPLETE.json',dict(epoch=time.time(),source_N=len(source),all_native_source_poses_match=True,all_native_K_mappings_match=True,scope='integrity, not physical camera certification'));print('FOUR_GROUP_INPUT_COORDINATES_VERIFIED',len(source),flush=True)
if __name__=='__main__':main()
