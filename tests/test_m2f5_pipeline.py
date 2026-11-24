import json,pathlib
import numpy as np,pandas as pd
from tools.m2f5_unified import sample_frames, RAW

def test_raw_sampling_has_16_real_unique_frames():
 p=sorted(RAW.glob('GP_Ip_12.0mm_closed_R10_single_refY_004.mp4'))[0]
 f=sample_frames(p)
 assert len(f)==16 and len(set(f))==16
 assert min(f)>=20 and max(f)>min(f)

def test_track_copy_is_removed():
 s=pathlib.Path('tools/run_w0_camera.py').read_text()
 assert 'if tr.exists()' not in s
 assert 'generated_by_pipeline_current_frames' in s
 for p in pathlib.Path('runs/m2f5_unified/work').glob('*/tracks_source.txt'):
  assert p.read_text().strip()=='generated_by_pipeline_current_frames'

def test_prepared_inputs_are_raw_not_historical():
 for p in pathlib.Path('runs/m2f5_unified/prepared').glob('*/PREPARED.json'):
  m=json.loads(p.read_text()); assert '/raw/' in m['video_path']; assert 'm1_final_39' not in m['video_path']

def test_hero_and_a2b_identity():
 h=pd.read_csv('runs/m2f5_unified/hero/HERO_EXECUTION_RESULTS.csv');a=pd.read_csv('runs/m2f5_unified/evaluation/A_TO_B_METRICS.csv')
 assert len(h)==174 and h.status.eq('PASS').all();assert h.groupby(['group_id','video_id','target_id','support_ids']).ngroups==174
 assert a.target_B_camera_used.all();assert len(a)==522
 for x in h.itertuples(): assert len(str(x.support_ids).split(';'))==3 and x.target_id not in str(x.support_ids).split(';')

def test_mask_clean_actual():
 rows=pd.concat([pd.read_csv(p) for p in pathlib.Path('runs/m2f5_unified/w0').glob('MASK_CLEAN_GP_*.csv')])
 assert len(rows)==432;assert rows.clean_sha.str.len().eq(64).all()
