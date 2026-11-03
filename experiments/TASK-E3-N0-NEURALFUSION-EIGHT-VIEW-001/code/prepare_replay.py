"""Prepare a separate identical-input replay. CPU check only; never launches GPU."""
from pathlib import Path
import json,shutil,datetime,subprocess,sys,hashlib
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    root=R/'runtime/replays'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')/'workspace';target=root/'experiments'/R.name;assert not root.exists()
    for name in ['code','config','provenance']:shutil.copytree(R/name,target/name,ignore=shutil.ignore_patterns('__pycache__'))
    (target/'metrics').mkdir();shutil.copy2(R/'metrics/CUMULATIVE_INPUT_SUPPRESSION.csv',target/'metrics/CUMULATIVE_INPUT_SUPPRESSION.csv')
    (root/'visualization').symlink_to(REPO/'visualization',target_is_directory=True)
    for name in ['TASK-CAMERA-GATE-G01-004-PILOT-001','TASK-E3-D0-OPEN3D-TSDF-BASELINE-001']:(root/'experiments'/name).symlink_to(REPO/'experiments'/name,target_is_directory=True)
    (target/'runtime/official_readonly').mkdir(parents=True);shutil.copy2(R/'runtime/official_readonly/training_utils.py',target/'runtime/official_readonly/training_utils.py')
    subprocess.run([sys.executable,'-B',str(target/'code/restore_inputs.py')],check=True)
    for path in (R/'frozen_inputs').glob('*/*.npz'):assert sha(target/path.relative_to(R))==sha(path)
    check="import sys;sys.path.insert(0,sys.argv[1]);from common import *;p=protocol();assert [len(a)for a in p['orders'].values()]==[8,5];assert crop(p['orders']['G01_004'][0])['depth_mm'].shape==(240,320);print('REPLAY_CPU_IO_PASS',R)"
    subprocess.run([sys.executable,'-B','-c',check,str(target/'code')],check=True)
    (R/'provenance/REPLAY_PREPARATION.json').write_text(json.dumps(dict(prepared_output=str(target),CPU_identity_check='PASS',new_GPU_forward_N=0),indent=2)+'\n')
    print('Prepared:',target,'No GPU run. When separately authorized, run infer.py <scene> <forward|reverse> in this separate task root.')
if __name__=='__main__':main()
