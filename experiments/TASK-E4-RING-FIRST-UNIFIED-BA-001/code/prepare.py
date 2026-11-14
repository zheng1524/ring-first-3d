from ucommon import *
import shutil

def main():
 if(N/'provenance/INPUTS_FROZEN.json').exists():checkfreeze('provenance/INPUTS_FROZEN.json');print('INPUTS_ALREADY_FROZEN');return
 vv=load(G/'config/VIEWS.json');hist=load(P/'config/HISTORICAL_CANDIDATES.json');H=np.array(next(r['T']for r in hist if r['tag']=='HISTORICAL_FULL_RoMa'));confs=load(P/'config/FOUR_GROUP_INPUTS.json');assets=[];read=[]
 for f in [ORIGINAL,OLD/'experiments/ring_first_v5_geometry_crossvideo/scripts/g5_common.py',OLD/'experiments/ring_first_v5_geometry_crossvideo/scripts/ring_observations.py',OLD/'experiments/ring_pose_contact_v1/scripts/recover.py',OLD/'experiments/ring_pose_contact_v1/scripts/torus_geometry.py',OLD/'experiments/ring_first_v6_local_reconstruction/scripts/local_ring_sfm.py',OLD/'experiments/ring_first_v8_registration_narrow_baseline/scripts/registration.py',OLD/'experiments/ring_first_v9_ring_guided_recovery/scripts/local_pose_refinement.py',OLD/'experiments/ring_first_v13_multisource/scripts/rigid13.py',P/'code/ba021.py',P/'mature_geometric_pose_refinement/code/cad_render.py',P/'mature_geometric_pose_refinement/FAILURE_LEDGER.md']:
  read.append(asset(f));d=N/'provenance/source_snapshots'/(sha(f)[:12]+'_'+f.name);d.parent.mkdir(exist_ok=True);shutil.copyfile(f,d)
 save('provenance/ORIGINAL_SOURCE_READ_RECEIPT.json',read)
 for v in vv:
  a=np.load(v['cache']);v['RF_native']=a['T'];v['T']=H@a['T']if v['group']=='G01'and v['video']=='005'else a['T'];v['H0']=H if v['group']=='G01'and v['video']=='005'else np.eye(4);v['R_mm']=5.6;v['r_mm']=.6;v['physical_parameter_source']=asset(OLD/'experiments/ring_pose_contact_v1/scripts/torus_geometry.py');assets.extend([Path(v['cache']),Path(v['ring_path'])]);
  # Verify actual CAD radii rather than inferring from group morphology.
  ring=np.load(v['ring_path']);V=ring['V'];rho=np.linalg.norm(V[:,:2],axis=1);rr=float((rho.max()-rho.min())/2);RR=float((rho.max()+rho.min())/2);assert abs(RR-5.6)<.01 and abs(rr-.6)<.01
 save('config/VIEWS.json',vv);save('config/H0.json',dict(G01_005_to004=H,source=asset(P/'config/HISTORICAL_CANDIDATES.json'),selected_tag='HISTORICAL_FULL_RoMa',not021_refined=True));shutil.copyfile(P/'config/FOUR_GROUP_INPUTS.json',N/'config/FOUR_GROUP_INPUTS.json')
 for folder in ['features','matches','landmarks','ring_evidence','inputs']:
  target=G/folder;link=N/folder
  if not link.exists():link.symlink_to(target,target_is_directory=True)
 tracks=[];identity=[]
 common=load(P/'observations/CROSS_COMMON_TRACKS.json');merge={('004',r['source_landmark004']):r['track']for r in common};merge.update({('005',r['source_landmark005']):r['track']for r in common})
 for g in GROUPS:
  raw=[]
  for video in sorted({v['video']for v in vv if v['group']==g}):
   label=g+'_'+video;lm=np.load(G/'landmarks'/(label+'.npz'));oo=load(G/'landmarks'/(label+'_OBSERVATIONS.json'));pts=lm['X'].copy()
   # The old geometric map005 was in021B3 world; undo exactly then apply predeterminedRoMa.
   if g=='G01'and video=='005':
    H21=np.array(load(P/'results/B3.json')['T']);D=H@np.linalg.inv(H21);pts=pts@D[:3,:3].T+D[:3,3]
   assets.extend([G/'landmarks'/(label+'.npz'),G/'landmarks'/(label+'_OBSERVATIONS.json')])
   for k,t in enumerate(oo):
    key=('COMMON',merge[video,k])if g=='G01'and(video,k)in merge else(video,k);raw.append(dict(key=key,video=video,k=k,X0=pts[k],observations=t['observations'],parallax_deg=t['parallax_deg']))
  by=collections.defaultdict(list)
  for r in raw:by[r['key']].append(r)
  for key,rs in by.items():
   obs=[];seen=set();conflict=False
   for r in rs:
    for o in r['observations']:
     if o['view']in seen:conflict=True
     seen.add(o['view']);obs.append(o|dict(video=r['video'],native_track=r['k']))
   # Shared RGB identity only from021's original18cross links; no3D nearest matches.
   preferred=next((r for r in rs if r['video']=='004'),rs[0]);held=preferred['k']%5==0
   tr=dict(group=g,track_id=len([t for t in tracks if t['group']==g]),identity=str(key),source_tracks=[dict(video=r['video'],index=r['k'])for r in rs],X0=preferred['X0'],observations=obs,role='TRACK_HELD'if held else'TRACK_FIT',min_source_parallax_deg=min(r['parallax_deg']for r in rs),cross_video=len(rs)>1,duplicate_view_identity=conflict)
   assert not conflict;tracks.append(tr)
 save('config/TRACKS.json',tracks);table('metrics/TRACK_IDENTITY_AND_INPUT_COUNTS.csv',[dict(group=g,tracks_N=sum(t['group']==g for t in tracks),FIT_tracks_N=sum(t['group']==g and t['role']=='TRACK_FIT'for t in tracks),held_tracks_N=sum(t['group']==g and t['role']=='TRACK_HELD'for t in tracks),cross_tracks_N=sum(t['group']==g and t['cross_video']for t in tracks),observations_N=sum(len(t['observations'])for t in tracks if t['group']==g))for g in GROUPS])
 protocol=dict(task='TASK-E4-RING-FIRST-UNIFIED-BA-001',frozen_before_actual_optimization=True,groups=GROUPS,views_N=98,FIT_N=81,HOLDOUT_N=17,H0='fullRoMa not chosenbyheld',solver='pyceres2.6 Ceres2.2 LM DENSE_SCHUR',outer_iterations=4,inner_iterations=20,backtracks=8,sigma_px=3.,lambda_R=1.,lambda_F=.2,lambda_pose=.01,lambda_point=.001,pose_scale=[.6,.6,.6,*([float(np.deg2rad(5))]*3)],camera_center_bound_mm=1.2,rotation_bound_deg=10.,point_displacement_bound_mm=3.,H_translation_bound_mm=1.2,H_rotation_bound_deg=10.,point_prior_sigma_mm=1.,torus_samples=1024,ring_observation_max_per_curve=128,loss='vectorHuber perRGB observation, scalarHuber perpendicularcurveerror; normalized perview/track/video',reference='firstFIT004 frozen full6DOF;H004=I;first005localdeltafixedtoidentifyH',B3='5D local SE3 chart omits ringaxisworld z twist; independent sharedH6 and XYZ jointly optimize; no arbitrary cameraEuler yaw claim',B4='release6th localaxis ONLY ifB3 fullgeometry independentgatepasses; never onHERO preference',HOLDOUT='neverlocalfit;G01video005sharedH maymoveheldcameras fromFIT; heldtrack IDsexcluded',GT=False,HERO_in_loss=False,body_in_loss=False,no_scale=True,photos_gate='only after fourgroup trustedBA;otherwiseNOT_RUN',sensitivity='one fixed common 0.03mm/0.05degree start onB3 G01, neverselectbyheld',severe_degradation='paired heldSIFT increase>max(1px,25percent) or severegeometry/visibility; investigateandstopphotoextension')
 save('config/PROTOCOL.json',protocol);assets+=list((N/'config').glob('*.json'));freeze('provenance/INPUTS_FROZEN.json',list(dict.fromkeys(assets)),GT=False,source_readonly=True);print('PREPARED',len(vv),'views',len(tracks),'realRGBtracks',flush=True)
if __name__=='__main__':main()
