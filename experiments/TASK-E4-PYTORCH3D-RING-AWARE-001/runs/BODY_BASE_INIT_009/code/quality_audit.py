from common import *
def main():
 gate=load('/home/liu/ring_first_3d_e3_sdf_multi/experiments/TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001/config/CAMERA_GATE_RESULTS.json');g={x['source']:x for x in gate['sources']};quality=[]
 for c in load(R/'config/CASE_LOCK.json'):
  for v in c['views']:
   rec=dict(case=c['name'],type=c['morphology'],source=v['id'],role=v['role'],input_status='FILES_READABLE_FRAME_POSE_UNIT_CHECK_PASSED',historical_qualification=v['qualification'],HERO_status=v['HERO_status'],admitted_by_integrity_not_Gate=True)
   if v['id']in g:rec.update(current_camera_diagnostics=g[v['id']])
   else:
    root=R/'new_input_pipeline/groups/G09'if c['name']=='G09'else Path('/home/liu/polyp_research/ring_anchor_3d/experiments/multigroup_ring_hero_visual_audit_v1/groups')/c['name'];p=root/'metrics/local_validation.json'
    if p.exists():
     a=load(p);ver=next(x for x in a['versions']if x['version']==a['primary']);idx=v.get('camera_index');rec['current_camera_diagnostics']=ver['per_frame'][idx]if idx is not None else'NO_EXACT_INDEX_DIAGNOSTIC'
   quality.append(rec)
 table('metrics/INPUT_AND_OBSERVATION_QUALITY.csv',quality);save('metrics/INPUT_AND_OBSERVATION_QUALITY.json',quality)
if __name__=='__main__':main()
