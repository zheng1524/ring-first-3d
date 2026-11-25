"""Prepare a separate replay from frozen011; never copy012 predictions or overwrite a run."""
from common import *
import argparse,shutil

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);out=Path(p.parse_args().output).resolve();assert not out.exists(),'Refuse to overwrite any existing run';assert out.parent==R.parent,'Keep the shared experiment/runtime layout';old=R.parent/'CAP_REPAIR_STABLE_011'
 for a in load(R/'assets_index/HISTORY_011_PROTECTION.json'):assert sha(a['path'])==a['sha256']
 out.mkdir()
 for d in ['code','config']:shutil.copytree(R/d,out/d,ignore=shutil.ignore_patterns('__pycache__'))
 for d in ['assets_index','runtime','local_results','figures','metrics']: (out/d).mkdir()
 shutil.copytree(old/'inputs',out/'inputs');shutil.copytree(old/'depth_observations',out/'depth_observations');shutil.copy2(R/'01_PROTOCOL.md',out/'01_PROTOCOL.md');shutil.copy2(R/'assets_index/HISTORY_011_PROTECTION.json',out/'assets_index/HISTORY_011_PROTECTION.json')
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];shutil.copy2(old/'inputs'/n/'INITIAL.npz',out/'inputs'/n/'C_011.npz');shutil.copy2(old/'local_results'/n/'FINAL.npz',out/'inputs'/n/'INITIAL.npz');q=out/'inputs'/n/'C_INITIAL_MODEL.json';m=load(q);m['012_note']='metadata only; initial actual geometry is exact011FINAL; no parameterized/spectral model used';q.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');support=R/'local_results'/(n+'_P0_SUPPORT.npz')
  if support.exists():shutil.copy2(support,out/'local_results'/support.name)
 print('PREPARED_INDEPENDENT_REPLAY',out,'No012 prediction, checkpoint or GT copied. Run preflight/freeze there before training.')

if __name__=='__main__':main()
