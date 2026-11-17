"""Normal current-tree alias consolidation; no history rewrite or old-tree removal."""
import json,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[3];T=Path(__file__).resolve().parents[1]
branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip();assert branch=='maintenance/TASK-MAINLINE-ASSET-CONSOLIDATION-001'
assert json.loads((T/'ACCEPTANCE.json').read_text())['engineering']=='PASS'
aliases=[]
for p in sorted((R/'experiments').iterdir()):
    if not p.is_symlink():continue
    paths=subprocess.check_output(['git','ls-files','-z','--',str(p.relative_to(R))],cwd=R).split(b'\0');files=[]
    for raw in paths:
        if not raw:continue
        name=raw.decode();data=subprocess.check_output(['git','show','bac3fc89:'+name],cwd=R)
        files.append(dict(original_path=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),tracked=True,retained_alternative='git:bac3fc89ef95db522b63cf6bb98e6914b9382864:'+name,reason='Promoted path becomes a relative canonical alias in the maintenance branch only; original history and working directories retained'))
    aliases.append(dict(path=str(p.relative_to(R)),canonical_target=str(p.resolve().relative_to(R)),retained_history_files=files))
(T/'CURRENT_TREE_ALIAS_MANIFEST.json').write_text(json.dumps(dict(aliases=aliases,history_rewrite=False,remote_branch_deletion=False,physical_space_claim=0),indent=2)+'\n')
for a in aliases:
    if a['retained_history_files']:subprocess.run(['git','rm','-r','--cached','--',a['path']],cwd=R,check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['git','add','-f','--',a['path']],cwd=R,check=True)
print('Current-tree relative aliases staged',len(aliases),'historical Git files retained in baseline',sum(len(a['retained_history_files'])for a in aliases))
