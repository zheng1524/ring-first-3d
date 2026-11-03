"""Bind relocated files and the exact local predecessor before any remote updates."""
from pathlib import Path
import json,hashlib,shutil,os
TASK=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def asset(p):return dict(relative_path=str(p.relative_to(TASK)),sha256=sha(p),bytes=p.stat().st_size)
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def main():
    import torch
    plan=json.loads((TASK/'config/MIGRATION_PLAN.json').read_text())
    for a in json.loads((TASK/'data/ASSET_MANIFEST.json').read_text()):assert sha(TASK/a['relative_path'])==a['sha256']
    official=json.loads((TASK/'lineage/OFFICIAL_SOURCE_MANIFEST.json').read_text())
    for a in official['files']:
        f=TASK/'vendor/official_exact'/a['relative_path'];assert sha(f)==a['sha256']
    code=[asset(p)for p in sorted((TASK/'code').glob('*.py'))]
    snapshots=json.loads((TASK/'config/PREDECESSORS.json').read_text())
    for scene in plan['orders']:
        root=TASK/'groups'/scene
        for d in ['runtime','provenance','metrics','checkpoints/single_M1','local_results']:(root/d).mkdir(parents=True,exist_ok=True)
        link=root/'runtime/official_exact'
        if not link.exists():link.symlink_to(TASK/'vendor/official_exact',target_is_directory=True)
        protocol=root/'config/PREREGISTERED.json';current=json.loads(protocol.read_text())
        predecessor=json.loads((TASK/'lineage'/(scene+'_BEFORE_FORMAL_TRAINING.json')).read_text())
        inputs=[asset(p)for p in sorted((root/'frozen_inputs').glob('*.npz'))]
        assert {r['sha256']for r in inputs}=={r['sha256']for r in predecessor['inputs']['files']}
        write(root/'provenance/INPUT_FREEZE.json',dict(files=inputs,predecessor_input_bytes_unchanged=True))
        execution=json.loads((root/'config/FORMAL_STAGE_FROZEN.json').read_text())
        execution.update(migration_baseline_N=2000,primary_goal=20000,remote_target='chosen by retained100-step4090 pilot within6.5h',old_execution_metadata_retained=True)
        write(root/'config/FORMAL_STAGE_FROZEN.json',execution)
        write(root/'provenance/BEFORE_FORMAL_TRAINING.json',dict(code=code,
            protocol=asset(protocol),training_authorization=dict(stages=['three_reference'],
            baseline_N=2000,primary_target=20000,user_may_extend_within_hours=6.5),
            input_files=inputs,predecessor=predecessor,official_commit=official['commit'],
            scientific_configuration='unchanged network/loss/sampler/optimizer/units; IO relocation only',GT=False))
        if scene in snapshots:
            info=snapshots[scene];source=TASK/info['relative_path'];assert sha(source)==info['sha256']
            state=torch.load(source,map_location='cpu',weights_only=False)
            assert state['scene']==scene and state['step']==state['loss_step']==info['step']
            assert set(int(s['step'])for s in state['optimizer']['state'].values())=={info['step']}
            for k in ['geometry','network','losses','sampler','optimizer','seed']:assert state['protocol'][k]==current[k],k
            for k in ['model','optimizer','scheduler','torch_rng','cuda_rng','python_rng','numpy_rng','sampling_state','accumulated_elapsed_seconds']:assert k in state
            target=root/'checkpoints/single_M1/latest.pt';assert not target.exists(),'DO_NOT_REINITIALIZE'
            shutil.copy2(source,target)
            write(target.parent/'LATEST.json',dict(step=info['step'],arm='M1',path=str(target),
                sha256=sha(target),validated_predecessor=True,source_checkpoint=info,
                original_code_freeze_sha256=state['code_freeze_sha256'],scientific_configuration_identical=True))
            write(root/'provenance/RESTORE_BINDING.json',dict(state_fields=list(state),step=info['step'],
                optimizer_parameter_states=len(state['optimizer']['state']),sampling_state=state['sampling_state'],
                LR=[g['lr']for g in state['optimizer']['param_groups']],checkpoint_sha256=sha(source),
                predecessor_code_freeze=state['code_freeze_sha256'],mode='COMPLETE_STATE_RESUME',GT=False))
        else:
            write(root/'provenance/RESTORE_BINDING.json',dict(mode='NEW_INDEPENDENT_MODEL',
                reason='no prior formal M1 checkpoint for this polyp; no transfer from G01',GT=False))
    print('BOOTSTRAP_VALIDATED',snapshots,'data/official source SHA and full optimizer states bound',flush=True)


if __name__=='__main__':main()
