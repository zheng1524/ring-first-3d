"""Full frozen-identity, interface and regression verification; no new fitting."""
from context import *
from ring_first_3d.sim.geometry import transform
import collections,re,ast

def main():
 inventory=read(T/'config/INVENTORY.json');verify(read(T/'evidence/UPSTREAM_TERMINAL.json')['files']);rows=[];retained={};total=0;usedcases=set();statuses=collections.Counter();reused=collections.Counter();domains=0
 for row in inventory['groups']:
  g=row['group'];out=group_out(g);asset,reg=verify_registration(out);group=read(out/'GROUP.json');assert group['registration_sha256']==sha(out/'REGISTRATION.json');assert len(group['sources'])==len(asset['sources']);assert {s['source_id']for s in group['sources']}=={s['source_id']for s in asset['sources']};assert len({s['source_id']for s in group['sources']})==len(group['sources']);retained.update({r['path']:r for r in asset['files']});statuses[reg['status']]+=1
  consumer=read(out/'CONSUMER_CHECK.json');assert consumer['sources_loaded']==len(asset['sources'])and consumer['max_camera_xyz_and_axial_z_difference_mm']<1e-7
  for v in asset['all_video_states']:
   statefile=FULL/'states'/(v['case']+'.json');assert read(statefile)==v['upstream'],'TERMINAL_VIDEO_STATE_DRIFT';retained[str(statefile)]=dict(path=str(statefile),sha256=sha(statefile),bytes=statefile.stat().st_size)
  for v in group['videos']:
   usedcases.add(v['case']);assert v['camera_coordinate_frame']==v['landmark_coordinate_frame']=='COMMON';local=np.load(v['local_camera']);source_video=next(x for x in asset['videos']if x['case']==v['case']);model=read(Path(source_video['run'])/'PLAN_FROZEN.json')['model_sha256'];assert all(s['model_sha256']==model for s in asset['sources']if s['case']==v['case']);glob=np.load(v['common_cameras']);assert sha(v['common_cameras'])==v['common_cameras_sha256'];tv=np.array(v['T_local_to_common']);np.testing.assert_allclose(glob['c2w'],tv@local['c2w'],atol=1e-12);np.testing.assert_array_equal(glob['K'],local['K']);np.testing.assert_array_equal(glob['ids'],local['ids']);np.testing.assert_allclose(glob['points'],transform(local['points'],tv),atol=1e-12,equal_nan=True);np.testing.assert_array_equal(glob['point_track_ids'],local['point_track_ids'])
  index=read(out/'CLEAN_INDEX.json');assert len(index)==len(asset['sources']);old=prior_run()/g
  for s,r in zip(group['sources'],index):
   assert r['status']=='COMPLETE'and s['connected'];assert sha(r['selection_path'])==r['selection_sha256'];assert sha(r['raw_domain'])==r['raw_domain_sha256'];sel=np.load(r['selection_path']);assert np.array_equal(sel['trusted_original_face_id'],np.flatnonzero(sel['state']==0));assert len(sel['state'])==r['raw_faces'];assert r['common_faces_additional_coordinate_change_mm']==0;reused[r['origin']]+=1;total+=1
   if g in CFG['regression_groups']:
    oldindex=read(old/'CLEAN_INDEX.json');prior=next(q for q in oldindex if q['source']['case']==s['case']and q['source']['tag']==s['tag']);rel=prior['raw_domain'].split('/runs/R1_001/',1)[1];q=T/'runtime/regression/runs/R1_001'/rel;a=np.load(r['raw_domain']);b=np.load(q);assert np.array_equal(a['original_face_id'],b['original_face_id'])and np.array_equal(a['bary'],b['bary']);domains+=1
  if g in CFG['regression_groups']:
   prior=read(old/'PREDICTIONS.json')['M4']['T'];assert np.max(abs(np.array(prior)-reg['edges'][0]['results']['M4']['T']))<1e-12
  if reg['edges']:
   tr=np.load(out/'tracks/observations/tracks005.npz');assert not np.any(tr['held'][reg['used_FIT_global_track_ids']]);assert np.array_equal(np.flatnonzero(tr['held']),reg['global_held_track_ids'])
   for e in reg['edges']:verify(e['files'])
  review=read(out/'REVIEW_COMPLETE.json')
  if not review.get('no_output'):verify(review['images'])
  rows.append(dict(group=g,sources=len(asset['sources']),input_records=len(asset['files']),status=reg['status'],max_camera_xyz_difference_mm=consumer['max_camera_xyz_and_axial_z_difference_mm']))
 for f in (T/'visuals').rglob('*.html'):
  for href in re.findall(r'(?:href|src)=[\"\x27]([^\"\x27]+)',f.read_text()):
   if '://'not in href and not href.startswith('#'):assert(f.parent/href.split('#')[0]).exists(),(f,href)
 for f in (T/'code').glob('*.py'):ast.parse(f.read_text())
 expected=inventory['progress'];assert len(rows)==expected['groups_total']==39 and len(usedcases)==expected['videos_with_output']==62 and total==expected['native_success']==1153;assert sum(r['videos']for r in inventory['groups'])==79
 save(T/'evidence/FINAL_VERIFICATION.json',dict(groups=rows,group_status=dict(statuses),output_videos=len(usedcases),sources=total,unique_input_files=len(retained),input_records=sum(r['input_records']for r in rows),six_group_raw_domains_identical=domains,six_group_T_identical=True,clean_origins=dict(reused),all_camera_landmarks_transformed_once=True,all_held_split_preserved=True,all_html_links_valid=True,all_code_syntax=True,resource=resource(),upstream_mutated=False,body_fitting_started=False))
 save(T/'evidence/RETAIN_DEPENDENCIES.json',dict(inputs=list(retained.values()),pinned_code=PINS,task_output='runs/FULL_001/groups + GROUP_INDEX.json; archive protected; not regenerable without declared original inputs',upstream_terminal=read(T/'evidence/UPSTREAM_TERMINAL.json')))
 print('FINAL VERIFIED',len(rows),len(usedcases),total,'inputs',len(retained),'regression domains',domains,flush=True)
if __name__=='__main__':main()
