"""Single mainline entry: verify copies, replay fixed modules, retain true failures."""
import argparse,json,sys,traceback,time
from pathlib import Path
from .paths import ROOT
from .execution_guard import install,EXECUTED
def main():
    p=argparse.ArgumentParser();p.add_argument('module',choices=['ring-first','hero','body-initialization','body-update','stalk-growth-g01','stalk-growth-g03','a-to-b','depth-supervised-pytorch']);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    out=a.out.resolve()
    if out.exists():raise FileExistsError('Immutable replay output already exists: '+str(out))
    out.mkdir(parents=True);install();start=time.monotonic()
    from .replays import FUNCTIONS,save,sha,read
    freeze=read(ROOT/'mainline/manifests/REPLAY_INPUT_FREEZE.json')
    try:
        for rec in freeze['source_files']:
            if sha(ROOT/rec['path'])!=rec['sha256']:raise RuntimeError('REPLAY_SOURCE_DRIFT: '+rec['path'])
        external=ROOT/'mainline/manifests/EXTERNAL_INPUTS.json'
        if sha(external)!=freeze['external_manifest_sha256']:raise RuntimeError('EXTERNAL_MANIFEST_DRIFT')
        for rec in read(external)['assets']:
            if rec['path'].endswith('.ckpt')and a.module!='hero':continue
            if not Path(rec['path']).is_file():raise FileNotFoundError(rec['path'])
            if sha(rec['path'])!=rec['sha256']:raise RuntimeError('EXTERNAL_INPUT_DRIFT: '+rec['path'])
        rt=ROOT/'mainline/manifests/RUNTIME_FILES.json'
        if sha(rt)!=freeze['runtime_manifest_sha256']:raise RuntimeError('RUNTIME_MANIFEST_DRIFT')
        for rec in read(rt):
            if sha(ROOT/rec['new_path'])!=rec['sha256']:raise RuntimeError('RUNTIME_SOURCE_DRIFT: '+rec['new_path'])
        result=FUNCTIONS[a.module](out)
    except FileNotFoundError as e:result=dict(status='NOT_EVALUABLE_EXTERNAL_DEPENDENCY',reason=str(e),traceback=traceback.format_exc())
    except Exception as e:result=dict(status='ENGINEERING_FAILURE',reason=str(e),traceback=traceback.format_exc())
    result.update(module=a.module,seconds=time.monotonic()-start,replay_freeze_sha256=sha(ROOT/'mainline/manifests/REPLAY_INPUT_FREEZE.json'),old_experiment_code_execution_forbidden=True,canonical_executed_sources=sorted(EXECUTED),no_new_training=True)
    save(out/'RESULT.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['traceback','canonical_executed_sources','camera','model_receipt']},indent=2));return 0 if result['status']=='PASS'else 1
if __name__=='__main__':sys.exit(main())
