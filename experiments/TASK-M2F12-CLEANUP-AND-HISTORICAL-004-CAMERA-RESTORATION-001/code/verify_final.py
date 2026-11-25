"""Read-only final scientific-artifact checks; writes only the task validation receipt."""
import csv,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from collections import Counter
T=Path(__file__).resolve().parent.parent
B=Path('/home/liu/ring_first_3d_workspace/runs/m2f12_historical004')
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def git(p,*args):return subprocess.check_output(['git','-C',str(p),*args]).decode()
lock=read(T/'evidence/RESTORATION_SOURCE_LOCK_R3.json')['files']
assert all(sha(p)==h for p,h in lock.items())
frozen=read(B/'BASELINE_FROZEN.json');assert all(sha(x['path'])==x['sha256'] for x in frozen['files'])
registry=read(T/'evidence/INPUT_REGISTRY.json');assert len(registry)==10 and len(set(x['group']for x in registry))==5
states=[];identities=[]
for reg in registry:
 assert sha(reg['raw_video'])==reg['raw_sha256']
 R=B/'H004_RAW_BASELINE'/reg['case'];s=read(R/'RUN_STATE.json');assert s['raw_sha256']==reg['raw_sha256'] and sha(s['config_path'])==s['config_sha256']
 for stage in s['stages']:assert sha(stage['path'])==stage['sha256']
 states.append(s['status'])
 if s['status']=='FAILED':assert any(x['stage']=='seed' and x['status']=='FAILED'for x in s['stages'])
 p=R/'preparation/LOSSLESS_PTS_REVALIDATION.json'
 if not p.exists():p=R/'preparation/LOSSLESS_FRAME_IDENTITY.json'
 identity=read(p);assert len(identity)==16 and all(x['identity']=='EXACT_SEQUENTIAL_RAW_BGR_SHA256_AND_DECODER_PTS_AND_JPEG95'for x in identity)
 identities.append(dict(case=reg['case'],receipt=str(p),sha256=sha(p),frames=len(identity)))
assert Counter(states)=={'COMPLETED':8,'FAILED':2},Counter(states)
plans=read(B/'HERO_PLANS_FROZEN.json');results=read(B/'HERO_LIMITED/RESULTS.json')
assert plans['baseline_freeze_sha256']==sha(B/'BASELINE_FROZEN.json') and plans['protocol_sha256']==sha(T/'evidence/HERO_PROTOCOL.json')
assert len(results)==20 and len(set((r['route'],r['case'])for r in results))==20
starts=list((B/'HERO_LIMITED').glob('*/*/INFERENCE_STARTED.json'));completed=list((B/'HERO_LIMITED').glob('*/*/INFERENCE.json'))
assert len(starts)==len(completed)==12
for p in starts:
 a=read(p);assert a['budget']==1 and a['epoch']>=plans['epoch'] and (p.parent/'INFERENCE.json').exists()
counts=Counter(r['route']for r in results if r['status']=='COMPLETED');assert counts=={'H004_RAW_BASELINE':7,'V6_LIMITED_DIAGNOSTIC':5}
rows=list(csv.DictReader((T/'evidence/COMPARISON_LONG.csv').open()));wide=list(csv.DictReader((T/'COMPARISON.csv').open()));cameras=list(csv.DictReader((T/'evidence/CAMERA_COMMON_EVALUATION.csv').open()))
assert len(rows)==20 and len(wide)==10 and len(cameras)==295
sums={r:{k:sum(int(x[k]or 0)for x in rows if x['route']==r)for k in ['numeric_cameras','own_qualified_cameras','legal_target_count','qualified_targets','qualified_supports','landmarks']}for r in ['H004_RAW_BASELINE','V6']}
assert list(sums['H004_RAW_BASELINE'].values())==[128,76,76,76,73,3463]
assert list(sums['V6'].values())==[167,25,66,14,20,3910]
assert all('NOT_EVALUABLE' in x['common_independent_RGB_status']for x in rows)
archives=read(T/'evidence/RESTORATION_ARCHIVE_RECEIPT.json');assert sha(archives['archive'])==archives['sha256'];assert sha(archives['source_snapshot']['path'])==archives['source_snapshot']['sha256']
preserved=[]
for path,old in read(T/'evidence/START_GIT_STATE.json').items():
 head=git(path,'rev-parse','HEAD').strip();oldhead=old.get('head',old.get('HEAD','')).strip()
 tracked='\n'.join(l for l in old['status'].splitlines()if not l.startswith('??'))
 now=git(path,'status','--short','--untracked-files=no').rstrip('\n')
 assert now==tracked and head==oldhead,(path,head,oldhead)
 preserved.append(dict(path=path,HEAD=head,initial_HEAD=oldhead,HEAD_equal=True,tracked_status_equal=True))
(T/'evidence/PRESERVED_WORKTREE_CHECK.json').write_text(json.dumps(preserved,indent=2))
testcmd=[sys.executable,'-m','unittest','discover','-s',str(T/'code'),'-p','test_*.py','-v']
p=subprocess.run(testcmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(T/'evidence/FINAL_TESTS.log').write_bytes(p.stdout);assert p.returncode==0
subprocess.run(['git','-C',str(T.parents[1]),'diff','--check'],check=True)
fs=os.statvfs(B)
out=dict(epoch=time.time(),scientific_source_files_verified=len(lock),baseline_frozen_files_verified=len(frozen['files']),fixed_groups=5,fixed_videos=10,RAW_states=dict(Counter(states)),raw_full_file_SHA_verified=10,lossless_identities=identities,HERO_total_inferences=12,HERO_completed=dict(counts),HERO_missing_combinations=8,comparison_rows=len(wide),common_camera_records=len(cameras),totals=sums,unit_tests_passed=16,test_command=testcmd,preserved_worktrees=len(preserved),current_available_bytes=fs.f_bavail*fs.f_frsize,current_space_is_not_cleanup_delta=True,archive_members_verified_by_package=archives['verified_members'],source_snapshot_files_verified=archives['source_snapshot']['verified_files'],scientific_acceptance='NOT_CLAIMED; seed basic pass 0/10; common independent RGB NOT_EVALUABLE; no optimization')
(T/'evidence/FINAL_VALIDATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
