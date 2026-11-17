"""Verify actual E/M evidence, fixed sources, rigid Meshes, GLB assets and final manifest."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,subprocess,re
import numpy as np
from ring_first_3d.policy.contracts import load_task,verify_task
from ring_first_3d.policy.artifacts import read_state,check_artifacts,heads
from ring_first_3d.policy.memory import registry
from ring_first_3d.synthetic.io import fetch
ROOT=Path.cwd();TD=ROOT/'experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001';RUN=TD/'runs/CONTOUR_004';task=load_task(TD/'TASK.yaml');state=read_state(RUN);identity=verify_task(task);assert state['accepted']and identity['freeze_sha256']==state['freeze_sha256'];check_artifacts(RUN,state);registry(TD/'FAILURE_REGISTRY.json');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hh=heads(RUN,state);assert len(hh)==13 and all(r['status']=='PASS'for r in hh.values());reg=hh['contour_regression']['payload'];assert reg['tests']==157 and reg['baseline_tests']==35 and not reg['errors']and not reg['failures'];lock=json.loads(Path(task['inita']['assets']['code_lock']['path']).read_text());source=json.loads(Path(task['inita']['assets']['sources']['path']).read_text())
for r in lock['files']:
 assert sha(Path(r['path']))==r['sha256'];raw=subprocess.check_output(['git','show',r['commit']+':'+r['git_path']]);assert hashlib.sha256(raw).hexdigest()==r['sha256']
# Trainer imports parent legacy directory; verify both the executing files and all archived source receipts.
executing_legacy=ROOT/'experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/legacy015';expected={Path(r['path']).name:r['sha256']for r in lock['files']}
for name,digest in expected.items():assert sha(executing_legacy/name)==digest
for g in task['inita']['cases']:
 for arm in ['A2D','A3']:
  try:receipt=fetch(RUN,'G1_all_train',g+'/'+arm+'/provenance/'+g+'_OPT_START.json')
  except(KeyError,ValueError,OSError):continue
  data=json.loads(receipt.read_text());assert {r['name']:r['sha256']for r in data['files']}==expected
# No scientific code/TASK changes after the first run that reached scientific GT evaluation.
math_files=['src/ring_first_3d/contour_guided/correspondence.py','src/ring_first_3d/contour_guided/objective.py','src/ring_first_3d/contour_guided/hero.py','src/ring_first_3d/contour_guided/experiment.py','tools/research/_contour_train.py']
assert not subprocess.check_output(['git','diff','b72ec35a6bd4ee11df15ef6f648b7588cf03c7d1','HEAD','--',*math_files],text=True)
for old_run in(TD/'runs').glob('CONTOUR_*'):
 if(old_run/'FREEZE.json').is_file():assert json.loads((old_run/'FREEZE.json').read_text())['fingerprint']['task']==json.loads((RUN/'FREEZE.json').read_text())['fingerprint']['task']
rows=json.loads((TD/'visualization/BODY_SHAPE_METRICS.json').read_text())['rows'];src={r['case']:r for r in source['cases']};assert {r['case']for r in rows}==set(task['inita']['cases']);models=0;actualupdates=0;inactive=[]
for r in rows:
 if r['status']!='NUMERIC':continue
 g,a=r['case'],r['arm'];world=dict(np.load(TD/'visualization/meshes'/(g+'_'+a+'_WORLD.npz')));aligned=dict(np.load(TD/'visualization/meshes'/(g+'_'+a+'_ALIGNED.npz')));T=aligned['T'];assert np.allclose(T[:3,:3].T@T[:3,:3],np.eye(3),atol=1e-7)and np.linalg.det(T[:3,:3])>.999999;np.testing.assert_allclose(aligned['V'],world['V']@T[:3,:3].T+T[:3,3],atol=1e-10);np.testing.assert_array_equal(world['F'],aligned['F']);np.testing.assert_array_equal(world['F_solid'],aligned['F_solid']);assert sha(fetch(RUN,'G1_all_train',g+'/'+a+'_WORLD.npz'))==r['world_prediction_sha256'];initial=dict(np.load(src[g]['resolved013_initial']['path']));np.testing.assert_array_equal(world['F'],initial['F']);np.testing.assert_array_equal(world['F_solid'],initial['F_solid']);models+=1
 if a in ['A0','A2']:
  frozen=np.load(task['contour']['baseline_meshes'][g][a]['path']);np.testing.assert_array_equal(frozen['V'],world['V'])
 if a=='A3':
  summary=json.loads((TD/'visualization'/(g+'_MECHANISM_SUMMARY.json')).read_text());assert not summary['depth_loss_used'];actualupdates+=summary['delta_max_mm']>1e-8
  if summary['initial_contour_gradient_nonzero_views']==0:inactive.append(g)
 if r['IoU_3D']is not None:assert r['IoU_3D_status']=='VALID_SOLID_SOBOL_ESTIMATE'
assert actualupdates>0 and 'G01'not in inactive
assert all(next(r for r in rows if r['case']=='G08'and r['arm']==a)['status']=='NOT_EVALUABLE'for a in ['A2','A2D','A3']);grad=json.loads((TD/'evidence/ACTUAL_CONTOUR_GRADIENT_FINITE_DIFFERENCE.json').read_text());assert grad['status']=='PASS'and grad['checked_coordinates']==36 and grad['max_absolute_error']<1e-8
# Every delivered HERO source triangle remains the exact rigidly transformed source.
from ring_first_3d.stress.real import load_view
real={g['group']:g for g in source['real_groups']};hp=json.loads((TD/'visualization/HERO_TRANSFORMS_AND_MOTION.json').read_text());hero_meshes=0
for r in hp:
 g=r['case'];assert r['GT_aligned_Body_used']is False;assert r['body_world_sha256']==sha(fetch(RUN,'G1_all_train',g+'/'+r['body_arm']+'_WORLD.npz'))
 for v in real[g]['views']:
  if v['role']!='FIT':continue
  original=load_view(v,[.3,.1]);m=np.load(TD/'visualization/meshes'/g/r['method']/(v['id']+'.npz'));T=np.asarray(r['corrections'][v['id']]);np.testing.assert_array_equal(m['F'],original['F']);np.testing.assert_allclose(m['V'],original['V']@T[:3,:3].T+T[:3,3],atol=1e-9);e=np.unique(np.sort(np.r_[m['F'][:,[0,1]],m['F'][:,[1,2]],m['F'][:,[2,0]]],axis=1),axis=0);assert np.max(abs(np.linalg.norm(m['V'][e[:,0]]-m['V'][e[:,1]],axis=1)-np.linalg.norm(original['V'][e[:,0]]-original['V'][e[:,1]],axis=1)))<1e-8;hero_meshes+=1
# H3/H4 candidates really lie on the stored actual Body face/bary; candidates remain constraints only.
verified_candidates=0
for rec in hp:
 if rec['method']not in ['H3','H4']:continue
 g=rec['case'];body=np.load(TD/'visualization/meshes'/(g+'_'+rec['body_arm']+'_WORLD.npz'))
 for v in real[g]['views']:
  if v['role']!='FIT':continue
  p=np.load(TD/'visualization/HERO_CORRESPONDENCES'/g/rec['method']/(v['id']+'.npz'));ok=p['confidence']>0
  if ok.any():
   face=p['face'][ok];bary=p['bary'][ok];assert(face>=0).all()and(face<len(body['F'])).all();np.testing.assert_allclose(bary.sum(1),1.,atol=1e-6);Q=np.einsum('ni,nij->nj',bary,body['V'][body['F'][face]]);np.testing.assert_allclose(Q,p['candidate_points'][ok],atol=1e-8);verified_candidates+=int(ok.sum())
for failure in json.loads((TD/'visualization/FAILURE_LEDGER.json').read_text())['failures']:
 if failure.get('evidence'):assert(TD/'visualization'/failure['evidence']).resolve().is_file(),failure
# GLB files parse into actual full Mesh geometry with no empty scene.
import trimesh
glbs=list((TD/'visualization/meshes').glob('*.glb'))
for p in glbs:
 scene=trimesh.load(p,force='scene',process=False);assert scene.geometry and sum(len(m.faces)for m in scene.geometry.values())>0
links=[]
class Links(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src']and v:links.append((current,v))
for current in(TD/'visualization').rglob('*.html'):Links().feed(current.read_text())
for current in TD.glob('*.md'):links.extend((current,x)for x in re.findall(r'\]\(([^)]+)\)',current.read_text()))
for current,link in links:
 u=urlsplit(link);assert not u.scheme and not u.netloc
 if u.path:assert(current.parent/unquote(u.path)).resolve().is_file(),(current,link)
assert re.search(r'!\[[^\]]*\]\(([^)]+)\)',(TD/'TECHNICAL_REPORT.md').read_text()).group(1)=='visualization/figures/Fig1_2D_TO_3D.png'
changed=subprocess.check_output(['git','diff','13a73f0422be5e5b0e221df4a41407b3b6d6d52c','--name-only','--','experiments'],text=True).splitlines();assert all(p.startswith(str(TD.relative_to(ROOT))+'/')for p in changed)
receipt=dict(status='PASS',regression_tests=reg['tests'],original_regressions=35,stages=13,exact015_files=len(lock['files']),real_aligned_models=models,actual_updated_A3_groups=int(actualupdates),initially_inactive_correspondence_groups=inactive,independent_finite_difference_coordinates=grad['checked_coordinates'],real_HERO_rigid_Meshes=hero_meshes,GLB_parsed=len(glbs),actual_Body_face_bary_candidates_verified=verified_candidates,local_links=len(links),GT_aligned_HERO=False,old_experiments_modified=0,scientific_code_unchanged_after_first_GT=True,TASK_identical_across_preserved_runs=True,visualization_absolute=str(TD/'visualization'),index_absolute=str(TD/'visualization/index.html'))
(TD/'evidence/FINAL_DELIVERY_VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n');m=json.loads((TD/'RUN_MANIFEST.json').read_text());files=sorted(p for p in TD.rglob('*')if p.is_file()and 'runs'not in p.relative_to(TD).parts and p!=TD/'RUN_MANIFEST.json');assert max(p.stat().st_size for p in files)<25000000;m.update(artifact_count=len(files),artifact_bytes=sum(p.stat().st_size for p in files),implementation_commit=json.loads((TD/'EXECUTION_VERSION.json').read_text())['implementation_commit']);m['artifacts']={str(p.relative_to(TD)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in files};(TD/'RUN_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(dict(**receipt,artifact_count=len(files),artifact_bytes=m['artifact_bytes']),indent=2))
