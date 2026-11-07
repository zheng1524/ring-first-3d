"""Three independent CPU-only case workers; same frozen evaluator for every stage."""
from common import *
import subprocess,concurrent.futures
PYTHON='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python'
def worker(n):
 with(R/'runtime'/('BEST_SE3_'+n+'.log')).open('w')as f:subprocess.run([PYTHON,'-B',str(R/'code/best_rigid.py'),'--case',n],stdout=f,stderr=subprocess.STDOUT,check=True)
 print('CASE_BEST_RIGID_COMPLETE',n,flush=True)
def main():
 assert(R/'assets_index/SCALE_LOCK_BEFORE_GT.json').exists();cases=[c['name']for c in load(R/'config/CASE_LOCK.json')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(worker,cases))
 metrics=[];Ts=[]
 for n in cases:metrics+=load(R/'metrics/eval_case'/(n+'_BLENDER_GEOMETRIC_METRICS.json'));Ts+=load(R/'metrics/eval_case'/(n+'_BLENDER_RIGID_ALIGNMENT.json'))
 assert len(metrics)==3*len(cases);save('metrics/BLENDER_GEOMETRIC_METRICS.json',metrics);table('metrics/BLENDER_GEOMETRIC_METRICS.csv',metrics);save('metrics/BLENDER_RIGID_ALIGNMENT.json',Ts);table('metrics/BLENDER_RIGID_ALIGNMENT.csv',Ts)
if __name__=='__main__':main()
