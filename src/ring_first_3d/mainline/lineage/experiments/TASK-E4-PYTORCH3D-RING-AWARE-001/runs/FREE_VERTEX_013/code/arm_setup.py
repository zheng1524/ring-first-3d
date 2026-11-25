from common import *
import shutil
MASTER=Path(__file__).resolve().parents[1]
def setup(tag,loss='A0',optimizer='O0',pilot=True):
 root=MASTER/'arms'/tag;root.mkdir(parents=True,exist_ok=True)
 for d in ['inputs','depth_observations']:
  if not(root/d).exists():(root/d).symlink_to(MASTER/d,target_is_directory=True)
 for d in ['config','assets_index','local_results','metrics','runtime']:(root/d).mkdir(exist_ok=True)
 cfg=load(MASTER/'config/PROTOCOL.json');cfg.update(loss_arm=loss,optimizer_arm=optimizer,total_trust_D=1. if optimizer=='O4'else .25)
 if pilot:cfg.update(cfg['pilot_budget'])
 (root/'config/PROTOCOL.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2));(root/'config/CASE_LOCK.json').write_text((MASTER/'config/CASE_LOCK.json').read_text())
 for p in (MASTER.parent/'FREE_VERTEX_012/local_results').glob('*_P0_SUPPORT.npz'):
  if not(root/'local_results'/p.name).exists():shutil.copyfile(p,root/'local_results'/p.name)
 deps=['common.py','p3d.py','free_model.py','components.py','depth_terms.py','safe_geometry.py','pmgr_self.py','train.py','train012_exact.py','strategy.py','contour_objective.py','evaluate.py']
 files=[asset(MASTER/'code'/p)for p in deps]+[asset(p)for d in ['inputs','depth_observations']for p in sorted((MASTER/d).rglob('*'))if p.is_file()]+[asset(root/'config/PROTOCOL.json')]
 (root/'assets_index/PREOPT_FREEZE.json').write_text(json.dumps(dict(files=files,GT_read=False,epoch=time.time()),indent=2));return root
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('tag');p.add_argument('--loss',default='A0');p.add_argument('--optimizer',default='O0');p.add_argument('--full',action='store_true');a=p.parse_args();print(setup(a.tag,a.loss,a.optimizer,not a.full))
