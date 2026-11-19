"""Exact cross-method common/gained/lost native HERO observations and pooled tails."""
from geometry021 import *
from eval021 import METHODS

def main():
 wait_freeze();ss=load(R/'config/HERO_EVALUATION_SOURCES.json');data=[]
 for s in ss:
  a=dict(np.load(s['observation']['path']));grid=np.full(tuple(a['native_shape']),np.nan);grid[a['uv'][:,1],a['uv'][:,0]]=a['z'];data.append(s|dict(obs=a,grid=grid))
 rv=np.load(R/'inputs/G01/RING.npz');cad=scene(rv['V'],rv['F']);trans={}
 for n in METHODS:
  H=np.asarray(load(R/'results'/(n+'.json'))['T']);trans[n]={s['id']:dict(X=s['obs']['X']@H[:3,:3].T+H[:3,3]if s['video']=='005'else s['obs']['X'],C=H@s['obs']['T']if s['video']=='005'else s['obs']['T'])for s in data}
 comparisons=[('B0_RoMa','B2'),('B1','B2'),('B2','B3'),('B0_020_R3','B2'),('B0_020_MASK','B3')];known={n:[]for n in METHODS};allcommon={n:[]for n in METHODS};acc={p:dict(common_N=0,gained_N=0,lost_N=0,a=[],b=[],g=[],l=[])for p in comparisons};pairrows=[];N=0;allN=0
 out=R/'evaluation/HERO_common_ids';out.mkdir(exist_ok=True)
 for a in data:
  for b in data:
   if a['video']==b['video']:continue
   q={n:visibility_query(trans[n][a['id']]['X'],trans[n][b['id']]['C'],b['obs']['K'],b['grid'],cad)for n in METHODS};common=np.logical_and.reduce([x['known']for x in q.values()]);N+=len(common);allN+=int(common.sum());arrays=dict(pixel_id=a['obs']['pixel_id'],all9_common=common);pairrows.append(dict(source=a['id'],target=b['id'],fixed_original_pixel_N=len(common),all9_common_N=int(common.sum())))
   for n in METHODS:
    x=q[n];known[n].append(x['dz'][x['known']]);allcommon[n].append(x['dz'][common]);arrays[n+'_known']=x['known'];arrays[n+'_dz_mm']=x['dz'].astype(np.float32)
   for p in comparisons:
    x,y=(q[n]for n in p);co=x['known']&y['known'];ga=~x['known']&y['known'];lo=x['known']&~y['known'];t=acc[p];t['common_N']+=int(co.sum());t['gained_N']+=int(ga.sum());t['lost_N']+=int(lo.sum());t['a'].append(x['dz'][co]);t['b'].append(y['dz'][co]);t['g'].append(y['dz'][ga]);t['l'].append(x['dz'][lo])
   np.savez_compressed(out/(a['id']+'__'+b['id']+'.npz'),**arrays)
  print('HERO_COMMON021_SOURCE',a['id'],flush=True)
 rows=[]
 for n in METHODS:rows.append(dict(method=n,fixed_source_target_denominator=N,known_error_mm=stats(np.concatenate(known[n])),all9_common_N=allN,all9_common_fraction_fixed=allN/N,all9_common_error_mm=stats(np.concatenate(allcommon[n])),source_target_repeated_observations_not_independent=True,legacy020_visibility_unchanged=True))
 changes=[]
 for(a,b),t in acc.items():changes.append(dict(method_before=a,method_after=b,fixed_source_target_denominator=N,common_N=t['common_N'],gained_N=t['gained_N'],lost_N=t['lost_N'],common_before_error_mm=stats(np.concatenate(t['a'])),common_after_error_mm=stats(np.concatenate(t['b'])),gained_after_error_mm=stats(np.concatenate(t['g'])),lost_before_error_mm=stats(np.concatenate(t['l'])),legacy_comparable_includes_deeper_not_physical_wrong_surface=True))
 save('metrics/HERO_EXACT_CROSS_METHOD_COMMON.json',rows);table('metrics/HERO_EXACT_CROSS_METHOD_COMMON.csv',rows);save('metrics/HERO_EXACT_COMMON_GAINED_LOST.json',changes);table('metrics/HERO_EXACT_COMMON_GAINED_LOST.csv',changes);save('metrics/HERO_ALL9_COMMON_PER_PAIR.json',pairrows);table('metrics/HERO_ALL9_COMMON_PER_PAIR.csv',pairrows);save('runtime/HERO_CROSS_METHOD_COMMON_COMPLETE.json',dict(epoch=time.time(),methods=METHODS,fixed_N=N,all9_common_N=allN,frozen_poses_unchanged=True));print('HERO_COMMON021_COMPLETE',N,allN,flush=True)
if __name__=='__main__':main()
