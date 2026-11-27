from context import *
import ast,re,shutil
from ring_first_3d.sim.geometry import transform

def main():
 checked=0;groups=[];deps={};allchanges={'A':0,'B':0}
 for row in read(T/'config/SELECTION.json')['groups']:
  g=row['group'];out=RUN/'real'/g;asset=read(T/'config'/g/'ASSETS.json');verify(asset['files']);checked+=len(asset['files']);deps.update({r['path']:r['sha256']for r in asset['files']});fr=read(out/'PREDICTION_FREEZE.json');assert sha(out/'PREDICTIONS.json')==fr['predictions_sha256'];verify([dict(path=p,sha256=h)for p,h in fr['inputs'].items()]);pred=read(out/'PREDICTIONS.json');replay=read(out/'DEPENDENCY_REPLAY.json')['results'];index=read(out/'CLEAN_INDEX.json');assert len(index)==len(asset['sources']);assert not any(r.get('status')=='MISSING'for r in index);verify(read(out/'DOMAIN_FREEZE.json')['files']);ev=read(out/'EVALUATION.json');assert len(read(out/'FIT_LOO.json'))==6
  for method,r in pred.items():
   np.testing.assert_allclose(r['T'],replay[method]['T'],rtol=0,atol=1e-12);T0=np.array(r['T']);np.testing.assert_allclose(T0[:3,:3].T@T0[:3,:3],np.eye(3),atol=1e-12);assert abs(np.linalg.det(T0[:3,:3])-1)<1e-12
   rows=read(out/'evaluation'/(method+'_HELD.json'));assert len(rows)==sum(ev['methods'][method]['bidir'][d]['N']for d in ['A_to_B','B_to_A'])
   for v in asset['videos']:
    local=np.load(v['camera']);globalcam=np.load(out/(method+'_CAMERAS_'+v['side']+'.npz'));expected=local['c2w']if v['side']=='A'else T0@local['c2w'];np.testing.assert_allclose(globalcam['c2w'],expected,atol=1e-12);assert np.array_equal(globalcam['K'],local['K']);assert np.array_equal(globalcam['ids'],local['ids'])
  for r in index:
   assert sha(r['selection_path'])==r['selection_sha256'];a=np.load(r['selection_path']);assert np.array_equal(a['trusted_original_face_id'],np.flatnonzero(a['state']==0));assert r['common_faces_additional_coordinate_change_mm']==0;comp=r['upstream_single_video_clean_comparison'];allchanges[r['source']['side']]+=comp.get('changed_faces',0)
   if comp.get('path'):deps[comp['path']]=comp['sha256']
  for html in (T/'visuals'/g).glob('*.html'):
   for link in re.findall(r'(?:src|href)="([^"]+)"',html.read_text()):assert (html.parent/link).exists(),link
  groups.append(dict(group=g,sources=len(index),input_records=len(asset['files']),all_T_camera_state_and_sample_checks_passed=True,held_tracks=ev['stages']['all_held_tracks'],two_sided_held=ev['methods']['M4']['bidir']['denominators']['two_sided_DLT_tracks']))
 g='GP_IIa_14.0mm_closed_R5_single_refY';out=RUN/'real'/g;primary=read(out/'CLEAN_INDEX.json');candidate=read(out/'CLEAN_INDEX_M4_CANDIDATE.json');assert len(primary)==len(candidate)==42
 for a,b in zip(primary,candidate):
  x=np.load(a['raw_domain']);y=np.load(b['raw_domain']);assert all(np.array_equal(x[k],y[k])for k in ['original_face_id','bary']);assert sha(b['selection_path'])==b['selection_sha256']
 for p in (T/'code').glob('*.py'):ast.parse(p.read_text())
 # Lightweight end snapshot; discovery only, no change to preselected cohort.
 progress=read(FULL/'PROGRESS.json');states=[]
 for p in (FULL/'states').glob('*.json'):
  r=read(p)
  if r.get('status')=='DONE'and r.get('native_success',0)>0 and r.get('renderable',0)>0:states.append(r)
 eligible={}
 for r in states:eligible.setdefault(r['group'],[]).append(r['case'])
 eligible={g:sorted(v)for g,v in eligible.items()if len(v)>=2};save(T/'evidence/R1_PROGRESS_AT_END.json',dict(progress_reference_only=progress,eligible_groups=eligible,new_since_initial=sorted(set(eligible)-set(read(T/'config/SELECTION.json')['eligible_groups'])),cohort_not_replaced=True))
 for p in [OLD/'code/solver2.py',OLD/'code/common2.py',OLD/'code/real2.py',OLD/'code/metrics2.py',OLD/'config/PROTOCOL.json',c.V001/'code/registration.py',c.V001/'config.json',V6/'track005.py',V6/'v6_common.py']:deps[str(p)]=sha(p)
 save(T/'evidence/RETAIN_DEPENDENCIES.json',dict(files=[dict(path=p,sha256=h)for p,h in deps.items()],policy='Keep exact selected R1 native meshes, native depths, camera/RGB/Mask, completed receipts and imported frozen code. Local unique downstream states/domains are protected in RUN_EVIDENCE.tar.gz. No upstream assets moved or deleted.'))
 save(T/'evidence/FINAL_VERIFICATION.json',dict(groups=groups,input_records_verified=checked,primary_sources=sum(r['sources']for r in groups),M4_candidate_sources=42,raw_domains_same_for_candidate=True,upstream_label_changes=allchanges,resource=resource(),source_syntax=True,html_links=True,upstream_process_mutations=False,body_fitting_started=False));print('FINAL VERIFIED',len(groups),sum(r['sources']for r in groups),checked,allchanges,resource(),flush=True)
if __name__=='__main__':main()
