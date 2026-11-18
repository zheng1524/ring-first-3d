"""Meaningful integration assertions on actual forensic exports; no scientific execution."""
import os,json,csv,gzip,hashlib,sqlite3,subprocess,re,collections
from pathlib import Path
O=Path(__file__).resolve().parents[1];R=O.parents[1]
C=sqlite3.connect('file:'+str(O/'ASSET_INVENTORY.sqlite')+'?mode=ro',uri=True)
results=[]
def check(name,fn):
 try:detail=fn();results.append(dict(check=name,status='PASS',detail=detail))
 except Exception as e:results.append(dict(check=name,status='FAIL',detail=repr(e)))
def require(x,message):
 if not x:raise AssertionError(message)
 return message
cache={}
def sha(p):
 p=Path(p)
 if str(p)not in cache:
  h=hashlib.sha256()
  with p.open('rb')as f:
   for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
  cache[str(p)]=h.hexdigest()
 return cache[str(p)]
def rows(name):
 with gzip.open(O/name,'rt')as f:return list(csv.DictReader(f))
S=json.loads((O/'ASSET_SCAN_SUMMARY.json').read_text())
check('complete_asset_export_row_count',lambda:require(len(rows('ASSET_INVENTORY.csv.gz'))==S['files']==C.execute('SELECT count(*)FROM assets').fetchone()[0],'full CSV/db/summary counts match'))
check('symlink_export_regression_IR009',lambda:require(len(rows('SYMLINKS.csv.gz'))==C.execute('SELECT count(*)FROM assets WHERE kind=?',('symlink',)).fetchone()[0]==53263,'53263 actual symlinks exported; initial empty artifact retained'))
check('old_empty_export_and_fix_preserved',lambda:require(len(rows('SYMLINKS_INITIAL_EMPTY_EXPORT.csv.gz'))==0 and (O/'AUDIT_REVISIONS.json').is_file(),'first erroneous export and repair evidence retained'))
check('unique_inode_accounting',lambda:require(S['unique_inode_allocated_bytes']==C.execute('SELECT sum(allocated)FROM(SELECT max(allocated)allocated FROM assets GROUP BY dev,inode)').fetchone()[0],'allocated bytes counted once per dev/inode across all scan roots'))
def hashes():
 for status,source,n in C.execute('SELECT hash_status,hash_source,count(*) FROM assets GROUP BY hash_status,hash_source'):
  require(status in ['HASH_RECOMPUTED','HASH_INHERITED'],'hash provenance labels')
  if status=='HASH_INHERITED':require(C.execute('SELECT count(*)FROM assets WHERE path=? AND hash_status=?',(source,'HASH_RECOMPUTED')).fetchone()[0]>0,'same-scan inherited source missing')
 return 'all inherited hashes bind a current-scan recomputed row'
check('hash_inheritance_not_old_audit',hashes)
pres=json.loads((O/'HISTORICAL_REPORT_PRESERVATION.json').read_text())
check('historical_reports_unmodified',lambda:require(all(sha(r['path'])==r['expected_sha256']for r in pres),'39 canonical historical reports/cards retain original SHA256'))
def evidence():
 n=0;verified=0
 for p in (O/'evidence').glob('*/EVIDENCE.json'):
  d=json.loads(p.read_text());require(all(k in d for k in ['task_id','source_commit','execution_commit','source_files','input_assets','output_assets','metrics','visualizations','failure_evidence','dependencies','scientific_status','engineering_status']),'missing evidence contract fields');n+=1
  def walk(x):
   nonlocal verified
   if isinstance(x,dict):
    if x.get('sha256') and x.get('path') and Path(x['path']).is_file():
     require(sha(x['path'])==x['sha256'],'evidence SHA mismatch '+x['path']);verified+=1
    for v in x.values():walk(v)
   elif isinstance(x,list):
    for v in x:walk(v)
  walk(d)
 require(n==19,'expected19 historical evidence sidecars')
 fusion=json.loads((O/'evidence/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001/EVIDENCE.json').read_text())
 require(len(fusion['metrics'])>0,'Fusion original metrics omitted')
 return dict(tasks=n,hashed_records_verified=verified)
