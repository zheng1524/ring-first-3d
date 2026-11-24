#!/usr/bin/env python3
"""M2C trajectory diagnostics, A0/A1/R2 comparison, analysis tables."""
import json,sys
from pathlib import Path
import numpy as np,pandas as pd
WS=Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2c_trajectory_admission'; A=OUT/'A_correctness'; B=OUT/'B_admission'; AN=OUT/'analysis'
for d in [A,B,AN]: d.mkdir(parents=True,exist_ok=True)
D=pd.read_csv(A/'W0_79_VIDEO_RESULTS.csv'); BASE=pd.read_csv(WS/'runs/m2b_ring_global_branch/W0_79_VIDEO_RESULTS.csv'); CLEAN=pd.read_csv(OUT/'MASK_CLEAN_PER_FRAME.csv')
# per-video trajectory
tr=[]
for _,v in D.iterrows():
 g,vv=str(v.group_id),f'{int(v.video_id):03d}'; p=Path(v.output_path); adm=pd.read_csv(p/'admission.csv').sort_values('raw_frame')
 # dt at 30 fps unless actual video fps
 meta=json.loads((Path(p)/'PREPARED.json').read_text()) if (Path(p)/'PREPARED.json').exists() else json.loads((WS/'runs/m1_final_39/prepared'/f'{g}_{vv}'/'PREPARED.json').read_text())
 fps=30.0
 try:
  import cv2; cap=cv2.VideoCapture(str(meta.get('video_path',''))); f=cap.get(cv2.CAP_PROP_FPS); cap.release()
  if f and f>1: fps=float(f)
 except Exception: pass
 dt=np.diff(adm.raw_frame.values.astype(float))/fps
 rot=adm.rotation_to_previous_deg.fillna(0).values[1:]; trans=adm.center_to_previous_mm.fillna(0).values[1:]
 rs=rot/np.maximum(dt,1e-6); ts=trans/np.maximum(dt,1e-6)
 jump_return=0; consecutive=0
 for i in range(1,len(rot)-1):
  if rot[i]>30 and rot[i-1]<15 and rot[i+1]<15: jump_return+=1
 if len(rot)>=2:
  for i in range(len(rot)-1):
   if rot[i]>30 and rot[i+1]>30: consecutive+=1
 large_gap=int((dt>1.8*np.median(dt)).sum()) if len(dt) else 0
 t4=bool(v.new_w0_poses<10 or (adm.held_n<6).any())
 cls='T2_ISOLATED_BRANCH' if jump_return else 'T3_CONSECUTIVE_BRANCH' if consecutive else 'T4_UNRESOLVED' if t4 else 'T1_SAMPLING_GAP' if large_gap else 'T0_CONTINUOUS'
 tr.append(dict(group_id=g,video_id=vv,fps=fps,dt_median_s=float(np.median(dt)) if len(dt) else None,dt_max_s=float(np.max(dt)) if len(dt) else None,
  n_large_gaps=large_gap,jump_return_count=jump_return,consecutive_high_rotation=consecutive,max_adj_rotation_deg=float(v.max_adjacent_rotation_deg or 0),max_adj_translation_mm=float(v.max_adjacent_translation_mm or 0),
  max_rot_speed_deg_s=float(np.max(rs)) if len(rs) else None,max_trans_speed_mm_s=float(np.max(ts)) if len(ts) else None,diagnostic_class=cls,repair_status='NO_REPAIR_A2_NOT_UNIVERSAL',repair_note='A2 corrected-CAD universal run not executed'))
pd.DataFrame(tr).to_csv(A/'TRAJECTORY_DIAGNOSTICS.csv',index=False)
# A0/A1 comparison and R2
comp=[]
for _,v in D.iterrows():
 g,vv=str(v.group_id),f'{int(v.video_id):03d}'; b=BASE[(BASE.group_id==g)&(BASE.video_id==v.video_id)]
 comp.append(dict(group_id=g,video_id=vv,method=v.method,A0_w0=(int(b.new_w0_poses.iloc[0]) if len(b) else None),A1_w0=int(v.new_w0_poses),A0_accept=(int(b.new_accept.iloc[0]) if len(b) and pd.notna(b.new_accept.iloc[0]) else None),A1_accept=int(v.new_accept),
  A0_ring=(float(b.new_ring_mae.iloc[0]) if len(b) and pd.notna(b.new_ring_mae.iloc[0]) else None),A1_ring=float(v.new_ring_mae),A0_held=(float(b.new_held_median.iloc[0]) if len(b) and pd.notna(b.new_held_median.iloc[0]) else None),A1_held=float(v.new_held_median),
  A0_p95=(float(b.new_held_p95.iloc[0]) if len(b) and pd.notna(b.new_held_p95.iloc[0]) else None),A1_p95=float(v.new_held_p95),clean_frames=int(v.mask_clean_frames),partial=v.partial_or_full_recovery))
