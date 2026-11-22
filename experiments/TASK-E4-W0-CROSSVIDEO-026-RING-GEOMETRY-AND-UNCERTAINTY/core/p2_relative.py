#!/usr/bin/env python3
"""P2.5 negative control + RELATIVE camera error: perturb ONE camera (or each independently)."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
N = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY'
RUN = N/'replay_020/runs'; OUT = N/'runs/G03'
sys.path.insert(0, str(N/'replay_020/code')); sys.path.insert(0, str(N/'core')); sys.path.insert(0, str(WS/'src'))
os.environ['E4_RUN_DIR'] = str(RUN)
import common, features019 as F19
from se3 import exp_se3
views = {v['id']: v for v in json.loads((RUN/'config'/'VIEWS.json').read_text())}
split = json.loads((OUT/'SPLIT.json').read_text())
ident = pd.read_csv(WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/runs/G03/IDENTITIES/HISTORICAL_020_IDENTITIES.csv')


def pdist(X):
    return np.array([np.linalg.norm(X[i]-X[j]) for i in range(len(X)) for j in range(i+1, len(X))])


def run(video, vids, label, mode, deg, mm, idx):
    local = {k: dict(views[k]) for k in vids}
    rng = np.random.default_rng(7)
    for k, v in local.items():
        w = np.zeros(6)
        if mode == 'single' and k != vids[0]: continue
        if mode == 'independent':
            w[3:6] = np.deg2rad(deg)*rng.normal(size=3)/np.sqrt(3)
            w[0:3] = mm*rng.normal(size=3)/np.sqrt(3)
        elif mode == 'single':
            w[3:6] = np.deg2rad(deg)*np.array([0.3, -0.4, 0.8])
            w[0:3] = mm*np.array([0.5, -0.3, 0.7])
        v['T'] = exp_se3(w) @ np.asarray(v['T'], float)
    common.VIEWS = {**common.VIEWS, **local}; F19.VIEWS = common.VIEWS
    return F19.landmarks(vids, label)


def main():
    common.VIEWS = {**{k: views[k] for k in split['fit4']}, **{k: views[k] for k in split['fit5']}}
    F19.VIEWS = common.VIEWS
    b4 = F19.landmarks(split['fit4'], 'REL_BASE_004'); b5 = F19.landmarks(split['fit5'], 'REL_BASE_005')
    Xb4 = np.asarray(b4['X'], float); Xb5 = np.asarray(b5['X'], float)
    i4, i5 = ident.landmark_004.values, ident.landmark_005.values
    rows = []
    for video, vids, Xb, idx in (('004', split['fit4'], Xb4, i4), ('005', split['fit5'], Xb5, i5)):
        base = pdist(Xb[idx])
        for mode in ('single', 'independent'):
            for deg, mm in ((0.5, 0.0), (1.0, 0.0), (0.0, 0.5)):
                lm = run(video, vids, f'REL_{video}_{mode}_{deg}_{mm}', mode, deg, mm, idx)
                Xp = np.asarray(lm['X'], float); n = min(len(Xp), len(Xb))
                disp = np.linalg.norm(Xp[:n]-Xb[:n], axis=1)
                pd_ = np.abs(pdist(Xp[idx])-base) if len(Xp) > idx.max() else np.array([np.nan])
                rows.append(dict(video=video, mode=mode, rot_deg=deg, trans_mm=mm, n=len(Xp),
                                 dr_p50=float(np.median(disp)), dr_p90=float(np.percentile(disp, 90)),
                                 dpair_p50=float(np.nanmedian(pd_)), dpair_max=float(np.nanmax(pd_))))
    df = pd.DataFrame(rows); df.to_csv(OUT/'TRIANGULATION_RELATIVE.csv', index=False)
    print(df.to_string(index=False))


if __name__ == '__main__':
    main()
