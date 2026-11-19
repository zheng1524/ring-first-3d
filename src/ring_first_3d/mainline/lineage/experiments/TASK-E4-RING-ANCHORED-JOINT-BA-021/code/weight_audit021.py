"""Actual observation mass, not just declared video/direction normalization."""
from common import *
import collections

def main():
 rows=[];tracks=[]
 for scope in ['CROSS','NEGATIVE']:
  data=load(R/'observations'/(scope+'_COMMON_TRACKS.json'));sums=collections.defaultdict(lambda:dict(N=0,mass=0.,tracks=set(),views=set()));tests=[]
  for t in data:
   for side in [0,1]:
    obs=[o for o in t['observations']if o['side']==side];mass=sum(o['weight']for o in obs);blocks=collections.defaultdict(float)
    for o in obs:
     k=(side,o['direction_block']);sums[k]['N']+=1;sums[k]['mass']+=o['weight']*t['track_weight'];sums[k]['tracks'].add(t['track']);sums[k]['views'].add(o['view']);blocks[o['direction_block']]+=o['weight']
    assert abs(mass-.5)<1e-12 and max(blocks.values())-min(blocks.values())<1e-12
    tracks.append(dict(scope=scope,track=t['track'],side=side,actual_observations_N=len(obs),observed_direction_blocks_N=len(blocks),actual_weight_before_equal_track_mass=mass,track_weight=t['track_weight'],weight_by_observed_direction=dict(blocks)))
  for(side,block),v in sums.items():rows.append(dict(scope=scope,side=side,direction_block=block,actual_observation_N=v['N'],actual_tracks_N=len(v['tracks']),actual_views_N=len(v['views']),normalized_objective_mass=v['mass']))
  assert abs(sum(t['track_weight']for t in data)-1)<1e-12
 save('metrics/ACTUAL_VIDEO_DIRECTION_WEIGHT_AUDIT.json',rows);table('metrics/ACTUAL_VIDEO_DIRECTION_WEIGHT_AUDIT.csv',rows);save('metrics/ACTUAL_PER_TRACK_WEIGHT_AUDIT.json',tracks);table('metrics/ACTUAL_PER_TRACK_WEIGHT_AUDIT.csv',tracks);save('provenance/WEIGHT_NORMALIZATION_CHECK.json',dict(passed=True,scope='all actual CROSS and NEGATIVE FIT observations; video0.5 each within every track, equal observed blocks, track/category sum1',no_missing_direction_invented=True));print('WEIGHT_AUDIT021_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
