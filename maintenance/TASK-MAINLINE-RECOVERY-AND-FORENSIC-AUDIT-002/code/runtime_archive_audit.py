"""Read-only environment, ZIP-member and explicitly referenced external-file audit."""
import os,sys,json,csv,sqlite3,pathlib,hashlib,subprocess,zipfile,gzip,collections
P=pathlib.Path;OUT=P(__file__).resolve().parents[1];OLD=P('/home/liu/ring_first_3d_mainline')
c=sqlite3.connect('file:'+str(OUT/'ASSET_INVENTORY.sqlite')+'?mode=ro',uri=True)
def dump(name,d): (OUT/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def command(cmd,env=None):
 try:
  r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=90,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':'/dev/shm','MPLCONFIGDIR':'/dev/shm/forensic_audit_mpl','OMP_NUM_THREADS':'2',**(env or {})})
  return dict(command=list(map(str,cmd)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
 except Exception as e:return dict(command=list(map(str,cmd)),error=str(e))
probe="""import sys,json,sysconfig,importlib,importlib.metadata as m
d=dict(executable=sys.executable,version=sys.version,prefix=sys.prefix,base_prefix=sys.base_prefix,SOABI=sysconfig.get_config_var('SOABI'),EXT_SUFFIX=sysconfig.get_config_var('EXT_SUFFIX'),packages={})
for name in ['torch','torchvision','pytorch3d','open3d','python-fcl','numpy','scipy','nvdiffrast','trimesh','transformers']:
 try:d['packages'][name]=m.version(name)
 except m.PackageNotFoundError:d['packages'][name]='NOT_IN_DEFAULT_METADATA'
try:
 import torch
 d['torch']=dict(path=torch.__file__,version=torch.__version__,cuda=torch.version.cuda,cxx11_abi=torch._C._GLIBCXX_USE_CXX11_ABI,cuda_available=torch.cuda.is_available())
except Exception as e:d['torch_import_error']=str(e)
print(json.dumps(d))
"""
envs=[];commands=[]
configs=[P(x[0]) for x in c.execute('SELECT path FROM assets WHERE path LIKE "%/pyvenv.cfg"')]
for cfg in configs:
 env=cfg.parent;exe=env/'bin/python';row=dict(environment_path=str(env),config=cfg.read_text(),config_sha256=sha(cfg),python_symlink_realpath=str(exe.resolve()),size_recorded_paths_bytes=c.execute('SELECT coalesce(sum(size),0) FROM assets WHERE path LIKE ?',(str(env)+'/%',)).fetchone()[0],size_unique_inode_allocated_bytes=c.execute('SELECT coalesce(sum(allocated),0) FROM (SELECT max(allocated) allocated FROM assets WHERE path LIKE ? GROUP BY dev,inode)',(str(env)+'/%',)).fetchone()[0],current_referencers=[x[0] for x in c.execute('SELECT distinct source FROM refs WHERE target LIKE ?',(str(env)+'%',))],unique='UNVERIFIED_NOT_DISPOSABLE',rebuild='REQUIRES_ABI_AND_WHEELS_NOT_CERTIFIED',hidden_dependencies='absolute base interpreter, vendor sys.path and compiled extensions; see probe and dependency references')
 result=command([exe,'-c',probe]);commands.append(result)
 try:row['probe']=json.loads(result.get('stdout',''))
 except ValueError:row['probe']=result
 envs.append(row)
print('ENVIRONMENTS',len(envs),flush=True)
# Probe the actual primary layered runtime, without inference/training or package writes.
layered=command([OLD/'mainline/scripts/python.sh','-c',"import json,importlib; d={};\nfor n in ['torch','pytorch3d','open3d','fcl','nvdiffrast','ring_first_3d']:\n try:\n  m=importlib.import_module(n);d[n]={'file':getattr(m,'__file__',None),'version':getattr(m,'__version__','not_declared')}\n except Exception as e:d[n]={'error':str(e)}\nprint(json.dumps(d))"])
commands.append(layered)
dump('RUNTIME_PROBE_COMMANDS.json',commands)
dump('RUNTIME_ENVIRONMENTS.json',dict(environments=envs,mainline_layered_runtime=layered,limitations='No environments were created, installed, deleted or trained. Directory symlinks in inventory not followed. Environment probes may use a shared base interpreter and do not establish cross-machine rebuildability.'))
fields=['environment_path','python_realpath','python_version','torch_version','CUDA','ABI','key_packages','size_unique_inode_allocated_bytes','referencers','unique','rebuild','hidden_dependencies']
with (OUT/'RUNTIME_ENVIRONMENT_MATRIX.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fields);w.writeheader()
 for row in envs:
  d=row['probe'];t=d.get('torch',{})
  w.writerow(dict(environment_path=row['environment_path'],python_realpath=row['python_symlink_realpath'],python_version=d.get('version','PROBE_FAILED'),torch_version=t.get('version','UNAVAILABLE'),CUDA=t.get('cuda'),ABI=json.dumps({k:d.get(k) for k in ['SOABI','EXT_SUFFIX']}|{'cxx11_abi':t.get('cxx11_abi')}),key_packages=json.dumps(d.get('packages',{})),size_unique_inode_allocated_bytes=row['size_unique_inode_allocated_bytes'],referencers=json.dumps(row['current_referencers']),unique=row['unique'],rebuild=row['rebuild'],hidden_dependencies=row['hidden_dependencies']))
dump('SYSTEM_RUNTIME.json',dict(nvidia=command(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv']),nvcc=command(['nvcc','--version']),blender=command(['/home/liu/blender/blender-5.0.1-linux-x64/blender','--version']),official_model_provenance=json.loads((OLD/'mainline/manifests/SOURCE_PROVENANCE.json').read_text()),dependency_lock=json.loads((OLD/'mainline/manifests/DEPENDENCY_LOCK.json').read_text())))

archive=P('/home/liu/polyp_research/smart_endoscope_20260805.zip');members=[]
with zipfile.ZipFile(archive) as z:
 for info in z.infolist():
  row=dict(name=info.filename,size=info.file_size,compressed_size=info.compress_size,CRC32=info.CRC,archive_timestamp=info.date_time,is_directory=info.is_dir())
  if not info.is_dir():
   h=hashlib.sha256()
   with z.open(info,'r') as f:
    for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
   row['sha256']=h.hexdigest();row['hash_status']='HASH_RECOMPUTED'
   row['standalone_byte_matches']=[x[0] for x in c.execute('SELECT path FROM assets WHERE sha256=? AND size=? AND kind="file"',(row['sha256'],info.file_size))]
  members.append(row)
jpg=[r for r in members if P(r['name']).suffix.lower() in ['.jpg','.jpeg']]
dump('SMART_ENDOSCOPE_ARCHIVE_AUDIT.json',dict(path=str(archive),sha256=sha(archive),hash_status='HASH_RECOMPUTED',size=archive.stat().st_size,members=len(members),jpg_members=len(jpg),jpg_with_standalone_identical_bytes=sum(bool(r.get('standalone_byte_matches')) for r in jpg),jpg_without_standalone_identical_bytes=sum(not r.get('standalone_byte_matches') for r in jpg),method='ZIP central directory plus in-memory streaming of member bytes for SHA256 and CRC verification. NO disk extraction, no source writes. Byte identity only; renamed/recompressed/visually similar images are not proven recoverable.',comparison_scope='All regular files in ASSET_INVENTORY; external directories outside scope not presumed complete',decision='KEEP_UNIQUE_RAW_ARCHIVE_DO_NOT_RETIRE'))
with gzip.open(OUT/'SMART_ENDOSCOPE_ARCHIVE_MEMBERS.json.gz','wt') as f:json.dump(members,f,ensure_ascii=False)
print('ZIP',len(members),len(jpg),flush=True)
# Audit explicit external files. Do not recursively claim coverage over arbitrary outside projects.
external=[]
for (target,) in c.execute('SELECT distinct target FROM refs WHERE scope="EXTERNAL_DEPENDENCY" AND exists_now=1'):
 p=P(target)
 try:
  s=p.stat();row=dict(path=target,realpath=str(p.resolve()),kind='file' if p.is_file() else 'directory',size=s.st_size,scope='EXTERNAL_RESEARCH_DEPENDENCY',action='KEEP')
  if p.is_file():row.update(sha256=sha(p),hash_status='HASH_RECOMPUTED')
  else:row.update(sha256=None,hash_status='NOT_APPLICABLE_DIRECTORY',coverage='REFERENCED_DIRECTORY_ONLY_NOT_RECURSIVELY_HASHED')
  external.append(row)
 except OSError as e:external.append(dict(path=target,error=str(e)))
dump('EXTERNAL_DEPENDENCY_AUDIT.json',dict(assets=external,limitations='Only concrete existing static references outside the registered roots. Dynamic values, files only addressed by glob/template and arbitrary unreferenced external folders remain UNRESOLVED; no completeness claim across /home/liu.'))
print('EXTERNAL',len(external),flush=True)
