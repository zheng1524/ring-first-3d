import ast,json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[3];T=Path(__file__).resolve().parents[1];BASE=Path('/home/liu/ring_first_3d_growth_recovery')
class UndoPaths(ast.NodeTransformer):
    def visit_ImportFrom(self,n):
        return None if n.module=='ring_first_3d.mainline.paths'and any(a.asname=='_mainline_path'for a in n.names)else n
    def visit_Call(self,n):
        if isinstance(n.func,ast.Name)and n.func.id=='str'and len(n.args)==1:
            q=n.args[0]
            if isinstance(q,ast.Call)and isinstance(q.func,ast.Name)and q.func.id=='_mainline_path':return q.args[0]
        return self.generic_visit(n)
v=json.loads((T/'COPY_VERIFICATION.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest();bad=[]
for x in v['files']:
    old=Path(x['original_path'])
    if old.is_absolute():original=old.read_bytes()
    else:original=subprocess.check_output(['git','show',x['source_commit']+':'+str(old)],cwd=BASE)
    new=(R/x['new_path']).read_bytes();good=sha(original)==x['original_sha256']and sha(new)==x['new_sha256'];x['copy_hash_verified']=good
    if Path(x['new_path']).suffix=='.py':
        repo=Path(*old.parts[:4])if old.is_absolute()and str(old).startswith('/home/liu/')else BASE
        gitpath=str(old.relative_to(repo))if old.is_absolute()else str(old)
        check=subprocess.run(['git','show',x['source_commit']+':'+gitpath],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        pinned=check.returncode==0 and sha(check.stdout)==x['original_sha256']
        x['source_commit_contains_exact_bytes']=pinned
        x['source_commit_role']='EXACT_FILE_VERSION'if pinned else'CONTEXT_BASELINE; actual copied version is independently identified by original_sha256'
    if x['modified']:
        x['scientific_AST_unchanged']=ast.dump(UndoPaths().visit(ast.parse(new)),include_attributes=False)==ast.dump(ast.parse(original),include_attributes=False)
        good=good and x['scientific_AST_unchanged']
    else:good=good and original==new
    x['dependencies']=[]
    if Path(x['new_path']).suffix=='.py':
        tree=ast.parse(new)
        x['dependencies']=[n.module for n in ast.walk(tree)if isinstance(n,ast.ImportFrom)and n.module]+[a.name for n in ast.walk(tree)if isinstance(n,ast.Import)for a in n.names]
        x['dynamic_path_audit_required']=any(s in new for s in [b'sys.path',b'spec_from_file_location',b'compile(',b'__file__'])
    if not good:bad.append(x['new_path'])
v.update(all_copy_hashes_verified=not bad,path_adaptations_preserve_scientific_AST=not bad,errors=bad)
(T/'COPY_VERIFICATION.json').write_text(json.dumps(v,indent=2)+'\n');(R/'mainline/manifests/SOURCE_PROVENANCE.json').write_text(json.dumps(dict(files=v['files'],source_status='ACTIVE_RESEARCH_MAINLINE',scientific_certification=False),indent=2)+'\n')
print('Copies',len(v['files']),'mismatches',bad);assert not bad
