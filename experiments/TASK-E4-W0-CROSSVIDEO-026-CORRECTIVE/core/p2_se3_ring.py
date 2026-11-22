#!/usr/bin/env python3
"""P1/P2/P3: corrected Ring I/O (real centerline), SE(3) composition tests, corrected sensitivity."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, torch
WS = Path('/home/liu/ring_first_3d_workspace')
K = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-CORRECTIVE'
REP = K/'replay'; RUN26 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY/replay_020/runs'
sys.path.insert(0, str(REP)); sys.path.insert(0, str(K/'core')); sys.path.insert(0, str(WS/'src'))
os.environ.update(E4_RUN_DIR=str(REP),
    RING_CAD=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz'),
    RING_NORM=str(WS/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/inputs/G03/NORMALIZATION.json'))
from ring020_026 import RingRenderer, tensor, canonical, exp_se3


def canonical_np(T):
    T = np.asarray(T, float)
    a = -np.arctan2(T[1, 3], T[0, 3]); c, s = np.cos(a), np.sin(a)
    G = np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.]])
    return G @ T
from se3 import exp_se3 as np_exp
views = {v['id']: v for v in json.loads((REP/'config'/'VIEWS.json').read_text())}
ids = sorted(views)
W = dict(M=0.25, I=0.35, O=0.35)
WC = dict(M=0.25, I=0.35, C=0.05, O=0.35)


def raw(H, cid):
    L, aux, _ = RingRenderer.losses.__self__ if False else (None, None, None)
    rr = raw.rr
    L, aux, _ = rr.losses(tensor(np.asarray(H), torch.float64), cid)
    d = dict(M=float(L['M']), I=float(L['I']), C=float(L['C']), O=float(L['O']))
    d['MIO'] = W['M']*d['M'] + W['I']*d['I'] + W['O']*d['O']
    d['MICO'] = WC['M']*d['M'] + WC['I']*d['I'] + WC['C']*d['C'] + WC['O']*d['O']
    return d


raw.rr = RingRenderer(ids)


def main():
    rr = raw.rr
    # ---------- P1: per-view M/I/C/O with REAL centerline
    rows = []
    for cid in ids:
        d = raw(np.eye(4), cid)
        rows.append(dict(view=cid, **d))
    r0 = pd.DataFrame(rows); r0.to_csv(K/'runs/G03/RING_IO_CORRECTIVE.csv', index=False)
    print('BASELINE MIO median', round(r0.MIO.median(), 4), 'MICO median', round(r0.MICO.median(), 4),
          'C median', round(r0.C.median(), 4), flush=True)
    # ---------- P2: SE(3) composition tests (actual matrices entering the renderer)
    tests = []
    def chk(name, H_in, cid, T_expect, T_start=None, verify_loss=False):
        d = rr.data[cid]; T0 = np.asarray(d['meta']['T'], float) if T_start is None else np.asarray(T_start, float)
        actual = canonical_np(H_in @ T0)
        exp = canonical_np(T_expect)
        dR = actual[:3, :3] @ exp[:3, :3].T
        ang = float(np.degrees(np.arccos(np.clip((np.trace(dR)-1)/2, -1, 1))))
        dt = float(np.linalg.norm(actual[:3, 3]-exp[:3, 3]))
        ev = None
        if verify_loss:
            d['T'] = tensor(T0, torch.float64)
            La = rr.losses(tensor(np.asarray(H_in), torch.float64), cid)[0]
            d['T'] = tensor(exp, torch.float64)
            Lb = rr.losses(tensor(np.eye(4), torch.float64), cid)[0]
            d['T'] = tensor(np.asarray(d['meta']['T'], float), torch.float64)
            ev = float(max(abs(float(La[k])-float(Lb[k])) for k in ('M', 'I', 'C', 'O')))
        tests.append(dict(test=name, view=cid, rot_diff_deg=ang, trans_diff_mm=dt,
                          T_original=T0.tolist(), H_input=np.asarray(H_in).tolist(),
                          T_expected=exp.tolist(), T_actual=actual.tolist(),
                          matrix_diff=float(np.abs(actual-exp).max()), loss_equivalence=ev))
    cid5 = sorted([k for k in ids if k in views and views[k]['video'] == '005'])[0]
    cid4 = sorted([k for k in ids if views[k]['video'] == '004'])[0]
    T5 = np.asarray(views[cid5]['T'], float); T4 = np.asarray(views[cid4]['T'], float)
    chk('T1_identity', np.eye(4), cid5, T5, verify_loss=True)
    dt3 = np.zeros(6); dt3[:3] = [0.5, -0.3, 0.2]
    chk('T2_translation', np_exp(dt3), cid5, np_exp(dt3) @ T5, verify_loss=True)
    dr3 = np.zeros(6); dr3[3:] = np.deg2rad([0.7, -0.4, 1.1])
    chk('T3_general_rotation', np_exp(dr3), cid5, np_exp(dr3) @ T5)
    dmix = np.zeros(6); dmix[:3] = [0.3, 0.1, -0.2]; dmix[3:] = np.deg2rad([0.5, 0.2, -0.9])
    chk('T4_mixed', np_exp(dmix), cid5, np_exp(dmix) @ T5, verify_loss=True)
    Hh = np_exp(np.r_[[0.2, -0.1, 0.3], np.deg2rad([1.0, -0.5, 2.0])])
    chk('T5_bidirectional', np.linalg.inv(Hh), cid5, T5, T_start=Hh @ T5, verify_loss=True)
    chk('T6a_004_side_H', Hh, cid4, Hh @ T4)
    chk('T6b_005_side_Hinv', np.linalg.inv(Hh), cid5, np.linalg.inv(Hh) @ T5)
    # cross-check the numpy canonicalisation against the historical torch implementation
    _t0 = np.asarray(views[cid5]['T'], float)
    _d = np.abs(canonical(tensor(_t0, torch.float64)).detach().cpu().numpy() - canonical_np(_t0)).max()
    print('canonical_np vs historical canonical max diff', float(_d), flush=True)
    assert _d < 1e-12, 'canonicalisation mismatch'
    pd.DataFrame(tests).to_csv(K/'runs/G03/SE3_COMPOSITION_TESTS.csv', index=False)
    assert max(t['matrix_diff'] for t in tests) < 1e-9, 'SE3 composition mismatch'
    print('SE3 tests PASS, max matrix diff', max(t['matrix_diff'] for t in tests), flush=True)
    # ---------- P3: corrected sensitivity (world axis vs camera local)
    probe = [cid5, cid4]
    sens = []
    for cid in probe:
        T0 = np.asarray(views[cid]['T'], float)
        for axis, name in ((2, 'world_ring_axis'), (0, 'world_x_tilt'), (1, 'world_y_tilt')):
            for deg in (0.0, 1.0, 5.0, 15.0, 45.0):
                w = np.zeros(6); w[3+axis] = np.deg2rad(deg); dHw = np_exp(w)
                Tp = dHw @ T0
                d = raw(Tp @ np.linalg.inv(T0), cid)
                sens.append(dict(view=cid, frame='world', axis=name, value=deg, **d))
        for axis, name in ((2, 'local_yaw'), (0, 'local_pitch'), (1, 'local_roll')):
            for deg in (0.0, 1.0, 5.0, 15.0, 45.0):
                w = np.zeros(6); w[3+axis] = np.deg2rad(deg); dHl = np_exp(w)
                Tp = T0 @ dHl
                d = raw(Tp @ np.linalg.inv(T0), cid)
                sens.append(dict(view=cid, frame='local', axis=name, value=deg, **d))
        for axis, name in ((0, 'world_tx'), (2, 'world_tz')):
            for mm in (0.0, 0.1, 0.25, 0.5):
                w = np.zeros(6); w[axis] = mm; dHw = np_exp(w)
                Tp = dHw @ T0
                d = raw(Tp @ np.linalg.inv(T0), cid)
                sens.append(dict(view=cid, frame='world', axis=name, value=mm, **d))
    s = pd.DataFrame(sens); s.to_csv(K/'runs/G03/RING_POSE_SENSITIVITY_CORRECTED.csv', index=False)
    for name in ('world_ring_axis', 'local_yaw'):
        d = s[(s.axis == name) & (s.view == cid5)]
        print(name, [(float(v), round(float(x), 4)) for v, x in zip(d.value, d.MIO)])
    # ---------- P5: H025 re-evaluation with corrected composition
    H025 = np.load(WS/'experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/runs/G03/CONSISTENCY/H_HYPOTHESIS.npz')['H']
    split = json.loads((K/'runs/G03/SPLIT.json').read_text()) if (K/'runs/G03/SPLIT.json').exists() else json.loads((RUN26/'SPLIT.json').read_text())
    hrows = []
    for cid in ids:
        side = '004' if cid in split['fit4'] + split['ho4'] else '005'
        inc = H025 if side == '004' else np.linalg.inv(H025)
        d = raw(inc, cid)
        hrows.append(dict(view=cid, side=side, role='FIT' if (cid in split['fit4'] or cid in split['fit5']) else 'HOLDOUT', **d))
    h = pd.DataFrame(hrows); h.to_csv(K/'runs/G03/H025_REEVALUATION.csv', index=False)
    print('H025 MIO median', round(h.MIO.median(), 4), 'baseline', round(r0.MIO.median(), 4), flush=True)
    print('H025 by side', h.groupby('side').MIO.median().round(3).to_dict(), flush=True)


if __name__ == '__main__':
    main()
