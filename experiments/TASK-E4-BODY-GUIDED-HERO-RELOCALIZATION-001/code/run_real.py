from resection import *

def main():
 assert load(R/'controls/PROJECTION_GATE.json')
 assert (R/'controls/EVALUATION_COMPLETED.json').exists()
 guard_optimizer()
 code=[asset(R/'code'/n)for n in ['resection.py','geometry.py','features.py','run_real.py']]
 freeze=dict(epoch=time.time(),code=code,protocol=asset(R/'config/PROTOCOL.json'),sources=asset(R/'config/REAL_SOURCES.json'),bodies=asset(R/'provenance/BODIES_FROZEN.json'),controls='scientific failures retained; no GT-driven tuning')
 f=R/'provenance/REAL_SOLVER_CODE_FREEZE.json'
 if f.exists():assert load(f)['code']==code,'Resume code mismatch'
 else:save(str(f.relative_to(R)),freeze)
 rows=[]
 for g in ['G03','G05','G01','G06']:
  for rec in [s for s in load(R/'config/REAL_SOURCES.json')if s['group']==g]:
   for b in ['Body-E','Body-U']:
    folder=R/'local_results'/g/b/rec['id'];done=folder/'CANDIDATES_FROZEN.json'
    if not done.exists():
     try:
      a=np.load(R/'local_results'/g/(b+'.npz'));run_source(rec,b,a['V'],a['F'],folder=folder)
     except Exception as e:
      import traceback
      save(str(done.relative_to(R)),dict(source=rec['id'],group=g,Body=b,status='ENGINEERING_FAILURE',chosen=None,error=repr(e),traceback=traceback.format_exc()));print('FAILED',g,b,rec['id'],repr(e),flush=True)
    rows.append(dict(group=g,source=rec['id'],Body=b,result=asset(done)))
 save('provenance/ALL_REAL_PREDICTIONS_FROZEN.json',dict(epoch=time.time(),results=rows,selection='FIT only',real_GT_access=False,all_bodies_fixed=True));print('REAL_ALL_FROZEN',len(rows),flush=True)
if __name__=='__main__':main()
