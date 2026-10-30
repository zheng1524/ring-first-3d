"""One bounded official weight download, exact revision and SHA, no retry loop."""
from pathlib import Path
import hashlib,json,time,traceback,urllib.request,os,shutil
R=Path(__file__).resolve().parents[1];folder=R/'runtime/map_checkpoint';folder.mkdir(exist_ok=True)
revision='00f9c245bbcb60522d1ed7f9e9d88462c6e3f38a';expected='fa06c0fdccefc5048e072c85935d5789b1e36b307f3859033c17f9dcb9fd5201';size=4914062480
out=folder/'model.safetensors';partial=folder/'model.safetensors.partial';record=R/'provenance/MAP_DOWNLOAD_RESULT.json'
assert not out.exists() and not partial.exists() and not record.exists()
start=time.monotonic();r=dict(repo='facebook/map-anything-apache',revision=revision,publisher_SHA256=expected,expected_bytes=size,time_limit_seconds=600,downloaded_bytes=0,success=False,attempts=1)
try:
 assert shutil.disk_usage(folder).free>size+700_000_000,'weight plus artifact reserve does not fit'
 url='https://huggingface.co/facebook/map-anything-apache/resolve/'+revision+'/model.safetensors'
 h=hashlib.sha256();last=0
 with urllib.request.urlopen(url,timeout=30)as response, partial.open('wb')as f:
  while True:
   if time.monotonic()-start>600:raise TimeoutError('600 second download budget exhausted')
   b=response.read(2**20)
   if not b:break
   f.write(b);h.update(b);r['downloaded_bytes']+=len(b)
   if r['downloaded_bytes']-last>256*1024**2:print('download MiB',round(r['downloaded_bytes']/1024**2),'seconds',round(time.monotonic()-start),flush=True);last=r['downloaded_bytes']
 assert r['downloaded_bytes']==size,(r['downloaded_bytes'],size)
 r['local_SHA256']=h.hexdigest();assert r['local_SHA256']==expected
 partial.rename(out)
 # Small config is fetched from the identical checkpoint revision.
 for name in ['config.json']:
  with urllib.request.urlopen('https://huggingface.co/facebook/map-anything-apache/resolve/'+revision+'/'+name,timeout=25)as response:(folder/name).write_bytes(response.read(1000000))
 r['success']=True;r['path']=str(out)
except Exception:r['error']=traceback.format_exc();print(r['error'],flush=True)
r['seconds']=time.monotonic()-start;record.write_text(json.dumps(r,indent=2)+'\n');print('DOWNLOAD_RESULT',r['success'],r['downloaded_bytes'],r['seconds'],flush=True)
