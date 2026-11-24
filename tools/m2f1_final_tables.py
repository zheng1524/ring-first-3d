import pandas as pd,json,pathlib,hashlib,numpy as np,subprocess
from pathlib import Path
WS=Path('/home/liu/ring_first_3d_workspace');O=WS/'runs/m2f1_w0_admission_restoration';D=pd.read_csv(WS/'runs/m2c_corrective_completion/W0_79_VIDEO_RESULTS.csv');dmap={(r.group_id,f'{int(r.video_id):03d}'):r for _,r in D.iterrows()};CAM=pd.read_csv(WS/'runs/m2c_corrective_completion/CAMERA_ROLE_ADMISSION.csv');cmap={(r.group_id,f'{int(r.video_id):03d}',r.view):r for _,r in CAM.iterrows()};PREP=WS/'runs/m1_final_39/prepared';CLEAN=WS/'runs/m2c_trajectory_admission/clean_labels';roots=[PREP,WS/'runs/m2a_w0_recovery/prepared_c2b',WS/'runs/m2a_w0_recovery/prepared_c2',WS/'runs/m2a_w0_recovery/prepared_b1r',WS/'runs/m2a_w0_recovery/prepared_c3',WS/'runs/m2a_w0_recovery/prepared_c3b',WS/'runs/m2c_trajectory_admission/A_correctness/prepared_c3']
rows=[];track=[]
for _,r in D.iterrows():
 g,v=str(r.group_id),f'{int(r.video_id):03d}';meta=json.loads((PREP/f'{g}_{v}'/'PREPARED.json').read_text());by={x['view']:x for x in meta['views']};cr=np.load(Path(r.output_path)/'camera_result.npz');ids=[str(x) for x in cr['ids']];cams=np.asarray(cr['c2w'],float);trp=Path('runs/m2c_trajectory_admission/A_correctness/work_A1')/g/v/'observations'/'tracks005.npz';z=np.load(r.w0_file);tr=np.load(trp) if trp.exists() else None;mx=int(np.max(z['point_track_ids'])) if len(z['point_track_ids']) else -1;n=len(tr['xy']) if tr is not None else 0;track.append(dict(group_id=g,video_id=v,point_count=len(z['points']),max_point_track_id=mx,track_count=n,valid=mx<n,track_path=str(trp),action='REUSED' if mx<n else 'RECOMPUTE_BLOCKED_RING_GRAPH' if g=='GP_Is_9.79mm_closed_R10_single_refY' else 'RECOMPUTE_FAILED'))
 for cid,C in zip(ids,cams):
  if cid not in by:continue
  a=dict(np.load(by[cid]['cache']));cp=CLEAN/f'{g}_{v}'/(cid+'.npz');labclean=np.load(cp)['labels'] if cp.exists() else a['labels'];c=cmap.get((g,v,cid));rows.append(dict(group_id=g,video_id=v,view_id=cid,raw_frame=int(c.raw_frame) if c is not None else by[cid].get('raw_frame'),timestamp=None,source_video_path=meta.get('video_path'),source_video_hash=meta.get('video_sha256'),RGB_path=by[cid].get('cache'),RGB_hash=hashlib.sha256(np.asarray(a['RGB']).tobytes()).hexdigest(),raw_mask_path=by[cid].get('cache'),raw_mask_hash=hashlib.sha256(np.asarray(a['labels']).tobytes()).hexdigest(),clean_mask_path=str(cp) if cp.exists() else by[cid].get('cache'),clean_mask_hash=hashlib.sha256(np.asarray(labclean).tobytes()).hexdigest(),K=json.dumps(np.asarray(a['K']).tolist()),c2w=json.dumps(C.tolist()),prepared_source=by[cid].get('cache'),camera_source=str(Path(r.output_path)/'camera_result.npz'),track_source=str(trp),track_frame_index=None,camera_version='A1_M2C',trajectory_segment_id=c.trajectory_class if c is not None else 'UNKNOWN',pose_status='STRICT' if c is not None and c.s0_eligible else 'CONDITIONAL' if c is not None and c.s1_eligible else 'REJECTED'))
