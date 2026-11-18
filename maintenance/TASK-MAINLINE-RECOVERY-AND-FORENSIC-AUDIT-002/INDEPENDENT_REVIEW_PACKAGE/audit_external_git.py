import pathlib,subprocess,json,os,csv,hashlib
O=pathlib.Path(__file__).resolve().parent
base=pathlib.Path('/home/liu/polyp_research')
rel=['ring_anchor_3d/experiments/ring_first_v8_registration_narrow_baseline/vendor/mast3r','ring_anchor_3d/experiments/ring_first_v8_registration_narrow_baseline/vendor/mast3r/dust3r','ring_anchor_3d/experiments/ring_first_v8_registration_narrow_baseline/vendor/mast3r/dust3r/croco','ring_anchor_3d/experiments/ring_first_v13_multisource/vendor/LightGlue','ring_anchor_3d/experiments/ring_first_v13_multisource/vendor/co-tracker','ring_anchor_3d/experiments/ring_first_v13_multisource/vendor/RoMa','ring_anchor_3d/vendor/Depth-Anything-3','external/depth_priors/ColonDepthEstimation','external/depth_priors/EndoDAC','external/depth_priors/Depth-Anything-V2']
roots=[base/p for p in rel]+[pathlib.Path('/home/liu/new-polyp-dxy')]
records=[]
def g(p,*a):
 r=subprocess.run(['git','-C',str(p),*a],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0'),timeout=120)
 return {'rc':r.returncode,'stdout':r.stdout.decode(errors='replace'),'stderr':r.stderr.decode(errors='replace')}
for p in roots:
 r=dict(path=str(p),classification='OTHER_INDEPENDENT_RESEARCH_PROJECT_READ_ONLY' if p.name=='new-polyp-dxy' else 'EXTERNAL_RESEARCH_DEPENDENCY',exists=p.exists(),git_marker='DIR' if (p/'.git').is_dir() else 'FILE' if (p/'.git').is_file() else 'MISSING',retirement='REJECT: third-party or independent DXY project, out of mainline worktree retirement scope')
 for k,a in {'root':['rev-parse','--show-toplevel'],'common_dir':['rev-parse','--git-common-dir'],'object_dir':['rev-parse','--git-path','objects'],'HEAD':['rev-parse','HEAD'],'branch':['symbolic-ref','--quiet','--short','HEAD'],'status':['status','--porcelain=v1','--untracked-files=all'],'remote':['remote','-v'],'count_objects':['count-objects','-v'],'worktrees':['worktree','list','--porcelain'],'submodules':['submodule','status','--recursive'],'refs':['for-each-ref','--format=%(refname) %(objectname) %(upstream:track)']}.items():r[k]=g(p,*a)
 common=pathlib.Path(p,r['common_dir']['stdout'].strip()).resolve();obj=pathlib.Path(p,r['object_dir']['stdout'].strip()).resolve()
 r['alternates']=(obj/'info/alternates').read_text() if (obj/'info/alternates').exists() else None
 alloc={};ls=0
 for b,ds,fs in os.walk(common):
  for f in fs:
   s=os.lstat(pathlib.Path(b,f));ls+=s.st_size;alloc[(s.st_dev,s.st_ino)]=s.st_blocks*512
 r['git_storage_logical']=ls;r['git_storage_unique_inode_allocated']=sum(alloc.values());records.append(r)
 print(str(p),r['HEAD']['stdout'].strip(),flush=True)
json.dump(records,open(O/'EXTERNAL_GIT_DEPENDENCIES.json','w'),ensure_ascii=False,indent=2)
