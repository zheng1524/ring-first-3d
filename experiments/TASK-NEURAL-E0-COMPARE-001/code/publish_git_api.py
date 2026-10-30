"""Exact local Git-object upload after Git smart-HTTP408; no force update."""
from pathlib import Path
import base64,concurrent.futures,datetime,hashlib,json,os,re,subprocess,sys,tempfile,threading,time,traceback
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];REMOTE='zheng1524/ring-first-3d';REF='heads/exp/TASK-NEURAL-E0-COMPARE-001'
source=sys.argv[1];start=time.monotonic();lock=threading.Lock()
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args])
source=git('rev-parse',source).decode().strip();parent=git('rev-parse',source+'^').decode().strip();tree=git('rev-parse',source+'^{tree}').decode().strip();parenttree=git('rev-parse',parent+'^{tree}').decode().strip()
record=(R/'runtime/GIT_API_CLOSING_RECEIPT.json')if'--closing'in sys.argv else R/'provenance'/('GIT_API_TRANSFER_'+source[:8]+'.json');data=dict(local_commit=source,parent=parent,expected_tree=tree,status='STARTED',force=False,uploaded_blobs=[],transport='gh api local authorized account; Git smart HTTP failed408; connector mutation403')
cached={}
if record.exists():
    previous=json.loads(record.read_text())
    assert previous['local_commit']==source
    for item in previous.get('uploaded_blobs',[]):cached[item['path']]=item
    data['uploaded_blobs']=list(cached.values())
    data['resume_verified_blob_N']=len(cached)
def save():record.write_text(json.dumps(data,indent=2)+'\n')
def api(path,payload=None,method=None):
    last=None
    for attempt in range(2):
        if time.monotonic()-start>600:raise TimeoutError('API transfer600s cap')
        cmd=['gh','api',path]
        tmp=None
        if payload is not None:
            f=tempfile.NamedTemporaryFile(mode='w',dir='/dev/shm',prefix='e0_api_',suffix='.json',delete=False);json.dump(payload,f);f.close();tmp=f.name;cmd+=['--method',method or'POST','--input',tmp]
        try:
            p=subprocess.run(cmd,text=True,capture_output=True,timeout=90)
            if p.returncode==0:return json.loads(p.stdout)
            last=p.stderr
            if '403'in last or '401'in last:break
        finally:
            if tmp:Path(tmp).unlink(missing_ok=True)
        time.sleep(1)
    raise RuntimeError('GitHub API operation failed: '+path+' '+str(last)[:1000])
def ident(s):
    match=re.fullmatch(r'(.*) <([^>]+)> (\d+) ([+-]\d{4})',s);name,email,ts,offset=match.groups();sign=1 if offset[0]=='+'else-1;zone=datetime.timezone(sign*datetime.timedelta(hours=int(offset[1:3]),minutes=int(offset[3:])));return dict(name=name,email=email,date=datetime.datetime.fromtimestamp(int(ts),zone).isoformat())
def raw_ident(d):
    t=datetime.datetime.fromisoformat(d['date'].replace('Z','+00:00'));offset=t.strftime('%z');return f"{d['name']} <{d['email']}> {int(t.timestamp())} {offset}"
try:
    current=api('repos/'+REMOTE+'/git/ref/'+REF)['object']['sha'];assert current==parent,('remote moved; refuse overwrite',current,parent)
    paths=git('diff','--name-only',parent,source).decode().splitlines();assert paths and all(p.startswith(('experiments/TASK-NEURAL-E0-COMPARE-001/','research/phase_e_neural/'))for p in paths)
    assert not any('/runtime/'in p or '/local_results/'in p for p in paths)
    def upload(path):
        line=git('ls-tree',source,'--',path).decode().strip()
        if not line:return dict(path=path,mode='100644',type='blob',sha=None)
        mode,kind,obj= line.split('\t')[0].split();assert kind=='blob'
        content=git('cat-file','blob',obj);assert len(content)<3*1024**2
        if path in cached and cached[path]['sha']==obj:return dict(path=path,mode=mode,type='blob',sha=obj)
        r=api('repos/'+REMOTE+'/git/blobs',dict(content=base64.b64encode(content).decode(),encoding='base64'));assert r['sha']==obj,(path,r['sha'],obj)
        with lock:
            data['uploaded_blobs'].append(dict(path=path,sha=obj,bytes=len(content)));save()
            if len(data['uploaded_blobs'])%10==0:print('API blobs',len(data['uploaded_blobs']),'/',len(paths),flush=True)
        return dict(path=path,mode=mode,type='blob',sha=obj)
    save()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:entries=list(pool.map(upload,paths))
    createdtree=api('repos/'+REMOTE+'/git/trees',dict(base_tree=parenttree,tree=entries));assert createdtree['sha']==tree,('tree mismatch',createdtree['sha'],tree)
    raw=git('cat-file','commit',source).decode();headers,message=raw.split('\n\n',1);hh=dict(line.split(' ',1)for line in headers.splitlines()if line.startswith(('author ','committer ')))
    payload=dict(message=message,tree=tree,parents=[parent],author=ident(hh['author']),committer=ident(hh['committer']))
    c=api('repos/'+REMOTE+'/git/commits',payload);newsha=c['sha'];assert c['tree']['sha']==tree
    if newsha!=source:
        # GitHub may canonicalize timezone formatting. Preserve exact content and
        # import that returned commit; do not fabricate equivalence of commit IDs.
        rawnew='tree '+tree+'\n'+''.join('parent '+p['sha']+'\n'for p in c['parents'])+'author '+raw_ident(payload['author'])+'\ncommitter '+raw_ident(payload['committer'])+'\n\n'+c['message']
        q=subprocess.run(['git','-C',str(REPO),'hash-object','-t','commit','-w','--stdin'],input=rawnew,text=True,capture_output=True,check=True);assert q.stdout.strip()==newsha,('cannot reconstruct returned commit',q.stdout,newsha)
    current=api('repos/'+REMOTE+'/git/ref/'+REF)['object']['sha'];assert current==parent,('concurrent remote move',current,parent)
    api('repos/'+REMOTE+'/git/refs/'+REF,dict(sha=newsha,force=False),method='PATCH')
    actual=api('repos/'+REMOTE+'/git/ref/'+REF)['object']['sha'];assert actual==newsha
    data.update(status='REMOTE_VERIFIED',remote_commit=newsha,tree_identical=True,local_commit_identity_matches=newsha==source,seconds=time.monotonic()-start)
    save();print('API_REMOTE_VERIFIED',source,newsha,flush=True)
except Exception:
    data.update(status='LOCAL_ONLY_FAILED',error=traceback.format_exc(),seconds=time.monotonic()-start);save();print(data['error'],flush=True);sys.exit(1)
