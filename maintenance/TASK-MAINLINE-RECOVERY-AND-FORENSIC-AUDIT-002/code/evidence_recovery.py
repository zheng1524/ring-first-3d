"""Recover registries and sidecar evidence without editing historical reports/code."""
import ast, csv, hashlib, json, os, re, subprocess, collections, html, sqlite3, shutil
from pathlib import Path
from urllib.parse import unquote, urlsplit
OUT=Path(__file__).resolve().parents[1]; ROOT=OUT.parents[1]
OLD=Path('/home/liu/ring_first_3d_mainline')
BASE='73568493d127d0aead361314afcb32e11fe886f0'
LINE=ROOT/'src/ring_first_3d/mainline/lineage/experiments'
copies=json.loads((OLD/'maintenance/TASK-MAINLINE-ASSET-CONSOLIDATION-001/COPY_VERIFICATION.json').read_text())['files']
bynew={x['new_path']:x for x in copies}
inventory=sqlite3.connect('file:'+str(OUT/'ASSET_INVENTORY.sqlite')+'?mode=ro',uri=True)
def origin(x):
 p=Path(x['original_path'])
 if p.is_absolute():return p
 matches=[Path(r[0]) for r in inventory.execute('SELECT path FROM assets WHERE sha256=? AND kind="file"',(x['original_sha256'],)) if r[0].endswith('/'+str(p))]
 matches.sort(key=lambda p:('mainline' in str(p),len(str(p))))
 return matches[0] if matches else OLD/p
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def rec(p):
 p=Path(p)
 return dict(path=str(p),exists=p.exists(),sha256=sha(p) if p.is_file() else None,hash_status='HASH_RECOMPUTED' if p.is_file() else 'NOT_APPLICABLE')
