from resection import *

def main():
 guard_optimizer();cfg=load(R/'controls/CONTROL_PROTOCOL.json');save('provenance/CONTROL_SOLVER_CODE_FREEZE.json',dict(epoch=time.time(),code=[asset(R/'code'/n)for n in ['resection.py','geometry.py','features.py']],protocol=asset(R/'config/PROTOCOL.json'),control_protocol=asset(R/'controls/CONTROL_PROTOCOL.json'),real_GT_used=False));results=[]
 for rec in load(R/'controls/SOURCES.json'):
  matches=[]
  for v in rec['references']:
   a=np.load(v['fit_match'])
   if len(a['p']):matches.append(dict(reference=v['reference'],C=np.array(v['ref_C']),K=np.array(v['ref_K']),p=a['p'],q=a['q']))
  for b in ['Body-E','Body-U']:
   folder=R/'controls/results'/rec['id']/b;done=folder/'CANDIDATES_FROZEN.json'
   if done.exists():results.append(dict(case=rec['id'],Body=b,result=str(done)));continue
   a=np.load(R/'controls/inputs'/(b+'.npz'));run_source(rec,b,a['V'],a['F'],matches,folder);results.append(dict(case=rec['id'],Body=b,result=str(done)))
 save('controls/ALL_PREDICTIONS_FROZEN.json',dict(epoch=time.time(),results=results,GT_access_in_solver=False));print('CONTROLS_FROZEN',len(results),flush=True)
if __name__=='__main__':main()
