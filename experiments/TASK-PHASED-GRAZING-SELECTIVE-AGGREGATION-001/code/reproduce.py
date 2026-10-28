"""Default verify only; explicit fresh replay writes an isolated local child."""
from common import *
import argparse, shutil
def main():
    p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');p.add_argument('--fresh-replay',action='store_true');args=p.parse_args()
    if not args.fresh_replay:
        verify()
        for f in load(R/'provenance/FINAL_SOURCE_MANIFEST.json')['files']:assert sha(f['path'])==f['sha256'],f['path']
        for a in load(R/'metrics/LOCAL_ASSET_INDEX.json'):assert sha(R/a['path'])==a['sha256'],a['path']
        print('All frozen inputs, delivered source and 344 local assets verified; no algorithm rerun');return
    out=R/'runtime'/('replay_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));out.mkdir(parents=True,exist_ok=False)
    for name in ['code','config']:shutil.copytree(R/name,out/name)
    shutil.copy2(R/'TASK.md',out/'TASK.md');(out/'runtime').mkdir();(out/'local_results').mkdir()
    shutil.copy2(R/'REPRODUCE.md',out/'REPRODUCE.md');(out/'provenance').mkdir()
    if(R/'provenance/EXECUTION_NOTES.json').exists():shutil.copy2(R/'provenance/EXECUTION_NOTES.json',out/'provenance/EXECUTION_NOTES.json')
    (out/'provenance/DELIVERY_COMMITS.json').write_text(json.dumps(dict(status='LOCAL_REPLAY_NOT_UPLOADED',original_delivery=str(R)),indent=2)+'\n')
    # Child common computes REPO from its new location; renderer imports must
    # remain bound to this checkout, never copied legacy code.
    # Use direct exact line replacement, without shell interpolation.
    text=(out/'code/common.py').read_text().replace('REPO = R.parents[1]','REPO = Path('+repr(str(REPO))+')');(out/'code/common.py').write_text(text)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MPLCONFIGDIR=str(out/'runtime/mpl'))
    for command in [['prepare.py'],['test_small.py'],['cleaning.py'],['aggregation.py','primary'],['anchors.py'],['aggregation.py'],['evaluate.py'],['supplemental.py'],['visualize.py'],['deliver.py','--assets-only'],['validate.py'],['deliver.py']]:subprocess.run([sys.executable,str(out/'code'/command[0]),*command[1:]],cwd=REPO,env=env,check=True)
    print('Fresh scientific replay complete at',out,'; original delivery unchanged; report/index use original delivery only')
if __name__=='__main__':main()
