"""Authenticated GitHub Git-data fallback when receive-pack transport fails.
Uploads only this task's committed changes; no force updates or credential output.
"""
import subprocess,json,base64,datetime,re,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];REPO='zheng1524/ring-first-3d';TASK='experiments/TASK-M2F13-CLEANUP-HERO-VISUALIZATION-MAINLINE-DESIGN-001/'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def api(path,payload=None,method=None):
 cmd=['gh','api','repos/'+REPO+'/'+path]
 if method:cmd+=['--method',method]
 if payload is not None:cmd+=['--input','-']
 p=subprocess.run(cmd,input=json.dumps(payload).encode()if payload is not None else None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
 if p.returncode:raise RuntimeError(p.stderr.decode())
 return json.loads(p.stdout)
def person(line):
 m=re.fullmatch(r'(.+) <(.+)> (\d+) ([+-]\d{4})',line);name,email,seconds,zone=m.groups();sign=1 if zone[0]=='+'else-1;offset=sign*(int(zone[1:3])*60+int(zone[3:]));tz=datetime.timezone(datetime.timedelta(minutes=offset));date=datetime.datetime.fromtimestamp(int(seconds),tz).isoformat()
 return dict(name=name,email=email,date=date)
branch=git('branch','--show-current').decode().strip();assert branch.startswith('exp/TASK-M2F13-')
remote=api('git/ref/heads/'+branch)['object']['sha'];head=git('rev-parse','HEAD').decode().strip();commits=git('rev-list','--reverse',remote+'..'+head).decode().splitlines();receipts=[]
for commit in commits:
 raw=git('cat-file','-p',commit).decode();header,message=raw.split('\n\n',1);fields=dict(x.split(' ',1)for x in header.splitlines());parent=fields['parent'];assert parent==remote,'Only linear task commits allowed'
 def upload(line):
  status,path=line.split('\t');assert path.startswith(TASK),path
  if status=='D':return dict(path=path,mode='100644',type='blob',sha=None)
  assert status in ['A','M'],status
  data=git('show',commit+':'+path);blob=api('git/blobs',dict(content=base64.b64encode(data).decode(),encoding='base64'));expected=git('rev-parse',commit+':'+path).decode().strip();assert blob['sha']==expected
  mode=git('ls-tree',commit,'--',path).decode().split()[0];return dict(path=path,mode=mode,type='blob',sha=blob['sha'])
 lines=git('diff-tree','--no-commit-id','--name-status','-r',parent,commit).decode().splitlines()
 with ThreadPoolExecutor(max_workers=6)as pool:elements=list(pool.map(upload,lines))
 tree=api('git/trees',dict(base_tree=git('rev-parse',parent+'^{tree}').decode().strip(),tree=elements));assert tree['sha']==fields['tree']
 obj=api('git/commits',dict(message=message,tree=tree['sha'],parents=[parent],author=person(fields['author']),committer=person(fields['committer'])))
 receipt=dict(local_commit=commit,remote_object_commit=obj['sha'],tree=tree['sha'],files=len(elements));receipts.append(receipt);print(receipt,flush=True)
 if obj['sha']!=commit:raise RuntimeError('Commit object SHA mismatch; branch not changed')
 current=api('git/ref/heads/'+branch)['object']['sha'];assert current==remote,'Concurrent branch update; no overwrite'
 api('git/refs/heads/'+branch,dict(sha=commit,force=False),method='PATCH');remote=api('git/ref/heads/'+branch)['object']['sha'];assert remote==commit
out=Path('/home/liu/ring_first_3d_workspace/runs/m2f13_hero_all/PUBLISH_RECEIPT.json');out.write_text(json.dumps(dict(branch=branch,head=head,remote_verified=remote,commits=receipts),indent=2));print('VERIFIED_REMOTE',remote,flush=True)
