"""Resumable M4-only entry: all inventory items get outcomes, errors retain evidence."""
from context import *
import argparse,traceback,subprocess
def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['all','audit','register','clean','review','deliver','verify'],default='all');p.add_argument('--group');p.add_argument('--resume',action='store_true');a=p.parse_args();stamp=str(time.time_ns());failures=[]
 save(T/'evidence'/('INVOCATION_'+stamp+'.json'),dict(args=vars(a),git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),sources=[dict(path=str(f),sha256=sha(f))for f in (T/'code').glob('*.py')],resource=resource()))
 if a.stage in ['all','audit']:
  if not a.resume or not(T/'config/INVENTORY.json').exists():
   from audit import main as audit;audit()
  else:verify(read(T/'evidence/UPSTREAM_TERMINAL.json')['files'])
 if a.stage=='audit':return
 inventory=read(T/'config/INVENTORY.json')
 if a.group:assert a.group in {r['group']for r in inventory['groups']},'GROUP_NOT_IN_R1_MANIFEST'
 for row in inventory['groups']:
  g=row['group']
  if a.group and a.group!=g:continue
  for stage in ['register','clean','review']:
   if a.stage not in ['all',stage]:continue
   try:
    if stage=='register':
     from run import predict,evaluate_edges;predict(g);evaluate_edges(g)
    elif stage=='clean':
     from outputs import outputs;outputs(g)
    else:
     from review import review;review(g)
   except Exception as e:
    rec=dict(group=g,stage=stage,error=repr(e),traceback=traceback.format_exc());failures.append(rec);save(group_out(g)/('ERROR_'+stage+'_'+stamp+'.json'),rec);print('STAGE ERROR',g,stage,repr(e),flush=True);break
 if a.stage in ['all','deliver']:
  from deliver import main as deliver;deliver()
 if a.stage in ['all','verify']and not a.group:
  from verify_final import main as verify_final;verify_final()
 if failures:raise SystemExit('Stages failed; retained receipts, rerun same command with --resume')
if __name__=='__main__':main()
