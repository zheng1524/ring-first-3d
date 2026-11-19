"""Explicit curated Git delivery; no source images/video/depth/Jacobian cache."""
from common import *
def main():
    assert load(R/'metrics/VALIDATION.json')['all_pass']
    files=[]
    for p in sorted(R.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(R)
        if rel.parts[0]=='inputs':continue
        if rel.parts[:2]==('figures','overlays'):continue
        if rel.parts[:2] in [('runtime','tmp'),('runtime','mpl')]:continue
        if p.suffix in ['.npz','.npy'] and not p.name.startswith('Body-E-'):continue
        if p.name=='GIT_DELIVERY_MANIFEST.json':continue
        if p.suffix not in ['.py','.md','.csv','.json','.png','.ply','.npz','.log']:continue
        assert p.stat().st_size<25*1024*1024,(p,p.stat().st_size)
        files.append(dict(relative_path=str(p.relative_to(REPO)),**asset(p)))
    save('assets_index/GIT_DELIVERY_MANIFEST.json',dict(files=files,total_bytes=sum(x['bytes'] for x in files),excluded_local_only=['inputs/*','figures/overlays/*','OBSERVATION_JACOBIAN.npz','per-pixel projections','TRACE_*.npz','runtime cache'],full_local_index='assets_index/LOCAL_ARTIFACTS.json',GT_or_raw_video_uploaded=False))
    print('DELIVERY',len(files),'files',round(sum(x['bytes'] for x in files)/1024**2,2),'MiB',flush=True)
if __name__=='__main__':main()