compdf=pd.DataFrame(comp); compdf.to_csv(A/'RING_OBSERVATION_COMPARISON.csv',index=False)
# group/video coverage tables from B
role=pd.read_csv(B/'CAMERA_ROLE_ADMISSION.csv'); targets=pd.read_csv(B/'HERO_TARGET_SELECTION.csv'); supports=pd.read_csv(B/'HERO_SUPPORT_SELECTION.csv')
grp=role.groupby(['group_id','video_id']).agg(n_cameras=('view','size'),S0=('s0_eligible','sum'),S1=('s1_eligible','sum'),S2=('s2_eligible','sum')).reset_index()
grp.to_csv(AN/'VIDEO_LEVEL_COMPARISON.csv',index=False)
g2=grp.groupby('group_id').agg(n_videos=('video_id','size'),S0=('S0','sum'),S1=('S1','sum'),S2=('S2','sum')).reset_index(); g2.to_csv(AN/'GROUP_LEVEL_COMPARISON.csv',index=False)
cov=pd.DataFrame([dict(arm=a,total_groups=39,total_videos=79,eligible_cameras=int(role[f'{a.lower()}_eligible'].sum()),videos_with_any=int(grp[grp[a]>0].shape[0]),targets_ready=int((targets[targets.arm==a].status=='ELIGIBLE').sum()),supports_ready=int((supports[supports.arm==a].status=='READY').sum())) for a in ['S0','S1','S2']]); cov.to_csv(AN/'COVERAGE_COMPARISON.csv',index=False)
# paired differences, only cameras where both arms eligible (eligibility is deterministic)
pd.DataFrame([dict(group_id=g,video_id=v,arm_pair='S1-S0',S0=int(r.S0),S1=int(r.S1),delta=int(r.S1-r.S0)) for _,r in grp.iterrows()]).to_csv(AN/'PAIRED_COMPARISON.csv',index=False)
# newly recovered / regressions vs A0
new=compdf[(compdf.A0_w0==0)&(compdf.A1_w0>0)]; new.to_csv(AN/'NEWLY_RECOVERED_CASES.csv',index=False)
reg=compdf[(compdf.A1_w0<compdf.A0_w0)|((compdf.A1_accept<compdf.A0_accept))]; reg.to_csv(AN/'REGRESSION_CASES.csv',index=False)
# failure registry
fail=[]
for _,v in D.iterrows():
 if v.new_w0_poses==0: fail.append(dict(group_id=v.group_id,video_id=v.video_id,stage='W0',reason='NO_W0'))
 if v.partial_or_full_recovery=='PARTIAL': fail.append(dict(group_id=v.group_id,video_id=v.video_id,stage='W0',reason='PARTIAL_W0'))
 if v.new_accept==0: fail.append(dict(group_id=v.group_id,video_id=v.video_id,stage='admission',reason='NO_ACCEPT'))
pd.DataFrame(fail).to_csv(AN/'FAILURE_REGISTRY.csv',index=False)
# representative auto selection: extreme of each trajectory class and low/high evidence
sel=[]
for cls in sorted(set(pd.DataFrame(tr).diagnostic_class)):
 sub=pd.DataFrame(tr)[pd.DataFrame(tr).diagnostic_class==cls].sort_values('max_adj_rotation_deg',ascending=False).head(1)
 for _,r in sub.iterrows(): sel.append(dict(category=cls,group_id=r.group_id,video_id=r.video_id,value=r.max_adj_rotation_deg,rule='max_adj_rotation_within_class'))
sel=pd.DataFrame(sel); sel.to_csv(AN/'REPRESENTATIVE_CASE_SELECTION.csv',index=False)
print(pd.DataFrame(tr).diagnostic_class.value_counts().to_dict()); print(cov.to_string(index=False)); print('new',len(new),'reg',len(reg))