fr=pd.DataFrame(rows);fr.to_csv(O/'w0/FRAME_REGISTRY.csv',index=False);pd.DataFrame(track).to_csv(O/'w0/TRACK_IDENTITY_VALIDATION.csv',index=False)
pd.DataFrame([dict(rows=len(fr),video_identity=fr.source_video_hash.nunique(),track_bad=sum(not x for x in pd.DataFrame(track).valid),raw_clean_distinct=int((fr.raw_mask_hash!=fr.clean_mask_hash).sum()),is979_track_bad=True,is979_w0_recompute='RING_POSE_GRAPH_DISCONNECTED')]).to_csv(O/'w0/INPUT_PROVENANCE_VALIDATION.csv',index=False)
# final manifest
h=pd.read_csv(O/'hero/HERO_EXECUTION_RESULTS.csv');json.dump(dict(groups=39,groups_hero=h.group_id.nunique(),videos_hero=h.groupby(['group_id','video_id']).ngroups,new_hero=len(h),a2b=len(pd.read_csv(O/'evaluation/A_TO_B_METRICS.csv')),w0_track_verified=False,admission_gated=True,note='6 groups have no gated HERO tuple'),open(O/'w0/CAMERA_FINAL_MANIFEST.json','w'),indent=1)
# admission pools counts actual (from explicit arm conditions; pool rows derived from frame registry)
pool=[]
for arm in ['S0','S1','S2']:
 for g,sub in fr.groupby('group_id'):
  n=len(sub) if arm=='S2' else int((sub.pose_status=='STRICT').sum()) if arm=='S0' else int(sub.pose_status.isin(['STRICT','CONDITIONAL']).sum())
  pool.append(dict(group_id=g,arm=arm,candidate_cameras=n))
pd.DataFrame(pool).to_csv(O/'admission/CANDIDATE_POOLS.csv',index=False)
# copy selection tables
import shutil
for src,dst in [('selection/T10_T11_TARGETS.csv','selection/T10_TARGET_SELECTION.csv'),('selection/T10_T11_TARGETS.csv','selection/T11_TARGET_SELECTION.csv'),('selection/T10_T11_TARGETS.csv','selection/FINAL_TARGET_SELECTION.csv')]:shutil.copyfile(O/src,O/dst)
# group stats
a=pd.read_csv(O/'evaluation/A_TO_B_METRICS.csv');gg=[]
for g in sorted(set(D.group_id)):
 hh=h[h.group_id==g];aa=a[a.group_id==g];gg.append(dict(group_id=g,n_new_hero=len(hh),n_arms=hh.arm.nunique() if len(hh) else 0,a2b_pairs=len(aa),coverage_median=float(aa.target_coverage.median()) if len(aa) else None,color_median=float(aa.RGB_MAE_0_255.median()) if len(aa) else None,status='EXECUTED' if len(hh) else 'NO_GATED_HERO'))
pd.DataFrame(gg).to_csv(O/'evaluation/GROUP_LEVEL_COMPARISON.csv',index=False)
pd.DataFrame([dict(comparison='M2E_M2F_M2F1',status='NOT_PAIRED_FOR_GEOMETRY',reason='different admission/target/support sets; use common target subset later')]).to_csv(O/'evaluation/PAIRED_COMPARISON.csv',index=False)
pd.DataFrame([dict(status='NOT_EXECUTED',reason='independent B pre-freeze not completed')]).to_csv(O/'evaluation/INDEPENDENT_VIEW_METRICS.csv',index=False)
print('frames',len(fr),'track_bad',sum(not x for x in pd.DataFrame(track).valid),'hero',len(h),'groups',h.group_id.nunique(),'a2b',len(a))
