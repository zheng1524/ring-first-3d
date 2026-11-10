from common import *
import subprocess

def main():
 while not(R/'results/NEGATIVE_SEARCH_SELECTION.json').exists():time.sleep(3)
 log=R/'refine.log'
 with log.open('w')as f:run=subprocess.run([sys.executable,'-B',str(R/'code/refine019.py')],stdout=f,stderr=subprocess.STDOUT)
 print('REFINEMENT_EXIT',run.returncode,flush=True)
if __name__=='__main__':main()
