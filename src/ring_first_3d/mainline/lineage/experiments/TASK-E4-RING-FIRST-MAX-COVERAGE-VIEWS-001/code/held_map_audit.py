from register import *
def main():
 vv=load(N/'config/G01_FINAL_CAMERA_POOL.json');rows=[];out=[];changes=[]
 for v in vv:
  if v['role']=='HOLDOUT':out.append(v);continue
  q=qualification(v,np.array(v['C'])if v.get('C')is not None else None);rows.append(dict(id=v['id'],video=v['video'],old_held=v.get('RGB_evaluation',{}).get('FEATURE_HELD'),correct_held=q.get('RGB_evaluation',{}).get('FEATURE_HELD'),old_eligible=v['formal'],correct_eligible=q['formal'],scope='005 noncommonmap followsH;cross-held004XYZ fixed'))
  if v['formal']!=q['formal']:changes.append(v['id'])
  out.append(v|q)
 save('config/G01_FINAL_CAMERA_POOL_CORRECTED_HELD_MAP.json',out);table('metrics/G01_HELD_MAP_GAUGE_CORRECTION.csv',rows);save('metrics/G01_HELD_MAP_GAUGE_CORRECTION.json',dict(membership_changes=changes,poses_changed=0,before_HERO=True));freeze('provenance/G01_CORRECTED_HELD_MAP_QUALITY.json',[N/'config/G01_FINAL_CAMERA_POOL_CORRECTED_HELD_MAP.json',N/'metrics/G01_HELD_MAP_GAUGE_CORRECTION.json'],pose_selection_unchanged=True,GT=False);print('HELD_MAP_CORRECTED','membership changes',changes,flush=True)
if __name__=='__main__':main()
