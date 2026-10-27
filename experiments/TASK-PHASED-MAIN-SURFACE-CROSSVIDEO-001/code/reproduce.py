"""Verify existing evidence or replay in a NEW isolated directory. No overwrites."""
import argparse,subprocess,os,sys,json,hashlib,shutil,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STAGES=[('model.py','prepare'),('test_small.py',),('model.py','D0'),('registration.py',),('yaw_observability.py',),('FREEZE_EVALUATION',),('evaluation.py','D0'),('evaluation.py','D1'),('backup_pnp.py',),('background_heldout.py',),('physical_export.py','D3'),('height_sensitivity.py',),('physical_export.py','export'),('comparison_extras.py',),('figures.py',),('diagnostic_views.py',),('paired_support.py',),('validate.py',)]
def freeze_evaluation(root):
    files=[root/'code/evaluation.py',root/'config.json',root/'provenance/TARGETS_FROZEN.json'];value=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)for p in files],GT_used=False,heldout_RGB_not_computed_yet=True,front_conflict_exposure_fraction_maximum=.15,acceptance='Frozen Ring bounds, multiple initialization stability, conditional observability and relative heldout deterioration; no 3px absolute veto');(root/'provenance/EVALUATION_D2_FROZEN.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['plan','verify','replay']);p.add_argument('--destination',type=Path);args=p.parse_args();env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'2'}
    if args.mode=='plan':
        print(json.dumps(dict(existing_output=str(ROOT),replay_stages=STAGES,read_only_input_manifests=['provenance/INPUTS.json','provenance/D1_BACKUP_BEFORE_COMPUTE.json'],GT_used=False),ensure_ascii=False,indent=2));return
    if args.mode=='verify':
        for name in ['test_small.py','validate.py']:subprocess.run([sys.executable,str(ROOT/'code'/name)],env=env,check=True)
        return
    dest=(args.destination or ROOT/'runtime/fresh_replay/experiments'/ROOT.name).resolve()
    if dest.exists():raise SystemExit('Destination exists; choose a new directory. No overwrite.')
    if dest.parent.name!='experiments':raise SystemExit('Destination must be <new-root>/experiments/<task-name>')
    repo=dest.parents[1];renderer=repo/'visualization'
    if renderer.exists():raise SystemExit('Replay root already has visualization; choose a fresh root')
    dest.mkdir(parents=True);renderer.symlink_to(ROOT.parents[1]/'visualization',target_is_directory=True);shutil.copytree(ROOT/'code',dest/'code')
    for name in ['TASK.md','PROTOCOL.md','config.json']:shutil.copy2(ROOT/name,dest/name)
    (dest/'runtime').mkdir();shutil.copy2(ROOT/'runtime/protected_start.json',dest/'runtime/protected_start.json');(dest/'logs').mkdir()
    for stage in STAGES:
        print('REPLAY',stage,flush=True)
        if stage[0]=='FREEZE_EVALUATION':freeze_evaluation(dest);continue
        with (dest/'logs'/('_'.join(stage)+'.log')).open('w')as log:subprocess.run([sys.executable,str(dest/'code'/stage[0]),*stage[1:]],env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
    print('REPLAY_COMPLETE',dest)
if __name__=='__main__':main()
