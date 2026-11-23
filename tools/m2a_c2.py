#!/usr/bin/env python3
"""M2A C2: add up to 4 real bridge frames from the raw video, verified by RGB matches."""
import json
import sys
from pathlib import Path
import cv2
import numpy as np
import pandas as pd

WS = Path('/home/liu/ring_first_3d_workspace'); OUT = WS/'runs/m2a_w0_recovery'
M1 = WS/'runs/m1_final_39'; PREP = M1/'prepared'
sys.path.insert(0, str(WS/'src')); sys.path.insert(0, str(WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/code'))
sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay'))
sys.path.insert(0, str(WS/'camera_mainline/code'))
sys.path.insert(0, str(WS/'tools'))
from prepare import prepare_view
from ring_first_3d.mainline.native.camera import observe
import features019 as F19
from m2a_c3 import pair_graph
from m2a_recover import run_one

F19.R = OUT/'features019_c2'; F19.R.mkdir(parents=True, exist_ok=True)
TARGETS = [('GP_Is_10.5mm_closed_R5_single_refY','005'),
           ('GP_Is_9.79mm_closed_R10_single_refY','004')]


def view_dict(q):
    a=np.load(q['cache']); return dict(id=q['view'], cache=str(q['cache']), raw_frame=int(q['raw_frame']),
        K=np.asarray(a['K']).tolist(), T=np.eye(4).tolist(), RGB_SHA256=q.get('rgb_sha256') or '')


def choose(g,v):
    meta=json.loads((PREP/f'{g}_{v}'/'PREPARED.json').read_text()); orig=meta['views']
    tr,edges,comps=pair_graph(OUT/'work/C1'/g/v)
    reps=[str(tr['ids'][c[0]]) for c in comps]
    views={q['view']:view_dict(q) for q in orig}; F19.VIEWS=views
    raw=Path(meta['video_path']); cap=cv2.VideoCapture(str(raw)); n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); cap.release()
    origs={int(q['raw_frame']) for q in orig}
    candidates=[f for f in np.linspace(20,n-20,12,dtype=int) if all(abs(int(f)-o)>8 for o in origs)]
    rows=[]
    for f in candidates:
        cache=OUT/'bridge'/f'{g}_{v}'/'frames'/f'M2A_BRIDGE_{g}_{v}_raw{int(f):05d}.npz'
        cache.parent.mkdir(parents=True,exist_ok=True)
        r=prepare_view(raw,int(f),cache); a=np.load(cache)
        if len(observe(a['labels'])['q_train'])<20: continue
        vd=dict(id=f'M2A_BRIDGE_{g}_{v}_raw{int(f):05d}', cache=str(cache), raw_frame=int(f),
                K=np.asarray(a['K']).tolist(), T=np.eye(4).tolist(), RGB_SHA256=r['rgb_sha256'])
        views[vd['id']]=vd; F19.VIEWS[vd['id']]=vd
        hits=[]
        for rp in reps:
            try:
                m=F19.matches(vd,views[rp]); hits.append(int(np.asarray(m['RGB_RANSAC']).sum()))
            except Exception: hits.append(0)
        rows.append(dict(frame=int(f),view=vd['id'],hits=hits,n_hit=sum(h>=12 for h in hits),
                         rgb_sha256=r['rgb_sha256'],cache=str(cache)))
    return meta,comps,rows


def main():
    out=[]
    for g,v in TARGETS:
        meta,comps,rows=choose(g,v)
        if not rows: print('NO_CANDIDATES',g,v); continue
        df=pd.DataFrame(rows); df.to_csv(OUT/'bridge'/f'{g}_{v}'/'BRIDGE_CANDIDATES.csv',index=False)
        # greedy: pick candidates covering the most not-yet-covered components
        selected=[]; covered=set()
        for k in range(4):
            best=None
            for _,r in df.iterrows():
                if r.view in selected: continue
                hit={i for i,h in enumerate(r.hits) if h>=12}
                gain=len(hit-covered)
                if gain>0 and (best is None or gain>best[0]): best=(gain,r)
            if best is None: break
            selected.append(best[1].view); covered |= {i for i,h in enumerate(best[1].hits) if h>=12}
            if len(covered)==len(comps): break
        if not selected: print('C2_NO_BRIDGE',g,v); continue
        # prepared original + bridges
        dst=OUT/'prepared_c2'/f'{g}_{v}'; dst.mkdir(parents=True,exist_ok=True)
        orig=meta['views']; bridges=[json.loads(pd.DataFrame(rows).set_index('view').loc[s].to_json()) for s in selected]
        m2=dict(meta); m2['views']=orig+[dict(view=s,raw_frame=int(pd.DataFrame(rows).set_index('view').loc[s].frame),
                                             cache=pd.DataFrame(rows).set_index('view').loc[s].cache) for s in selected]
        m2['bridge_frames']=selected; m2['original_frame_ids']=[q['view'] for q in orig]
        m2['selection_reason']='M2A_C2_REAL_BRIDGE_RGB_MATCHES'
        (dst/'PREPARED.json').write_text(json.dumps(m2,indent=1))
        r=run_one(g,v,OUT/'prepared_c2','C2',OUT/'recovery/C2',OUT/'work/C2',list(range(1,10+len(selected))))
        r['bridge_frames']=';'.join(selected); out.append(r); print('C2',g,v,r['execution_status'],r['n_w0_poses'],selected,flush=True)
    pd.DataFrame(out).to_csv(OUT/'RECOVERY_C2.csv',index=False)
    print(pd.DataFrame(out)[['group_id','video_id','execution_status','n_w0_poses','n_accept']].to_string(index=False) if out else 'NO_C2')

if __name__=='__main__': main()
