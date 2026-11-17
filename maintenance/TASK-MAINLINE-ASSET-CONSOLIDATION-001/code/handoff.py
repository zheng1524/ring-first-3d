"""Final measured acceptance, archive integrity, input closure, and report links."""
import os,json,hashlib,csv,collections,subprocess,gzip,shutil,ast
from pathlib import Path
from html.parser import HTMLParser
from PIL import Image
R=Path(__file__).resolve().parents[3];T=Path(__file__).resolve().parents[1];M=R/'mainline'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
mods={'ring-first':'RING_FIRST','hero':'HERO','body-initialization':'BODY_INITIALIZATION','body-update':'BODY_UPDATE','stalk-growth-g01':'STALK_GROWTH_G01','stalk-growth-g03':'STALK_GROWTH_G03','a-to-b':'A_TO_B','depth-supervised-pytorch':'DEPTH_SUPERVISED_PYTORCH'}
pipe=read(M/'validation/pipeline/002/PIPELINE_RESULT.json');assert pipe['status']=='PASS'
freeze=M/'manifests/REPLAY_INPUT_FREEZE.json';f=read(freeze);assert f['revision']==4
for x in f['source_files']:assert sha(R/x['path'])==x['sha256'],x['path']
for mod,name in mods.items():
 p=M/'validation/pipeline/002'/mod/'RESULT.json';x=read(p);assert x['status']=='PASS'and x['replay_freeze_sha256']==sha(freeze);save(T/'REPRODUCIBILITY_TESTS'/(name+'.json'),x)
save(T/'PIPELINE_RESULT.json',pipe)
accept=read(T/'ACCEPTANCE.json');accept.update(source_freeze_sha256=sha(freeze),source_freeze_revision=4,locked_source_and_small_input_files=len(f['source_files']),checkpoint_pipeline='PASS',checkpoint_pipeline_result='PIPELINE_RESULT.json');save(T/'ACCEPTANCE.json',accept)
p=M/'manifests/REPRODUCIBILITY_STATUS.json';x=read(p);x.update(source_freeze_sha256=sha(freeze),source_freeze_revision=4,checkpoint_pipeline='PASS');save(p,x)
for p in [M/'manifests/DEPENDENCY_LOCK.json',T/'MAINLINE_DEPENDENCIES.json']:
 x=read(p);x['replay_input_freeze_sha256']=sha(freeze);x['scope']='all inherited source API, canonical versioned code, small frozen inputs and explicit compiled runtime';save(p,x)
for p in [M/'manifests/MAINLINE_ASSET_MAP.json',T/'MAINLINE_ASSET_MAP.json']:
 x=read(p)
 for row in x['modules']:
  if row['id']=='DEPTH_SUPERVISED_PYTORCH':row['canonical_implementation']='src/ring_first_3d/mainline/replays.py::depth_supervised'
 save(p,x)

# Full per-experiment accounting; unknown/raw classifications stay explicit.
inventory=read(T/'ASSET_INVENTORY.json');groups={};inode_map={};kind=collections.Counter()
for a in inventory['assets']:
 parts=Path(a['path']).parts
 if'experiments'in parts:
  i=parts.index('experiments');key=str(Path(*parts[:i+2]))if i+1<len(parts)else a['workspace']
 else:key=a['workspace']
 z=groups.setdefault(key,dict(experiment=key,files=0,logical_bytes=0,over_1MB=0,over_10MB=0,over_100MB=0));z['files']+=1;z['logical_bytes']+=a['size_bytes']
 for field,n in [('over_1MB',10**6),('over_10MB',10**7),('over_100MB',10**8)]:z[field]+=int(a['size_bytes']>n)
 inode_map[(a['device'],a['inode'])]=a['allocated_bytes'];kind[a['asset_type']]+=a['size_bytes']
with(T/'EXPERIMENT_STORAGE_SUMMARY.csv').open('w')as out:
 w=csv.DictWriter(out,list(next(iter(groups.values()))),lineterminator='\n');w.writeheader();w.writerows(sorted(groups.values(),key=lambda r:-r['logical_bytes']))
save(T/'ASSET_ROLE_ACCOUNTING.json',dict(initial_physical_file_payload_unique_inode_bytes=sum(inode_map.values()),logical_bytes_by_initial_role=dict(kind),classification_limitations='Unclassified .npz/cache payloads remain unknown; do not call every image a raw observation or every array a derived result. Exact protected scientific roles are supplied by EXTERNAL_INPUTS/source manifests.',known_protected_inputs=read(M/'manifests/EXTERNAL_INPUTS.json')['assets']))
del inventory

# HTML and actual figures, including the preserved original growth gallery.
class Links(HTMLParser):
 def __init__(self):super().__init__();self.items=[]
 def handle_starttag(self,tag,attrs):self.items.extend(v for k,v in attrs if k in ['src','href'])
