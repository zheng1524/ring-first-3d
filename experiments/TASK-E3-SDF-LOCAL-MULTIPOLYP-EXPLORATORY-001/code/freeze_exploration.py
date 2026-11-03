"""Freeze 1000->10000 cumulative M1 updates, not resource benchmark batches."""
from common import *
import difflib


def main():
    all_code=[asset(p)for p in sorted((TASK/'code').glob('*.py'))]
    estimate=[]
    for scene in ORDERS:
        root=TASK/'groups'/scene;perf=load(root/'metrics/PERFORMANCE.json')
        assert perf['unchanged']and perf['formal_updates']==0
        estimate.append(dict(scene=scene,bare_hours_10000=perf['mean_seconds']*10000/3600,
            max_allocated_MiB=max(r['peak_allocated_MiB']for r in perf['records'])))
        old_R=globals()['R'];import common as shared;shared.R=root;globals()['R']=root
        assert not(root/'provenance/BEFORE_FORMAL_TRAINING.json').exists()
        # Normalize inherited planning metadata; network/loss/sampler/units are unchanged.
        p=load(root/'config/PREREGISTERED.json');p['task']=TASK.name;p['arms']=['M1']
        p['executed_budget']=dict(baseline_updates=1000,total_updates=10000,independent_physical_groups=3,
            phases=[200,500,1000,2000,5000,10000],official200k_is_reference_not_executed=True)
        p['resource_benchmark']=dict(optimizer_updates=0,real_forward_backward_probes=3,parameters_unchanged=True)
        p['recovery']=dict(max_additional_runs=0,engineering_repair_only=True,no_quality_early_stop=True)
        save('config/PREREGISTERED.json',p)
        inputs=load(root/'provenance/INPUT_FREEZE.json');inputs['config']=asset(root/'config/PREREGISTERED.json')
        inputs['metadata_normalized_before_first_formal_update']=True;save('provenance/INPUT_FREEZE.json',inputs)
        permit=dict(stages=['three_reference'],arm='M1',historical_M1_updates=0,
            user_decision='M1 基线1000步，累计到10000步',baseline=1000,target_total=10000,
            comparison_steps=[1000,2000,5000,10000],optimizer_reset_at_baseline=False)
        save('config/FORMAL_STAGE_FROZEN.json',dict(**permit,scene=scene,sources=ORDERS[scene],
            total_rays_per_update=1024,gradient_accumulation=False,
            learning_rate='5e-4; same1000 warmup and .1 exponential over200k (not compressed to10k)',
            all_stage_mesh_resolution=256,geometry_quality_early_stop=False,
            physical_GT='NOT_EVALUABLE'))
        save('provenance/BEFORE_FORMAL_TRAINING.json',dict(code=all_code,training_authorization=permit,
            protocol=asset(root/'config/PREREGISTERED.json'),formal_stage=asset(root/'config/FORMAL_STAGE_FROZEN.json'),
            inputs=load(root/'provenance/INPUT_FREEZE.json'),official_commit='12513009cd20a08b35ddc2c55a7e42da2c7baf43',
            formal_updates_before_freeze=0,GT=False))
        globals()['R']=old_R;shared.R=old_R
    import common as shared
    old_R=shared.R;shared.R=TASK
    save('metrics/RESOURCE_ESTIMATE.json',dict(groups=estimate,
        bare_total_hours=sum(r['bare_hours_10000']for r in estimate),
        planning_hours=[sum(r['bare_hours_10000']for r in estimate)*1.2,sum(r['bare_hours_10000']for r in estimate)*1.6],
        exactly_30000_optimizer_updates=True,not_official_full_training=True))
    shared.R=old_R
    ports=load(TASK/'provenance/PORT_MANIFEST.json')
    for row in ports:
        source=Path(row['source']);target=Path(row['target']);row['final_target_sha256']=sha(target)
        (TASK/'provenance'/(target.name+'.diff')).write_text(''.join(difflib.unified_diff(source.read_text().splitlines(True),target.read_text().splitlines(True),fromfile=str(source),tofile=str(target))))
    (TASK/'provenance/PORT_MANIFEST.json').write_text(json.dumps(ports,indent=2)+'\n')
    print('FROZEN',estimate,flush=True)


if __name__=='__main__':main()
