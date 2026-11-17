"""Wait for the one existing GPU worker; then finish prerequisite selection and Phase B."""
from common import *
from phase_a import command
import subprocess

def main():
 assert not(R/'provenance/ALL_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json').exists()
 while not(R/'provenance/PHASE_A_PREDICTIONS_FROZEN.json').exists():
  pid=load(R/'runtime/SERVICE_PID.json')['pid']
  try:os.kill(pid,0)
  except ProcessLookupError:raise RuntimeError('Phase A stopped before freeze; inspect logs, no automatic bypass')
  time.sleep(20)
 if not(R/'provenance/PHASE_A_SELECTION_FREEZE.json').exists():command('select_phase_a.py',[])
 command('phase_b.py',[])
 print('PHASE_A_AND_B_PREDICTIONS_COMPLETE',flush=True)
if __name__=='__main__':main()
