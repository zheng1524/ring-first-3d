"""Freeze a new leaf manifest, retaining historical metadata and small examples."""
from audit import *
from protected_delete import protected,open_inodes,OLD

inv=read(O/'INVENTORY_BEFORE.json');protection=read(T/'PROTECTED_PATHS.json');rows=protection['paths']
def protect(p,reason):rows.append(dict(path=str(p),real_path=str(Path(p).resolve()),reason=reason,consumer='本轮退役路线代表证据保留',exists=Path(p).exists()))
protect(W/'runs/m2f12_historical004/H004_RAW_BASELINE/GP_Ip_12.0mm_closed_R10_single_refY_005','完整H004代表视频：相机、地图、输入及有限HERO')
protect(W/'runs/m2f13_hero_all/H004/GP_Ip_12.0mm_closed_R10_single_refY_005/view_004','一个完整新增H004面源、原生深度、原Mesh和映射证据')
for route in ['H004','V6']:
 candidates=sorted((W/'runs/m2f13_hero_all/source_evaluation').glob(route+'*'))
 if candidates:protect(candidates[0],'一套完整历史评价代表，其他逐面数值指标仍保留')
# Coherent native + mesh example per old strategy run, not an arbitrary pretty result.
groups=collections.defaultdict(list)
for r in inv:
 p=Path(r['path'])
 if p.parent.name=='raw' and p.suffix=='.npz':
  key=(r['route'],p.relative_to(r['root']).parts[0]);groups[key].append(p)
for (route,run),candidates in groups.items():
 p=sorted(candidates)[0];protect(p,'保留按路径顺序首个原生深度代表，未按结果择优')
 for q in (p.parent.parent/'meshes').glob(p.stem+'*'):protect(q,'与保留原生深度同源的原Mesh/点云')
for route in {r['route'] for r in inv}:
 images=sorted(Path(r['path']) for r in inv if r['route']==route and Path(r['path']).suffix.lower()=='.png' and any(s in Path(r['path']).parts for s in ['visualization','figures']))
 for p in images[:2]:protect(p,'少量真实诊断图保留；完整已交付图在原任务工作树')
# Expand newly retained examples through real symlink targets AND their JSON inputs.
# Scope recursion to candidate trees; existing external roots already remain protected.
allowed=[Path(x['root']) for x in inv];allowed=list(set(allowed));closure=[]
queue=[Path(r['path']) for r in rows if r['consumer']=='本轮退役路线代表证据保留']
# Ancestor assets may hold links into candidates even when their own roots are protected.
queue.append(W/'assets');visited=set()
while queue:
 q=queue.pop()
 if str(q) in visited or not q.exists():continue
 visited.add(str(q));members=[]
 if q.is_dir():
  for a,ds,fs in os.walk(q,followlinks=False):
   members += [Path(a,n) for n in ds+fs if Path(a,n).is_symlink()]
   if q!=W/'assets':members += [Path(a,n) for n in fs if Path(a,n).suffix=='.json']
   ds[:]=[n for n in ds if not Path(a,n).is_symlink()]
 else:members=[q]
 for member in members:
  targets=[]
  if member.is_symlink():targets.append(member.resolve())
  if member.suffix=='.json' and member.is_file():
   try:targets += [Path(v) for v in strings(read(member)) if v.startswith('/home/liu/') and Path(v).exists()]
   except (ValueError,OSError):pass
  for target in targets:
   if any(under(target,root) for root in allowed):
    protect(target,'完整代表/祖先的链接与manifest真实依赖闭包');closure.append(dict(consumer=str(member),target=str(target),kind='symlink' if member.is_symlink() else 'manifest'))
    if str(target) not in visited:queue.append(target)
