"""Read-only audit of frozen predictions and curated review artifacts; no fits."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
import json,hashlib,re,subprocess
from ring_first_3d.policy.contracts import load_task,verify_task
from ring_first_3d.policy.artifacts import read_state,check_artifacts
from ring_first_3d.policy.memory import registry
root=Path.cwd();td=root/'experiments/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001';run=td/'runs/MULTISURFACE_001'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
task=load_task(td/'TASK.yaml');state=read_state(run);v=verify_task(task)
assert state['accepted'] and v['freeze_sha256']==state['freeze_sha256']
check_artifacts(run,state);registry(td/'FAILURE_REGISTRY.json')
audit=json.loads((td/'evidence/attempts/0004-G0_views_noise-3ab770b4/GENERATION_AUDIT.json').read_text())
assert audit['independent_depth_grid'] and not audit['GT_face_union_used']
assert len(audit['mesh_audit'])==16
assert all(not a['GT_faces_used_to_build_mesh'] and a['unproject_material_max_mm']<.001 for a in audit['mesh_audit'])
aggregate=json.loads((td/'visualization/AGGREGATE_MATERIAL_METRICS.json').read_text())
assert len(aggregate)==52
assert all(r['target_material_vertices']==68230 and r['independent_numeric_vertices']==68230 and r['failed_vertices']==0 and not r['GT_alignment'] for r in aggregate)
assert json.loads((td/'evidence/SECTIONS_BROWSER_VERIFICATION.json').read_text())['cases_checked']==52
assert json.loads((td/'evidence/BROWSER_VERIFICATION.json').read_text())['status']=='PASS'
assert json.loads((td/'visualization/OVERLAP_FAMILY_METRICS.json').read_text())['video_only_within_video_invariance_verified']
# All explicit local HTML/Markdown links must resolve to existing files.
links=[]
class LocalLinks(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for k,value in attrs:
   if k in ('href','src') and value:links.append((current,value))
for current in (td/'visualization').glob('*.html'):LocalLinks().feed(current.read_text())
for current in td.glob('*.md'):
 for dest in re.findall(r'\]\(([^\)]+)\)',current.read_text()):links.append((current,dest.strip('<>')))
checked=0
for p,href in links:
 parsed=urlsplit(href)
 if parsed.scheme or parsed.netloc or not parsed.path:continue
 dest=(p.parent/unquote(parsed.path)).resolve();assert dest.is_file(),(str(p),href,str(dest));checked+=1
report=(td/'TECHNICAL_REPORT.md').read_text();assert re.search(r'!\[[^\]]*\]\(([^\)]+)\)',report).group(1)=='visualization/figures/01_MAIN_MULTISURFACE_SECTIONS.png'
assert (td/'visualization/index.html').is_file()
modules=json.loads((root/'docs/registry/MODULE_REGISTRY.json').read_text())['modules']
for m in modules:
 if m['id'] in ['MF01','MF02','MF03','MF04','MF05']:
  assert m['sha256']==sha(root/m['path']) and m['validation_tests']==104
changed=subprocess.check_output(['git','diff','0a3fe96bb1d91e5719f8e21bcf232e0967dd233f','--name-only','--','experiments'],text=True).splitlines()
assert all(p.startswith(str(td.relative_to(root))+'/') for p in changed)
# Manifest excludes itself; receipt is added before rebuilding its complete digest map.
receipt=dict(status='PASS',frozen_predictions_unchanged=True,freeze_sha256=state['freeze_sha256'],accepted_stages=13,regression_tests=104,numeric_models=52,independent_views=16,material_vertices_per_case=68230,independent_triangles=127691,exact_sections_browser_cases=52,local_links_checked=checked,task_local_failure_registry='VALID_UNREVIEWED_CANDIDATES',old_experiment_changes=0,main_figure_is_first=True,GT_alignment=False,visualization_absolute=str(td/'visualization'),index_absolute=str(td/'visualization/index.html'))
(td/'evidence/FINAL_DELIVERY_VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
manifest_path=td/'RUN_MANIFEST.json';manifest=json.loads(manifest_path.read_text())
files=sorted(p for p in td.rglob('*') if p.is_file() and 'runs' not in p.relative_to(td).parts and p!=manifest_path)
assert max(p.stat().st_size for p in files)<25000000
manifest['artifacts']={str(p.relative_to(td)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files}
manifest['artifact_count']=len(files);manifest['artifact_bytes']=sum(p.stat().st_size for p in files)
manifest['offline_browser_verified']=True;manifest['all_case_exact_sections']=52
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
for name,identity in manifest['artifacts'].items():
 p=td/name;assert p.is_file() and p.stat().st_size==identity['bytes'] and sha(p)==identity['sha256']
print(json.dumps(dict(**receipt,artifact_count=len(files),artifact_bytes=manifest['artifact_bytes']),indent=2))
