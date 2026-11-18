import pathlib,json,csv,gzip,hashlib,zipfile,os,subprocess,collections
P=pathlib.Path(__file__).resolve().parent.parent;O=P/'INDEPENDENT_REVIEW_PACKAGE';R=P.parents[1]
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb')as f:
  while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
checks={};zpath=pathlib.Path('/home/liu/polyp_research/smart_endoscope_20260805.zip');claim=json.load(open(P/'SMART_ENDOSCOPE_ARCHIVE_AUDIT.json'));sha_z=sha(zpath)
with zipfile.ZipFile(zpath)as z:
 infos=z.infolist();jpg=[i for i in infos if i.filename.lower().endswith('.jpg')];allclaim=json.load(gzip.open(P/'SMART_ENDOSCOPE_ARCHIVE_MEMBERS.json.gz','rt'));mp={r['name']:r for r in allclaim};samples=[]
 for i in jpg[::max(1,len(jpg)//12)][:12]:
  h=hashlib.sha256()
  with z.open(i)as f:
   while b:=f.read(1024*1024):h.update(b)
  c=mp[i.filename];samples.append(dict(member=i.filename,sha256=h.hexdigest(),claim_sha256=c.get('sha256'),match=h.hexdigest()==c.get('sha256'),size_match=i.file_size==c['size'],CRC32_match=i.CRC==c['CRC32']))
checks['archive']=dict(archive_sha256=sha_z,claim_hash_match=sha_z==claim['sha256'],members=len(infos),jpg_members=len(jpg),member_counts_match=(len(infos),len(jpg))==(claim['members'],claim['jpg_members']),independent_streaming_member_samples=samples,disk_extraction=False)
modules=json.load(open(R/'docs/registry/MODULE_REGISTRY.json'))['modules'];mr=[]
for m in modules:
 if not m['id'].startswith(('SU','SB','GR')):continue
 p=R/m['path'];orig=m.get('original_source',{});r=dict(id=m['id'],path=str(p),exists=p.exists(),source_sha_match=p.exists()and sha(p)==m['sha256'],source_commit=m.get('source_commit'),execution_commit=m.get('execution_commit'),original_sha_match=bool(orig.get('exists'))and sha(pathlib.Path(orig['path']))==orig['sha256'],execution_evidence_exists=all(pathlib.Path(e['path']).exists()for e in m.get('execution_evidence',[])))
 source=p.name;task=m['source_task'];target=f'experiments/{task}/code/{source}'
 if m.get('source_commit')and m['source_commit']!='SOURCE_COMMIT_UNVERIFIED':
  proc=subprocess.run(['git','-C',str(R),'show',m['source_commit']+':'+target],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
  r['publication_snapshot_git_sha_match']=(proc.returncode==0 and hashlib.sha256(proc.stdout).hexdigest()==orig.get('sha256'))
 mr.append(r)
checks['restored_modules']=dict(count=len(mr),records=mr,caveat='Publication source Git bytes matching is not automatic proof of actual execution identity. Frozen run contract checks and per-stage identity remain required.')
links=list(csv.DictReader(open(P/'REPORT_LINK_AUDIT.csv')));lr=[]
for status in ['VALID','MOVED_TARGET','EXTERNAL_DEPENDENCY']:
 candidates=[r for r in links if r['status']==status and r['sha256']and pathlib.Path(r['resolved_path']).is_file()and pathlib.Path(r['resolved_path']).stat().st_size<2000000]
 for r in candidates[:12]:lr.append(dict(source=r['source'],reference=r['reference'],status=status,resolved_path=r['resolved_path'],sha_match=sha(pathlib.Path(r['resolved_path']))==r['sha256']))
checks['link_samples']=lr
pres=json.load(open(P/'HISTORICAL_REPORT_PRESERVATION.json'));checks['historical_reports']=[dict(path=d['path'],original=d['original_path'],copy_sha_match=sha(pathlib.Path(d['path']))==d['sha256'],original_sha_match=sha(pathlib.Path(d['original_path']))==d['expected_sha256'])for d in pres]
checks['symlinks_corrected_export_rows']=sum(1 for _ in csv.DictReader(gzip.open(P/'SYMLINKS.csv.gz','rt')))
checks['metric_paths']=[dict(metric_id=r['metric_id'],code_exists=pathlib.Path(r['code_path']).is_file(),evidence_exists=pathlib.Path(r['evidence_path']).is_file(),code_sha_match=pathlib.Path(r['code_path']).is_file()and sha(pathlib.Path(r['code_path']))==r['code_sha256'],evidence_sha_match=pathlib.Path(r['evidence_path']).is_file()and sha(pathlib.Path(r['evidence_path']))==r['evidence_sha256'])for r in csv.DictReader(open(P/'METRIC_DEFINITION_MATRIX.csv'))]
json.dump(checks,open(O/'FINAL_PACKAGE_CHECKS.json','w'),ensure_ascii=False,indent=2)
print('Archive',checks['archive']['claim_hash_match'],checks['archive']['members'],checks['archive']['jpg_members']);print('module count',len(mr),'mismatch',[r for r in mr if not all(r.get(k,True)for k in ['source_sha_match','original_sha_match','execution_evidence_exists','publication_snapshot_git_sha_match'])]);print('metric issues',[r for r in checks['metric_paths']if not all(v for k,v in r.items()if k!='metric_id')]);print('links',len(lr),all(r['sha_match']for r in lr),'reports',len(pres),'symlinks',checks['symlinks_corrected_export_rows'])
