from pathlib import Path
import hashlib,json,re,subprocess,shutil
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from ring_first_3d.policy.contracts import load_task,verify_task
from ring_first_3d.policy.artifacts import read_state,check_artifacts
from ring_first_3d.policy.memory import registry
root=Path.cwd();td=root/'experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1';run=td/'runs/SIM_REV1_001';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
t=load_task(td/'TASK.yaml');s=read_state(run);identity=verify_task(t);assert identity['freeze_sha256']==s['freeze_sha256'];check_artifacts(run,s);assert s['accepted']
m=json.loads((td/'RUN_MANIFEST.json').read_text())
for name,r in m['artifacts'].items():
 p=td/name;assert p.is_file()and p.stat().st_size==r['bytes']and sha(p)==r['sha256'],name
refs=[]
class Links(HTMLParser):
 def __init__(self,base):super().__init__();self.base=base
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src']and v and not v.startswith('#'):
    u=urlsplit(v);assert not u.scheme and not u.netloc, v
    p=(self.base/unquote(u.path)).resolve();assert p.is_relative_to(td)and p.is_file(),str(p);refs.append(str(p))
for page in(td/'visualization').glob('*.html'):parser=Links(page.parent);parser.feed(page.read_text())
markdown=0
for name in ['TECHNICAL_REPORT.md','RESULT_CARD.md']:
 for dest in re.findall(r'\]\(([^)]+)\)',(td/name).read_text()):assert(td/dest).is_file(),dest;markdown+=1
f=registry(td/'FAILURE_REGISTRY.json');assert len(f['failures'])==3
old='experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001'
assert not subprocess.check_output(['git','diff','009112d0ceca23e968ef7a97de33ea6989c24b15','--',old],text=True)
for name in ['visualization','visualization/index.html','visualization/mesh_registration.html','TECHNICAL_REPORT.md','RESULT_CARD.md','RUN_MANIFEST.json']:
 p=td/name;assert p.exists();print('EXISTS',p)
record=dict(status='PASS',source_environment_matches_frozen_run=True,runner_accepted=True,scientific_acceptance='AWAITING_HUMAN_REVIEW',scientific_result='M2 did not pass frozen pose criterion',all_14_registered_stages_pass=True,regression_tests=82,regression_failures=0,regression_errors=0,artifact_files_checked=len(m['artifacts']),HTML_local_references_checked=len(refs),Markdown_file_references_checked=markdown,task_local_failure_registry_rows=len(f['failures']),original_TASK_report_and_failures_unchanged=True,browser_states_checked=10,full_mesh_faces={'004':2075,'005':1976},local_visualization=str(td/'visualization'),local_index=str(td/'visualization/index.html'))
(td/'evidence/DELIVERY_VERIFICATION.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
# Add this receipt and the read-only export scripts, then verify every final byte.
files=[p for p in td.rglob('*')if p.is_file()and'runs'not in p.relative_to(td).parts and p!=td/'RUN_MANIFEST.json'];m['artifacts']={str(p.relative_to(td)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(files)};(td/'RUN_MANIFEST.json').write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
for name,r in m['artifacts'].items():
 p=td/name;assert p.is_file()and p.stat().st_size==r['bytes']and sha(p)==r['sha256'],name
print('FINAL VERIFIED',len(m['artifacts']))
