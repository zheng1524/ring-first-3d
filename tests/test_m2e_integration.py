import json,pathlib,pandas as pd
O=pathlib.Path('/home/liu/ring_first_3d_workspace/runs/m2e_historical_method_integration')
def test_inventory():
 h=pd.read_csv(O/'hero/HERO_EXECUTION_RESULTS.csv');assert len(h)==217;assert set(h.status)=={'PASS'};assert h.group_id.nunique()==39
 s=pd.read_csv(O/'support/SUPPORT_SELECTION_RESULTS.csv');r=s[s.status=='READY'];assert len(r)==217
 for _,x in r.iterrows():
  ids=str(x.support_ids).split(';');assert len(ids)==3 and x.target_id not in ids
 a=pd.read_csv(O/'a_to_b/A_TO_B_METRICS.csv');assert len(a)==311;assert set(a.target_id)<=set(h.target_id);assert (a.target_coverage>=0).all() and (a.target_coverage<=1).all()
 assert len(list((O/'visualization/six_view').glob('*.png')))==8
 assert json.loads((O/'VALIDATION_39.json').read_text())['ALL_39_GROUPS_ATTEMPTED'] is True
