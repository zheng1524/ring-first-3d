"""Standard pipeline including the mature native-reference preparation stage."""
import argparse
import pipeline as p
import run
from ring_first_3d.mainline.native.io import save_json,sha256

def freeze():
    lock=p.TASK/'audit/REF_BUILD_REV1_SOURCE_FREEZE.json'
    if lock.exists():
        for r in p.read(lock)['files']:assert sha256(r['path'])==r['sha256']
        return
    files=[p.TASK/'PROTOCOL_REF_BUILD_REV1.yaml',p.TASK/'code/bootstrap_references.py',p.TASK/'code/standard.py']+sorted((p.TASK/'code/frozen_calibration').glob('*'))
    save_json(lock,dict(files=[p.asset(f) for f in files],GT_HERO_or_historical_camera_for_reference_bootstrap=False,original_task_and_source_freezes_preserved=True))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['run','check']);ap.add_argument('--stage',choices=['all','audit','banks','cameras','hero','body','evaluate','report','check'],default='all');ap.add_argument('--group',choices=p.GROUPS);ap.add_argument('--video',choices=['004','005']);a=ap.parse_args()
    p.verify();run.freeze_code();freeze()
    if a.action=='check':print('STANDARD_INPUT_SOURCE_AND_REFERENCE_PROTOCOL_CHECK_PASS');return
    for stage in (['banks','cameras','hero','body','evaluate','report','check'] if a.stage=='all' else [a.stage]):
        if stage=='banks':
            from banks import build
            from bootstrap_references import build_one
            build(a.group,a.video)
            for g in p.GROUPS:
                for video in ['004','005']:
                    if a.group and a.group!=g or a.video and a.video!=video or p.inherited(g,video):continue
                    admission=p.OUT/g/video/'bank/ADMISSION.json'
                    if not admission.exists() or p.read(admission)['status']!='PASS':build_one(g,video)
        else:run.execute(stage,a.group,a.video)

if __name__=='__main__':main()
