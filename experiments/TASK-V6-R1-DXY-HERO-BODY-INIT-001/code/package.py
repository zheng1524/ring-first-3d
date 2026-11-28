"""Upload compact parameters/inputs/evidence; leave all upstream imagery and full gallery local."""
from core import *
import tarfile
def main():
 archive=T/'evidence/CORE_RESULTS.tar.gz';paths=[]
 for root in [T/'runs/inputs',T/'runs/observations',T/'runs/results',T/'runs/control']:
  paths.extend(p for p in root.rglob('*')if p.is_file()and p.suffix not in ['.png','.html','.lock']and p.name not in ['FIGURES.json'])
 # Preserve the actual small historical code definitions, not only pointers.
 paths.extend(p for p in (T/'runtime/pinned').rglob('*.py'))
 paths.extend(p for p in (T/'runtime/pinned').rglob('*.json')if p.name in ['PROTOCOL.json','DECISION.json','config.json','source_lock.json','SOURCES_FROZEN.json'])
 # The new zero-HERO M4 supplements are local scientific evidence too: protect
 # actual matched tracks, independently triangulated points and Ring priors.
 supplement=T/'runtime/pinned'/BASE/'experiments/TASK-V6-R1-M4-REGISTRATION-MAINLINE-002/runs'
 paths.extend(p for p in supplement.rglob('*')if p.is_file()and p.suffix in ['.npz','.json'])
 paths=sorted(set(paths));records=[dict(path=str(p.relative_to(T)),sha256=sha(p),bytes=p.stat().st_size)for p in paths]
 with tarfile.open(archive,'w:gz',compresslevel=6)as tf:
  for p in paths:tf.add(p,arcname=str(p.relative_to(T)),recursive=False)
 assert archive.stat().st_size<90*1024**2,'Keep GitHub archive below 90 MiB; split rather than discard results'
 with tarfile.open(archive)as tf:
  members=tf.getmembers();assert len(members)==len(records)
  for member,rec in zip(members,records):assert member.name==rec['path']and hashlib.sha256(tf.extractfile(member).read()).hexdigest()==rec['sha256']
 save(T/'evidence/ARCHIVE_MANIFEST.json',dict(archive=asset(archive),files=records,scope='all compact fixed observations, coarse meshes, parameters, biases, planes, provenance, visibility and historical code; no upstream RGB/video/weights; full gallery remains local',gallery=str(T/'runs/results/index.html'),extract='tar -xzf evidence/CORE_RESULTS.tar.gz -C .',verify='each extracted path and SHA is listed here'))
 print('ARCHIVE',archive.stat().st_size,len(records),flush=True)
if __name__=='__main__':main()
