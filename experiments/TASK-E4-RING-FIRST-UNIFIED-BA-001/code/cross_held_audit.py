"""Independent cross-video 2D-2D held track residuals; no native005-map gauge ambiguity."""
from evaluate import *
import itertools
if __name__=='__main__':
 checkfreeze('provenance/ALL_FINAL_CAMERA_CANDIDATES_FROZEN_BEFORE_HERO.json');vs={v['id']:v for v in load(N/'config/VIEWS.json')};res=getresults();rows=[];summary=[]
 for method in ['B0','B1','B2','B3']:
  errors=[];ntr=0
  for t in load(N/'config/TRACKS.json'):
   if t['group']!='G01'or not t['cross_video']or t['role']!='TRACK_HELD':continue
   ntr+=1
   for a,b in itertools.product([o for o in t['observations']if o['video']=='004'],[o for o in t['observations']if o['video']=='005']):
    va,vb=vs[a['view']],vs[b['view']];e=epi(getpose(res,'G01',method,a['view']),getpose(res,'G01',method,b['view']),np.array(va['K']),np.array(vb['K']),a['uv'],b['uv']);errors.append(e);rows.append(dict(method=method,group='G01',track_id=t['track_id'],source=a['view'],target=b['view'],source_feature_id=a['feature_id'],target_feature_id=b['feature_id'],source_uv=a['uv'],target_uv=b['uv'],symmetric_normalized_epipolar_px=e,held_track=True,no_XYZ_or_HERO_used=True))
  summary.append(dict(method=method,group='G01',tracks_N=ntr,raw_2D_pair_N=len(errors),epipolar_px=stats(errors),two_directions_same_symmetric_scalar=True,not_absolute_GT=True))
 save('metrics/INDEPENDENT_CROSS_VIDEO_HELD_RGB.json',summary);table('metrics/INDEPENDENT_CROSS_VIDEO_HELD_RGB.csv',summary);table('metrics/INDEPENDENT_CROSS_VIDEO_HELD_RGB_PER_PAIR.csv',rows);print('CROSS_HELD347pairs4tracks_verified')
