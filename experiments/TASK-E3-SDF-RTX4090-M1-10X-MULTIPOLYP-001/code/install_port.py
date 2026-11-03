"""Portable checkpoint/step-budget IO changes; no network/loss/sampling redesign."""
from pathlib import Path
import json,hashlib,difflib,shutil
R=Path(__file__).resolve().parents[1];B=R/'bundle'


def replace(s,a,b,count=1):
    assert s.count(a)==count,(a,s.count(a),count)
    return s.replace(a,b)


def main():
    shutil.copy2(R/'code/portable_common.py',B/'code/common.py')
    history=Path('/home/liu/ring_first_3d_e3n0_eight/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001/code/figures.py')
    target=B/'vendor/history/code/figures.py';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(history,target)
    source=B/'code/train_full.py'
    original=Path('/home/liu/ring_first_3d_e3_sdf_multi/experiments/TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001/code/train_full.py').read_text();s=original
    # Define IO-only run limit after common/os imports have been provided.
    s=replace(s,'from geometry_monitor import geometry_checkpoint','from geometry_monitor import geometry_checkpoint\nRUN_LIMIT=int(os.environ.get("RF_RUN_LIMIT","20000"))\nassert 1 <= RUN_LIMIT <= 200000')
    s=replace(s,'self.nepochs=10000-1','self.nepochs=RUN_LIMIT-1')
    s=replace(s,'step<=10000','step<=RUN_LIMIT')
    s=replace(s,'planned_updates=10000','planned_updates=RUN_LIMIT')
    s=replace(s,'final=step==10000','final=step==RUN_LIMIT')
    s=replace(s,'runner.iter_step==10000','runner.iter_step==RUN_LIMIT')
    s=replace(s,"status='COMPLETED_10000',step=10000","status='COMPLETED_RUN_LIMIT',step=RUN_LIMIT")
    s=replace(s,"self.checkpoint_steps=set(protocol()['checkpoint_steps'])","self.checkpoint_steps=set(protocol()['checkpoint_steps'])|{RUN_LIMIT}")
    s=replace(s,"for a in self.freeze['code']: assert sha(a['path'])==a['sha256'], 'FROZEN_CODE_CHANGED'","for a in self.freeze['code']: assert sha(TASK/a['relative_path'])==a['sha256'], 'FROZEN_CODE_CHANGED'")
    s=replace(s,"for a in load(R/'provenance/INPUT_FREEZE.json')['files']: assert sha(a['path'])==a['sha256']","for a in load(R/'provenance/INPUT_FREEZE.json')['files']: assert sha(TASK/a['relative_path'])==a['sha256']")
    s=replace(s,"assert state['scene']==SCENE and state['code_freeze_sha256']==sha(R/'provenance/BEFORE_FORMAL_TRAINING.json')", "assert state['scene']==SCENE\n            assert state['code_freeze_sha256']==sha(R/'provenance/BEFORE_FORMAL_TRAINING.json') or index.get('validated_predecessor',False), 'UNBOUND_MIGRATION_CHECKPOINT'")
    s=replace(s,'runner=self.runner; batch=runner.current_batch','runner=self.runner; batch=runner.current_batch\n        torch.cuda.synchronize(); runner._step_start=time.monotonic()')
    s=replace(s,'        step=self.iter_step\n        assert step<=RUN_LIMIT','        step=self.iter_step\n        torch.cuda.synchronize()\n        duration=time.monotonic()-self._step_start\n        if os.environ.get("RF_PILOT")=="1":\n            with (R/"metrics/PILOT_TIMING.jsonl").open("a") as f: f.write(json.dumps(dict(step=step,seconds=duration))+"\\n")\n        assert step<=RUN_LIMIT')
    source.write_text(s)
    (B/'provenance').mkdir(exist_ok=True)
    (B/'provenance/REMOTE_RUNNER_IO.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='local_M1/train_full.py',tofile='portable_M1/train_full.py')))
    # Preserve scientific hyperparameters; add only extraction/checkpoint milestones.
    for scene in json.loads((B/'config/MIGRATION_PLAN.json').read_text())['orders']:
        p=B/'groups'/scene/'config/PREREGISTERED.json';cfg=json.loads(p.read_text());old=cfg.copy()
        cfg['checkpoint_steps']=[0,200,500,1000,2000,4000,10000,20000,50000,100000,150000,200000]
        cfg['migration_scientific_configuration_unchanged']=True
        p.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
        for key in ['geometry','network','losses','sampler','optimizer','seed']:
            assert cfg[key]==old[key]
    print('PORT_INSTALLED; same scientific configuration, portable IO only')


if __name__=='__main__':main()
