"""Restore task-local links/manifests from immutable019 assets. No fitting."""
from common import *
import shutil
P19=REPO/'experiments/TASK-E4-RING-POLYP-REGISTRATION-019'
def main():
 assert not(R/'provenance/ALL_POSES_FROZEN_BEFORE_EVALUATION.json').exists(),'Do not reinitialize a completed experiment; use an independent replay copy'
 for folder in ['features','matches','landmarks','ring','config','provenance','inputs']:(R/folder).mkdir(exist_ok=True)
 for folder,pattern in [('features','*.npz'),('matches','*.npz'),('ring','*')]:
  for p in(P19/folder).glob(pattern):
   dest=R/folder/p.name
   if not dest.exists():dest.symlink_to(p)
 for n in ['CROSS_004.npz','CROSS_004_OBSERVATIONS.json','NEGATIVE_004.npz','NEGATIVE_004_OBSERVATIONS.json']:
  p=R/'landmarks'/n
  if not p.exists():p.symlink_to(P19/'landmarks'/n)
 for n in ['CROSS_PNP.json','CROSS_EPI.json','NEGATIVE_PNP.json','NEGATIVE_EPI.json']:
  p=R/'features'/n
  if not p.exists():shutil.copyfile(P19/'features'/n,p)
 for n in ['VIEWS.json','NEGATIVE_SPLIT.json','HISTORICAL_CANDIDATES.json']:
  p=R/'config'/n
  if not p.exists():shutil.copyfile(P19/'config'/n,p)
  else:assert sha(p)==sha(P19/'config'/n),'Frozen019 view configuration must match'
 if not(R/'inputs/G01').exists():(R/'inputs/G01').symlink_to(P19/'inputs/G01',target_is_directory=True)
 vv={v['id']:v for v in load(R/'config/VIEWS.json')};rows=[]
 for a in load(P19/'derived/HERO_SCENE_SOURCE_INDEX.json')['sources']:
  root=Path(a['source']['path']).parent;rows.append(dict(id=a['id'],video=a['video'],role=vv[a['id']]['role'],mesh=asset(root/'TRUSTED_HERO.npz'),observation=asset(root/'OBS_TRUSTED.npz'),native=asset((root/'HERO_native.npz').resolve()),labels=asset(root/'FACE_EVIDENCE.npz'),evaluation_only=True))
 p=R/'config/HERO_EVALUATION_SOURCES.json'
 if not p.exists():save('config/HERO_EVALUATION_SOURCES.json',rows)
 print('020_INPUT_LINKS_READY',len(vv),'views',len(rows),'HERO evaluation sources',flush=True)
if __name__=='__main__':main()
