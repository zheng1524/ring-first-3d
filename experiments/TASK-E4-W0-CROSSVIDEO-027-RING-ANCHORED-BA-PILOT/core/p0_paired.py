#!/usr/bin/env python3
"""P0.1 fix check + P0.2 paired Ring/3D sensitivity from the SAME camera matrices."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, torch
WS = Path('/home/liu/ring_first_3d_workspace')
B = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-RING-ANCHORED-BA-PILOT'
R26 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY/replay_020/runs'
sys.path.insert(0, str(B/'replay')); sys.path.insert(0, str(B/'core')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(B/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
import features019 as F19
from ring020_026 import RingRenderer, tensor, canonical
from se3 import exp_se3
import fixed_track_tri as FTT
views = {v['id']: v for v in json.loads((B/'replay'/'config'/'VIEWS.json').read_text())}
split = json.loads((B/'runs/G03/SPLIT.json').read_text()) if (B/'runs/G03/SPLIT.json').exists() else json.loads((WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY/runs/G03/SPLIT.json').read_text())
W = dict(M=0.25, I=0.35, O=0.35)


def ring_mio(rr, inc, cid):
    L, _, _ = rr.losses(tensor(np.asarray(inc), torch.float64), cid)
    return W['M']*float(L['M']) + W['I']*float(L['I']) + W['O']*float(L['O'])


def main():
    split_dst = B/'runs/G03/SPLIT.json'; split_dst.parent.mkdir(parents=True, exist_ok=True)
    split_dst.write_text(json.dumps(split, indent=1))
    F19.VIEWS = {**{k: views[k] for k in split['fit4']}, **{k: views[k] for k in split['fit5']}}
    # baseline tracks (from historical landmarks run on W0 cameras, cached in 026)
    O4 = json.loads((R26/'landmarks'/'REL_BASE_004_OBSERVATIONS.json').read_text())
    O5 = json.loads((R26/'landmarks'/'REL_BASE_005_OBSERVATIONS.json').read_text())
    tracks4 = [[(x['view'], int(x['feature_id'])) for x in o['observations']] for o in O4]
    tracks5 = [[(x['view'], int(x['feature_id'])) for x in o['observations']] for o in O5]
    base4 = FTT.triangulate_tracks(tracks4, F19.VIEWS); base5 = FTT.triangulate_tracks(tracks5, F19.VIEWS)
    Xb4 = np.array([r['X'] for r in base4]); Xb5 = np.array([r['X'] for r in base5])
    # equivalence check against the historical landmarks output (same tracks, same cameras)
    h4 = np.load(R26/'landmarks'/'REL_BASE_004.npz')['X']; h5 = np.load(R26/'landmarks'/'REL_BASE_005.npz')['X']
    eq = dict(n4=len(h4), n5=len(h5), max_diff4=float(np.abs(Xb4[:len(h4)]-h4).max()), max_diff5=float(np.abs(Xb5[:len(h5)]-h5).max()))
    assert eq['max_diff4'] < 1e-6 and eq['max_diff5'] < 1e-6, eq
    print('FIXED_TRACK_EQUIVALENCE', eq, flush=True)
    rr = RingRenderer(sorted(views))
    ident = pd.read_csv(WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/runs/G03/IDENTITIES/HISTORICAL_020_IDENTITIES.csv')
    i4, i5 = ident.landmark_004.values, ident.landmark_005.values
    def pdist(X): return np.array([np.linalg.norm(X[a]-X[b]) for a in range(len(X)) for b in range(a+1, len(X))])
    rows = []
    seed = 11
    for video, vids, tracks, Xb in (('004', split['fit4'], tracks4, Xb4), ('005', split['fit5'], tracks5, Xb5)):
        for mode, deg, mm in (('common', 0.5, 0.0), ('common', 1.0, 0.0), ('single', 0.5, 0.0), ('independent', 0.5, 0.0), ('independent', 0.0, 0.25)):
            rng = np.random.default_rng(seed)
            local = {k: dict(views[k]) for k in vids}
            for n, (k, v) in enumerate(local.items()):
                w = np.zeros(6)
                if mode == 'common':
                    w[3:] = np.deg2rad(deg)*np.array([0.3, -0.4, 0.8]); w[:3] = mm*np.array([0.5, -0.3, 0.7])
                elif mode == 'single':
                    if n != 0: continue
                    w[3:] = np.deg2rad(deg)*np.array([0.3, -0.4, 0.8]); w[:3] = mm*np.array([0.5, -0.3, 0.7])
                else:
                    w[3:] = np.deg2rad(deg)*rng.normal(size=3)/np.sqrt(3); w[:3] = mm*rng.normal(size=3)/np.sqrt(3)
                v['T'] = exp_se3(w) @ np.asarray(v['T'], float)
            # Ring: same cameras (increment = T_pert @ inv(T0))
            ring = [ring_mio(rr, np.asarray(local[k]['T']) @ np.linalg.inv(np.asarray(views[k]['T'])), k) for k in vids]
            # 3D: same fixed tracks, same cameras
            tri = FTT.triangulate_tracks(tracks, {**F19.VIEWS, **local})
            Xn = np.array([r['X'] for r in tri])
            dr = np.linalg.norm(Xn-Xb, axis=1)
            dpair = np.abs(pdist(Xn[i4 if video == '004' else i5])-pdist(Xb[i4 if video == '004' else i5]))
            rows.append(dict(video=video, mode=mode, rot_deg=deg, trans_mm=mm, n_tracks=len(tracks),
                             ring_mio_median=float(np.median(ring)), ring_mio_max=float(np.max(ring)),
                             dr_p50=float(np.median(dr)), dr_p90=float(np.percentile(dr, 90)), dr_max=float(dr.max()),
                             dpair_p50=float(np.median(dpair)), dpair_max=float(dpair.max())))
            print('PAIR', video, mode, deg, mm, round(rows[-1]['ring_mio_median'], 3), round(rows[-1]['dr_p50'], 3), flush=True)
    pd.DataFrame(rows).to_csv(B/'runs/G03/RING_3D_PAIRED_SENSITIVITY.csv', index=False)
    (B/'runs/G03/FIXED_TRACK_EQUIVALENCE.json').write_text(json.dumps(eq, indent=1))


if __name__ == '__main__':
    main()
