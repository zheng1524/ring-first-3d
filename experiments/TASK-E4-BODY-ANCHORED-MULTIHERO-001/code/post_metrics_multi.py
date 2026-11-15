"""Reproducible derived tables, local artifact SHA inventory and browser evidence."""
from common import *
def main():
 rows=[]
 for p in (R/'local_results').glob('*_CORRESPONDENCE.npz'):
  a=np.load(p);g,arm,source=p.stem.removesuffix('_CORRESPONDENCE').split('_',2)
  for st,label in enumerate(['MATCHED','UNEXPLAINED','CONFLICT','UNKNOWN']):
   mask=a['state']==st;rows.append(dict(group=g,arm=arm,source=source,state=label,fixed_N=len(mask),unit='mm',role='qualified_same_layer_distance'if st==0 else'diagnostic_only_not_correspondence_identity',**stats(a['distance_mm'][mask])))
 table('metrics/HERO_BODY_SURFACE_DISTANCE.csv',rows)
 scope=load(R/'config/SOURCES.json');save('assets_index/SOURCE_SCOPE_AUDIT.json',dict(primary_sources=len(scope),by_group={g:sum(s['group']==g for s in scope)for g in ['G01','G03','G05','G06']},by_origin={o:sum(s['origin']==o for s in scope)for o in ['018','MAX']},photographs=[s['id']for s in scope if s['video']=='PHOTO'],excluded='018 UPDATE_HOLDOUT remain evaluation; historical evaluation_only005 not promoted; one alternate MAX E4-support prediction outside primary GEOMETRIC3 scope',camera_admission='existing frozen conditional labels, not absolute calibration',additional_component_deletions=0,retained_TRUSTED_faces_ratio=1.))
 checks=[];params=[]
 for g in ['G01','G03','G05','G06']:
  p=R/'runtime'/(g+'_VIEWER_DOM.html');a=load(R/'assets_index'/(g+'_GLB_LAYERS.json'));text=p.read_text()if p.exists()else'';checks.append(dict(group=g,status='TESTED'if p.exists()else'MISSING_BROWSER_CAPTURE',loaded='data-loaded="true"'in text,checkboxes=text.count('type="checkbox"'),expected_mesh_layers=len(a['layers']),PASS='data-loaded="true"'in text and text.count('type="checkbox"')==len(a['layers']),local_GLB=a['path'],sha256=a['sha256']))
  for arm in ['B0','B1','B2','B3']:
   arr=np.load(R/'runs'/g/arm/'FINAL.npz');log=load(R/'metrics'/(g+'_'+arm+'_BIAS.json'))if arm!='B0'else[];h=load(R/'metrics'/(g+'_'+arm+'_ROUNDS.json'))if arm!='B0'else[];accepted_rounds={x['round']for x in h if x['accepted']}
   for sid,t in zip(arr['source_ids'],arr['theta']):
    matches=[x for x in log if x['source']==sid];committed=[x for x in matches if x['status']=='ACCEPTED'and x['round']in accepted_rounds];status='FIXED_NATIVE_NOT_ESTIMATED'if arm in ['B0','B2']else'CALIBRATION_COMMITTED'if committed else'INSUFFICIENT_CONSTRAINT'if matches and all(x['status']=='INSUFFICIENT_CONSTRAINT'for x in matches)else'NO_CALIBRATION_COMMITTED';params.append(dict(group=g,arm=arm,source=sid,status=status,applied_b_mm=t[0],applied_a_mm=t[1],applied_c_mm=t[2],estimated_b_mm=float(t[0])if committed else None,estimated_a_mm=float(t[1])if committed else None,estimated_c_mm=float(t[2])if committed else None,zero_identity_not_a_measured_zero=not bool(committed)))
 save('metrics/VIEWER_VALIDATION.json',checks);table('metrics/BIAS_PARAMETER_STATUS.csv',params)
 inventory=[]
 for folder in ['runs','local_results']:
  for p in (R/folder).rglob('*'):
   if p.is_file():inventory.append(dict(category=folder,**asset(p)))
 table('assets_index/LOCAL_ARTIFACTS.csv',inventory);save('assets_index/LOCAL_ARTIFACT_TOTALS.json',dict(files=len(inventory),bytes=sum(a['bytes']for a in inventory),local_only_includes='GLB, dense per-native correspondence and derived HERO; git tracks selected small Body states separately'))
 print('POST_METRICS',len(rows),'rows',len(inventory),'local files; viewer passes',sum(c['PASS']for c in checks),flush=True)
if __name__=='__main__':main()
