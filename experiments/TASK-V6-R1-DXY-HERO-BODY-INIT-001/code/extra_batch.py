"""Optional two additional idle-priority CPUs; reverse pending groups under the same locks."""
from batch import *
def main():
 allgroups=[r['group']for r in read(M4/'GROUP_INDEX.json')['groups']]
 # Only not-yet-started groups, selected without viewing model scores.
 groups=[g for g in reversed(allgroups)if not(T/'runtime'/('batch_'+g+'.log')).exists()];cpus=sorted(os.sched_getaffinity(0))[2:4]
 save(T/'evidence/EXTRA_BATCH_EXECUTION.json',dict(groups=groups,cpus=cpus,max_total_workers=4,epoch=time.time(),scientific_code_key=code_key(),reason='Measured available RAM 5.5 GiB and 16 CPUs; no upstream inference process. Per-group OS lock serializes any overlap. No changed scientific parameters.'))
 def shard(slot):
  result=[]
  for g in groups[slot::len(cpus)]:
   r=one(g,cpus[slot]);result.append(r);print('EXTRA',g,r['returncode'],flush=True)
  return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=len(cpus))as pool:rows=sum(list(pool.map(shard,range(len(cpus)))),[])
 save(T/'evidence/EXTRA_BATCH_RECEIPTS.json',rows)
if __name__=='__main__':main()
