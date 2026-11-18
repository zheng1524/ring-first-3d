import os,sys,json,csv,subprocess,pathlib,glob,hashlib,gzip,datetime,collections,time
OUT=pathlib.Path(__file__).resolve().parent
ENV=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0')
commands=[]
def run(root,args,timeout=180):
    t=time.time(); p=subprocess.run(['git','-C',str(root),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=ENV,timeout=timeout)
    out=p.stdout.decode(errors='replace'); err=p.stderr.decode(errors='replace'); commands.append(dict(root=str(root),args=args,rc=p.returncode,seconds=time.time()-t,stderr=err[:10000]))
    return out,p.returncode,err
def g(root,*args):return run(root,list(args))[0].strip()
def absolute(root,p):return str((pathlib.Path(root)/p).resolve())
def measure(path):
    inode={}; logical=0; files=0; symlinks=0
    if not pathlib.Path(path).exists():return dict(files=0,logical=0,allocated_unique_inode=0)
    for base,ds,fs in os.walk(path,followlinks=False):
        for f in fs:
            p=os.path.join(base,f)
            try:s=os.lstat(p)
            except OSError:continue
            files+=1;logical+=s.st_size
            if os.path.islink(p):symlinks+=1
            inode[(s.st_dev,s.st_ino)]=s.st_blocks*512
    return dict(files=files,logical=logical,allocated_unique_inode=sum(inode.values()),symlinks=symlinks)
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        while b:=f.read(4*1024*1024):h.update(b)
    return h.hexdigest()
roots=sorted(set(glob.glob('/home/liu/ring_first_3d*')+['/home/liu/polyp_research','/home/liu/polyp_research/ring-first-3d','/home/liu/polyp_research/ring_anchor_3d','/home/liu/ring-first-hero-core']))
rows=[]; clones={}
for root in roots:
    if not os.path.isdir(root):continue
    head,rc,err=run(root,['rev-parse','--show-toplevel'])
    if rc:continue
    top=head.strip()
    if top!=root:
        rows.append(dict(path=root,repository_root=top,nested_nonrepository_directory=True)); continue
    common=absolute(root,g(root,'rev-parse','--git-common-dir'))
    gd=absolute(root,g(root,'rev-parse','--git-dir'))
    obj=absolute(root,g(root,'rev-parse','--git-path','objects'))
    c=clones.setdefault(common,dict(owner=root,common_dir=common,objects=obj,worktrees=[]))
    c['worktrees'].append(root)
    status=g(root,'status','--porcelain=v1','--untracked-files=all').splitlines()
    ignored=g(root,'ls-files','--others','--ignored','--exclude-standard','-z').split('\x00');ignored=[x for x in ignored if x]
    untracked=[s[3:] for s in status if s.startswith('?? ')]
    trackedchanges=[s for s in status if not s.startswith('?? ')]
    branch=g(root,'symbolic-ref','--quiet','--short','HEAD')
    upstream=g(root,'rev-parse','--abbrev-ref','--symbolic-full-name','@{upstream}')
    ab=g(root,'rev-list','--left-right','--count','HEAD...'+upstream) if upstream else ''
    unique=g(root,'rev-list','HEAD','--not','--remotes').splitlines()
    row=dict(path=root,repository_root=top,git_marker='DIRECTORY' if os.path.isdir(root+'/.git') else 'FILE',git_dir=gd,common_dir=common,object_dir=obj,branch=branch,HEAD=g(root,'rev-parse','HEAD'),upstream=upstream,ahead_behind=ab,detached=not bool(branch),dirty=bool(trackedchanges),tracked_changes=len(trackedchanges),untracked=len(untracked),ignored=len(ignored),not_in_local_remote_tracking_refs=len(unique),not_in_local_remote_tracking_ref_SHAs=unique,last_commit=g(root,'log','-1','--format=%cI'),last_filesystem_root_mtime=datetime.datetime.fromtimestamp(os.stat(root).st_mtime,datetime.timezone.utc).isoformat(),research_role='AUDIT_OUTPUT' if 'forensic_audit_002' in root else 'CANONICAL_MAINLINE' if root.endswith('_mainline') else 'HISTORICAL_OR_EXTERNAL_REQUIRES_DEPENDENCY_AUDIT',retirement_candidate='NO_IMMEDIATE_RETIREMENT: unique/ignored assets and absolute-path dependencies require resolution')
    rows.append(row)
    with gzip.open(OUT/('WORKTREE_FILES_'+hashlib.sha256(root.encode()).hexdigest()[:12]+'.json.gz'),'wt') as f:json.dump(dict(path=root,status=status,ignored=ignored),f,ensure_ascii=False)
    print('WT',root,'dirty',len(trackedchanges),'untracked',len(untracked),'ignored',len(ignored),flush=True)
for cid,(common,c) in enumerate(clones.items(),1):
    root=c['owner']; c['clone_id']='CLONE_'+str(cid);c['git_storage']=measure(common);c['objects_storage']=measure(c['objects']);c['pack_storage']=measure(pathlib.Path(c['objects'])/'pack');c['refs_storage']=measure(pathlib.Path(common)/'refs');c['reflogs_storage']=measure(pathlib.Path(common)/'logs');c['lfs_storage']=measure(pathlib.Path(common)/'lfs')
    c['worktree_porcelain']=g(root,'worktree','list','--porcelain');c['remotes']=g(root,'remote','-v');c['refs']=g(root,'for-each-ref','--format=%(refname) %(objectname) %(upstream) %(upstream:track)');c['branches_not_in_local_remote_tracking_refs']=g(root,'for-each-ref','--format=%(refname:short)','refs/heads').splitlines();c['unpublished_by_tracking']={b:g(root,'rev-list',b,'--not','--remotes').splitlines() for b in c['branches_not_in_local_remote_tracking_refs']};c['alternates']=(pathlib.Path(c['objects'])/'info/alternates').read_text() if (pathlib.Path(c['objects'])/'info/alternates').exists() else None
    c['count_objects']=g(root,'count-objects','-v');c['submodules']=g(root,'submodule','status','--recursive');c['gitmodules']=(pathlib.Path(root)/'.gitmodules').read_text() if (pathlib.Path(root)/'.gitmodules').exists() else None
    c['packs']=[dict(path=str(p),size=p.stat().st_size,allocated=p.stat().st_blocks*512,device=p.stat().st_dev,inode=p.stat().st_ino,nlink=p.stat().st_nlink,sha256=sha(p),hash_status='HASH_RECOMPUTED') for p in pathlib.Path(c['objects'],'pack').glob('*.pack')]
    c['objects_all_batch_check']=g(root,'cat-file','--batch-all-objects','--batch-check=%(objectname) %(objecttype) %(objectsize) %(objectsize:disk)')
    c['reachable_all_reflog']=g(root,'rev-list','--objects','--all','--reflog')
    c['fsck_full_no_reflogs_unreachable'],c['fsck_rc'],c['fsck_stderr']=run(root,['fsck','--full','--no-reflogs','--unreachable'],timeout=600)
    for remote in g(root,'remote').splitlines():
        out,rc,err=run(root,['ls-remote',remote],timeout=180);c.setdefault('live_remotes',{})[remote]=dict(rc=rc,stderr=err,refs=out)
    print('CLONE',root,c['git_storage'],flush=True)
# Cross-store exact object membership and pack overlap, no misleading disk saving estimate.
object_maps={c['clone_id']:{s.split()[0]:s.split()[1:] for s in c['objects_all_batch_check'].splitlines() if len(s.split())>=4} for c in clones.values()}
for c in clones.values():
    mine=object_maps[c['clone_id']];others=set().union(*(set(v) for k,v in object_maps.items() if k!=c['clone_id']))
    unique=set(mine)-others;c['unique_object_count']=len(unique);c['unique_objects_uncompressed_bytes']=sum(int(mine[k][1]) for k in unique);c['unique_objects_disk_record_bytes']=sum(int(mine[k][2]) for k in unique);c['unique_object_SHAs']=sorted(unique)
    c['unique_objects_disk_caveat']='cat-file objectsize:disk sum is an estimate of per-object representation, not reclaimable pack bytes; delta bases/shared inodes and pack overhead prevent direct savings claim.'
    # object metadata can be large; save exact table compressed.
    for field in ['objects_all_batch_check','reachable_all_reflog']:
        with gzip.open(OUT/(c['clone_id']+'_'+field+'.txt.gz'),'wt') as f:f.write(c.pop(field))
    live=set()
    for v in c.get('live_remotes',{}).values():
        if v['rc']==0:live.update(s.split()[0] for s in v['refs'].splitlines() if s.split())
    c['branch_live_remote_ancestry']={}
    for b in c['branches_not_in_local_remote_tracking_refs']:
        absent=[];unknown=[]
        for s in c['unpublished_by_tracking'].get(b,[]):
            # exact remote tip equality confirms; branch stale tracking needs ancestry to live tips already locally present.
            confirmed=s in live
            if not confirmed:
                for tip in live:
                    if run(c['owner'],['cat-file','-e',tip+'^{commit}'])[1]==0 and run(c['owner'],['merge-base','--is-ancestor',s,tip])[1]==0:confirmed=True;break
            if not confirmed:absent.append(s)
        c['branch_live_remote_ancestry'][b]=dict(not_confirmed_on_live_remote=absent,status='LOCAL_COMMITS_NOT_CONFIRMED_ON_REMOTE' if absent else 'NO_UNCONFIRMED_TRACKING_ONLY_COMMITS',caveat='No fetch performed. Remote tips not present locally cannot establish ancestry; not-confirmed is not proof of loss.')
# output
with open(OUT/'GIT_OBJECT_AUDIT.json','w') as f:json.dump(dict(scope=roots,clones=list(clones.values()),method='Read-only git metadata, GIT_OPTIONAL_LOCKS=0. No fetch/gc/prune/repack/history changes. New audit worktree registration occurred before this independent audit.'),f,ensure_ascii=False,indent=2)
fields=list(dict.fromkeys(k for r in rows for k in r))
with open(OUT/'CLONE_WORKTREE_MATRIX.csv','w') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
with open(OUT/'INDEPENDENT_COMMAND_LOG.json','w') as f:json.dump(commands,f,ensure_ascii=False,indent=2)
print('DONE',len(rows),'roots',len(clones),'clones',flush=True)
