from common import *
import argparse
ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['before','after']);args=ap.parse_args()
if args.phase=='before':
 assert load(R/'metrics/PARAMETRIC_PREFLIGHT.json')['passed'];assert load(R/'metrics/PROJECTION_GATE.json')['passed'];files=[asset(p)for folder in['code','config','inputs','depth_observations']for p in sorted((R/folder).rglob('*'))if p.is_file()and p.suffix!='.png'];files.append(asset(R/'01_PROTOCOL.md'));save('assets_index/PREOPT_FREEZE.json',dict(files=files,time_epoch=time.time(),body_optimization_not_started=True,real_GT_not_read=True,case_N=9,physical_independence_frozen=True))
else:
 save('assets_index/PREDICTIONS_FROZEN.json',dict(files=[asset(p)for p in sorted((R/'local_results').rglob('*'))if p.is_file()],time_epoch=time.time(),selection_done_using_FIT_only=True,real_GT_not_read=True));print('PREDICTIONS_FROZEN')
