"""Two bounded CPU workers; unchanged single-group pipeline and isolated group receipts."""
import os,sys,subprocess,concurrent.futures,time
from core import *
def one(group,slot):
 log=T/'runtime'/('batch_'+group+'.log')
 with log.open('a')as f:
  result=subprocess.run(['taskset','-c',str(slot),'bash',str(T/'run_python.sh'),str(T/'code/batch_group.py'),group],cwd=T,stdout=f,stderr=subprocess.STDOUT)
 return dict(group=group,returncode=result.returncode,log=str(log))
def main():
 groups=[r['group']for r in read(M4/'GROUP_INDEX.json')['groups']];cpus=sorted(os.sched_getaffinity(0))[:2]
 save(T/'evidence/BATCH_EXECUTION.json',dict(scientific_code_key=code_key(),config_sha256=sha(T/'config.json'),cpus=cpus,workers=len(cpus),same_pipeline=True,reason='No active upstream inference observed; each worker uses one CPU, nice19/idle I/O. No method or data-budget change.',epoch=time.time()))
 def shard(slot):
  rows=[]
  for g in groups[slot::len(cpus)]:
   r=one(g,cpus[slot]);rows.append(r);print('BATCH',g,r['returncode'],flush=True)
  return rows
 with concurrent.futures.ThreadPoolExecutor(max_workers=len(cpus))as pool:rows=sum(list(pool.map(shard,range(len(cpus)))),[])
 save(T/'evidence/BATCH_RECEIPTS.json',rows);results=[read(T/'runs/results'/g/'GROUP_RESULT.json')for g in groups if(T/'runs/results'/g/'GROUP_RESULT.json').exists()];save(T/'evidence/FULL_STATUS.json',results)
if __name__=='__main__':main()
