"""Reproduce the pre-optimization freeze in a fresh isolated copy only."""
from prepare016 import *
def main():
 assert not(R/'provenance/FORMAL_FREEZE.json').exists(),'Never rewrite frozen run'
 proof=load(R/'arms/DIAGNOSTIC/metrics/G03_SHADOW_UPDATES.json');assert any(x['direction']=='FULL'and x['mode']=='CONTACT_FACE_FIXED'and not x['geometry_reasons']and x['full_objective_change']<0 for x in proof)
 sel=load(R/'config/VIEW_SELECTION_016.json');rows=[]
 for n in ['G03','G01']:
  root=arm('MECH_COHERENT',n,sel[n]['OLD'],OLD15/'arms/Init-A/local_results'/n/'FINAL.npz','COHERENT','mechanism');rows.extend([dict(case=n,tag='MECH_COHERENT',kind='NEW_ROUTE',scene='real',script='train016.py',final=str(root/'local_results'/n/'FINAL.npz'),comparator='MECH_015_B'),dict(case=n,tag='MECH_015_B',kind='READ_ONLY_015_BASELINE',scene='real',final=str(OLD15/'arms/Stalk-B/local_results'/n/'FINAL.npz'),metrics=str(OLD15/'arms/Stalk-B/metrics'/(n+'_RUN.json')))])
 for n in sel:rows.extend([dict(case=n,tag='S0_015',kind='READ_ONLY_015_BASELINE',scene='real',final=str(OLD15/'arms/Init-A/local_results'/n/'FINAL.npz'),metrics=str(OLD15/'arms/Init-A/metrics'/(n+'_RUN.json'))),dict(case=n,tag='S1_BALANCED',kind='NEW_ROUTE',scene='real',script='train_mesh.py',final=str(R/'arms/S1_BALANCED/local_results'/n/'FINAL.npz'),comparator='S0_015')])
 save('config/RUN_REGISTRY.json',rows);files=[asset(p)for d in ['code','config']for p in(R/d).glob('*')if p.is_file()]+[asset(p)for p in R.glob('*.md')];save('provenance/FORMAL_FREEZE.json',dict(epoch=time.time(),files=files,new_real_runs=13,reused_baselines=13,GT_real_geometry_read=False,decision_evidence=asset(R/'arms/DIAGNOSTIC/metrics/G03_SHADOW_UPDATES.json')));print('FRESH_RUN_FROZEN',flush=True)
if __name__=='__main__':main()
