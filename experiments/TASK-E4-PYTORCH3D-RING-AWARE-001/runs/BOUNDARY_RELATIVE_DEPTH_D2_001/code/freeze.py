from common import *
import argparse
ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['before','after']);args=ap.parse_args()
if args.phase=='before':
 assert load(R/'metrics/PREFLIGHT.json')['passed']and load(R/'metrics/PROJECTION_GATE.json')['passed']
 for name,old in[('virtual_IIa','virtual'),('real_Ip','real')]:
  parent=R/'local_results'/name;parent.mkdir(exist_ok=True);p=parent/'B';p.symlink_to(R.parent/'PROGRESSIVE_HERO_001/local_results'/old/'B',target_is_directory=True)
  save('metrics/'+name+'_B_RUN.json',dict(case=name,arm='B',status='REUSED_FROZEN_B',optimizer_steps=300,elapsed_seconds=None,new_optimizer_steps=0,source=str(p.resolve()),source_files=[asset(x)for x in p.iterdir()if x.is_file()]))
 files=[asset(p)for folder in['code','config','inputs','depth_observations']for p in sorted((R/folder).rglob('*'))if p.is_file()and p.suffix!='.png'];files.append(asset(R/'01_PROTOCOL.md'));save('assets_index/PREOPT_FREEZE.json',dict(time_epoch=time.time(),files=files,GT_mesh_used_for_choice=False,crossview_HERO_diagnostic_not_yet_run=True,geometry_ranking=False))
else:
 files=[asset(p)for p in sorted((R/'local_results').rglob('*'))if p.is_file()];files += [asset(p)for p in sorted((R/'metrics').glob('*_RUN.json'))];save('assets_index/PREDICTIONS_FROZEN.json',dict(time_epoch=time.time(),files=files,all_expected_finals=all((R/'local_results'/c/a/'FINAL.npz').exists()for c in load(R/'config/PROTOCOL.json')['cases']for a in['B','E1','E2','E3']),GT_3D_evaluation_not_yet_started=True))
 print('PREDICTIONS_FROZEN',len(files))
