from common import *
from phase_a import command

def main():
 while not(R/'provenance/PHASE_B_PREDICTIONS_FROZEN.json').exists():
  pid=load(R/'runtime/CONTINUATION_PID.json')['pid'];state=Path('/proc')/str(pid)/'stat'
  if not state.exists()or state.read_text().split()[2]=='Z':raise RuntimeError('Phase B prerequisite stopped; do not bypass or open GT')
  time.sleep(20)
 command('postprocess_all.py',[])
if __name__=='__main__':main()