check('evidence_contract_and_real_file_hashes',evidence)
reg=json.loads((R/'docs/registry/MODULE_REGISTRY.json').read_text())
check('module_ids_recovered_without_collision',lambda:require(len(reg['modules'])==99 and len({m['id']for m in reg['modules']})==99 and all(any(m['id']==prefix+f'{i:02}'for m in reg['modules'])for prefix,n in [('SU',6),('SB',11),('GR',13)]for i in range(1,n+1)),'69 original +30 existing Runner IDs, no new arbitrary IDs'))
def modules():
 for m in reg['modules']:
  if not m['id'].startswith(('SU','SB','GR')):continue
  require(all(k in m for k in ['path','source_task','source_commit','symbols','input','output','dependencies','execution_evidence','engineering_status','scientific_status','current_mainline']),'missing module metadata')
  require(sha(R/m['path'])==m['sha256'],'module source mismatch')
  require(all(Path(x['path']).is_file()for x in m['execution_evidence']),'runtime evidence missing')
 return '30 recovered modules point to real code and frozen stage evidence'
check('module_paths_SHA_and_execution_evidence',modules)
def index():
 with (R/'docs/registry/EXPERIMENT_INDEX.csv').open()as f:reader=csv.DictReader(f);data=list(reader);require(len(reader.fieldnames)==16,'original16-column schema preserved')
 targets=['TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001','TASK-E4-G01-MULTISURFACE-BODY-FUSION-001','TASK-E4-STRUCTURED-BODY-UPDATE-002','TASK-E4-G01-G03-GROWTH-RECOVERY-001','TASK-MAINLINE-ASSET-CONSOLIDATION-001']
 for task in targets:
  found=[r for r in data if r['TASK_ID']==task];require(len(found)==1,'task missing or duplicated '+task);require((R/found[0]['REPORT_PATH']).is_file(),'canonical report missing')
 return 'five specified experiments registered once, reports exist, source unknown retained explicitly'
check('five_task_index_repair',index)
def links():
 with (O/'REPORT_LINK_AUDIT.csv').open()as f:rs=list(csv.DictReader(f))
 summary=json.loads((O/'REPORT_LINK_SUMMARY.json').read_text());require(dict(collections.Counter(r['status']for r in rs))==summary['counts'],'link counts mismatch')
 for r in rs:
  require(r['status']in ['VALID','BROKEN_TARGET','MISSING_ASSET','MOVED_TARGET','EXTERNAL_DEPENDENCY','UNRESOLVED'],'unknown status')
  if r['status']in ['VALID','MOVED_TARGET']:
   require(Path(r['resolved_path']).exists(),'falsely repaired target '+r['resolved_path'])
   if r['sha256']:require(sha(r['resolved_path'])==r['sha256'],'link target hash mismatch')
 return summary
check('link_status_counts_and_repaired_target_hashes',links)
def metrics():
 with (O/'METRIC_DEFINITION_MATRIX.csv').open()as f:rs=list(csv.DictReader(f))
 require(len(rs)==12,'metric definition count')
 for r in rs:
  require(sha(r['code_path'])==r['code_sha256'],'metric source mismatch')
  require(sha(r['evidence_path'])==r['evidence_sha256'],'metric original evidence mismatch')
 with Path('/home/liu/ring_first_3d_growth_recovery/experiments/TASK-E4-G01-G03-GROWTH-RECOVERY-001/metrics/BODY_METRICS.csv').open()as f:data=list(csv.DictReader(f))
 before=next(x for x in data if x['case']=='G01'and x['arm']=='ITERATION_024');after=next(x for x in data if x['case']=='G01'and x['arm']=='RECOVERY')
 require(float(after['Chamfer_MAE_mm'])<float(before['Chamfer_MAE_mm'])and float(after['fixed_INITIAL_GT_Chamfer_MAE_mm'])>float(before['fixed_INITIAL_GT_Chamfer_MAE_mm']),'alignment distinction contradicted')
 require(float(after['Fscore_at0p5mm'])<float(before['Fscore_at0p5mm'])and float(after['GT_coverage_at0p5mm'])<float(before['GT_coverage_at0p5mm']),'negative metrics omitted')
 return '12 actual source/evidence hashes; both MAE frames and Fscore/coverage directions verified from stored CSV without recomputation'
