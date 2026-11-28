"""Two low-priority fitting workers; wait only for the exact selected 2D receipts."""
from pathlib import Path
import argparse,json,hashlib,subprocess,time,concurrent.futures,os
T=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 pa=argparse.ArgumentParser();pa.add_argument('--groups',nargs='*');pa.add_argument('--workers',type=int,default=2);args=pa.parse_args()
 q=read(T/'evidence/REGISTRATION_QUALIFICATION.json');index=read(T/'evidence/DXY_INPUT_INDEX.json');dxysha=sha(T/'code/dxy_full.py')
 selected={g['group']:[] for g in q['groups']}
 for row in index['rows']:
  if row['role'] in ['FIT','HOLDOUT']:
   key=hashlib.sha256(json.dumps([row,index['source'],dxysha],sort_keys=True).encode()).hexdigest();selected[row['group']].append((T/'runs/dxy'/row['case']/row['frame_id']/'FRAME.json',key))
 groups=args.groups or list(selected)
 if not args.groups:
  assert (T/'evidence/FULL_RUN_FREEZE.json').exists(),'SMOKE_REVIEW_AND_FREEZE_REQUIRED'
 def ready(g):
  for p,key in selected[g]:
   try:
    if read(p)['cache_key']!=key or not(p.parent/'COMPLETE.json').exists():return False
   except (FileNotFoundError,json.JSONDecodeError):return False
  return True
 def run(g):
  log=T/'runtime'/('fit_'+g+'.log');start=time.time()
  with log.open('w') as f:r=subprocess.run(['bash',str(T/'run_python.sh'),'code/pipeline_revision.py','--group',g],cwd=T,stdout=f,stderr=subprocess.STDOUT)
  return dict(group=g,returncode=r.returncode,seconds=time.time()-start,log=str(log),result=str(T/'runs/results'/g/'GROUP_RESULT.json'))
 pending=groups.copy();active={};done=[];last=0
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
  while pending or active:
   for g in pending.copy():
    if len(active)>=args.workers:break
    if ready(g):active[pool.submit(run,g)]=g;pending.remove(g);print('START',g,flush=True)
   for f in list(active):
    if f.done():
     g=active.pop(f);row=f.result();done.append(row);print('DONE',g,row['returncode'],round(row['seconds'],1),flush=True)
   if time.time()-last>60:print('WAIT',len(pending),'ACTIVE',len(active),'DONE',len(done),flush=True);last=time.time()
   if pending or active:time.sleep(3)
 out=T/'evidence'/('SMOKE_BATCH.json' if args.groups else 'FULL_BATCH.json');out.write_text(json.dumps(done,indent=2)+'\n')
if __name__=='__main__':main()
