"""Verify current artifacts, or replay once in a fresh task directory."""
from pathlib import Path
import argparse,sys,os,subprocess,shutil,json
ROOT=Path(__file__).resolve().parents[1]
STAGES=[('prepare.py',),('supplemental_audit.py',),('test_small.py',),('pipeline.py','A'),('pipeline.py','B'),('metric_geometry.py',),('feret_definition_audit.py',),('review_assets.py',),('common_support.py',),('exemption_audit.py',),('visualize.py',),('index_results.py',),('validate.py',)]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['plan','verify','replay']);p.add_argument('--destination',type=Path);a=p.parse_args();env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'2'}
    if a.mode=='plan':print(json.dumps(dict(stages=STAGES,frozen_upstream=True,new_HERO_calls=0,formal_Dxy_imports=0,physical_groups=4,local_video_scenes=5),ensure_ascii=False,indent=2));return
    if a.mode=='verify':
        for name in ['test_small.py','validate.py']:subprocess.run([sys.executable,str(ROOT/'code'/name)],env=env,check=True)
        return
    dst=(a.destination or ROOT/'runtime/fresh_replay/experiments'/ROOT.name).resolve()
    if dst.exists()or dst.parent.name!='experiments':raise SystemExit('Use a NEW <root>/experiments/<task> directory; no overwrite.')
    renderer=dst.parents[1]/'visualization'
    if renderer.exists():raise SystemExit('Replay root already has visualization; choose a fresh root')
    dst.mkdir(parents=True);renderer.symlink_to(ROOT.parents[1]/'visualization',target_is_directory=True);shutil.copytree(ROOT/'code',dst/'code')
    for name in ['TASK.md','PROTOCOL.md','config.json']:shutil.copy2(ROOT/name,dst/name)
    (dst/'runtime').mkdir();(dst/'logs').mkdir();shutil.copy2(ROOT/'runtime/protected_start.json',dst/'runtime/protected_start.json')
    for stage in STAGES:
        print('REPLAY',stage,flush=True)
        with (dst/'logs'/('_'.join(stage)+'.log')).open('w')as log:subprocess.run([sys.executable,str(dst/'code'/stage[0]),*stage[1:]],env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
    print('REPLAY_COMPLETE',dst)
if __name__=='__main__':main()
