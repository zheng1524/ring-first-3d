"""Replay in a NEW sibling experiment directory; never overwrites frozen results."""
import argparse,shutil,subprocess,os,json,hashlib,re
from pathlib import Path
import sys

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-name',required=True,help='New experiment directory name, e.g. SPARSE-STRETCH-REPLAY-01')
    args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.output_name):parser.error('Use a plain directory name')
    source=Path(__file__).resolve().parents[1];repo=source.parents[1];dest=repo/'experiments'/args.output_name
    if dest.exists():parser.error('Output exists: choose a new name to preserve frozen results')
    dest.mkdir()
    shutil.copytree(source/'code',dest/'code')
    for name in ['parameters.json','PROTOCOL.md']:shutil.copy2(source/name,dest/name)
    for name in ['metrics','provenance','figures','local_results','logs','runtime']:(dest/name).mkdir()
    snapshot={}
    for root in ['/home/liu/polyp_research','/home/liu/new-polyp-dxy']:
        def git(*a):return subprocess.check_output(['git','-C',root,*a])
        def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
        idx=Path(git('rev-parse','--git-path','index').decode().strip());idx=idx if idx.is_absolute()else Path(root)/idx
        paths=git('diff','--name-only','HEAD','-z').decode().split('\0');snapshot[root]=dict(HEAD=git('rev-parse','HEAD').decode().strip(),status_sha256=hashlib.sha256(git('status','--porcelain=v1','-uall','-z')).hexdigest(),index_sha256=sha(idx),modified_sha256={p:sha(Path(root)/p)for p in paths if p and (Path(root)/p).is_file()})
    (dest/'provenance/protected_worktrees.json').write_text(json.dumps(snapshot,indent=2))
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2')
    commands=[['test_small.py'],['run.py','prepare'],['run.py','run'],['analyze.py'],['figures.py'],['validate.py']]
    for command in commands:
        subprocess.run([sys.executable,str(dest/'code'/command[0]),*command[1:]],cwd=repo,env=env,check=True)
    print('REPLAY_COMPLETE',dest,'; no upstream models, no upload, no original result overwritten')
if __name__=='__main__':main()
