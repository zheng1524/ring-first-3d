import tarfile,hashlib,json
from pathlib import Path
OUT=Path('/dev/shm/mainline_consolidation_001')
root=Path('/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001')
reports=[]
for archive in sorted((root/'local_results').glob('*.tar.gz')):
 records=[];missing=[];changed=[]
 with tarfile.open(archive,'r|gz')as tar:
  for member in tar:
   name=Path(member.name)
   if name.is_absolute()or'..'in name.parts:raise RuntimeError('Unsafe archive member')
   p=root.parent/name
   if member.isdir():continue
   if not member.isfile():
    if member.issym()and p.is_symlink():continue
    missing.append(dict(name=member.name,type='nonregular'));continue
   h=hashlib.sha256();f=tar.extractfile(member)
   for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
   actual=h.hexdigest();current=None
   if p.is_file():
    h=hashlib.sha256()
    with p.open('rb')as f:
     for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    current=h.hexdigest()
   if current is None:missing.append(member.name)
   elif current!=actual:changed.append(member.name)
   records.append(dict(member=member.name,retained_path=str(p),archive_content_sha256=actual,retained_sha256=current,bytes=member.size))
 rep=dict(archive=str(archive),all_member_contents_preserved=not missing and not changed,members=records,missing=missing,changed=changed)
 reports.append(rep);print(archive.name,'members',len(records),'missing',len(missing),'changed',len(changed),flush=True)
(OUT/'ARCHIVE_CONTENT_VERIFICATION.json').write_text(json.dumps(reports,indent=2)+'\n')
