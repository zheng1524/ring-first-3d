"""Delivery checks with full denominators, preserved M4 and immutable upstream file hashes."""
from core import *
from geometry import *
def main():
 files={};summary=[];oldT=0;video_total=0;source_total=0;completed=0;failures=[];phase_checks=0;clip_checks=0
 groups=read(M4/'GROUP_INDEX.json')['groups'];assert len(groups)==39
 for item in groups:
  g=item['group'];a=read(T/'runs/inputs'/g/'AUDIT.json');asset(item['path'],item['sha256']);old=read(item['path']);video_total+=len(a['all_video_states']);source_total+=len(a['sources'])
  for v in old['videos']:assert np.array_equal(a['transforms'][v['case']],v['T_local_to_common']);oldT+=1
  for x in a['files']:files[x['path']]=x['sha256']
  root=T/'runs/results'/g;group=read(root/'GROUP_RESULT.json');failures+=group['failures'];assert sorted(group['all_video_cases'])==sorted(s['case']for s in a['all_video_states'])
  for r in group['results']:
   conf=root/r['configuration'];completed+=1;ph=read(conf/'STAGES.json');base=read(conf/'BASE.json');body=np.load(conf/'BODY.npz');uncut=np.load(conf/'FINAL_UNCUT.npz');ev=read(conf/'EVALUATION.json')
   for stage in ph:
    assert stage['objective_after_theta']<=stage['objective_before']+1e-8;assert stage['objective_after']<=stage['objective_after_theta']+1e-8;phase_checks+=1
   for item2 in read(conf/'COMPLETE.json')['files']:asset(item2['path'],item2['sha256'])
   for name in ['FIGURES.json','VISIBILITY.json']:
    for item2 in read(conf/name)['files']:asset(item2['path'],item2['sha256'])
   visibility=np.load(conf/'VISIBILITY.npz');assert visibility['visible_model_faces_by_frame'].shape[1]==len(body['F_solid']);assert np.array_equal(visibility['inferred_base_faces'],body['inferred_base_faces'])
   assert all(abs(x['b_mm'])<=read(T/'config.json')['bias_bound_mm']+1e-9 for x in r['bias'])
   identities=[]
   for p in r['source_indices']:
    idx=read(p);assert idx['case']in r['videos'];identities+=idx['sources'];assert sum(f['role']=='FIT'for f in idx['frames'])==read(T/'config.json')['frames_per_video']
    for source in idx['sources']:
     for original in source['source_files']:files[original['path']]=original['sha256']
    for f in idx['frames']:
     for key in ['RGB','Mask','DXY','observations_2D']:asset(f[key]['path'],f[key]['sha256'])
   assert sorted(s['source_id']for s in identities)==sorted(x['source_id']for x in r['bias'])
   if r['configuration']!='JOINT':assert len(r['videos'])==1
   if base.get('source_ids'):assert set(base['source_ids'])<=set(s['source_id']for s in identities)
   for r0,rf in zip(ev['initial']['depth'],ev['final']['depth']):assert r0['source_id']==rf['source_id']and r0['fixed_N']==rf['fixed_N'];assert rf['valid_N']+rf['invalid_N']==rf['fixed_N']
   if r['base_applied']:
    ids=body['original_vertex_ID'];assert np.array_equal(body['V'][ids>=0],uncut['V'][ids[ids>=0]]);assert (body['V']@np.array(base['plane'][:3])+base['plane'][3]>=-1e-7).all();assert (body['original_face_ID'][body['inferred_base_faces']]==-1).all();clip_checks+=1
   summary.append(dict(group=g,configuration=r['configuration'],status=r['status'],videos=len(r['videos']),sources=r['source_N'],base_status=r['base_status'],base_applied=r['base_applied'],input_kind=r['input_kind']))
 for p,h in files.items():asset(p,h)
 assert video_total==79 and oldT==62 and source_total==1153
 receipt=dict(groups=len(groups),all_videos=video_total,old_transforms_identical=oldT,original_HERO_sources=source_total,completed_configurations=completed,failures=failures,upstream_files_rehashed=len(files),monotone_stage_steps=phase_checks,exact_clip_checks=clip_checks,summary=summary,config_sha256=sha(T/'config.json'),code_key=code_key(),real_GT='NOT_EVALUABLE')
 save(T/'evidence/FINAL_VERIFICATION.json',receipt);print(json.dumps({k:v for k,v in receipt.items()if k not in ['summary']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
