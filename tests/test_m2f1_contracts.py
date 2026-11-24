import json,pathlib,pandas as pd
O=pathlib.Path('/home/liu/ring_first_3d_workspace/runs/m2f1_w0_admission_restoration')
def test_new_hero():
 h=pd.read_csv(O/'hero/HERO_EXECUTION_RESULTS.csv');assert len(h)==294;assert set(h.arm)=={'S0','S1','S2'};assert h.group_id.nunique()==33
def test_a2b_b_camera():
 a=pd.read_csv(O/'evaluation/A_TO_B_METRICS.csv');assert len(a)==882;assert a.target_B_camera_used.all();assert a.target_B_id.ne(a.target_id).all()
def test_gate():
 t=pd.read_csv(O/'selection/FINAL_HERO_TUPLES.csv');assert t[t.ready].shape[0]==294;assert (t[t.ready].n_support==3).all();assert not (t[t.ready].target_id==t[t.ready].support_ids).any()
def test_honest_status():
 f=pd.read_csv(O/'w0/TRACK_IDENTITY_VALIDATION.csv');assert int((~f.valid).sum())==2
 v=json.loads((O/'VALIDATION_39.json').read_text());assert v['W0_TRACK_IDENTITY_VERIFIED'] is False;assert v['ALL_39_GROUPS_ATTEMPTED'] is False
