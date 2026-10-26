"""Fresh output closure: copy this task's code, reference read-only frozen inputs.

Creates new freezes before new bounded trials. Never overwrites original evidence.
"""
import argparse,os,sys,json,shutil,subprocess
from pathlib import Path
def main():
    p=argparse.ArgumentParser();p.add_argument('--output-root',required=True,type=Path);p.add_argument('--no-render',action='store_true');a=p.parse_args();source=Path(__file__).resolve().parents[1];repo=source.parents[1];dest=a.output_root.resolve()
    if dest.exists():p.error('Output root must not exist')
    task=dest/'experiments'/source.name;task.mkdir(parents=True);shutil.copytree(source/'code',task/'code',ignore=shutil.ignore_patterns('__pycache__'));shutil.copy2(source/'config.json',task/'config.json');shutil.copy2(source/'PROTOCOL.md',task/'PROTOCOL.md');(dest/'visualization').symlink_to(repo/'visualization',target_is_directory=True);(dest/'experiments/TASK-PHASEC-SCENE-POINTCLOUD-AUDIT-001').symlink_to(repo/'experiments/TASK-PHASEC-SCENE-POINTCLOUD-AUDIT-001',target_is_directory=True)
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',PYTHONPATH=str(dest))
    def run(script,*args):subprocess.run([sys.executable,str(task/'code'/script),*args],env=env,cwd=dest,check=True)
    for script,mode in [('p1.py','prepare'),('reprojection.py','prepare'),('p1.py','freeze'),('p1.py','run')]:run(script,mode)
    code="from common import *;save('provenance/P2_EXECUTION_FROZEN.json',stamp([R/'code/reprojection.py',R/'code/common.py',R/'provenance/P2_PAIRS_FROZEN.json',R/'provenance/P3_PAIRS_FROZEN.json',R/'metrics/P1_video_decisions.json']))"
    subprocess.run([sys.executable,'-c',"import sys;sys.path.insert(0,"+repr(str(task/'code'))+");"+code],env=env,cwd=dest,check=True)
    run('reprojection.py','run');run('reprojection.py','cross');run('descriptive.py')
    equal=[]
    for name in ['P1_video_decisions.json','P1_candidate_damage.json','P2_results.json','P3_results.json']:
        original=json.loads((source/'metrics'/name).read_text());replay=json.loads((task/'metrics'/name).read_text())
        for rows in [original,replay]:
            for row in rows:row.pop('local_output',None)
        assert original==replay,name;equal.append(name)
    if not a.no_render:
        for stage in ['P1','layers','P2','P3']:run('figures.py',stage)
    receipt=dict(status='PASS',exact_scientific_metrics=equal,task_output=str(task),rendered=not a.no_render,upstream_runs=0,original_assets_overwritten=0)
    (source/'runtime').mkdir(exist_ok=True);(source/'runtime/REPLAY_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print('FRESH_REPLAY_EXACT',json.dumps(receipt),flush=True)
if __name__=='__main__':main()