save(T/'evidence/REPRESENTATIVE_CLOSURE.json',closure)
rows=list({(r['path'],r['reason'],r['consumer']):r for r in rows}.values());protection['paths']=rows
save(T/'PROTECTED_PATHS.json',protection);table(T/'PROTECTED_PATHS.csv',rows)
paths={r[k] for r in rows for k in ['path','real_path']};opened=open_inodes()
proposed=[];kept=[]
binary={'.npz','.npy','.ply','.png','.jpg','.jpeg'}
for r in inv:
 p=Path(r['path']);parts=set(p.parts);reason=None
 if protected(p,paths) or protected(p.resolve(),paths):reason='CURRENT_CONSUMER_OR_REPRESENTATIVE'
 elif not r['regular']:reason='SYMLINK_OR_NONREGULAR_NO_TOUCH'
 elif (r['device'],r['inode']) in opened:reason='OPEN_INODE'
 elif p.suffix.lower() not in binary:reason='SOURCE_CONFIG_INPUT_IDENTITY_METRICS_LOG_OR_UNKNOWN_KIND'
 elif any(s in p.name.lower() for s in ['ground_truth','virtual_gt','calibration']) or p.stem.lower() in ['gt','ring','r5','r10']:reason='GT_CAD_CALIBRATION'
 elif r['route']=='m2f12_historical004' and (parts & {'landmarks','cameras'} or 'camera' in p.name.lower()):reason='H004_CAMERA_LANDMARK_METHOD_EVIDENCE'
 elif p.suffix.lower() in {'.png','.jpg','.jpeg'} and not (re.search(r'(raw\d|hero|fig|overlay|mask|rgb|depth|render|diagnostic)',p.name,re.I) or parts & {'masks','rgb','visualization','figures','frames'}):reason='IMAGE_ORIGIN_NOT_CONFIRMED'
 if reason:kept.append(dict(r,reason=reason))
 else:proposed.append(dict(r,reason='Retired generated depth/mesh/point/frame/feature/render cache; source/config/input identity/metrics and representative evidence retained; absent from live and future consumer closure'))
# If another link is outside this exact removal set, retain all aliases conservatively.
groups=collections.defaultdict(list)
for r in proposed:groups[(r['device'],r['inode'])].append(r)
planned=[]
for rr in groups.values():
 if len(rr)!=rr[0]['nlink']:
  kept += [dict(r,reason='EXTERNAL_OR_PROTECTED_HARDLINK_ALIAS') for r in rr]
 else:planned+=rr
for r in planned:r['sha256']=sha(r['path'])
save(O/'RETAINED_LEAVES.json',kept)

# Static read-set: protected old leaves, all live source/config, frozen method,
# original videos/model by metadata (no full raw/model rehash), explicit retained manifests.
static={}
def keepstat(p,hash_content=False):
 p=Path(p)
 if not p.is_file():return
 q=p.resolve();r=identity(q)
 if hash_content:r['sha256']=sha(q)
 static[str(q)]=r
for r in kept:
 if r['regular']:keepstat(r['path'],Path(r['path']).suffix in {'.py','.json','.yaml','.yml','.toml','.sh','.md','.csv','.patch'})
for root in [W/'src',W/'tools']+[D/n/s for n in ['TASK-V6-RAW-TO-HERO-001','TASK-V6-FULL-RUN-001','TASK-V6-TRUSTED-CLEAN-001','TASK-RING-SIFT-COMPARISON-001','TASK-M2F10','TASK-M2F12'] for s in ['src','tools']]:
 for p in files(root):
  if p.suffix in {'.py','.json','.yaml','.yml','.toml','.sh','.md'}:keepstat(p,True)
for p in [B/'start.sh',B/'SNAPSHOT.json',Path(read(B/'SNAPSHOT.json')['config']),Path(read(read(B/'SNAPSHOT.json')['config'])['manifest']),Path('/home/liu/ring-first-hero-core/site_config.local.json')]:keepstat(p,True)
for p in (B/'protocols').glob('*.json'):
 keepstat(p,True);static[str(p.resolve())]['allow_identical_atomic_rewrite']=True
 for name in read(p).get('files',{}):keepstat(name,Path(name).suffix in {'.py','.json','.yaml','.sh'})
