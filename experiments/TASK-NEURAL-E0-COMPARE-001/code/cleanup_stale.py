"""One-off user-authorized deletion of explicitly invalid V8 download artifacts."""
from pathlib import Path
import hashlib,json,os,shutil,datetime
R=Path(__file__).resolve().parents[1]
old=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v8_registration_narrow_baseline')
w=old/'weights';out=R/'provenance/USER_AUTHORIZED_CLEANUP.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
assert not out.exists(),'refuse to repeat one-off cleanup'
evidence=(w/'INCOMPLETE_DO_NOT_LOAD.md').read_text();record=json.loads((old/'metrics/mast3r_download.json').read_text())
assert '不完整传输/装配尝试'in evidence and record['success'] is False
candidates=[w/n for n in ['MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth','MASt3R_official_complete.pth','MASt3R_ready.pth','HF_speed_probe.bin']]+list(w.glob('resume_*.bin'))+list((w/'range_parts').glob('*.bin'))
assert len(candidates)>10 and all(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(w)for p in candidates)
rows=[dict(path=str(p),bytes=p.stat().st_size,allocated_bytes=p.stat().st_blocks*512,sha256=sha(p),reason='explicitly INCOMPLETE_DO_NOT_LOAD; failed range assembly; not a valid model or prediction')for p in sorted(candidates)]
valid=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v9_ring_guided_recovery/weights/MASt3R_official.pth')
validsha=sha(valid);assert validsha=='e28f91b488554653e2b46ddae9c78c1143e0bcb2e27d3e26cdb0b717f1568eb2'
d=dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),authorization='latest user explicitly allows obvious stale/useless artifacts after disk recheck',protected_valid_weight=str(valid),protected_valid_SHA256=validsha,original_failure_note=evidence,original_download_failure=record,before_disk=shutil.disk_usage(w)._asdict(),deleted_files=rows,deleted_N=0)
out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
for p in candidates:p.unlink();d['deleted_N']+=1
assert sha(valid)==validsha
d['after_disk']=shutil.disk_usage(w)._asdict();d['deleted_logical_bytes']=sum(r['bytes']for r in rows);d['deleted_allocated_bytes']=sum(r['allocated_bytes']for r in rows)
out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('Removed',d['deleted_N'],'invalid artifacts; allocated bytes',d['deleted_allocated_bytes'],'free',d['after_disk']['free'],flush=True)
