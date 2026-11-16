"""CPU process batch, preserving each official call's stdout and record."""
from common import *
from concurrent.futures import ThreadPoolExecutor,as_completed
def worker(cid):
    with (R/'runtime'/('DXY_'+cid+'.log')).open('w') as f:
        r=subprocess.run(['/home/liu/new-polyp-dxy/.venv/bin/python',str(R/'code/generate_dxy.py'),cid],stdout=f,stderr=subprocess.STDOUT)
    return cid,r.returncode
def main():
    assert subprocess.check_output(['git','-C',str(DXY),'rev-parse','HEAD'],text=True).strip()=='75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95'
    assert not subprocess.check_output(['git','-C',str(DXY),'status','--porcelain'],text=True).strip()
    save('provenance/DXY_VERSION_AUDIT.json',dict(commit='75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95',clean=True,pipeline=asset(DXY/'src/dxy_mid/pipeline.py')))
    save('provenance/PROTOCOL_FROZEN_BEFORE_DXY.json',dict(epoch=time.time(),protocol=asset(R/'01_PROTOCOL.md'),inputs=asset(R/'config/SOURCE_BINDING.json'),code=[asset(p) for p in sorted((R/'code').glob('*.py'))],GT_read=False))
    ss=load(R/'config/SOURCE_BINDING.json')
    with ThreadPoolExecutor(max_workers=4) as ex:
        fs=[ex.submit(worker,s['source_id']) for s in ss]
        for i,f in enumerate(as_completed(fs)):
            cid,rc=f.result();print('DXY',i+1,'/75',cid,'exit',rc,flush=True)
            if rc:raise RuntimeError('DXY_WORKER_FAILED:'+cid)
    rr=[load(R/'provenance/dxy_records'/(s['source_id']+'.json')) for s in ss]
    save('provenance/DXY_GENERATED.json',rr)
    save('provenance/DXY_SOURCE_SHA.json',[{k:s[k] for k in ['source_id','RGB_source','Mask_source','cache','RGB_content_SHA','Mask_content_SHA']} for s in ss])
    save('provenance/DXY_RUNTIME_SOURCE_INDEX.json',[asset(p) for p in sorted((DXY/'src').rglob('*.py'))])
    table('metrics/DXY_QUALITY_AUDIT.csv',[dict(source=r['source'],available=r['available'],entrypoint=r['entrypoint'],ring_id=r['ring_id'],DXY_commit=r['DXY_commit'],VERSION=r['VERSION'],shape=r.get('shape'),center_native=r.get('center_px'),basis_native=r.get('basis_px'),candidate_provenance=r.get('candidate_provenance'),status=r.get('status'),error=r.get('error'),**r['quality']) for r in rr])
    print('DXY_COMPLETE',sum(r['available'] for r in rr),'/',len(rr),flush=True)
if __name__=='__main__':main()
