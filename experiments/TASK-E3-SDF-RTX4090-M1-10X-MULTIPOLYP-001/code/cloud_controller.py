"""Retained pilot, three compulsory10x runs, then measured-budget continuation.

No quality-based stopping or model selection. Runs/outputs stay per physical polyp.
"""
from pathlib import Path
import os,sys,json,time,subprocess,statistics,traceback
TASK=Path(__file__).resolve().parents[1]
PLAN=json.loads((TASK/'config/MIGRATION_PLAN.json').read_text())
SCENES=list(PLAN['orders']);START=time.monotonic()
LIMIT_SECONDS=6.5*3600


def write(name,value):
    p=TASK/name;p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,p)
def state(scene):
    p=TASK/'groups'/scene/'checkpoints/single_M1/LATEST.json'
    return json.loads(p.read_text())if p.exists()else None
def visualize():
    with (TASK/'runtime/visualization.log').open('a')as out:
        rc=subprocess.run([sys.executable,'-B',str(TASK/'code/cloud_report.py')],cwd=TASK,stdout=out,stderr=subprocess.STDOUT).returncode
    if rc:write('provenance/VISUALIZATION_ERROR.json',dict(returncode=rc,training_not_changed=True))
def run(scene,until,pilot=False):
    before=state(scene);step=before['step']if before else 0
    if step>=until:return dict(scene=scene,start=step,end=step,wall_seconds=0)
    env=os.environ.copy();env.update(MONOSDF_SCENE=scene,RF_RUN_LIMIT=str(until),RF_PILOT='1'if pilot else'0',PYTHONUNBUFFERED='1')
    command=[sys.executable,'-B',str(TASK/'code/train_full.py'),'M1']+(['--resume']if before else[])
    log=TASK/'runtime'/f'{scene}_from{step:06d}_to{until:06d}.log'
    assert not log.exists(),'NO_OVERWRITE_OF_RUN_LOG'
    write('provenance/LIVE_RUN.json',dict(scene=scene,start=step,until=until,pilot=pilot,command=command))
    clock=time.monotonic()
    with log.open('w')as out:rc=subprocess.run(command,cwd=TASK,env=env,stdout=out,stderr=subprocess.STDOUT).returncode
    after=state(scene)
    result=dict(scene=scene,start=step,end=after['step']if after else None,wall_seconds=time.monotonic()-clock,returncode=rc,log=str(log.relative_to(TASK)))
    assert rc==0 and after['step']==until,('ENGINEERING_INTERRUPTION',result)
    print('RUN_DONE',result,flush=True)
    return result


def main():
    (TASK/'runtime').mkdir(exist_ok=True)
    assert not(TASK/'provenance/CONTROLLER_STARTED.json').exists(),'DO_NOT_RELAUNCH_CONTROLLER'
    write('provenance/CONTROLLER_STARTED.json',dict(primary_steps_each=20000,baseline_N=2000,budget_hours=6.5,source_order=SCENES))
    try:
        subprocess.run([sys.executable,'-B',str(TASK/'code/remote_bootstrap.py')],cwd=TASK,check=True)
        env=os.environ.copy();env['MONOSDF_SCENE']='G01_004'
        subprocess.run([sys.executable,'-B',str(TASK/'code/cloud_snapshots.py')],cwd=TASK,env=env,check=True)
        visualize()
        start=state('G01_004')['step'];pilot=run('G01_004',start+100,pilot=True)
        timing=[json.loads(s)for s in (TASK/'groups/G01_004/metrics/PILOT_TIMING.jsonl').read_text().splitlines()]
        measured=[r['seconds']for r in timing[5:]]
        median=statistics.median(measured);ordered=sorted(measured);p95=ordered[int(.95*(len(ordered)-1))]
        primary_remaining=sum(max(0,20000-(state(s)['step']if state(s)else 0))for s in SCENES)
        estimate=primary_remaining*max(median,p95)*1.35+30*60
        write('metrics/RTX4090_PERFORMANCE.json',dict(retained_pilot=pilot,median_seconds=median,p95_seconds=p95,
            initial_updates_excluded=5,primary_remaining_steps=primary_remaining,
            estimated_primary_remaining_hours=estimate/3600,projected_batch_rays=1024,
            no_discarded_optimizer_updates=True))
        visualize()
        if estimate>LIMIT_SECONDS-(time.monotonic()-START):
            write('provenance/RESOURCE_REVIEW_REQUIRED.json',dict(reason='primary20k per group estimate exceeds delegated6.5h budget',estimate_hours=estimate/3600,scientific_failure=False))
            return 3
        runs=[pilot]
        for scene in SCENES:
            result=run(scene,20000);runs.append(result)
            write('metrics/RUN_HISTORY.json',runs);visualize()
        # Extend all groups equally, based on timing only, never on geometry or loss.
        rates=[r['wall_seconds']/max(1,r['end']-r['start'])for r in runs[1:]]
        worst=max(rates+[p95])*1.2
        remaining=LIMIT_SECONDS-(time.monotonic()-START)-30*60
        extra_per_scene=max(0,int(remaining/(len(SCENES)*worst)))
        final_target=min(200000,20000+(extra_per_scene//10000)*10000)
        write('config/MEASURED_CONTINUATION_PLAN.json',dict(primary_complete=True,
            final_cumulative_steps_each=final_target,budget_hours=6.5,
            worst_measured_seconds_with_margin=worst,selection_uses='time/memory only; no loss/mesh/GT',
            all_scientific_hyperparameters_unchanged=True))
        if final_target>20000:
            for scene in SCENES:
                result=run(scene,final_target);runs.append(result)
                write('metrics/RUN_HISTORY.json',runs);visualize()
        write('provenance/TRAINING_DONE.json',dict(scene_steps={s:state(s)['step']for s in SCENES},
            wall_seconds=time.monotonic()-START,primary_10x_completed=True,GT=False,
            scientific_acceptance='REQUIRES_RESEARCHER_PM_REVIEW'))
        visualize()
        return 0
    except BaseException as exc:
        write('provenance/CONTROLLER_INTERRUPTION.json',dict(type=type(exc).__name__,reason=str(exc),
            traceback=traceback.format_exc(),scientific_failure=False,wall_seconds=time.monotonic()-START))
        visualize();print(traceback.format_exc(),flush=True);return 2


if __name__=='__main__':sys.exit(main())
