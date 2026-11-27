"""Strengthened dependency receipt and deterministic prediction replay; no tuning."""
from context import *
from solver2 import solve_methods
from registration import pack_pairs,solve_m5

def main():
 for row in read(T/'config/SELECTION.json')['groups']:
  out=RUN/'real'/row['group'];freeze('DEPENDENCY_REPLAY',out,[out/'PREDICTION_FREEZE.json']);pred=read(out/'PREDICTIONS.json');assert sha(out/'PREDICTIONS.json')==read(out/'PREDICTION_FREEZE.json')['predictions_sha256'];a=np.load(out/'LANDMARKS.npz');ring=read(out/'RING_PRIOR.json');fit=a['fit'];results=solve_methods(a['xyz'][fit,0],a['xyz'][fit,1],ring,methods=['M4']);p=pack_pairs(read(out/'FRAMES.json'),np.load(out/'CAMERAS.npz')['c2w'],np.load(out/'tracks/observations/tracks005.npz'),~a['held']);results['M5']=solve_m5(p,ring,results['M4']['T'])
  for name,r in results.items():np.testing.assert_allclose(r['T'],pred[name]['T'],atol=1e-12,rtol=0)
  save(out/'DEPENDENCY_REPLAY.json',dict(prediction_values_identical=True,results=results,initial_freeze_limitation='initial receipt omitted inherited config/V001 kernel; this full-dependency replay reproduces same T; no prior prediction overwritten'));print('REPLAY IDENTICAL',row['group'],results['M5']['degenerate_pairs'],flush=True)
if __name__=='__main__':main()
