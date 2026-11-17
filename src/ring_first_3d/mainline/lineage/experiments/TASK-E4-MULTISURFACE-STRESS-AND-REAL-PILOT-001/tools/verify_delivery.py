"""Verify accepted freeze, scoped sources, links, figures and all artifact hashes."""
from pathlib import Path
import json,hashlib,re,subprocess
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from ring_first_3d.policy.contracts import load_task,verify_task
from ring_first_3d.policy.artifacts import read_state,check_artifacts
from ring_first_3d.policy.memory import registry
root=Path.cwd();td=root/'experiments/TASK-E4-MULTISURFACE-STRESS-AND-REAL-PILOT-001';run=td/'runs/STRESS_REAL_001';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();state=read_state(run);task=load_task(td/'TASK.yaml')
assert state['accepted']and verify_task(task)['freeze_sha256']==state['freeze_sha256'];check_artifacts(run,state);registry(td/'FAILURE_REGISTRY.json')
files=sorted(p for p in td.rglob('*')if p.is_file()and'runs'not in p.relative_to(td).parts and p!=td/'RUN_MANIFEST.json')
links=[]
class Links(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for key,value in attrs:
   if key in ('href','src')and value:links.append((current,value))
for current in (td/'visualization').rglob('*.html'):Links().feed(current.read_text())
for current in td.glob('*.md'):
 links.extend((current,h.strip('<>'))for h in re.findall(r'\]\(([^)]+)\)',current.read_text()))
checked=0
for current,link in links:
 u=urlsplit(link)
 assert not u.scheme and not u.netloc,(str(current),link)
 if not u.path:continue
 p=(current.parent/unquote(u.path)).resolve();assert p.is_file(),(str(current),link,str(p));checked+=1
first=re.search(r'!\[[^\]]*\]\(([^)]+)\)',(td/'TECHNICAL_REPORT.md').read_text()).group(1);assert first=='visualization/figures/01_MAIN_STRESS_SECTIONS.png'
browser=json.loads((td/'evidence/OFFLINE_BROWSER_VERIFICATION.json').read_text());assert browser['status']=='PASS'and browser['pages']==8 and browser['exact_cut_cases']==46
s=json.loads((td/'SCIENTIFIC_RESULT.json').read_text());assert s['simulation_models']==34 and s['simulation_numeric']==34 and s['real_groups_numeric']==3 and s['real_groups_target']==3 and s['tests']==117 and s['stages']==16
assert len(json.loads((td/'visualization/DISPERSION_GT_SURFACE_CONTRADICTIONS.json').read_text())['rows'])==4
assert len(json.loads((td/'visualization/CANDIDATE_FAILURE_DIAGNOSTICS.json').read_text())['rows'])==544
locked=json.loads((td/'inputs/ALGORITHM_LOCK.json').read_text());assert all(sha(root/r['path'])==r['sha256']for r in locked['files'])
old=subprocess.check_output(['git','diff','b16a6f813ecf9214958cae3b88d624725a0fa484','--name-only','--','experiments'],text=True).splitlines();assert all(p.startswith(str(td.relative_to(root))+'/')for p in old)
modules=json.loads((root/'docs/registry/MODULE_REGISTRY.json').read_text())['modules']
for m in modules:
 if m['id']in ['SR01','SR02','SR03','SR04']:assert m['sha256']==sha(root/m['path'])and m['validation_tests']==117
assert max(p.stat().st_size for p in files)<25000000
receipt=dict(status='PASS',accepted_stages=16,regression_tests=117,simulation_numeric=34,real_groups_numeric=3,real_groups_target=3,full_Mesh_cases_browser_checked=46,offline_pages_rendered=8,static_local_links=checked,source_algorithms_unchanged=len(locked['files']),old_experiment_changes=0,freeze_sha256=state['freeze_sha256'],main_figure_first=True,task_local_failure_registry='VALID_CANDIDATES_NOT_PERMANENT',visualization_absolute=str(td/'visualization'),index_absolute=str(td/'visualization/index.html'),GT_alignment=False)
(td/'evidence/FINAL_DELIVERY_VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
files=sorted(p for p in td.rglob('*')if p.is_file()and'runs'not in p.relative_to(td).parts and p!=td/'RUN_MANIFEST.json');m=json.loads((td/'RUN_MANIFEST.json').read_text());m.update(summary=s,artifact_count=len(files),artifact_bytes=sum(p.stat().st_size for p in files),offline_browser_verified=True,all_46_Mesh_cut_results=True);m['artifacts']={str(p.relative_to(td)):dict(bytes=p.stat().st_size,sha256=sha(p))for p in files};(td/'RUN_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
for name,identity in m['artifacts'].items():
 p=td/name;assert p.is_file()and p.stat().st_size==identity['bytes']and sha(p)==identity['sha256']
print(json.dumps(dict(**receipt,artifact_count=len(files),artifact_bytes=m['artifact_bytes']),indent=2))
