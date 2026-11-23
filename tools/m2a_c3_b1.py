#!/usr/bin/env python3
"""M2A C3 on B1 subsets (ring-insufficient videos that still have a graph)."""
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace'); OUT = WS/'runs/m2a_w0_recovery'
sys.path.insert(0, str(WS/'tools'))
from m2a_recover import make_subset, run_one
from m2a_c3 import pair_graph

def main():
    b1 = pd.read_csv(OUT/'RECOVERY_RESULTS.csv')
    b1 = b1[b1.method == 'B1']
    jobs=[]
    for _,r in b1.iterrows():
        g,v=str(r.group_id),f'{int(r.video_id):03d}'
        if r.execution_status in ('COMPLETED_VALID','COMPLETED_LIMITED'): continue
        work=OUT/'work/B1'/g/v
        if not (work/'observations/tracks005.npz').exists(): continue
        tr,edges,comps=pair_graph(work); keep=[str(tr['ids'][i]) for i in comps[0]]
        if len(keep)<4: print('SKIP',g,v,len(keep)); continue
        # subset of the B1 prepared subset
        src=OUT/'prepared_b1'/f'{g}_{v}'/'PREPARED.json'; meta=json.loads(src.read_text())
        m2=dict(meta); m2['views']=[q for q in meta['views'] if q['view'] in set(keep)]
        dst=OUT/'prepared_c3b1'/f'{g}_{v}'; dst.mkdir(parents=True,exist_ok=True)
        (dst/'PREPARED.json').write_text(json.dumps(m2,indent=1)); jobs.append((g,v,len(keep)))
    rows=[]
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs={ex.submit(run_one,g,v,OUT/'prepared_c3b1','C3B',OUT/'recovery/C3B',OUT/'work/C3B',list(range(1,n))):(g,v,n) for g,v,n in jobs}
        for f in as_completed(futs):
            g,v,n=futs[f]
            try:r=f.result()
            except Exception as e:r=dict(group_id=g,video_id=v,method='C3B',returncode=-1,execution_status='IMPLEMENTATION_ERROR',failure_stage='runner',failure_reason=str(e),n_w0_poses=None,n_accept=None,n_quarantine=None,n_insufficient=None,n_reject=None,ring_mae=None,held_median=None,held_p95=None,output_path=None)
            rows.append(r); print('C3B',g,v,n,r['execution_status'],r['n_w0_poses'],flush=True)
    pd.DataFrame(rows).to_csv(OUT/'RECOVERY_C3B1.csv',index=False)
    print(pd.DataFrame(rows)[['group_id','video_id','execution_status','n_w0_poses','n_accept']].to_string(index=False))
if __name__=='__main__': main()