for p in (Path(read(B/'SNAPSHOT.json')['snapshot'])/'src').rglob('*.py'):keepstat(p,True)
for r in read(O/'HEALTH_BEFORE.json')['raw_future_readability']:keepstat(r['path'],False)
for c in read(CT/'config/SOURCES_FROZEN.json')['cases']:
 for p,h in c['artifacts'].items():assert sha(p)==h;keepstat(p,True)
for p in [CT/'METHOD.md',CT/'TECHNICAL_REPORT.md',CT/'config/SOURCES_FROZEN.json',CT/'evidence/VERIFICATION.json',CT/'evidence/RENDER_RECEIPT.json',W/'runs/m2f5_unified/cad/R5.npz',W/'runs/m2f5_unified/cad/R10.npz',OLD]:keepstat(p,True)
for item in protection['dependency_manifests']:
 p=Path(item['path']);keepstat(p,True)
 for s in strings(read(p)):
  if s.startswith('/home/liu/') and Path(s).is_file():keepstat(s,Path(s).suffix in {'.py','.json','.md','.csv'})
virtual=D/'TASK-V6-VIRTUAL-REG-001/experiments/TASK-V6-VIRTUAL-POLYP-REGISTRATION-001/runs/RUN_001'
for p in files(virtual):keepstat(p,False)
for root in [W/'runs/v6_raw_to_hero_001',W/'runs/v6_trusted_clean_restore_001']:
 for p in files(root):
  if p.is_file() and not any(x in p.parts for x in ['runtime','__pycache__']) and p.suffix not in {'.log','.lock'}:keepstat(p,p.suffix in {'.py','.json','.csv'})
for p in (W/'runs/v6_trusted_clean_restore_001').glob('source*/COMPLETE.json'):
 for q,h in read(p)['outputs'].items():assert sha(q)==h;keepstat(q,True)
save(O/'STATIC_BEFORE.json',dict(created_beijing=now(),files=list(static.values()),raw_model_hash_policy='stat identity and existing declared hash; no whole raw/model rehash'))
table(T/'evidence/STATIC_IDENTITIES.csv',list(static.values()))
routes=sorted({r['route'] for r in planned},key=lambda route:-sum(r['blocks'] for r in planned if r['route']==route))
plan=dict(task=T.name,created_beijing=now(),roots=sorted({r['root'] for r in inv}),protected_sha256=sha(T/'PROTECTED_PATHS.json'),static_sha256=sha(O/'STATIC_BEFORE.json'),historical_guard_path=str(OLD),historical_guard_sha256=sha(OLD),batch_order=routes,files=planned,allowed_scope='exact new manifest regular leaf files only; no old manifest replay; no recursive directory removal')
save(O/'DELETE_PLAN.json',plan);table(T/'CLEANUP_MANIFEST.csv',[dict(r,status='PLANNED',dependency_result='NO_CURRENT_OR_FUTURE_CONSUMER') for r in planned]);save(T/'evidence/PLAN_IDENTITY.json',dict(path=str(O/'DELETE_PLAN.json'),sha256=sha(O/'DELETE_PLAN.json'),protected_sha256=plan['protected_sha256'],static_sha256=plan['static_sha256'],historical_guard_sha256=plan['historical_guard_sha256']))
summary=[]
for route in sorted({r['route'] for r in inv}):
 rr=[r for r in planned if r['route']==route];kk=[r for r in kept if r['route']==route];ins={(r['device'],r['inode']):r for r in rr}
 summary.append(dict(route=route,planned_files=len(rr),expected_last_link_bytes=sum(r['blocks'] for r in ins.values()),retained_files=len(kk),retained_bytes_within_root=sum(r['blocks'] for r in {(r['device'],r['inode']):r for r in kk}.values()),reasons=dict(collections.Counter(r['reason'] for r in kk))))
save(T/'evidence/PLAN_SUMMARY.json',summary)
print('PLAN',len(planned),'leaves',sum(x['expected_last_link_bytes'] for x in summary),'bytes; static',len(static));print([(x['route'],x['planned_files'],round(x['expected_last_link_bytes']/2**20,2)) for x in summary])
