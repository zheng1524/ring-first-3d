"""Actually rerun the unchanged prior B1 workflow into an isolated child root."""
from common import *
import shutil,subprocess

def main():
 out=R/'local_results/A1_LEGACY_REPLAY';out.mkdir(exist_ok=True)
 for d in ['inputs','config','metrics','runtime','local_results']:(out/d).mkdir(exist_ok=True)
 for name in ['PROTOCOL.json','SOURCES.json']:shutil.copy2(P/'config'/name,out/'config'/name)
 for name in ['SYNTHETIC_TESTS.json','BASELINE_REPRODUCTION.json']:shutil.copy2(P/'metrics'/name,out/'metrics'/name)
 for g in ['G03','G05','G01','G06']:
  if not(out/'inputs'/g).exists():(out/'inputs'/g).symlink_to(P/'inputs'/g,target_is_directory=True)
  log=R/'logs'/('A1_REPLAY_'+g+'.log');env=dict(os.environ,E4_RUN_DIR=str(out));
  if not(out/'runs'/g/'B1/FINAL.npz').exists():
   with log.open('w')as f:r=subprocess.run([sys.executable,'-B',str(P/'code/run_multi.py'),g,'B1'],env=env,stdout=f,stderr=subprocess.STDOUT)
   if r.returncode:raise RuntimeError('A1 replay failed '+g)
  got=np.load(out/'runs'/g/'B1/FINAL.npz');old=np.load(P/'runs'/g/'B1/FINAL.npz');save('metrics/'+g+'_A1_REPLAY.json',dict(parameters_max_difference=float(abs(got['theta']-old['theta']).max()),Body_unchanged=bool(np.array_equal(got['V'],old['V'])),source_ids_equal=bool(np.array_equal(got['source_ids'],old['source_ids'])),new_output=asset(out/'runs'/g/'B1/FINAL.npz'),historical=asset(P/'runs'/g/'B1/FINAL.npz'),code=asset(P/'code/run_multi.py'),actual_rerun=True));print('A1_REPLAY_DONE',g,flush=True)
if __name__=='__main__':main()
