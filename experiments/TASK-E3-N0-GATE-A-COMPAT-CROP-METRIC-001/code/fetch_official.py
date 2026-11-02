"""Explicit preflight fetch only; never import or run downloaded model code.
For reuse on another machine. Exact version, lengths and Git blobs are checked.
"""
from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1]
def main():
    m=json.loads((R/'config/OFFICIAL_ARTIFACTS.json').read_text());base=R/'runtime/neuralfusion_official'
    for row in m['official_files']:
        p=base/row['relative_path'];assert p.resolve().is_relative_to(base.resolve());p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():
            subprocess.run(['curl','--fail','--location','--retry','1','--connect-timeout','15','--max-time','120','--silent','--show-error','--output',str(p),row['download_url']],check=True)
        b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256']and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha1'],'OFFICIAL_BYTES_MISMATCH'
    row=m['easydict'];p=R/'runtime/python/easydict/__init__.py';p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists():subprocess.run(['curl','--fail','--location','--retry','1','--silent','--show-error','--output',str(p),row['download_url']],check=True)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==row['module_sha256'];print('OFFICIAL_ASSETS_VERIFIED_NO_MODEL_EXECUTION',len(m['official_files']))
if __name__=='__main__':main()