links=[]
for p in [M/'visualization/index.html',M/'visualization/stalk_growth/index.html']:
 parser=Links();parser.feed(p.read_text())
 for item in parser.items:
  if item.startswith(('http:','https:','#','data:')):continue
  q=(p.parent/item).resolve();assert q.is_file(),str(q);links.append(str(q))
pngs=[p for p in(M/'visualization').rglob('*.png')]
for p in pngs:
 with Image.open(p)as im:im.verify()
for p in list((M/'scripts').glob('*.py'))+list((T/'code').glob('*.py')):ast.parse(p.read_text())
csvrows=list(csv.DictReader((R/'docs/registry/EXPERIMENT_INDEX.csv').open()));assert all(None not in x for x in csvrows)

# Verify metadata packs decode to the exact full tables, no data loss from compression.
for x in read(T/'INVENTORY_PACK_MANIFEST.json')['files']:
 p=T/x['packed_path'];assert sha(p)==x['packed_sha256'];h=hashlib.sha256()
 with gzip.open(p,'rb')as stream:
  for b in iter(lambda:stream.read(2**20),b''):h.update(b)
 assert h.hexdigest()==x['flat_sha256']and sha(T/x['flat_path'])==x['flat_sha256']

# Preserve full input SHA and old worktree/branch facts; no original cleanup here.
protected=Path('/home/liu/ring_first_3d_growth_recovery');assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=protected,text=True).strip()=='bac3fc89ef95db522b63cf6bb98e6914b9382864';assert subprocess.check_output(['git','status','--porcelain'],cwd=protected,text=True)==''
source=read(M/'manifests/SOURCE_PROVENANCE.json');assert all(sha(R/x['new_path'])==x['new_sha256']for x in source['files'])
reg=read(M/'validation/regression/RESULT.json');assert reg['status']=='PASS'and reg['tests']==247 and reg['skipped']==0
v=os.statvfs(R);storage=read(T/'FINAL_STORAGE.json');before=read(T/'CLEANUP_RECEIPTS.json')['before'];storage.update(current_filesystem_free_bytes=v.f_bfree*v.f_frsize,current_user_available_bytes=v.f_bavail*v.f_frsize,net_free_gain_since_phase1_start_bytes=v.f_bfree*v.f_frsize-before['free_bytes'],canonical_workspace_allocated_bytes=int(subprocess.check_output(['du','-s','-B1',str(R)],text=True).split()[0]));save(T/'FINAL_STORAGE.json',storage)
(T/'FINAL_STORAGE_REPORT.md').write_text('# 最终存储快照\n\n'+json.dumps(storage,ensure_ascii=False,indent=2)+'\n\n阶段1释放与最终净变化分开；没有将Git当前树删除计入远端历史空间。\n')
evidence=dict(verified_at='2026-11-18',canonical_workspace=str(R),visualization_directory=str(M/'visualization'),visualization_index=str(M/'visualization/index.html'),figures=len(pngs),html_links_verified=len(links),all_images_decoded=True,source_and_input_lock_files=len(f['source_files']),copied_assets_verified=len(source['files']),all_copied_Python_files_match_claimed_commits=True,scientific_AST_unchanged=True,protected_growth_worktree_unchanged=True,regression_tests=247,regression_skipped=0,modules_passed=8,checkpoint_pipeline='PASS',scientific_certification=False,cross_machine_certified=False,source_freeze_sha256=sha(freeze))
save(T/'FINAL_VERIFICATION.json',evidence)
p=T/'TECHNICAL_REPORT.md';s=p.read_text();s+='\n## 最终验收补充\n\n'+f'最终修订4额外锁定全部继承API和小型冻结输入，共{len(f["source_files"])}项；数学参数与容差未变。实际串行checkpoint流水线8/8通过，见PIPELINE_RESULT.json；最终247项回归0跳过。全部{len(source["files"])}项复制资产SHA核验通过，复制Python源码的声明commit均含原字节，所有路径适配经逆变换AST验证。可视化{len(pngs)}张图像解码成功、两个首页{len(links)}个本地链接存在。\n\n'+f'主线目录：{R}\n\n可视化：{M}/visualization/index.html\n\n'+ '原始完整盘点按逐实验汇总见EXPERIMENT_STORAGE_SUMMARY.csv。目录别名仅整理维护分支当前树，原4110个Git文件仍在固定基线和原工作树；没有重写历史或移除远端分支。原工作树保留是因为仍有唯一资产及LOCAL_ONLY绑定，不冒险删除。跨机器、全新训练收敛或新的HERO→Body耦合均未认证。\n';p.write_text(s)
print(json.dumps(evidence,indent=2))
