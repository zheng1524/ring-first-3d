#!/usr/bin/env python3
"""Aggregate M2C A1 W0 and correctness diagnostics."""
import json,sys
from pathlib import Path
import numpy as np,pandas as pd
WS=Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2c_trajectory_admission'; A=OUT/'A_correctness'; PREP=WS/'runs/m1_final_39/prepared'
sys.path.insert(0,str(WS/'tools')); from m2a_c3 import pair_graph
BASE=pd.read_csv(WS/'runs/m2b_ring_global_branch/W0_79_VIDEO_RESULTS.csv')
ST=pd.read_csv(A/'A1_RUN_STATUS.csv'); REC=pd.read_csv(A/'A1_RECOVERY_RESULTS.csv')
CLEAN=pd.read_csv(OUT/'MASK_CLEAN_PER_FRAME.csv')
rows=[]; pos=[]
for _,b in BASE.iterrows():
 g,v=str(b.group_id),f'{int(b.video_id):03d}'
 st=ST[(ST.group_id==g)&(ST.video_id.astype(str).str.zfill(3)==v)]; status=st.status.iloc[0] if len(st) else 'NOT_RUN'
 recs=REC[(REC.group_id==g)&(REC.video_id.astype(str).str.zfill(3)==v)]
 rec=recs[recs.execution_status.isin(['COMPLETED_VALID','COMPLETED_LIMITED'])].iloc[-1] if len(recs) and recs.execution_status.isin(['COMPLETED_VALID','COMPLETED_LIMITED']).any() else None
 if status.startswith('COMPLETED'):
  p=OUT/'A_correctness/w0_A1'/g/v; method='A1'; work=OUT/'A_correctness/work_A1'/g/v; prep=PREP/f'{g}_{v}'
 elif rec is not None:
  p=Path(rec.output_path); method=rec.method; work=OUT/'A_correctness/work_recovery'/method/g/v
  roots=[A/'prepared_c3',WS/'runs/m2a_w0_recovery/prepared_c2b',WS/'runs/m2a_w0_recovery/prepared_c2',WS/'runs/m2a_w0_recovery/prepared_b1r',WS/'runs/m2a_w0_recovery/prepared_c3',WS/'runs/m2b_ring_global_branch/prepared_c3b']
  prep=None
  for root in roots:
   q=root/f'{g}_{v}'/'PREPARED.json'
   if q.exists(): prep=q.parent; break
 else: raise RuntimeError((g,v,status))
 q=json.loads((p/'quality_summary.json').read_text()); meta=json.loads((prep/'PREPARED.json').read_text()); orig=json.loads((PREP/f'{g}_{v}'/'PREPARED.json').read_text())
 orig_ids={x['view'] for x in orig['views']}; new_ids={x['view'] for x in meta['views']}
 full=orig_ids<=new_ids and q['n_w0_poses']>=10
 try: tr,e,comps=pair_graph(work); ncomp=len(comps)
 except Exception: ncomp=None
 c=CLEAN[(CLEAN.group_id==g)&(CLEAN.video_id.astype(str).str.zfill(3)==v)]
 rows.append(dict(group_id=g,video_id=v,ring_type=b.ring_type,baseline_w0_poses=int(b.new_w0_poses),new_w0_poses=int(q['n_w0_poses']),
  original_frames=10,new_frames=len(new_ids),replacement_frames=len(meta.get('bridge_frames',[])),bridge_frames=len(meta.get('bridge_frames',[])),
  mask_clean_frames=int(c.clean_changed.sum()),mask_clean_pixels=int(c.changed_pixels.sum()),ring_valid_frames=q['n_evaluated_poses'],
  original_components=(int(b.new_components) if pd.notna(b.new_components) else None),new_components=ncomp,
  partial_or_full_recovery=('FULL' if full else 'PARTIAL' if q['n_w0_poses']>0 else 'NOT_COMPUTABLE'),
  baseline_accept=(b.new_accept if pd.notna(b.new_accept) else None),new_accept=q['n_accept'],new_quarantine=q['n_quarantine'],new_insufficient=q['n_insufficient_evidence'],new_reject=q['n_reject'],
  baseline_ring_mae=(b.new_ring_mae if pd.notna(b.new_ring_mae) else None),new_ring_mae=q['ring_mae_mean_px'],
  baseline_held_median=(b.new_held_median if pd.notna(b.new_held_median) else None),new_held_median=q['held_median_px'],
  baseline_held_p95=(b.new_held_p95 if pd.notna(b.new_held_p95) else None),new_held_p95=q['held_p95_px'],
  trajectory_jump_count=q.get('trajectory_jump_count'),max_adjacent_rotation_deg=q.get('max_adjacent_rotation_deg'),max_adjacent_translation_mm=q.get('max_adjacent_translation_mm'),
  ring_cad_radius_mm=q['ring_cad_mm'][0],ring_cad_wire_mm=q['ring_cad_mm'][1],clean_used=True,method=method,
  geometry_diagnostic_status=('AUTO_ACCEPTED' if q['n_accept']>0 else 'AUTO_LIMITED'),human_review_status='HUMAN_REVIEW_PENDING',
  output_path=str(p),w0_file=str(p/'W0.npz')))
 adm=pd.read_csv(p/'admission.csv')
 for _,r in adm.iterrows(): pos.append(dict(group_id=g,video_id=v,view=r.view,raw_frame=r.raw_frame,status=r.admission_status,ring_mae=r.ring_raw_mae,
   positive_depth=r.get('positive_depth'),positive_depth_training_fraction=r.get('positive_depth_training_fraction'),positive_depth_held_fraction=r.get('positive_depth_held_fraction'),
   positive_depth_source_fraction=r.get('positive_depth_source_fraction'),positive_depth_target_fraction=r.get('positive_depth_target_fraction'),positive_depth_sample_count=r.get('positive_depth_sample_count'),
   world_origin_positive_depth=r.get('world_origin_positive_depth'),reasons=r.admission_reasons))
