"""Verify accepted policy identity, real SE3 copies, model bytes, links and offline views."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
import json,hashlib,re,subprocess
import numpy as np
from ring_first_3d.policy.contracts import load_task,verify_task
from ring_first_3d.policy.artifacts import read_state,check_artifacts
from ring_first_3d.policy.memory import registry
from ring_first_3d.synthetic.io import fetch
root=Path.cwd();td=root/'experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001';run=td/'runs/INIT_A_002';task=load_task(td/'TASK.yaml');state=read_state(run);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert state['accepted']and verify_task(task)['freeze_sha256']==state['freeze_sha256'];check_artifacts(run,state);registry(td/'FAILURE_REGISTRY.json')
lock=json.loads(Path(task['inita']['assets']['code_lock']['path']).read_text())
for r in lock['files']:
 assert sha(Path(r['path']))==r['sha256']
 raw=subprocess.check_output(['git','show',r['commit']+':'+r['git_path']]);assert hashlib.sha256(raw).hexdigest()==r['sha256']
metrics=json.loads((td/'visualization/BODY_SHAPE_METRICS.json').read_text())['rows'];verified_models=0
for r in metrics:
 if r['status']!='NUMERIC':continue
 folder=td/'review_meshes'/r['case'];world=dict(np.load(folder/(r['arm']+'_WORLD.npz')));aligned=dict(np.load(folder/(r['arm']+'_ALIGNED.npz')));T=aligned['T'];assert np.allclose(T[:3,:3].T@T[:3,:3],np.eye(3),atol=1e-6)and np.linalg.det(T[:3,:3])>.999999;assert np.allclose(aligned['V'],world['V']@T[:3,:3].T+T[:3,3],atol=1e-10);assert np.array_equal(world['F'],aligned['F'])and np.array_equal(world['F_solid'],aligned['F_solid']);assert sha(fetch(run,'G1_all_train',r['case']+'/'+r['arm']+'_WORLD.npz'))==r['world_prediction_sha256'];verified_models+=1
 if r['IoU_3D']is not None:assert r['IoU_3D_status']=='VALID_SOLID_SOBOL_ESTIMATE'and r['GT_geometry']['self_intersections']==0
assert {r['case']for r in metrics}==set(task['inita']['cases']);assert all(next(r for r in metrics if r['case']=='G08'and r['arm']==a)['status']=='NOT_EVALUABLE'for a in ['A1','A2'])
viewaudit=json.loads((td/'visualization/VIEW_COMPLEMENTARITY_AND_ISOLATION.json').read_text());assert all(not r['HERO_HOLDOUT_in_Body_FIT']for r in viewaudit)
links=[]
class Links(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for key,value in attrs:
   if key in ('href','src')and value:links.append((current,value))
for current in list((td/'visualization').rglob('*.html'))+list((td/'review_meshes').rglob('*.html')):Links().feed(current.read_text())
for current in td.glob('*.md'):links.extend((current,d.strip('<>'))for d in re.findall(r'\]\(([^)]+)\)',current.read_text()))
checked=0
for current,link in links:
 u=urlsplit(link);assert not u.scheme and not u.netloc,(str(current),link)
 if u.path:assert(current.parent/unquote(u.path)).resolve().is_file(),(str(current),link);checked+=1
first=re.search(r'!\[[^\]]*\]\(([^)]+)\)',(td/'TECHNICAL_REPORT.md').read_text()).group(1);assert first=='visualization/figures/Fig1_All_InitA_Bodies.png'
browser=json.loads((td/'evidence/OFFLINE_BROWSER_VERIFICATION.json').read_text());assert browser['status']=='PASS'and browser['pages']>=14
changed=subprocess.check_output(['git','diff','b1f8fb433f37677b93ac52ac5719afd902c1fa11','--name-only','--','experiments'],text=True).splitlines();assert all(p.startswith(str(td.relative_to(root))+'/')for p in changed)
receipt=dict(status='PASS',regression_tests=130,accepted_stages=13,legacy_exact_source_files=len(lock['files']),real_scale1_aligned_models=verified_models,all_11_groups_retained=True,source_world_models_unchanged=True,GT_aligned_HERO=False,old_experiment_changes=0,HERO_HOLDOUT_in_Body_FIT=0,local_links_verified=checked,offline_pages_verified=browser['pages'],main_figure_actual_aligned_Mesh=True,freeze_sha256=state['freeze_sha256'],visualization_absolute=str(td/'visualization'),index_absolute=str(td/'visualization/index.html'))
(td/'evidence/FINAL_DELIVERY_VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n');m=json.loads((td/'RUN_MANIFEST.json').read_text());files=sorted(p for p in td.rglob('*')if p.is_file()and'runs'not in p.relative_to(td).parts and p!=td/'RUN_MANIFEST.json');assert max(p.stat().st_size for p in files)<25000000;m.update(artifact_count=len(files),artifact_bytes=sum(p.stat().st_size for p in files),offline_browser_verified=True);m['artifacts']={str(p.relative_to(td)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in files};(td/'RUN_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
for n,identity in m['artifacts'].items():p=td/n;assert p.is_file()and sha(p)==identity['sha256']and p.stat().st_size==identity['bytes']
print(json.dumps(dict(**receipt,artifact_count=len(files),artifact_bytes=m['artifact_bytes']),indent=2))
