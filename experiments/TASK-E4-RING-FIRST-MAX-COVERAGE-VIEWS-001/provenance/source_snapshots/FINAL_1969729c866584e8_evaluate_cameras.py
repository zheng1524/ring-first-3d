from register import *
from coverage import direction_stats

def epipolar(Ca,Cb,u,v):
 D=np.linalg.inv(Cb)@Ca;t=D[:3,3];sk=np.array([[0,-t[2],t[1]],[t[2],0,-t[0]],[-t[1],t[0],0]]);F=np.linalg.inv(K0).T@sk@D[:3,:3]@np.linalg.inv(K0);p=np.r_[u,1.];q=np.r_[v,1.];return float(abs(q@F@p)/max(np.sqrt(np.sum((F@p)[:2]**2)+np.sum((F.T@q)[:2]**2)),1e-12))
def main():
 rows=[];sources=[];directions=[];scope=[];photos=[]
 for g in GROUPS:
  vv=load(camera_file(g));vd={v['id']:v for v in vv};byalias={a:v for v in vv for a in [v['id']]+v.get('aliases',[])};ext='_NATIVE005'if g=='G01'else'';joint=load(N/'registration'/g/('JOINT_FULL6'+ext+'_FINAL.json'));shared=load(N/'registration'/g/('SHARED_SE3'+ext+'_FINAL.json'));initial={v['id']:v.get('C')for v in load(N/'config'/(g+'_INITIAL_CAMERAS.json'))};rrs={}
  for v in vv:
   if v['role']=='HOLDOUT' or v.get('C')is None:continue
   path=Path(v.get('rgb_geometry_path',N/'inputs'/v['id']/'RGB_GEOMETRY.json'))
   if path.exists():rrs[v['id']]=load(path)
  for tag,pred in [('ORIGINAL_RF_RGB',initial),('SHARED_SE3',shared['poses']),('JOINT_FULL6',joint['poses'])]:
   for v in vv:
    C=pred.get(v['id']);
    if C is None or v['role']=='HOLDOUT':continue
    C=np.array(C);base=np.array(initial[v['id']])if initial.get(v['id'])is not None else C;ob=observe(v);rec=dict(group=g,id=v['id'],video=v['video'],method=tag,role=v['role'],actual_source=v['input_origin'],physical=physical(v,C,ob),center_delta_mm=float(np.linalg.norm(C[:3,3]-base[:3,3])),rotation_delta_deg=float(np.degrees(Rotation.from_matrix(C[:3,:3]@base[:3,:3].T).magnitude())),unit='mm',RGB=None)
    if v['id']in rrs:
     rr=rrs[v['id']];rec['RGB']=errors(v,C,rr);epis=[];cross=[]
     for m in rr['matches']:
      if m['role']!='FEATURE_HELD':continue
      vid=m.get('native_map','004');uid=m.get('native_landmark',m['landmark']);label=g+'_'+vid;obs=load(G/'landmarks'/(label+'_OBSERVATIONS.json'))
      if uid>=len(obs):continue
      for o in obs[uid]['observations']:
       ref=byalias.get(o['view']);
       if ref is None or ref['id']==v['id']or ref['role']=='HOLDOUT':continue
       Ca=pred.get(ref['id']);
       if Ca is None:continue
       e=epipolar(np.array(Ca),C,o['uv'],m['uv']);epis.append(e)
       if ref['video']!=v['video']:cross.append(e)
       break
     rec['map_held_2D2D_Sampson_px']=stats(epis);rec['cross_video_held_2D2D_Sampson_px']=stats(cross)
    rows.append(rec)
  # No preset latestwinner. Preserve named historical G01 candidates on their original cameras.
  if g=='G01':
   hist=load(P/'config/HISTORICAL_CANDIDATES.json');oldU={v['id']:v for v in load(U/'config/VIEWS.json')}
   for h in hist:
    if h['tag']not in ['HISTORICAL_FULL_RoMa','HISTORICAL_FULL_LightGlue']:continue
    for v in vv:
     if v['role']!='FIT'or v['video']!='005':continue
     ov=oldU.get(v.get('initial_canonical_id'))
     if not ov:continue
     C=np.array(h['T'])@np.array(ov['RF_native']);rows.append(dict(group=g,id=v['id'],video='005',method=h['tag'],role='FIT',physical=physical(v,C,observe(v)),source=asset(P/'config/HISTORICAL_CANDIDATES.json'),unit='mm',RGB=None))
  for s in ['004','005','PHOTO']:
   a=[v for v in vv if v['video']==s];formal=[v for v in a if v['formal']];numeric=[v for v in a if v.get('C')is not None];sources.append(dict(group=g,source=s,raw_frame_N=next((x['frame_count']for x in load(N/'config/SOURCE_DISCOVERY.json')if x['group']==g and x['video']==s),3 if s=='PHOTO'else None),processed_candidates_N=len(a),unprocessed_raw_status='UNKNOWNnotmaskednotposed;complete timelineexists',Ring_present_in_candidates_N=sum((v.get('ring_pixels')or 0)>0 for v in a),numeric_pose_N=len(numeric),Ring5DoF_N=sum(v.get('original_ring5_N',0)>0 for v in a),RGB_registerable_N=sum(v.get('RGB_inliers_N',0)>=6 for v in a),validated_conditional_N=len(formal),HOLDOUT_N=sum(v['role']=='HOLDOUT'for v in a),failed_or_exploratory_N=sum(not v['formal']and v['role']!='HOLDOUT'for v in a),failure_reasons=dict(collections.Counter(r for v in a for r in v.get('qualification_reasons',[]))),no_absolute_camera_GT=True))
   directions.append(dict(group=g,source=s,kind='formal',**direction_stats(formal)))
  directions.append(dict(group=g,source='ALL',kind='formal',**direction_stats([v for v in vv if v['formal']])));directions.append(dict(group=g,source='ALL',kind='numeric_RGB_exploratory',**direction_stats([v for v in vv if v.get('C')is not None and v.get('RGB_inliers_N',0)>=6])))
  for mode,reg in [('SHARED_SE3',shared),('JOINT_FULL6',joint)]:scope.append(dict(group=g,mode=mode,camera_pool_N=len(vv),actual_optimized_subset_N=len(reg['selected']),shared_XYZ_N=reg['sharedXYZ_N'],actual_RGB_observation_N=reg['realRGB_N'],outer_accepted=reg['accepted'],initial_objective=reg['initial_objective'],final_objective=reg['final_objective'],seconds=reg['seconds'],scale=1.,H=reg['source_H'],physical=reg['physical']))
  for v in vv:
   if v['video']=='PHOTO':photos.append(v)
 table('metrics/ALL_POSE_CANDIDATE_COMPARISONS.csv',rows);save('metrics/ALL_POSE_CANDIDATE_COMPARISONS.json',rows);table('metrics/SOURCE_CAMERA_COUNTS.csv',sources);save('metrics/SOURCE_CAMERA_COUNTS.json',sources);table('metrics/CANDIDATE_DIRECTION_COVERAGE.csv',directions);save('metrics/CANDIDATE_DIRECTION_COVERAGE.json',directions);save('metrics/ACTUAL_CERES_SCOPE.json',scope);table('metrics/ACTUAL_CERES_SCOPE.csv',scope);save('metrics/ALL12_PHOTO_RESULTS.json',photos)
 old=Q/'config/G01_PHOTO_POSES.json';save('metrics/G01_HISTORICAL_PHOTO_CANDIDATES.json',dict(source=asset(old),poses=load(old),role='namedhistoryonly;notselectedbyHOLDOUT;notcopiedasnewphotoestimates'))
 print('ALL_CAMERA_EVALUATIONS_DONE',len(rows),flush=True)
if __name__=='__main__':main()
