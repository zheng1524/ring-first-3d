"""Reuse021 independent evaluation ONLY after quick candidates freeze; task-local outputs."""
from qcommon import *
import evaluate020 as ev
from geometry021 import visibility_query

def main():
 while not(Q/'provenance/SOLVER_CANDIDATES_FROZEN.json').exists():time.sleep(5)
 for a in load(Q/'provenance/SOLVER_CANDIDATES_FROZEN.json')['files']:assert sha(a['path'])==a['sha256']
 methods=[]
 for i,arm in enumerate(['B1','B2','B3'],1):
  old=load(P/'results'/(arm+'.json'));new=load(Q/'results'/arm/'FINAL.json');methods.extend([dict(method='A0_'+arm,T=old['T']),dict(method='A'+str(i),T=new['T'])]);qsave('results/A0_'+arm+'.json',dict(T=old['T'],static=True,source=asset(P/'results'/(arm+'.json'))));qsave('results/A'+str(i)+'.json',new)
 for folder in ['inputs','features','landmarks','matches','ring','ring_evidence_v2']:
  dest=Q/folder
  if folder=='inputs':
   (dest/'G01').symlink_to((P/'inputs/G01').resolve(),target_is_directory=True)if not(dest/'G01').exists()else None
  elif not dest.exists():dest.symlink_to((P/folder).resolve(),target_is_directory=True)
 for n in ['VIEWS.json','HERO_EVALUATION_SOURCES.json','NEGATIVE_SPLIT.json']:(Q/'config'/n).write_bytes((P/'config'/n).read_bytes())
 qsave('results/R0.json',load(P/'results/B0_RoMa.json'))
 ev.R=Q;ev.save=qsave;ev.table=qtable;ev.methods=lambda:methods;ev.body_ring_eval();ev.hero_eval()
 # Exact native common/gained/lost subsets, no mean-comparison across changed populations.
 ss=load(P/'config/HERO_EVALUATION_SOURCES.json');sources=[];rv=np.load(P/'inputs/G01/RING.npz');cad=scene(rv['V'],rv['F'])
 for s in ss:
  a=dict(np.load(s['observation']['path']));grid=np.full(tuple(a['native_shape']),np.nan);grid[a['uv'][:,1],a['uv'][:,0]]=a['z'];sources.append(s|dict(obs=a,grid=grid))
 records=[]
 for i,arm in enumerate(['B1','B2','B3'],1):
  old=np.asarray(load(P/'results'/(arm+'.json'))['T']);new=np.asarray(load(Q/'results'/arm/'FINAL.json')['T']);ca=[];cb=[];ge=[];lo=[];N=0;ng=0;nl=0;nc=0
  for a in sources:
   for b in sources:
    if a['video']==b['video']:continue
    pair=[]
    for H in [old,new]:
     A=H if a['video']=='005'else np.eye(4);B=H if b['video']=='005'else np.eye(4);pair.append(visibility_query(a['obs']['X']@A[:3,:3].T+A[:3,3],B@b['obs']['T'],b['obs']['K'],b['grid'],cad))
    x,y=pair;co=x['known']&y['known'];g=~x['known']&y['known'];l=x['known']&~y['known'];N+=len(co);nc+=int(co.sum());ng+=int(g.sum());nl+=int(l.sum());ca.extend(x['dz'][co]);cb.extend(y['dz'][co]);ge.extend(y['dz'][g]);lo.extend(x['dz'][l])
  records.append(dict(method='A'+str(i),baseline='A0_'+arm,fixed_N=N,common_N=nc,gained_N=ng,lost_N=nl,common_before_mm=stats(ca),common_after_mm=stats(cb),gained_mm=stats(ge),lost_mm=stats(lo),includes_deeper_as020_proxy_not_GT=True))
 qsave('metrics/HERO_EXACT_COMMON_GAINED_LOST.json',records);qtable('metrics/HERO_EXACT_COMMON_GAINED_LOST.csv',records);qsave('runtime/SOLVER_EVALUATION_COMPLETE.json',dict(epoch=time.time(),source=asset(Path(__file__)),no_feedback_to_optimization=True));print('QUICK_SOLVER_EVALUATION_COMPLETE',flush=True)
if __name__=='__main__':main()
