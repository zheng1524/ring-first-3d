"""Freeze user-authorized single-view full-budget continuation before update 1."""
from common import *
import train_full  # materializes auditable runner/extraction import ports, no model construction


def main():
    assert not (R/'provenance/BEFORE_FORMAL_TRAINING.json').exists(), 'FORMAL_ALREADY_FROZEN'
    assert not list((R/'checkpoints').glob('single_*/latest.pt')), 'MODEL_ALREADY_STARTED'
    for a in load(R/'provenance/ORIGINAL_ASSETS.json')['files']: assert sha(a['path'])==a['sha256']
    for a in load(R/'provenance/INPUT_FREEZE.json')['files']: assert sha(a['path'])==a['sha256']
    authorization=dict(user_reply='先完整执行ref08的M0/M1，再审阅三CORE安排',
        stages=['single'],arms=['M0','M1'],steps_per_arm=200000,total_updates=400000,
        three_CORE='AWAIT_RESEARCHER_REVIEW',resource_estimate_hours=[40,55])
    save('provenance/RESOURCE_DECISION.json',authorization)
    save('config/FORMAL_STAGE_FROZEN.json',dict(
        authorized_stages=['single'],arms=['M0','M1'],steps_per_arm=200000,
        data_protocol=asset(R/'config/PREREGISTERED.json'),
        initialization='official geometric initialization bias .6, shared seed; no new shell search',
        stop_rule='no geometry-quality early stopping; genuine nonfinite/hardware interruption only',
        recovery='one registered LR candidate only; not automatically run; no new resource budget assumed',
        evaluation='all three CORE original-native denominators; ref13/ref03 diagnostic not independent GT',
        training_source='G01_004_ref08',three_CORE_training=False))
    save('provenance/BEFORE_FORMAL_TRAINING.json',dict(
        code=[asset(p)for p in sorted((R/'code').glob('*.py'))],
        training_authorization=authorization,
        protocol=asset(R/'config/PREREGISTERED.json'),formal_stage=asset(R/'config/FORMAL_STAGE_FROZEN.json'),
        official_source=asset(R/'provenance/OFFICIAL_SOURCE_MANIFEST.json'),
        inputs=load(R/'provenance/INPUT_FREEZE.json'),formal_updates_before_freeze=0,
        official_runner_update_block_unchanged=True,GT=False,
        parent_commit=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()))
    print('FORMAL_FROZEN ref08 M0/M1 x200000; three CORE not launched')


if __name__=='__main__':main()