def dump(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def git(args):
 r=subprocess.run(['git','-C',str(ROOT),*args],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'},capture_output=True)
 return r.stdout if r.returncode==0 else None
def commit_match(commit,path,digest):
 b=git(['show',commit+':'+path]);return b is not None and hashlib.sha256(b).hexdigest()==digest
links=[];evidences=[];report_preservation=[]
if (OUT/'REPORT_LINK_AUDIT.csv').exists() and not (OUT/'REPORT_LINK_AUDIT_BEFORE_REPO_CONTEXT_REPAIR.csv.gz').exists():
 import gzip
 with (OUT/'REPORT_LINK_AUDIT.csv').open('rb')as first,gzip.open(OUT/'REPORT_LINK_AUDIT_BEFORE_REPO_CONTEXT_REPAIR.csv.gz','wb')as archived:shutil.copyfileobj(first,archived)
def resolve_link(src,orig,value,kind,key=''):
 value=unquote(value.strip().strip('<>'))
 if not value or value.startswith(('data:','mailto:','javascript:')):return
 if value.startswith(('https://','http://','app://')):
  links.append(dict(source=str(src),kind=kind,key=key,reference=value,status='EXTERNAL_DEPENDENCY',resolved_path='',exists=None,sha256='',note='URL recorded, not fetched in local forensic audit'));return
 path=value.split('#')[0].split('?')[0]
 if not path: return
 if any(c in path for c in ['*','{','}','$','\n']):
  links.append(dict(source=str(src),kind=kind,key=key,reference=value,status='UNRESOLVED',resolved_path='',exists=False,sha256='',note='Pattern/template is not a concrete file identity'));return
 proposed=Path(path) if Path(path).is_absolute() else src.parent/path
 original=Path(path) if Path(path).is_absolute() else orig.parent/path
 if not Path(path).is_absolute() and path.startswith(('experiments/','src/','docs/','tools/','tests/','mainline/')):
  repo=next((p for p in orig.parents if (p/'.git').exists()),None)
  if repo is not None:original=repo/path;proposed=ROOT/path
 if proposed.exists():
  target=proposed.resolve();status='EXTERNAL_DEPENDENCY' if proposed.is_absolute() and not str(target).startswith(str(ROOT)+'/') else 'VALID'
 elif original.exists():target=original.resolve();status='MOVED_TARGET'
 else:
  target=proposed;status='MISSING_ASSET' if kind in ['image','html_image'] else 'BROKEN_TARGET'
 links.append(dict(source=str(src),kind=kind,key=key,reference=value,status=status,resolved_path=str(target),exists=target.exists(),sha256=sha(target) if target.is_file() else '',note='Original-relative location follows COPY_VERIFICATION, no basename-only relocation'))
 return links[-1]
def json_strings(obj,prefix=''):
 if isinstance(obj,dict):
  for k,v in obj.items():yield from json_strings(v,prefix+'/'+k)
 elif isinstance(obj,list):
  for i,v in enumerate(obj):yield from json_strings(v,prefix+'/'+str(i))
 elif isinstance(obj,str):yield prefix,obj

execution_known={
 'TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001':'6415993f4c6aa2370e80841d1803ed701b257bee',
 'TASK-E4-STRUCTURED-BODY-UPDATE-002':'cadde3e9efc64e0925933d0a663150db9031caee',
 'TASK-E4-G01-MULTISURFACE-BODY-FUSION-001':'1648935501781d6acb47a288253255134bdedb89'}
scientific={
 'TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001':'C0_PARTIAL_VALIDATION_REAL_NEGATIVE',
 'TASK-E4-STRUCTURED-BODY-UPDATE-002':'MIXED_NO_ACCEPTED_SWEEP',
 'TASK-E4-G01-G03-GROWTH-RECOVERY-001':'G01_CONDITIONAL_G03_REJECTED_ROOT_DEFECTS_RETAINED',
 'TASK-E4-G01-MULTISURFACE-BODY-FUSION-001':'LOCALIZATION_UNPROVEN_C0_DRIFT'}
for taskdir in sorted(LINE.iterdir()):
 report=taskdir/'TECHNICAL_REPORT.md'
 if not report.is_file():continue
 task=taskdir.name; item=bynew.get(str(report.relative_to(ROOT)))
 if not item:continue
 orig=origin(item); original_root=next((p for p in orig.parents if (p/'.git').exists()),None)
 matching=[x for x in copies if x['source_task']==task and x['new_path'].startswith(str(taskdir.relative_to(ROOT))+'/')]
 sourcefiles=[]
 for x in matching:
  p=ROOT/x['new_path']
  if '/code/' not in x['new_path'] or not p.suffix=='.py':continue
  op=origin(x)
  f=dict(**rec(p),original=rec(op),source_commit=x['source_commit'],copy_status=x['status'])
  f['commit_byte_match']=commit_match(x['source_commit'],str(op.relative_to(original_root)) if original_root and op.is_relative_to(original_root) else x['original_path'] if not Path(x['original_path']).is_absolute() else 'INVALID',x['original_sha256'])
  sourcefiles.append(f)
 if task=='TASK-E4-G01-MULTISURFACE-BODY-FUSION-001':
  fp=orig.parent/'runs/MULTISURFACE_001/FREEZE.json'
  if fp.is_file():
   for mid,contract in json.loads(fp.read_text())['module_contracts'].items():
    if not mid.startswith('MF'):continue
    relative='src/ring_first_3d/'+contract['path'];p=ROOT/relative;op=original_root/relative
    sourcefiles.append(dict(**rec(p),original=rec(op),source_commit=execution_known[task],copy_status='BASELINE_SHARED_API',commit_byte_match=commit_match(execution_known[task],relative,sha(op)),execution_contract_sha256=contract['sha256'],matches_frozen_contract=sha(op)==contract['sha256']))
 execution=execution_known.get(task,'SOURCE_COMMIT_UNVERIFIED')
 checks=[]
 if execution!='SOURCE_COMMIT_UNVERIFIED':
  for f in sourcefiles:
   op=Path(f['original']['path'])
   if original_root and op.is_relative_to(original_root):checks.append(commit_match(execution,str(op.relative_to(original_root)),f['original']['sha256']))
  if not checks or not all(checks):execution='SOURCE_COMMIT_UNVERIFIED'
 reports=[x for x in matching if Path(x['new_path']).name in ['TECHNICAL_REPORT.md','RESULT_CARD.md']]
 first=len(links)
 for x in reports:
  p=ROOT/x['new_path'];op=origin(x);text=p.read_text()
  report_preservation.append(dict(path=str(p),original_path=str(op),source_commit=x['source_commit'],sha256=sha(p),expected_sha256=x['original_sha256'],preserved=sha(p)==x['original_sha256']))
  for m in re.finditer(r'(!?)\[[^\]]*\]\(([^)]+)\)',text):resolve_link(p,op,m.group(2),'image' if m.group(1) else 'markdown')
  for m in re.finditer(r'`([^`\n]+\.(?:py|json|csv|npz|png|html|glb|md|yaml))`',text):resolve_link(p,op,m.group(1),'code_or_artifact')
 # Inspect all copied structured evidence JSON and HTML, including nested runs.
 for x in matching:
  p=ROOT/x['new_path'];op=origin(x)
  if p.suffix=='.json' and p.stat().st_size<3_000_000:
   try:
    for key,value in json_strings(json.loads(p.read_text())):
     if value.startswith('/home/liu/') or (len(value)<400 and re.match(r'^[A-Za-z0-9_.\-/]+\.(?:py|json|csv|npz|png|html|glb|md|yaml|ply|obj)$',value)):
      resolve_link(p,op,value,'json_path',key)
   except (ValueError,OSError):pass
  elif p.suffix=='.html':
   for m in re.finditer(r'(src|href)=[\x22\x27]([^\x22\x27]+)',p.read_text(errors='replace')):resolve_link(p,op,m.group(2),'html_image' if m.group(1)=='src' else 'html_link')
 tasklinks=links[first:]
 # Bind real original files: historical outputs are not silently copied into lineage.
 inputassets=[];outputassets=[];metrics=[];visual=[];failures=[];deps=[]
 for name in ['TASK.yaml','TASK_FREEZE.json','inputs/INPUT_MANIFEST.json','inputs/CODE_LOCK.json']:
  if (orig.parent/name).is_file():inputassets.append(rec(orig.parent/name))
 for name in ['RUN_MANIFEST.json','RESULT_CARD.md','FAILURE_REGISTRY.json']:
  if (orig.parent/name).is_file():outputassets.append(rec(orig.parent/name))
 for p in sorted((orig.parent/'metrics').glob('*.csv'))+sorted(orig.parent.glob('*METRICS.csv')):metrics.append(rec(p))
 for pattern in ['metrics.json','SCIENTIFIC_RESULT.json','visualization/*METRICS*.csv','visualization/*METRICS*.json','visualization/*COMPARISONS*.json']:
  for p in sorted(orig.parent.glob(pattern)):
   if p.is_file() and str(p)not in {r['path']for r in metrics}:metrics.append(rec(p))
 for e in tasklinks:
  if not e['exists'] or not Path(e['resolved_path']).is_file():continue
  r={k:e[k] for k in ['resolved_path','sha256','status']};r['path']=r.pop('resolved_path');r['hash_status']='HASH_RECOMPUTED'
  if Path(r['path']).suffix in ['.png','.glb','.html']:visual.append(r)
  if any(t in r['path'].upper() for t in ['FAIL','REJECT','GATES','ROOT']):failures.append(r)
  if e['status']=='EXTERNAL_DEPENDENCY':deps.append(r)
 for p in [orig.parent/'FAILURE_REGISTRY.json',orig.parent/'FAILURE_LEDGER.md']:
  if p.is_file():failures.append(rec(p))
 sourcecommits=sorted(set(f['source_commit'] for f in sourcefiles))
 ev=dict(schema_version=1,task_id=task,source_commit=sourcecommits[0] if len(sourcecommits)==1 else sourcecommits or 'SOURCE_COMMIT_UNVERIFIED',execution_commit=execution,execution_commit_status='VERIFIED_REPORT_CLAIM_AND_SCIENTIFIC_CODE_BYTES' if execution!='SOURCE_COMMIT_UNVERIFIED' else 'SOURCE_COMMIT_UNVERIFIED',source_commit_semantics='Per-file source snapshot, distinct from original execution; current HEAD never substituted.',source_files=sourcefiles,input_assets=inputassets,output_assets=outputassets,metrics=metrics,visualizations=visual,failure_evidence=failures,dependencies=deps,scientific_status=scientific.get(task,'HISTORICAL_REPORTED_STATUS_NOT_RECERTIFIED'),engineering_status='HISTORICAL_EXECUTION_EVIDENCE_PRESENT' if (orig.parent/'RUN_MANIFEST.json').is_file() else 'EVIDENCE_PARTIAL',report=dict(canonical_copy=rec(report),original=rec(orig),publication_commit=item['source_commit']),link_counts=dict(collections.Counter(e['status'] for e in tasklinks)),notes=[])
 if task.endswith('GROWTH-RECOVERY-001'):ev['notes']=['LOCAL_002 resumes G03 from LOCAL_001; execution source identity is per-stage hashes. Publication commit bac3fc89 is not asserted as execution commit.','G01 gate passes with root exposure defect; G03 formal prediction NaN.']
 if task.endswith('STRUCTURAL-UPDATE-001'):ev['notes']=['C0 originally executed d78cacd86b095ade5c4753537e216f900a018bcd, resumed with identity proof; not rerun by final source.']
 evidence_dir=ROOT/'experiments'/task
 # Existing aliases target frozen lineage: never write through them.
 if evidence_dir.is_symlink():evidence_dir=OUT/'evidence'/task
 else:evidence_dir=OUT/'evidence'/task
 dump(evidence_dir/'EVIDENCE.json',ev);evidences.append(ev)
 canonical=evidence_dir/'CANONICAL_REPORT.md'
 rows=['# '+task+' — evidence navigation','',f'Historical report preserved: [{report.name}]({report})',f'Original SHA256: `{item["original_sha256"]}`',f'Execution commit: `{execution}`','', 'This navigation supplement does not revise historical results. No old links were edited.','', '| Original reference | Status | Verified local target |','|---|---|---|']
 for e in tasklinks:
  if e['kind'] in ['markdown','image','code_or_artifact']:
   rows.append('| '+e['reference'].replace('|','\\|')+' | '+e['status']+' | '+('['+Path(e['resolved_path']).name+']('+e['resolved_path']+')' if e['exists'] else 'Unresolved, retain evidence')+' |')
 canonical.write_text('\n'.join(rows)+'\n')
dump(OUT/'EVIDENCE_INDEX.json',[dict(task_id=e['task_id'],path=str(OUT/'evidence'/e['task_id']/'EVIDENCE.json'),engineering=e['engineering_status'],scientific=e['scientific_status'],execution_commit=e['execution_commit']) for e in evidences])
dump(OUT/'HISTORICAL_REPORT_PRESERVATION.json',report_preservation)
with (OUT/'REPORT_LINK_AUDIT.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,['source','kind','key','reference','status','resolved_path','exists','sha256','note']);w.writeheader();w.writerows(links)
dump(OUT/'REPORT_LINK_SUMMARY.json',dict(total=len(links),counts=dict(collections.Counter(e['status'] for e in links)),reports_scanned=len(report_preservation),tasks=len(evidences),original_report_bytes_all_preserved=all(r['preserved'] for r in report_preservation),semantics='Existing targets need not be portable; external dependencies are explicit. Missing/template links remain failures, not fabricated repairs.'))

# Add existing Runner module IDs from real stage contracts, rather than inventing IDs.
registry=ROOT/'docs/registry/MODULE_REGISTRY.json';reg=json.loads(git(['show',BASE+':docs/registry/MODULE_REGISTRY.json']));before=list(reg['modules']);ids={x['id'] for x in before};added=[]
runtime_specs=[('structural_update','TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001','STRUCTURAL_004','SU'),('structured_body_002','TASK-E4-STRUCTURED-BODY-UPDATE-002','PILOT_002','SB'),('growth_recovery','TASK-E4-G01-G03-GROWTH-RECOVERY-001','LOCAL_002','GR')]
for folder,task,run,prefix in runtime_specs:
 op=Path('/home/liu/ring_first_3d_'+folder)/'experiments'/task;freeze=op/'runs'/run/'FREEZE.json';fd=json.loads(freeze.read_text())
 ev=next(e for e in evidences if e['task_id']==task)
 for mid,c in fd['module_contracts'].items():
  if not mid.startswith(prefix) or mid in ids:continue
  original=Path(c['path']);target=LINE/task/'code'/original.name
  if not target.is_file():continue
  tree=ast.parse(target.read_text());symbols=[n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
  imports=sorted({n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module}|{a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names})
  description=ast.get_docstring(tree) or original.stem.replace('_',' ')
  # AST signatures + actual contract input/output descriptions link to canonical code.
  definitions={}
  for n in tree.body:
   if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
    definitions[n.name]=dict(line=n.lineno,end_line=n.end_lineno,args=ast.unparse(n.args) if isinstance(n,ast.FunctionDef) else None)
  x=dict(id=mid,module=description,path=str(target.relative_to(ROOT)),symbols=symbols,engineering='EXECUTED_WITH_FROZEN_RUNNER_CONTRACT',scientific=ev['scientific_status'],reuse='CURRENT_MAINLINE' if prefix=='GR' or mid in ['SB01','SB02','SB03','SB05','SB06'] else 'REUSABLE_REFERENCE',input='Frozen mm Mesh, source-bound FIT Mask/K/opencv_c2w; exact arguments in symbol_definitions and source; no GT in predictor',output='Function-specific geometry, gate record or metrics; exact signatures and original run evidence attached',call='; '.join(symbols),limit='Module execution does not establish scientific success; inherited rejection and root exposure evidence retained.',evidence=str(freeze),sha256=sha(target),bytes=target.stat().st_size,source_task=task,source_commit=next((f['source_commit'] for f in ev['source_files'] if Path(f['path']).name==original.name),'SOURCE_COMMIT_UNVERIFIED'),execution_commit=ev['execution_commit'],historical_branch='exp/'+task,dependencies=imports,symbol_definitions=definitions,current_mainline=prefix=='GR' or mid in ['SB01','SB02','SB03','SB05','SB06'],original_source=rec(original),frozen_contract_sha256=c['sha256'],original_matches_execution_contract=sha(original)==c['sha256'],execution_evidence=[rec(freeze),rec(op/'RUN_MANIFEST.json')],scientific_status=ev['scientific_status'],engineering_status='EXECUTED_WITH_FROZEN_RUNNER_CONTRACT')
  reg['modules'].append(x);ids.add(mid);added.append(x)
# Existing initialization module gains identity evidence without changing its algorithm.
ia=next(x for x in reg['modules'] if x['id']=='IA01')
ia['current_mainline']=True;ia['canonical_identity']='EXACT_013_INPUT_MESH_V_F_SOLID_CAP';ia['canonical_entry']='src/ring_first_3d/mainline/replays.py:body_initialization';ia['mainline_evidence']='maintenance/TASK-MAINLINE-ASSET-CONSOLIDATION-001/REPRODUCIBILITY_TESTS/BODY_INITIALIZATION.json'
reg['forensic_repair']=dict(task='TASK-MAINLINE-RECOVERY-AND-FORENSIC-AUDIT-002',previous_modules=len(before),added_modules=[x['id'] for x in added],no_scientific_code_changed=True,existing_runner_contract_ids_preserved=True)
dump(registry,reg);dump(OUT/'MODULE_REGISTRY_REPAIR.json',dict(before=len(before),after=len(reg['modules']),added=added,existing_ids_unchanged=True))

index=ROOT/'docs/registry/EXPERIMENT_INDEX.csv'
reader=csv.DictReader(git(['show',BASE+':docs/registry/EXPERIMENT_INDEX.csv']).decode().splitlines());fields=reader.fieldnames;rows=list(reader)
repairs=[]
for ev in evidences:
 if ev['task_id'] not in scientific:continue
 task=ev['task_id'];existing=next((r for r in rows if r['TASK_ID']==task),None);old=dict(existing) if existing else None
 if existing is None:existing={k:'' for k in fields};rows.append(existing)
 original=Path(ev['report']['original']['path']);branch=git(['for-each-ref','--format=%(refname:short)','refs/heads/exp/'+task]);branch=branch.decode().strip() if branch else 'SOURCE_BRANCH_UNVERIFIED'
 existing.update(THEME='多视角主体与结构恢复',TASK_ID=task,BRANCH=branch,COMMIT_SHA=ev['execution_commit'],RESEARCH_QUESTION='多视角轮廓是否改善共享主体及缺失结构',METHOD='Original formal code; see EVIDENCE.json; no audit reoptimization',GROUPS='2 groups G01/G03' if 'GROWTH-RECOVERY' in task else 'G01-like 1 scene' if 'MULTISURFACE' in task else '3 groups G01/G03/G05',RESULT=ev['scientific_status'],ENGINEERING_STATUS=ev['engineering_status'],SCIENTIFIC_STATUS=ev['scientific_status'],REUSABLE_COMPONENTS=';'.join(x['id'] for x in added if x['source_task']==task),FAILURE_EVIDENCE=str((OUT/'evidence'/task/'EVIDENCE.json').relative_to(ROOT)),REPORT_PATH=str((OUT/'evidence'/task/'CANONICAL_REPORT.md').relative_to(ROOT)),HISTORICAL_BRANCH_TIP=ev['report']['publication_commit'],SOURCE_SNAPSHOT_NOTE='COMMIT_SHA=verified execution source claim and code bytes, otherwise SOURCE_COMMIT_UNVERIFIED. HISTORICAL_BRANCH_TIP=report publication snapshot, not original execution. Per-stage provenance preserved in EVIDENCE.json.')
 repairs.append(dict(task_id=task,before=old,after=existing))
task='TASK-MAINLINE-ASSET-CONSOLIDATION-001'
existing=next((r for r in rows if r['TASK_ID']==task),None)
if existing is None:existing={k:'' for k in fields};rows.append(existing)
old=dict(existing)
existing.update(THEME='主线工程与证据',TASK_ID=task,BRANCH='maintenance/'+task,COMMIT_SHA='SOURCE_COMMIT_UNVERIFIED',RESEARCH_QUESTION='主线集中和固定输入重放是否可复现',METHOD='247 regression + 8 fixed module replays; checkpoint-continuation, no fresh training',GROUPS='8 modules; G01/G03 preserved',RESULT='ENGINEERING_REPLAYS_PASS_SCIENCE_NOT_RECERTIFIED',ENGINEERING_STATUS='247_TESTS_8_REPLAYS_RECORDED',SCIENTIFIC_STATUS='ACTIVE_RESEARCH_MAINLINE',REUSABLE_COMPONENTS='mainline CLI; source guard; manifests',FAILURE_EVIDENCE='maintenance/'+task+'/FAILURE_REGISTRY.json',REPORT_PATH='maintenance/'+task+'/TECHNICAL_REPORT.md',HISTORICAL_BRANCH_TIP=BASE,SOURCE_SNAPSHOT_NOTE='Publication SHA verified, not substituted for execution SHA; immutable replay source hashes in REPLAY_INPUT_FREEZE.json.')
repairs.append(dict(task_id=task,before=old,after=existing))
with index.open('w',newline='') as f:
 w=csv.DictWriter(f,fields,lineterminator='\n');w.writeheader();w.writerows(rows)
dump(OUT/'EXPERIMENT_INDEX_REPAIR.json',repairs)
maint=OLD/'maintenance'/task
dump(OUT/'evidence'/task/'EVIDENCE.json',dict(task_id=task,source_commit=BASE,execution_commit='SOURCE_COMMIT_UNVERIFIED',source_files=[rec(OLD/'mainline/manifests/REPLAY_INPUT_FREEZE.json')],input_assets=[rec(OLD/'mainline/manifests/EXTERNAL_INPUTS.json')],output_assets=[rec(maint/'TECHNICAL_REPORT.md'),rec(maint/'RESULT_CARD.md')],metrics=[rec(maint/'FINAL_VERIFICATION.json')],visualizations=[rec(OLD/'mainline/visualization/index.html')],failure_evidence=[rec(maint/'FAILURE_REGISTRY.json')],dependencies=[rec(OLD/'mainline/manifests/RUNTIME_FILES.json')],scientific_status='ACTIVE_RESEARCH_MAINLINE',engineering_status='HISTORICAL_247_TESTS_8_REPLAYS_RECORDED',notes='Audit does not rerun science or assert original execution commit from publication HEAD.'))
print('Recovered',len(evidences),'tasks;',len(links),'links;',len(added),'existing Runner module IDs')
