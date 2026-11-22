#!/usr/bin/env python3
"""P4: triangulation sensitivity with STABLE track identities (key = member observations).

026 matched landmarks by array row (Xp[:n] - Xb[:n]) -> different physical points.
Key = tuple(sorted((view, feature_id))) from the historical <label>_OBSERVATIONS.json.
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
K = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-CORRECTIVE'
L26 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY/replay_020/runs/landmarks'
OUT = K/'runs/G03'


def load(label, run_dir=L26):
    X = np.load(run_dir/(label+'.npz'))['X']
    O = json.loads((run_dir/(label+'_OBSERVATIONS.json')).read_text())
    keys = [tuple(sorted((x['view'], int(x['feature_id'])) for x in o['observations'])) for o in O]
    return np.asarray(X, float), keys


def main():
    pw = pd.read_csv(WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY/runs/G03/PAIRWISE_DISTANCES_12.csv')
    ident = pd.read_csv(WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/runs/G03/IDENTITIES/HISTORICAL_020_IDENTITIES.csv')
    rows = []
    for video, base_label, pert_labels in (
            ('004', 'REL_BASE_004', ['PERT_004_rot_0.25_0.0', 'PERT_004_rot_1.0_0.0', 'PERT_004_trans_0.0_0.25']),
            ('005', 'REL_BASE_005', ['PERT_005_rot_0.25_0.0', 'PERT_005_rot_1.0_0.0', 'REL_005_single_0.5_0.0', 'REL_005_independent_0.5_0.0'])):
        Xb, kb = load(base_label)
        for pl in pert_labels:
            Xp, kp = load(pl)
            mb = {k: i for i, k in enumerate(kb)}; mp = {k: i for i, k in enumerate(kp)}
            common = sorted(set(mb) & set(mp))
            disp = np.array([np.linalg.norm(Xp[mp[k]]-Xb[mb[k]]) for k in common]) if common else np.array([])
            # 12 identity landmarks (indices refer to the 004/005 baseline landmark arrays used in 026)
            rows.append(dict(video=video, run=pl, n_base=len(kb), n_pert=len(kp), n_common=len(common),
                             survival=len(common)/max(len(kb), 1),
                             disp_p50=float(np.median(disp)) if len(disp) else None,
                             disp_p90=float(np.percentile(disp, 90)) if len(disp) else None,
                             disp_max=float(disp.max()) if len(disp) else None,
                             lost=len(set(mb)-set(mp)), new=len(set(mp)-set(mb))))
    df = pd.DataFrame(rows); df.to_csv(OUT/'TRIANGULATION_TRACK_ALIGNED.csv', index=False)
    print(df.to_string(index=False))
    # ---- 12 identities: is the landmark still present in perturbed runs?
    ir = []
    for pl in ['PERT_004_rot_1.0_0.0', 'PERT_004_trans_0.0_0.25', 'REL_005_independent_0.5_0.0']:
        Xb, kb = load('REL_BASE_004' if '004' in pl else 'REL_BASE_005')
        Xp, kp = load(pl); mp = {k: i for i, k in enumerate(kp)}
        idx = ident.landmark_004.values if '004' in pl else ident.landmark_005.values
        for n, i in enumerate(idx):
            k = kb[i]
            if k in mp:
                ir.append(dict(run=pl, identity=int(n), landmark=int(i), status='AVAILABLE',
                               disp_mm=float(np.linalg.norm(Xp[mp[k]]-Xb[i]))))
            else:
                ir.append(dict(run=pl, identity=int(n), landmark=int(i), status='NOT_EVALUABLE', disp_mm=np.nan))
    ir = pd.DataFrame(ir); ir.to_csv(OUT/'IDENTITY_TRACK_STABILITY.csv', index=False)
    print(ir.groupby(['run', 'status']).size().to_string())


if __name__ == '__main__':
    main()
