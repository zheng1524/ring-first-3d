"""One terminal <=128MiB range recovery of the same official checkpoint."""
from pathlib import Path
import urllib.request,time,json,traceback,hashlib
R=Path(__file__).resolve().parents[1];folder=R/'runtime/map_checkpoint';p=folder/'model.safetensors.partial';prior=json.loads((R/'provenance/MAP_DOWNLOAD_RESULT.json').read_text());dest=R/'provenance/MAP_DOWNLOAD_RECOVERY_RESULT.json';assert not dest.exists()
start=time.monotonic();n=p.stat().st_size;total=prior['expected_bytes'];assert 0<total-n<=128*1024**2
r=dict(repo=prior['repo'],revision=prior['revision'],publisher_SHA256=prior['publisher_SHA256'],expected_bytes=total,prefix_bytes=n,remaining_bytes=total-n,range_recovery_limit_seconds=60,total_transfer_limit_seconds=660,success=False,reason='user requested best effort after authorized stale-artifact cleanup; same weight, bounded terminal range only; original 600s failure preserved')
try:
 url='https://huggingface.co/facebook/map-anything-apache/resolve/'+prior['revision']+'/model.safetensors?download=true'
 request=urllib.request.Request(url,headers={'Range':f'bytes={n}-{total-1}'})
 with urllib.request.urlopen(request,timeout=25)as response:
  r['http_status']=response.status;r['content_range']=response.headers.get('Content-Range');assert response.status==206 and r['content_range'].startswith(f'bytes {n}-'),r
  with p.open('ab')as f:
   while True:
    if time.monotonic()-start>60:raise TimeoutError('terminal range recovery budget')
    b=response.read(2**20)
    if not b:break
    f.write(b)
 assert p.stat().st_size==total
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 r['local_SHA256']=h.hexdigest();assert r['local_SHA256']==prior['publisher_SHA256']
 p.rename(folder/'model.safetensors')
 # Preview was fetched from this exact revision, no model configuration edit.
 (folder/'config.json').write_bytes((R/'runtime/map_config_preview.json').read_bytes())
 r.update(success=True,path=str(folder/'model.safetensors'))
except Exception:r['error']=traceback.format_exc();print(r['error'],flush=True)
r['seconds']=time.monotonic()-start;dest.write_text(json.dumps(r,indent=2)+'\n');print('TAIL_RECOVERY',r['success'],r['seconds'],flush=True)
