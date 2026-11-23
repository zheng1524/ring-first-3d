#!/usr/bin/env python3
"""M2B R0/R1 Ring observation diagnostics."""
import json,sys
from pathlib import Path
import numpy as np,pandas as pd,cv2
WS=Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2b_ring_global_branch'; PREP=WS/'runs/m1_final_39/prepared'
sys.path.insert(0,str(WS/'src'))
from ring_first_3d.mainline.native.camera import observe
TARGETS=[('GP_IIa_14.0mm_closed_R5_single_refY','005'),('GP_IIa_22.0mm_closed_R5_single_refY','004'),
         ('GP_IIa_22.0mm_closed_R5_single_refY','005'),('GP_Is_18.0mm_closed_R5_single_refY','005')]

def angular_coverage(pts):
    if len(pts)==0: return 0
    c=pts.mean(0); a=np.arctan2(pts[:,1]-c[1],pts[:,0]-c[0]); return int(len(np.unique(np.floor((a+np.pi)/(2*np.pi)*16))))
rows=[]
for g,v in TARGETS:
 meta=json.loads((PREP/f'{g}_{v}'/'PREPARED.json').read_text())
 for q in meta['views']:
  a=np.load(q['cache']); labels=a['labels']
  o0=observe(labels,'legacy'); o1=observe(labels,'all')
  rows.append(dict(group_id=g,video_id=v,frame_id=q['view'],raw_frame=q['raw_frame'],ring_type='R5',
   ring_mask_pixels=int((labels==2).sum()),ring_boundary_all=int(len(o1['ring_boundary_all'])),
   ring_contact_polyp=int(o1['ring_boundary_contact_polyp_count']),ring_contact_background=int(o1['ring_boundary_contact_background_count']),
   q_train_original=int(len(o0['q_train'])),q_train_corrected=int(len(o1['q_train'])),
   q_train_original_raw=int(o0['q_train_original']),q_train_corrected_raw=int(o1['q_train_corrected']),
   angular_bins_original=angular_coverage(o0['q_train']),angular_bins_corrected=angular_coverage(o1['q_train']),
   status_original=('OK' if len(o0['q_train'])>=20 else 'INSUFFICIENT'),
   status_corrected=('OK' if len(o1['q_train'])>=20 else 'INSUFFICIENT')))
df=pd.DataFrame(rows); df.to_csv(OUT/'RING_OBSERVATION_PER_FRAME.csv',index=False)
s=df.groupby(['group_id','video_id']).agg(frames=('frame_id','size'),ok_original=('status_original',lambda x:int((x=='OK').sum())),
  ok_corrected=('status_corrected',lambda x:int((x=='OK').sum())),q_orig_mean=('q_train_original','mean'),
  q_corr_mean=('q_train_corrected','mean'),contact=('ring_contact_polyp','sum'),boundary=('ring_boundary_all','sum')).reset_index()
s.to_csv(OUT/'RING_OBSERVATION_BEFORE_AFTER.csv',index=False)
print(s.to_string(index=False)); print(df[['group_id','video_id','raw_frame','q_train_original','q_train_corrected','ring_contact_polyp']].head(12).to_string(index=False))
