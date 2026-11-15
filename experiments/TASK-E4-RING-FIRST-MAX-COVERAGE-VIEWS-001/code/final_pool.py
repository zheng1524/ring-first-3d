from context import *
def main():
 rows=[];protected=[];replays=[]
 for g in GROUPS:
  vv=load(camera_file(g));allheld=set();heldframe=set()
  for vid in ['004','005']:
   for v in load(P14/'new_views'/(g+'_v'+vid)/'inputs/ledger_all.json'):
    if 'HOLDOUT'in v['role']:allheld.add(v['id']);heldframe.add((vid,int(v['raw_frame'])));protected.append(dict(group=g,id=v['id'],video=vid,raw_frame=v['raw_frame'],origin='014_UPDATE_HOLDOUT'))
  r=load(N/'registration'/g/('JOINT_FULL6_NATIVE005_FINAL.json'if g=='G01'else'JOINT_FULL6_FINAL.json'));assert not(allheld&set(r['selected'])),('HOLDOUT_IN_SHARED_BA',g)
  for v in vv:
   if (v['video'],v.get('raw_frame'))in heldframe or v['id']in allheld or allheld.intersection(v.get('aliases',[])):
    if v['role']!='HOLDOUT':replays.append(dict(group=g,id=v['id'],old_numeric_local_diagnostic=True,used_as_shared_BA_observation=False,used_as_HERO_target_or_support=False,repair='restore original014holdoutstatus before anynewHERO; diagnostics retained;posevisualizationonly'))
    v.update(role='HOLDOUT',formal=False,HERO_target_eligible=False,status='PROTECTED_HOLDOUT',HOLDOUT_origin='existing014UPDATE_HOLDOUT+canonical')
   rows.append(v)
  save('config/'+g+'_FINAL_CAMERA_POOL.json',vv)
 save('provenance/PROTECTED_014_ALIAS_REPAIR.json',dict(additional_protected=protected,diagnostics_only=replays,none_used_shared_BA=True,none_used_HERO=True,old_standalone_local_photo_or_frame_diagnostics_not_independent_for_thoseimages=True));table('ALL_CAMERA_CANDIDATES.csv',rows);table('CAMERA_QUALITY_AND_UNCERTAINTY.csv',rows);save('config/FINAL_CAMERA_POOL.json',rows);freeze('provenance/ALL_CAMERAS_FROZEN_BEFORE_COVERAGE_HERO.json',[N/'config'/(g+'_FINAL_CAMERA_POOL.json')for g in GROUPS],GT=False,newHERO=False,protected014andcanonical=True);print('FINAL_CAMERAS',len(rows),'formal',sum(r['formal']for r in rows),flush=True)
if __name__=='__main__':main()
