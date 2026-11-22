#!/usr/bin/env python3
"""P2/P4: real G03 baselines A (W0), B (H / H+landmarks), C (limited BA)."""
import json, os, sys, time
from pathlib import Path
import numpy as np, pandas as pd, torch
from scipy.optimize import least_squares
WS = Path('/home/liu/ring_first_3d_workspace')
B = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-RING-ANCHORED-BA-PILOT'
R26 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY/replay_020/runs'
sys.path.insert(0, str(B/'core')); sys.path.insert(0, str(B/'replay')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(B/'replay'),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
import ba_core as BA
from ring020_026 import RingRenderer, tensor
from se3 import exp_se3
OUT = B/'runs/G03'
views = {v['id']: v for v in json.loads((B/'replay'/'config'/'VIEWS.json').read_text())}
split = json.loads((B/'runs/G03/SPLIT.json').read_text())
ident = pd.read_csv(WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/runs/G03/IDENTITIES/HISTORICAL_020_IDENTITIES.csv')
def _lm(name):
    for base in (R26/'landmarks', WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/replay_019_020/runs/landmarks'):
        p = base/name
        if p.exists(): return json.loads(p.read_text())
    raise FileNotFoundError(name)
O4 = _lm('REL_BASE_004_OBSERVATIONS.json')
O5 = _lm('REL_BASE_005_OBSERVATIONS.json')


def build():
    cams = {}
    for c in split['fit4']: cams[c] = ('004', np.asarray(views[c]['T'], float))
    for c in split['fit5']: cams[c] = ('005', np.asarray(views[c]['T'], float))
    K_of = {c: np.asarray(views[c]['K'], float) for c in cams}
    obs = []
    for k, r in ident.iterrows():
        i, j = int(r.landmark_004), int(r.landmark_005)
        for o in O4[i]['observations']:
            if o['view'] in cams: obs.append((o['view'], k, np.asarray(o['uv'], float)))
        for o in O5[j]['observations']:
            if o['view'] in cams: obs.append((o['view'], k, np.asarray(o['uv'], float)))
    X0 = ident[['X005_x', 'X005_y', 'X005_z']].values
    rings = {c: {'inner': None, 'outer': None} for c in cams}
    return cams, K_of, obs, X0, rings


def evaluate_single(cams, K_of, obs, X4, X5, rr, label):
    """W0 baseline: each video's OWN landmarks explained by its OWN cameras."""
    rows = []
    for (cid, li, uv) in obs:
        X = X4[li] if cams[cid][0] == '004' else X5[li]
        C = cams[cid][1]
        p, z = BA.project(X, C, K_of[cid])
        rows.append(dict(cam=cid, lm=li, err=float(np.linalg.norm(p-uv)), neg=bool(z <= 0)))
    d = pd.DataFrame(rows)
    rg = []
    for cid in cams:
        L, _, _ = rr.losses(tensor(np.eye(4), torch.float64), cid)
        rg.append(dict(cam=cid, M=float(L['M']), I=float(L['I']), O=float(L['O']),
                       MIO=0.25*float(L['M'])+0.35*float(L['I'])+0.35*float(L['O'])))
    rgg = pd.DataFrame(rg)
    return dict(label=label, rgb_median=float(d.err.median()), rgb_p90=float(d.err.quantile(.9)),
                rgb_p95=float(d.err.quantile(.95)), rgb_max=float(d.err.max()), n_obs=int(len(d)),
                neg_depth=int(d.neg.sum()), ring_MIO_fit=float(rgg.MIO.median()), ring_I=float(rgg.I.median()),
                ring_O=float(rgg.O.median()), ring_MIO_004=float(rgg[rgg.cam.isin(split['fit4'])].MIO.median()),
                ring_MIO_005=float(rgg[rgg.cam.isin(split['fit5'])].MIO.median())), d, rgg


def evaluate(H, dx, X, cams, K_of, obs, rr, label):
    rows = []
    for (cid, li, uv) in obs:
        C = BA.apply_cam(dx.get(cid, np.zeros(6)), cams[cid][1])
        if cams[cid][0] == '004': C = H @ C
        p, z = BA.project(X[li], C, K_of[cid])
        rows.append(dict(cam=cid, lm=li, err=float(np.linalg.norm(p-uv)), neg=bool(z <= 0)))
    d = pd.DataFrame(rows)
    ring = {}
    for cid in cams:
        C = BA.apply_cam(dx.get(cid, np.zeros(6)), cams[cid][1])
        if cams[cid][0] == '004': C = H @ C
        L, _, _ = rr.losses(tensor(np.linalg.inv(np.asarray(cams[cid][1])) @ C, torch.float64), cid)
        ring[cid] = dict(M=float(L['M']), I=float(L['I']), O=float(L['O']),
                         MIO=0.25*float(L['M'])+0.35*float(L['I'])+0.35*float(L['O']))
    rg = pd.DataFrame([dict(cam=c, **v) for c, v in ring.items()])
    return dict(label=label, rgb_median=float(d.err.median()), rgb_p90=float(d.err.quantile(.9)),
                rgb_p95=float(d.err.quantile(.95)), rgb_max=float(d.err.max()), n_obs=int(len(d)),
                neg_depth=int(d.neg.sum()), ring_MIO_fit=float(rg.MIO.median()),
                ring_I=float(rg.I.median()), ring_O=float(rg.O.median()),
                ring_MIO_004=float(rg[rg.cam.isin(split['fit4'])].MIO.median()),
                ring_MIO_005=float(rg[rg.cam.isin(split['fit5'])].MIO.median())), d, rg


def main():
    t0 = time.time()
    cams, K_of, obs, X0, rings = build()
    rr = RingRenderer(sorted(cams))
    for c in cams:
        rings[c] = {'inner': rr.data[c]['evidence']['inner'], 'outer': rr.data[c]['evidence']['outer']}
    anchor = sorted(split['fit5'])[-1]
    rows = []
    # A: W0 per-video baseline (valid model), plus the invalid "shared with H=I" variant for the record
    X4 = ident[['X004_x', 'X004_y', 'X004_z']].values; X5 = X0
    A, dA, rgA = evaluate_single(cams, K_of, obs, X4, X5, rr, 'A_W0_single')
    A_bad, _, _ = evaluate(np.eye(4), {c: np.zeros(6) for c in cams}, X5, cams, K_of, obs, rr, 'A_W0_shared_H_eq_I')
    rows.append({k: v for k, v in A.items() if k != 'cams'})
    print('A_single', round(A['rgb_median'], 2), round(A['ring_MIO_fit'], 3), ' A_shared_invalid', round(A_bad['rgb_median'], 2), flush=True)
    # B1: H only (landmarks frozen)
    BA.W_RING = 10.0
    P = BA.Problem(cams, K_of, obs, rings, X0.copy(), None,
                   dict(sig_rot=np.deg2rad(.5), sig_trans=.25, sig_geo=50.), anchor=('005', 0), freeze_edges=True)
    P.curves = rr.curves; P.H0 = np.eye(4)
    th0 = np.r_[np.zeros(6), np.zeros(6*len(P.order)), X0.ravel()]
    def res_H(t):
        return P.residuals(np.r_[t[:6], th0[6:6+6*len(P.order)], t[6:6+3*len(X0)]], np.eye(4))
    r = least_squares(res_H, np.r_[np.zeros(6), X0.ravel()], method='trf', loss='huber', f_scale=3.,
                      x_scale='jac', max_nfev=20)
    HB = exp_se3(r.x[:6]) @ np.eye(4); XB = r.x[6:].reshape(-1, 3)
    B1, dB, rgB = evaluate(HB, {c: np.zeros(6) for c in cams}, XB, cams, K_of, obs, rr, 'B1_H_only_lam10')
    rows.append({k: v for k, v in B1.items() if k != 'cams'})
    print('B1', round(B1['rgb_median'], 2), round(B1['ring_MIO_fit'], 3), flush=True)
    # C: release 004 FIT cameras (priors), H + landmarks
    C_rows = []
    Pc = BA.Problem(cams, K_of, obs, rings, X0.copy(), None,
                    dict(sig_rot=np.deg2rad(.5), sig_trans=.25, sig_geo=50.), anchor=('005', 0), freeze_edges=True)
    Pc.curves = rr.curves
    th0c = np.r_[np.zeros(6), np.zeros(6*len(Pc.order)), XB.ravel()]
    rc = least_squares(lambda t: Pc.residuals(t, np.eye(4)), th0c, method='trf', loss='huber', f_scale=3.,
                       x_scale='jac', max_nfev=20)
    HC = exp_se3(rc.x[:6]); dc = {c: rc.x[6+6*i:6+6*i+6] for i, c in enumerate(Pc.order)}; dc[anchor] = np.zeros(6)
    XC = rc.x[6+6*len(Pc.order):].reshape(-1, 3)
    C, dC, rgC = evaluate(HC, dc, XC, cams, K_of, obs, rr, 'C_BA')
    rows.append({k: v for k, v in C.items() if k != 'cams'})
    upd = []
    for c in cams:
        dd = dc.get(c, np.zeros(6))
        upd.append(dict(cam=c, video=cams[c][0], rot_deg=float(np.degrees(np.linalg.norm(dd[3:]))),
                        trans_mm=float(np.linalg.norm(dd[:3])), ring_A=float(rgA[rgA.cam == c].MIO.iloc[0]),
                        ring_C=float(rgC[rgC.cam == c].MIO.iloc[0])))
    pd.DataFrame(rows).to_csv(OUT/'ABC_EVALUATION.csv', index=False)
    pd.DataFrame(upd).to_csv(OUT/'PER_CAMERA_UPDATES.csv', index=False)
    dA.to_csv(OUT/'RGB_A.csv', index=False); dC.to_csv(OUT/'RGB_C.csv', index=False)
    json.dump(dict(n_obs=len(obs), n_cams=len(cams), n_lm=len(X0), anchor=anchor,
                   lam_ring=BA.W_RING, sig_rot_deg=0.5, sig_trans_mm=0.25,
                   B_cost=float(r.cost), C_cost=float(rc.cost), B_nfev=int(r.nfev), C_nfev=int(rc.nfev),
                   B_success=bool(r.success), C_success=bool(rc.success), seconds=round(time.time()-t0, 1)),
              open(OUT/'BA_RUN_STATE.json', 'w'), indent=1)
    print(pd.DataFrame(rows).to_string(index=False))
    print('seconds', round(time.time()-t0, 1))


if __name__ == '__main__':
    main()
