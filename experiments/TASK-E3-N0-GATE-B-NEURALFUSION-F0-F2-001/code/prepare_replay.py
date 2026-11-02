"""Prepare an isolated, identical-input replay; never launch GPU automatically.

Private original source paths and the audited Gate-A runtime must be available.
This copies only small derived inputs/code. No Git repository is initialized.
"""
from pathlib import Path
import shutil,json,hashlib,datetime,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    destination=ROOT/'runtime/replays'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')/'workspace'
    target=destination/'experiments'/ROOT.name;assert not destination.exists()
    for name in ['code','config','provenance']:
        shutil.copytree(ROOT/name,target/name,ignore=shutil.ignore_patterns('__pycache__'))
    for row in json.loads((ROOT/'provenance/FROZEN_INPUTS.json').read_text())['sources']:
        src=ROOT/'frozen_inputs'/row['version']/row['kind']/(row['source']+'.npz')
        if not src.exists():src=Path(row['original']['path'])
        assert sha(src)==row['original']['sha256']
        out=target/'frozen_inputs'/row['version']/row['kind']/(row['source']+'.npz')
        out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,out)
    # Read-only links supply already verified visualization/metadata/dependencies.
    (destination/'visualization').symlink_to(REPO/'visualization',target_is_directory=True)
    d0='TASK-E3-D0-OPEN3D-TSDF-BASELINE-001'
    (destination/'experiments'/d0).symlink_to(REPO/'experiments'/d0,target_is_directory=True)
    (target/'runtime/official_readonly').mkdir(parents=True)
    shutil.copy2(ROOT/'runtime/official_readonly/training_utils.py',target/'runtime/official_readonly/training_utils.py')
    (target/'runtime/python').symlink_to(ROOT/'runtime/python',target_is_directory=True)
    # Import only geometry/common to verify the prepared output root and crop IDs.
    check="import sys;sys.path.insert(0,sys.argv[1]);from common import *;assert len(native(CORE[0],'V6')['ids'])==13379;assert crop(CORE[0],'V6')['depth_mm'].shape==(240,320);print('REPLAY_CPU_IO_PASS',R)"
    subprocess.run([sys.executable,'-B','-c',check,str(target/'code')],check=True)
    print('Prepared isolated output:',target)
    print('No model has been run. Identical frozen F0 command:')
    print(sys.executable,'-B',target/'code/infer.py','V6 F0')
    print('F1/F2 still depend on that isolated run passing the unchanged F0 gate.')
if __name__=='__main__':main()
