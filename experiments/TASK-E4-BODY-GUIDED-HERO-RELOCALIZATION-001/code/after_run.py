from common import *
import subprocess
while not (R/'provenance/ALL_REAL_PREDICTIONS_FROZEN.json').exists():time.sleep(10)
for script in ['evaluate_real.py','visualize.py','finish_reports.py']:
 with (R/'logs'/(script+'.log')).open('w')as f:
  p=subprocess.run([sys.executable,'-B',str(R/'code'/script)],stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,E4_RUN_DIR=str(R)))
 if p.returncode:raise RuntimeError('FAILED '+script+' see task logs')
print('POSTPROCESSING_COMPLETE',flush=True)
