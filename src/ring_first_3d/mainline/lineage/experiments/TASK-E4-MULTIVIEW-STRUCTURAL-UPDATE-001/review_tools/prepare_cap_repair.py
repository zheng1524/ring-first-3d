"""Run only after original run completes; preserves its contract and artifacts."""
from pathlib import Path
import json,shutil,hashlib
import yaml
TD=Path(__file__).resolve().parents[1];ROOT=TD.parents[1];run=TD/'runs/STRUCTURAL_003';state=json.loads((run/'RUN_MANIFEST.json').read_text())
assert state['accepted'] is True
D=TD/'inputs/BEFORE_CAP_PARAMETERIZATION_REPAIR';D.mkdir()
for p in [TD/'TASK.yaml',TD/'TASK_FREEZE.json',TD/'inputs/CODE_LOCK.json']:shutil.copyfile(p,D/p.name)
shutil.copyfile(TD/'code/body_update.py',D/'ORIGINAL_BODY_UPDATE.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rec(p):return dict(path=str(p.resolve()),sha256=sha(p))
freeze=json.loads((run/'FREEZE.json').read_text());cache=dict(source_run=str(run),source_freeze_sha256=freeze['freeze_sha256'],source_task=freeze['fingerprint']['task'],original_updater=rec(D/'ORIGINAL_BODY_UPDATE.py'),entries={})
for stage,cases in [('G1_C0_update',['C0']),('G5_real_update',['G01','G03']),('G2_C0_evaluate',[None])]:
    result=next(json.loads((run/r['path']).read_text()) for r in state['attempts'] if '-'+stage+'-' in r['path']);folder=run/'attempts'/result['attempt_id']
    for case in cases:
        selected=[]
        for rel,info in result['payload']['files'].items():
            q=Path(rel)
            if case:
                if q.parts[0]!=case:continue
                # Full update trajectories; representative exact states; no reoptimization.
                if any(x.startswith('STEP_') and x not in {'STEP_000','STEP_012','STEP_024','STEP_035'} for x in q.parts):continue
            selected.append(dict(**rec(folder/rel),target_relative=rel))
        entry=dict(files=selected)
        if case:entry['initial']=rec(folder/case/'INITIAL.npz')
        cache['entries'][stage+(':'+case if case and stage=='G5_real_update' else '')]=entry
# C0 predictor adoption includes both arms and its global freeze record.
r=next(json.loads((run/r['path']).read_text()) for r in state['attempts'] if '-G1_C0_update-' in r['path']);p=run/'attempts'/r['attempt_id']/'BODY_PREDICTIONS_FROZEN.json';cache['entries']['G1_C0_update']['files'].append(dict(**rec(p),target_relative=p.name))
(TD/'inputs/CAP_REPAIR_CACHE.json').write_text(json.dumps(cache,indent=2)+'\n')
print('prepared',sum(len(e['files']) for e in cache['entries'].values()),'frozen cache files')
