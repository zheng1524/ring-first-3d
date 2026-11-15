"""Freeze native source identity; no HERO inference, resampling, or geometry fallback."""
from common import *
import shutil
P18=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018'
MAX=REPO/'experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001'

def main():
 cfg=load(R/'config/PROTOCOL.json'); sources=[]; receipts=[]
 for g in cfg['groups']:
  dest=R/'inputs'/g;dest.mkdir(exist_ok=True)
  for p in (P18/'inputs'/g).iterdir():
   q=dest/p.name
   if not q.exists():q.symlink_to(p.resolve())
  conf=next(c for c in load(MAX/'config/FOUR_GROUP_INPUTS.json')if c['group']==g)
  for s in conf['sources']:
   if s['role']!='FIT' or s.get('evaluation_only'):continue
   root=Path(s['mesh']['path']).parent
   sources.append(dict(id='OLD018__'+s['id'],view_id=s['id'],group=g,video=s['video'],origin='018',root=str(root),obs=s['observation']['path'],mesh=s['mesh']['path'],source=str(root/'SOURCE.json'),target_cache=s['cache'],role='FIT'))
 for s in load(MAX/'metrics/HERO_INFERENCE_RESULTS.json'):
  if not s['success']or s['variant']!='GEOMETRIC3':continue
  root=MAX/'hero_fit'/s['id']
  sources.append(dict(id='MAX__'+s['id'],view_id=s['id'],group=s['group'],video=('PHOTO'if 'photo'in s['id']else s['id'].split('_')[1].removeprefix('v')),origin='MAX',root=str(root),obs=str(root/'OBS_TRUSTED.npz'),mesh=str(root/'TRUSTED_HERO.npz'),source=str(root/'SOURCE.json'),target_cache=None,role='FIT'))
 for s in sources:
  source=load(s['source']);s['pack']=source['pack'];s['parent_sha']=source.get('source_SHA',[p['sha256']for p in source.get('parent_RGB',[])])
  if source.get('target_SHA'):s['parent_sha']+=[source['target_SHA']]
  elif s['target_cache']:
   v=next(x for x in getcase(s['group'])['views']if x['id']==s['view_id']);s['parent_sha']+=[v['RGB_sha']]
  for k in ['obs','mesh','source','pack']:
   receipts.append(dict(source_id=s['id'],kind=k,**asset(s[k])))
  ev=Path(s['root'])/'FACE_EVIDENCE.npz';a=np.load(ev);states=a['state'];area=a['area_mm2'];comp=a['component'];ids=np.unique(comp[states==0]);small=0;small_area=0
  for i in ids:
   ii=(comp==i)&(states==0)
   if ii.sum()<8:small+=1;small_area+=area[ii].sum()
  s['cleaning']=dict(TRUSTED_N=int((states==0).sum()),UNCERTAIN_N=int((states==1).sum()),REJECTED_N=int((states==2).sum()),UNKNOWN_N=int((states==3).sum()),trusted_area_mm2=float(area[states==0].sum()),trusted_components=len(ids),small_components_faces_lt8=small,small_component_area_mm2=float(small_area),additional_removed_faces=0,reason='retain all existing TRUSTED; tiny-component audit only')
 sources.sort(key=lambda x:x['id']);save('config/SOURCES.json',sources);save('provenance/INPUT_SHA.json',receipts);table('metrics/CLEANING_AUDIT.csv',[dict(source=s['id'],group=s['group'],**s['cleaning'])for s in sources]);save('provenance/PREREGISTRATION.json',dict(epoch=time.time(),protocol=asset(R/'config/PROTOCOL.json'),source_list=asset(R/'config/SOURCES.json'),code=[asset(p)for p in (R/'code').glob('*.py')],GT_used=False));print('SOURCES',len(sources),{g:sum(s['group']==g for s in sources)for g in cfg['groups']},flush=True)
if __name__=='__main__':main()