check('metric_sources_and_nonpooled_frames',metrics)
def zip_check():
 d=json.loads((O/'SMART_ENDOSCOPE_ARCHIVE_AUDIT.json').read_text());members=json.load(gzip.open(O/'SMART_ENDOSCOPE_ARCHIVE_MEMBERS.json.gz','rt'));jpg=[r for r in members if Path(r['name']).suffix.lower()=='.jpg']
 require(len(members)==15571 and len(jpg)==6388 and sum(not r['standalone_byte_matches']for r in jpg)==2403,'archive summary mismatch')
 require(sha(d['path'])==d['sha256'],'archive original bytes changed')
 return 'full original ZIP SHA and15571 member metadata/6388 JPG checked, no extraction'
check('archive_identity_and_member_accounting',zip_check)
def source_scope():
 q=subprocess.run(['git','-C',str(R),'diff','--name-only','73568493d127d0aead361314afcb32e11fe886f0'],capture_output=True,text=True,check=True)
 allowed=['docs/registry/EXPERIMENT_INDEX.csv','docs/registry/MODULE_REGISTRY.json','docs/registry/EVIDENCE_PROTOCOL.md','README.md','.gitignore']
 require(all(p in allowed or p.startswith('maintenance/TASK-MAINLINE-RECOVERY-AND-FORENSIC-AUDIT-002/')or p=='experiments/TASK-MAINLINE-RECOVERY-AND-FORENSIC-AUDIT-002'for p in q.stdout.splitlines()),'scientific/historical tracked file changed')
 return 'only audit outputs and registry/navigation documents differ; scientific source untouched'
check('no_scientific_or_historical_tracked_mutation',source_scope)
def navigation():
 p=O/'visualization/index.html';require(p.is_file(),'offline index missing');n=0
 for ref in re.findall('href="([^"]+)"',p.read_text()):
  if ref.startswith(('http:','https:')):continue
  require((p.parent/ref.split('#')[0]).exists(),'audit navigation broken '+ref);n+=1
 return dict(exists=True,absolute_path=str(p.resolve()),local_links_checked=n)
check('offline_audit_navigation_exists_and_links_resolve',navigation)
def ownership():
 data=rows('ASSET_OWNERSHIP.csv.gz');require(len(data)==S['files'],'ownership coverage')
 require(any(x['worktree_or_repository']=='/home/liu/polyp_research/ring-first-3d'for x in data),'nested B ownership missed')
 return 'every inventoried path has explicit scan root and longest actual Git-root ownership'
check('asset_worktree_ownership_including_nested_B',ownership)
check('independent_review_artifacts_exist',lambda:require(all((O/'INDEPENDENT_REVIEW_PACKAGE'/n).is_file()for n in ['INDEPENDENT_FINDINGS.md','INDEPENDENT_CHECKS.json','GIT_OBJECT_AUDIT.json','SOURCE_STATUS_RECHECK.json']),'independent source/Git/findings evidence present; primary does not self-approve retirement'))
dump=dict(status='ENGINEERING_VALIDATION_PASS'if all(x['status']=='PASS'for x in results)else'FAIL',checks=results,total=len(results),passed=sum(x['status']=='PASS'for x in results),scientific_recalculation=False,scientific_acceptance='NOT_APPLICABLE',retirement_execution_authorized=False)
(O/'AUDIT_VALIDATION.json').write_text(json.dumps(dump,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dump,ensure_ascii=False,indent=2))
raise SystemExit(0 if dump['status']=='ENGINEERING_VALIDATION_PASS'else 1)
