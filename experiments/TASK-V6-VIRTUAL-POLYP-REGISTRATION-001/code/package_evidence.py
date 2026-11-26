"""Small run evidence archive, exact manifest, retention list. No full video or weights."""
import tarfile,subprocess
from common import *
def package():
 chosen=[RUN/'GENERATION_FREEZE.json']
 for directory in ['public','private','tracks','predictions','exports/V1/M2']:
  chosen += [p for p in (RUN/directory).rglob('*')if p.is_file()]
 members=[dict(member=str(p.relative_to(RUN)),sha256=sha(p),bytes=p.stat().st_size)for p in sorted(chosen)]
 archive=T/'evidence/RUN_EVIDENCE.tar.gz'
 with tarfile.open(archive,'w:gz')as tar:
  for p in sorted(chosen):tar.add(p,arcname=str(p.relative_to(RUN)),recursive=False)
 with tarfile.open(archive)as tar:
  by={m['member']:m for m in members}
  for member in tar.getmembers():assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==by[member.name]['sha256']
 save(T/'evidence/ARCHIVE_MANIFEST.json',dict(root='runs/RUN_001',members=members,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,verified_all_members=True,private_role='generator/evaluator only'))
 paths=[p for p in (T/'inputs').rglob('*')if p.is_file()]
 retain=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,protection='VERSIONED_TASK_INPUT')for p in paths]
 retain+=[dict(path=str(RUN),protection='LOCAL_FULL_RUN_RETAIN; selected replay archive in evidence/RUN_EVIDENCE.tar.gz'),dict(path='/home/liu/ring_first_3d_workspace/.runtime',protection='SHARED_RUNTIME_READONLY_RETAIN'),dict(path='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python',protection='SHARED_RUNTIME_READONLY_RETAIN')]
 for a in read(T/'evidence/ASSET_IDENTITIES.json'):retain.append(dict(path=a['source'],sha256=a['sha256'],protection='SHARED_ORIGINAL_RETAIN; task has small protected copy'))
 for a in read(T/'evidence/V6_INTERFACE.json'):
  for dep in a['dependencies']:retain.append(dict(**dep,protection='HIST_READONLY_RETAIN; selected files protected in task'))
 for k in ['track005.py','v6_common.py']:retain.append(dict(path=str(V6/k),sha256=sha(V6/k),protection='ORIGINAL_KERNEL_RETAIN; identical inputs/V6_KERNELS copy'))
 save(T/'evidence/RETAIN_DEPENDENCIES.json',retain)
 print('archive verified',len(members),'members',archive.stat().st_size,'bytes; retain',len(retain))
if __name__=='__main__':package()