df=pd.DataFrame(rows); df.to_csv(A/'W0_79_VIDEO_RESULTS.csv',index=False); pd.DataFrame(pos).to_csv(A/'POSITIVE_DEPTH_DIAGNOSTICS.csv',index=False)
gs=[]
for g,rr in df.groupby('group_id'):
 w0=int((rr.new_w0_poses>0).sum()); full=int((rr.partial_or_full_recovery=='FULL').sum()); part=int((rr.partial_or_full_recovery=='PARTIAL').sum()); acc=int(rr.new_accept.fillna(0).sum())
 gs.append(dict(group_id=g,ring_type=rr.ring_type.iloc[0],n_videos=len(rr),n_videos_w0=w0,n_full=full,n_partial=part,n_poses=int(rr.new_w0_poses.sum()),n_accept=acc,
  n_quarantine=int(rr.new_quarantine.fillna(0).sum()),n_insufficient=int(rr.new_insufficient.fillna(0).sum()),n_reject=int(rr.new_reject.fillna(0).sum()),
  clean_frames=int(rr.mask_clean_frames.sum()),status=('VALID' if acc>0 else 'LIMITED')))
gs=pd.DataFrame(gs); gs.to_csv(A/'W0_39_GROUP_SUMMARY.csv',index=False)
# CAD contract validation
rows=[]
for _,r in df.iterrows():
 ring=5.0 if r.ring_type=='R5' else 10.0; exp=ring/2+0.6
 rows.append(dict(group_id=r.group_id,video_id=r.video_id,ring_type=r.ring_type,ring_inner_mm=ring,expected_centerline_mm=exp,actual_centerline_mm=r.ring_cad_radius_mm,wire_mm=r.ring_cad_wire_mm,
  radius_ok=abs(r.ring_cad_radius_mm-exp)<1e-9,wire_ok=abs(r.ring_cad_wire_mm-.6)<1e-9,w0_file=r.w0_file))
cc=pd.DataFrame(rows); cc.to_csv(A/'CAD_CONTRACT_VALIDATION.csv',index=False)
summary=dict(groups=39,videos=len(df),w0_generated=int((df.new_w0_poses>0).sum()),full=int((df.partial_or_full_recovery=='FULL').sum()),partial=int((df.partial_or_full_recovery=='PARTIAL').sum()),
 not_computable=int((df.new_w0_poses==0).sum()),poses=int(df.new_w0_poses.sum()),accept=int(df.new_accept.fillna(0).sum()),quarantine=int(df.new_quarantine.fillna(0).sum()),
 insufficient=int(df.new_insufficient.fillna(0).sum()),reject=int(df.new_reject.fillna(0).sum()),cad_r5_ok=bool(cc[cc.ring_type=='R5'].radius_ok.all()),
 cad_r10_ok=bool(cc[cc.ring_type=='R10'].radius_ok.all()),cad_all_ok=bool(cc.radius_ok.all() and cc.wire_ok.all()),clean_frames=int(df.mask_clean_frames.sum()),clean_pixels=int(df.mask_clean_pixels.sum()),
 implementation_errors=int((ST.status=='IMPLEMENTATION_ERROR').sum()),positive_depth_pose_rows=len(pos))
(A/'CAD_CONTRACT_VALIDATION.json').write_text(json.dumps(summary,indent=1))
print(json.dumps(summary,indent=1)); print(gs.status.value_counts().to_dict())
