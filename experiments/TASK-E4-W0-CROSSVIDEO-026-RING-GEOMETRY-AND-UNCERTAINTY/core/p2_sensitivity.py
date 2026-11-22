#!/usr/bin/env python3
"""P1 sensitivity (full Ring) + P2 triangulation sensitivity under frozen camera perturbations."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, torch
WS = Path('/home/liu/ring_first_3d_workspace')
N = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY'
RUN = N/'replay_020/runs'; OUT = N/'runs/G03'
sys.path.insert(0, str(N/'replay_020/code')); sys.path.insert(0, str(N/'core')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(RUN),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
import common, features019 as F19
from ring020_026 import RingRenderer, tensor, exp_se3
from se3 import exp_se3 as np_exp

views = {v['id']: v for v in json.loads((RUN/'config'/'VIEWS.json').read_text())}
ids = sorted(views)
rr = RingRenderer(ids)
split = json.loads((OUT/'SPLIT.json').read_text())


def losses_for(H, cid):
    L, aux, _ = rr.losses(tensor(np.asarray(H), torch.float64), cid)
    return dict(M=float(L['M']), I=float(L['I']), C=float(L['C']), O=float(L['O']),
                ring=0.25*float(L['M'])+0.35*float(L['I'])+0.05*float(L['C'])+0.35*float(L['O']))


def main():
    # ---------- P1: candidate H vs full Ring
    H025 = np.load(WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/runs/G03/CONSISTENCY/H_HYPOTHESIS.npz')['H']
    rows = []
    for cid in ids:
        base = losses_for(np.eye(4), cid)
        Hc = H025 @ np.asarray(views[cid]['T']) if cid in split['fit4'] else np.linalg.inv(H025) @ np.asarray(views[cid]['T'])
        cand = losses_for(Hc, cid)
        rows.append(dict(view=cid, side='004' if cid in split['fit4'] or cid in split['ho4'] else '005',
                         M_w0=base['M'], I_w0=base['I'], C_w0=base['C'], O_w0=base['O'], ring_w0=base['ring'],
                         ring_H025=cand['ring']))
    pd.DataFrame(rows).to_csv(OUT/'RING_IO_CANDIDATE_H.csv', index=False)
    # ---------- P1: sensitivity to pose perturbations (yaw / pitch / roll / tx / tz)
    probe = [split['fit5'][0], split['fit4'][0]]
    sens = []
    for cid in probe:
        C0 = np.asarray(views[cid]['T'], float)
        for axis, name in ((2, 'yaw'), (0, 'pitch'), (1, 'roll')):
            for deg in (0.0, 1.0, 5.0, 15.0, 45.0):
                w = np.zeros(6); w[3+axis] = np.deg2rad(deg)
                dH = np_exp(w); C = dH @ C0
                l = losses_for(np.linalg.inv(C0) @ C, cid)
                sens.append(dict(view=cid, kind=name, value=deg, unit='deg', ring=l['ring'], M=l['M'], I=l['I'], C=l['C'], O=l['O']))
        for axis, name in ((0, 'tx'), (2, 'tz')):
            for mm in (0.0, 0.1, 0.25, 0.5):
                w = np.zeros(6); w[axis] = mm
                dH = np_exp(w); C = dH @ C0
                l = losses_for(np.linalg.inv(C0) @ C, cid)
                sens.append(dict(view=cid, kind=name, value=mm, unit='mm', ring=l['ring'], M=l['M'], I=l['I'], C=l['C'], O=l['O']))
    pd.DataFrame(sens).to_csv(OUT/'RING_POSE_SENSITIVITY.csv', index=False)
    # ---------- P2: triangulation sensitivity under frozen perturbations
    common.VIEWS = {**{k: views[k] for k in split['fit4']}, **{k: views[k] for k in split['fit5']}}
    F19.VIEWS = common.VIEWS
    base4 = F19.landmarks(split['fit4'], 'BASE_004'); base5 = F19.landmarks(split['fit5'], 'BASE_005')
    Xb4 = np.asarray(base4['X'], float); Xb5 = np.asarray(base5['X'], float)
    ident = pd.read_csv(WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/runs/G03/IDENTITIES/HISTORICAL_020_IDENTITIES.csv')
    idx4 = ident.landmark_004.values; idx5 = ident.landmark_005.values
    def pdist(X):
        return np.array([np.linalg.norm(X[i]-X[j]) for i in range(len(X)) for j in range(i+1, len(X))])
    dbase4, dbase5 = pdist(Xb4[idx4]), pdist(Xb5[idx5])
    pert = []
    for kind, deg, mm in (('rot', 0.25, 0.0), ('rot', 1.0, 0.0), ('trans', 0.0, 0.25), ('trans', 0.0, 0.5)):
        for video, vids, Xb, idx in (('004', split['fit4'], Xb4, idx4), ('005', split['fit5'], Xb5, idx5)):
            local = {k: dict(v) for k, v in views.items() if k in vids}
            rng = np.random.default_rng(0)
            for k, v in local.items():
                w = np.zeros(6)
                if kind == 'rot': w[3:6] = np.deg2rad(deg)*np.array([0.3, -0.4, 0.8])
                else: w[0:3] = mm*np.array([0.5, -0.3, 0.7])
                v['T'] = np_exp(w) @ np.asarray(v['T'], float)
            common.VIEWS = {**common.VIEWS, **local}; F19.VIEWS = common.VIEWS
            lm = F19.landmarks(vids, f'PERT_{video}_{kind}_{deg}_{mm}')
            Xp = np.asarray(lm['X'], float)
            n = min(len(Xp), len(Xb))
            disp = np.linalg.norm(Xp[:n]-Xb[:n], axis=1)
            pert.append(dict(video=video, kind=kind, rot_deg=deg, trans_mm=mm, n_before=len(Xb), n_after=len(Xp),
                             dr_mm_p50=float(np.median(disp)), dr_mm_p90=float(np.percentile(disp, 90)),
                             pairwise_p50=float(np.median(np.abs(pdist(Xp[idx])-pdist(Xb[idx])))) if len(Xp) > idx.max() else None))
    pd.DataFrame(pert).to_csv(OUT/'TRIANGULATION_SENSITIVITY.csv', index=False)
    # ---------- P2: pairwise distance between the 12 identities at baseline
    pw = []
    for i in range(len(idx4)):
        for j in range(i+1, len(idx4)):
            pw.append(dict(i=i, j=j, d004=float(np.linalg.norm(Xb4[idx4[i]]-Xb4[idx4[j]])),
                           d005=float(np.linalg.norm(Xb5[idx5[i]]-Xb5[idx5[j]]))))
    pdf = pd.DataFrame(pw); pdf['diff_mm'] = (pdf.d004-pdf.d005).abs()
    pdf.to_csv(OUT/'PAIRWISE_DISTANCES_12.csv', index=False)
    summ = dict(ring_io=dict(I=float(pd.read_csv(OUT/'RING_IO_PER_VIEW.csv').I.median()),
                             O=float(pd.read_csv(OUT/'RING_IO_PER_VIEW.csv').O.median()),
                             ring=float(pd.read_csv(OUT/'RING_IO_PER_VIEW.csv').ring.median())),
                ring_H025=dict(ring_w0=float(pd.DataFrame(rows).ring_w0.median()), ring_H=float(pd.DataFrame(rows).ring_H025.median())),
                yaw_sensitivity={str(k): float(v) for k, v in pd.DataFrame(sens).query("kind=='yaw'").groupby('value').ring.median().items()},
                triangulation=pd.DataFrame(pert).to_dict('records'),
                pairwise=dict(n=len(pdf), median_diff_mm=float(pdf.diff_mm.median()), p90_diff_mm=float(pdf.diff_mm.quantile(.9)),
                              max_diff_mm=float(pdf.diff_mm.max())))
    (OUT/'SENSITIVITY_SUMMARY.json').write_text(json.dumps(summ, indent=1, default=str))
    print(json.dumps({k: summ[k] for k in ('ring_io', 'ring_H025', 'yaw_sensitivity', 'pairwise')}, indent=1, default=str))
    print(pd.DataFrame(pert).to_string(index=False))


if __name__ == '__main__':
    main()
